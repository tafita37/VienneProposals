import json
import logging

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage
from django.core.validators import validate_email
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from authentification.decoratos import user_required
from commercial.controllers.PDFController import build_proposal_pdf
from commercial.metier.CommercialProposal import CommercialProposal

logger = logging.getLogger(__name__)

SUBJECT_MAX_LENGTH = 255


def _parse_cc(raw_cc):
    """Accepte une liste d'adresses ou une chaîne séparée par des virgules / points-virgules."""
    if raw_cc in (None, ''):
        return []
    if isinstance(raw_cc, str):
        raw_cc = raw_cc.replace(';', ',').split(',')
    if not isinstance(raw_cc, list):
        raise ValidationError('Format de copie (CC) invalide.')

    cc = []
    for address in raw_cc:
        address = str(address or '').strip()
        if address and address.lower() not in (existing.lower() for existing in cc):
            cc.append(address)
    return cc


@require_POST
@user_required
def send_proposal_mail_api(request):
    """
    Envoie par mail le PDF d'une proposition commerciale validée.

    Payload JSON attendu :
        {
            "proposal_id": 12,
            "to": "client@exemple.fr",
            "cc": ["collegue@exemple.fr"] ou "a@exemple.fr, b@exemple.fr"   (optionnel),
            "subject": "Votre proposition commerciale",
            "body": "Bonjour..."
        }
    """
    try:
        payload = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Payload JSON invalide.'}, status=400)

    if not isinstance(payload, dict):
        return JsonResponse({'success': False, 'message': 'Payload JSON invalide.'}, status=400)

    proposal_id = payload.get('proposal_id')
    if proposal_id in (None, ''):
        return JsonResponse({'success': False, 'message': 'ID de proposition manquant.'}, status=400)

    # Un commercial ne peut envoyer que ses propres propositions
    proposal = (
        CommercialProposal.objects.select_related('client', 'commercial')
        .filter(id=proposal_id, commercial=request.user)
        .first()
    ) if str(proposal_id).isdigit() else None
    if proposal is None:
        return JsonResponse({'success': False, 'message': 'Proposition introuvable.'}, status=404)

    if proposal.state != 1:
        return JsonResponse(
            {'success': False, 'message': 'Seule une proposition validée peut être envoyée.'},
            status=400,
        )

    to = str(payload.get('to', '') or '').strip()
    subject = str(payload.get('subject', '') or '').strip()
    body = str(payload.get('body', '') or '').strip()

    try:
        validate_email(to)
    except ValidationError:
        return JsonResponse({'success': False, 'message': 'Adresse du destinataire invalide.'}, status=400)

    try:
        cc = _parse_cc(payload.get('cc'))
        for address in cc:
            validate_email(address)
    except ValidationError:
        return JsonResponse({'success': False, 'message': 'Une adresse en copie (CC) est invalide.'}, status=400)
    cc = [address for address in cc if address.lower() != to.lower()]

    if not subject:
        return JsonResponse({'success': False, 'message': "L'objet du mail est obligatoire."}, status=400)
    # Un retour à la ligne dans l'objet permettrait d'injecter des en-têtes (Django lèverait BadHeaderError)
    if '\n' in subject or '\r' in subject:
        return JsonResponse({'success': False, 'message': "L'objet ne doit pas contenir de retour à la ligne."}, status=400)
    if len(subject) > SUBJECT_MAX_LENGTH:
        return JsonResponse(
            {'success': False, 'message': f"L'objet est trop long.."},
            status=400,
        )

    if not body:
        return JsonResponse({'success': False, 'message': 'Le message est obligatoire.'}, status=400)

    try:
        pdf_bytes = build_proposal_pdf(proposal, base_url=request.build_absolute_uri('/'))
    except Exception:
        logger.exception("Échec de génération du PDF pour la proposition %s", proposal.id)
        return JsonResponse({'success': False, 'message': 'Impossible de générer le PDF de la proposition.'}, status=500)

    reply_to = [proposal.commercial.email] if proposal.commercial.email else []
    message = EmailMessage(
        subject=subject,
        body=body,
        # L'expéditeur doit être une adresse vérifiée auprès du fournisseur d'envoi ;
        # les réponses du client arrivent directement chez le commercial via reply_to.
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[to],
        cc=cc,
        reply_to=reply_to,
    )
    message.attach(f"proposition_{proposal.id}.pdf", pdf_bytes, 'application/pdf')

    try:
        message.send(fail_silently=False)
    except Exception:
        logger.exception("Échec d'envoi du mail pour la proposition %s", proposal.id)
        return JsonResponse(
            {'success': False, 'message': "L'envoi du mail a échoué. Veuillez réessayer plus tard."},
            status=502,
        )

    return JsonResponse({
        'success': True,
        'message': 'La proposition a bien été envoyée.',
        'recipients': {'to': [to], 'cc': cc},
    })
