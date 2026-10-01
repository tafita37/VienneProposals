import json
from datetime import date, timedelta

from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from authentification.decoratos import admin_required, user_required
from commercial.controllers.ProposalService import (
    DEFAULT_CGV,
    DEFAULT_NO_INCLUDED,
    DEFAULT_VALIDITY_DAYS,
    TVA_RATE,
    ProposalSession,
    billable_lines,
    build_summary,
    decode_multiline,
    encode_multiline,
    lines_total,
    make_session_item,
    multiline_items,
    parse_iso_date,
    product_category_label,
    proposal_lines,
    session_item_from_line,
    session_line,
    session_lines,
    to_float,
    to_int,
    tva_amount,
)
from commercial.metier.Category import Category
from commercial.metier.Client import Client
from commercial.metier.Company import Company
from commercial.metier.CompanyType import CompanyType
from commercial.metier.CommercialProposal import CommercialProposal
from commercial.metier.Individual import Individual
from commercial.metier.Product import Product
from commercial.metier.ProposalProduct import ProposalProduct


def _json_error(message, status=400):
    return JsonResponse({'success': False, 'message': message}, status=status)


def _read_json_payload(request):
    """Renvoie (payload, None) ou (None, réponse d'erreur)."""
    try:
        return json.loads(request.body or '{}'), None
    except json.JSONDecodeError:
        return None, _json_error('Payload JSON invalide.')


def _session_lines_by_product(proposal_session):
    return {line['product_id']: line for line in proposal_session.lines if line['product_id'] > 0}


def _resolve_line_unit_price(raw_item, existing_item, product, coefficient):
    """Prix unitaire d'une ligne : saisie manuelle prioritaire, sinon prix catalogue.

    Le prix affiche vaut toujours prix unitaire x coefficient : un prix saisi a la
    main remplace donc le prix catalogue et ramene le coefficient a 1. Il reste
    conserve tant que la ligne n'est pas re-enregistree avec un coefficient.
    Retourne (prix_unitaire, coefficient, prix_modifie_manuellement).
    """
    catalog_unit_price = max(0.0, float(product.sale_unit_price))
    raw_unit_price = raw_item.get('unit_price', raw_item.get('sale_unit_price'))

    if raw_unit_price not in (None, ''):
        try:
            return max(0.0, float(raw_unit_price)), 1.0, True
        except (TypeError, ValueError):
            pass

    if existing_item.get('price_overridden') and 'coefficient' not in raw_item:
        existing_product = existing_item.get('product') or {}
        try:
            existing_unit_price = max(0.0, float(existing_product.get('sale_unit_price', catalog_unit_price)))
        except (TypeError, ValueError):
            existing_unit_price = catalog_unit_price

        return existing_unit_price, coefficient, True

    return catalog_unit_price, coefficient, False


# ────────── Catalogue et API produits / clients ──────────

@require_GET
@user_required
def catalogue_page(request):
    proposal_session = ProposalSession(request)
    nom = request.GET.get('nom', '').strip()
    category_id = request.GET.get('category_id', '').strip()
    allCategory = Category.objects.all()
    allProducts = Product.objects.select_related('unit').prefetch_related('categories').all()

    if nom:
        allProducts = allProducts.filter(designation__icontains=nom)

    if category_id:
        allProducts = allProducts.filter(categories__id=category_id).distinct()

    lines_by_product = _session_lines_by_product(proposal_session)
    for product in allProducts:
        line = lines_by_product.get(product.id)
        product.catalogue_coefficient = line['coefficient'] if line else float(product.coefficient)
        product.catalogue_quantity = line['quantity'] if line else 0.0
        product.catalogue_explanation = line['explanation'] if line else ''

    return render(
        request,
        "views/catalogue.html",
        {
            "categories": allCategory,
            "products": allProducts,
            "nom": nom,
            "category_id": category_id,
            "list_proposal": proposal_session.items,
        }
    )

@require_GET
@user_required
def get_product_by_id_api(request):
    product_id = request.GET.get('product_id')

    try:
        product_id = int(product_id)
    except (TypeError, ValueError):
        return JsonResponse({'success': False, 'message': 'product_id invalide.'}, status=400)

    # Récupération du produit avec ses relations
    product = Product.objects.filter(id=product_id).select_related('unit').prefetch_related('categories').first()

    if product is None:
        return JsonResponse({'success': False, 'message': 'Produit introuvable.'}, status=404)

    # On sérialise (transforme en dictionnaire) manuellement le produit et ses relations
    product_data = {
        'id': product.id,
        'designation': product.designation, # Remplace par tes vrais noms de champs
        'purchase_unit_price' : float(product.purchase_unit_price),
        'sale_unit_price' : float(product.sale_unit_price),
        'coefficient' : float(product.coefficient),
        'unit': product.unit.name if product.unit else None,
        'categories': [cat.name for cat in product.categories.all()],
        'explanation': product.explanation,
    }

    return JsonResponse({'success': True, 'product': product_data})

@require_GET
@user_required
def get_products_api(request):
    nom = request.GET.get('nom', '').strip()
    category_id = request.GET.get('category_id', '').strip()
    lines_by_product = _session_lines_by_product(ProposalSession(request))

    products = Product.objects.select_related('unit').prefetch_related('categories').all()

    if nom:
        products = products.filter(designation__icontains=nom)

    if category_id:
        products = products.filter(categories__id=category_id).distinct()

    data = [
        {
            'id': p.id,
            'designation': p.designation,
            'category_id': p.category_id,
            'category_ids': p.category_ids,
            'category_name': product_category_label(p),
            'unit_name': p.unit.name,
            'sale_unit_price': float(p.sale_unit_price),
            'coefficient': lines_by_product[p.id]['coefficient'] if p.id in lines_by_product else float(p.coefficient),
            'quantity': lines_by_product[p.id]['quantity'] if p.id in lines_by_product else 0.0,
        }
        for p in products
    ]

    return JsonResponse({'products': data})


@require_GET
@user_required
def get_client_by_id_api(request, client_id):
    client = Client.objects.filter(id=client_id).first()

    if client is None:
        return JsonResponse({'success': False, 'message': 'Client introuvable.'}, status=404)

    company = None
    individual = None
    if client.is_company:
        company = Company.objects.select_related('company_type').filter(client_id=client.id).order_by('-id').first()
    else:
        individual = Individual.objects.filter(client_id=client.id).order_by('-id').first()

    return JsonResponse({
        'success': True,
        'client': {
            'id': client.id,
            'name': client.name,
            'address': client.address,
            'phone': client.phone,
            'email': client.email,
            'website_url': client.website_url,
            'is_company': bool(client.is_company),
            'client_type': 'BtoB' if client.is_company else 'BtoC',
            'company': {
                'name': company.name if company is not None else '',
                'company_type_id': company.company_type_id if company is not None else None,
                'company_type': company.company_type.name if company is not None and company.company_type is not None else '',
                'registration_number': company.registration_number if company is not None else '',
                'tax_identification_number': company.tax_identification_number if company is not None else '',
                'created_at': company.created_at.isoformat() if company is not None and company.created_at is not None else '',
            },
            'individual': {
                'first_name': individual.first_name if individual is not None else '',
                'last_name': individual.last_name if individual is not None else '',
                'birth_date': individual.birth_date.isoformat() if individual is not None and individual.birth_date is not None else '',
                'id_card_number': individual.id_card_number if individual is not None else '',
            },
        }
    })


@require_POST
@user_required
def update_client_from_proposal_api(request):
    try:
        payload = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Payload JSON invalide.'}, status=400)

    client_id = payload.get('client_id')
    if client_id in (None, ''):
        return JsonResponse({'success': False, 'message': 'client_id manquant.'}, status=400)

    client = Client.objects.filter(id=client_id).first()
    if client is None:
        return JsonResponse({'success': False, 'message': 'Client introuvable.'}, status=404)

    address = str(payload.get('address', '') or '').strip()
    phone = str(payload.get('phone', '') or '').strip()
    email = str(payload.get('email', '') or '').strip()
    website_url = str(payload.get('website_url', '') or '').strip()

    if not address or not phone or not email:
        return JsonResponse({'success': False, 'message': 'Adresse, téléphone et email sont obligatoires.'}, status=400)

    client.address = address
    client.phone = phone
    client.email = email
    client.website_url = website_url

    if client.is_company:
        company = Company.objects.select_related('company_type').filter(client_id=client.id).first()
        if company is None:
            return JsonResponse({'success': False, 'message': 'Dossier société introuvable.'}, status=404)

        company_name = str(payload.get('company_name', '') or '').strip()
        company_type_id = payload.get('company_type_id')
        registration_number = str(payload.get('registration_number', '') or '').strip()
        tax_identification_number = str(payload.get('tax_identification_number', '') or '').strip()
        created_at = str(payload.get('created_at', '') or '').strip()

        if not company_name or not company_type_id or not registration_number or not tax_identification_number or not created_at:
            return JsonResponse({'success': False, 'message': 'Toutes les informations société sont obligatoires.'}, status=400)

        company_type = CompanyType.objects.filter(id=company_type_id).first()
        if company_type is None:
            return JsonResponse({'success': False, 'message': "Type d'entreprise invalide."}, status=400)

        company.name = company_name
        company.company_type = company_type
        company.registration_number = registration_number
        company.tax_identification_number = tax_identification_number
        company.created_at = created_at
        company.save()

        client.name = company_name
    else:
        individual = Individual.objects.filter(client_id=client.id).first()
        if individual is None:
            return JsonResponse({'success': False, 'message': 'Dossier personne physique introuvable.'}, status=404)

        first_name = str(payload.get('first_name', '') or '').strip()
        last_name = str(payload.get('last_name', '') or '').strip()
        birth_date = str(payload.get('birth_date', '') or '').strip()
        id_card_number = str(payload.get('id_card_number', '') or '').strip()

        if not first_name or not last_name or not birth_date or not id_card_number:
            return JsonResponse({'success': False, 'message': 'Toutes les informations personne physique sont obligatoires.'}, status=400)

        individual.first_name = first_name
        individual.last_name = last_name
        individual.birth_date = birth_date
        individual.id_card_number = id_card_number
        individual.save()

        client.name = f'{first_name} {last_name}'.strip()

    client.save()
    return JsonResponse({'success': True, 'message': 'Client mis à jour avec succès.'})


@require_GET
@user_required
def new_client_user_page(request):
    all_company_types = CompanyType.objects.all()
    return render(
        request,
        'views/newClientUser.html',
        {'company_types': all_company_types}
    )


@require_POST
@user_required
def save_client_user(request):
    address = request.POST.get('address')
    email = request.POST.get('email')
    website_url = request.POST.get('website_url') or None
    phone = request.POST.get('phone')
    is_company = bool(int(request.POST.get('is_company')))

    first_name = request.POST.get('first_name')
    last_name = request.POST.get('last_name')
    birth_date = request.POST.get('birth_date')
    id_card_number = request.POST.get('id_card_number')

    company_name = request.POST.get('company_name')
    company_type = request.POST.get('company_type')
    registration_number = request.POST.get('registration_number')
    tax_identification_number = request.POST.get('tax_identification_number')
    created_at = request.POST.get('created_at')

    name = company_name if is_company else f"{first_name} {last_name}"

    client_data = {
        'name': name,
        'address': address,
        'email': email,
        'website_url': website_url,
        'phone': phone
    }

    created_client_id = None
    if is_company:
        company = Company(
            name=company_name,
            registration_number=registration_number,
            tax_identification_number=tax_identification_number,
            created_at=created_at,
            company_type_id=CompanyType(id=company_type)
        )
        company.save(client_data=client_data)
        created_client_id = company.client_id
    else:
        individual = Individual(
            first_name=first_name,
            last_name=last_name,
            birth_date=birth_date,
            id_card_number=id_card_number
        )
        individual.save(client_data=client_data)
        created_client_id = individual.client_id

    if created_client_id:
        ProposalSession(request).set('client_id', created_client_id)

    return redirect('new_proposition_page')

@require_POST
@admin_required
def save_explanation_product_admin_api(request) :
    try:
        payload = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Payload JSON invalide.'}, status=400)

    product_id = payload.get('product_id')
    explanation = str(payload.get('explanation', '') or '').strip()

    if product_id in (None, ''):
        return JsonResponse({'success': False, 'message': 'product_id manquant.'}, status=400)

    try:
        product_id = int(product_id)
    except (TypeError, ValueError):
        return JsonResponse({'success': False, 'message': 'product_id invalide.'}, status=400)

    product = Product.objects.filter(id=product_id).first()
    if product is None:
        return JsonResponse({'success': False, 'message': 'Produit introuvable.'}, status=404)

    product.explanation = explanation
    product.save(update_fields=['explanation'])

    return JsonResponse({'success': True, 'message': 'Explication du produit mise à jour avec succès.'})


# ────────── Proposition en cours de saisie : logique commune création / modification ──────────

def _save_selected_products(request, edit):
    """Ajoute ou met à jour des produits dans la proposition en session."""
    payload, error = _read_json_payload(request)
    if error:
        return error

    raw_selected_products = payload.get('selected_products', [])
    if not isinstance(raw_selected_products, list):
        return _json_error('Le champ selected_products doit être une liste.')

    proposal_session = ProposalSession(request, edit)
    items_by_product = {
        line['product_id']: session_item_from_line(line)
        for line in proposal_session.lines
        if line['product_id'] > 0 and line['quantity'] > 0
    }

    selected_items = [item for item in raw_selected_products if isinstance(item, dict)]
    products_by_id = Product.objects.select_related('unit').prefetch_related('categories').in_bulk(
        [to_int(item.get('product_id', item.get('product', 0))) for item in selected_items]
    )

    for item in selected_items:
        product_id = to_int(item.get('product_id', item.get('product', 0)))
        existing_item = items_by_product.get(product_id, {})
        coefficient = to_float(item.get('coefficient', existing_item.get('coefficient', 0)), default=None)
        quantity = to_float(item.get('quantity', existing_item.get('quantity', 0)), default=None)

        if coefficient is None or quantity is None or product_id <= 0 or quantity <= 0:
            continue

        product = products_by_id.get(product_id)
        if product is None:
            continue

        sale_unit_price, coefficient, price_overridden = _resolve_line_unit_price(
            item, existing_item, product, coefficient
        )
        items_by_product[product_id] = make_session_item(
            product_id=product.id,
            designation=product.designation,
            unit=product.unit.name,
            category_name=product_category_label(product),
            sale_unit_price=sale_unit_price,
            purchase_unit_price=float(product.purchase_unit_price),
            coefficient=coefficient,
            quantity=quantity,
            explanation=str(item.get('explanation', existing_item.get('explanation', '')) or '').strip(),
            price_overridden=price_overridden,
        )

    proposal_session.items = list(items_by_product.values())

    return JsonResponse({
        'success': True,
        'message': 'Produits enregistrés avec succès.',
        'proposal': proposal_session.items,
    })


def _remove_selected_product(request, edit):
    """Retire un produit de la proposition en session."""
    payload, error = _read_json_payload(request)
    if error:
        return error

    product_id = to_int(payload.get('product_id', 0))
    if product_id <= 0:
        return _json_error('product_id invalide.')

    proposal_session = ProposalSession(request, edit)
    remaining_items = []
    for item in proposal_session.items:
        line = session_line(item)
        if line is not None and line['product_id'] != product_id:
            remaining_items.append(item)

    proposal_session.items = remaining_items

    return JsonResponse({
        'success': True,
        'message': 'Produit supprimé avec succès.',
        'proposal': remaining_items,
        'proposal_total': lines_total(session_lines(remaining_items)),
    })


def _clean_iso_date_input(raw_value, format_error_message):
    """Valide une date saisie au format YYYY-MM-DD. Renvoie (valeur, message d'erreur)."""
    if raw_value in (None, ''):
        return '', None

    value = str(raw_value).strip()
    if len(value) != 10 or value[4] != '-' or value[7] != '-':
        return None, format_error_message
    return value, None


def _save_proposal_options(request, edit):
    """Enregistre en session les informations générales de la proposition (client, dates, TVA, textes)."""
    payload, error = _read_json_payload(request)
    if error:
        return error

    client_id = None
    client_id_raw = payload.get('client_id')
    if client_id_raw not in (None, '', 0):
        client_id = to_int(client_id_raw)
        if client_id <= 0:
            return _json_error('client_id invalide.')

    date_proposition, error_message = _clean_iso_date_input(
        payload.get('date_proposition'), 'Format de date invalide (YYYY-MM-DD attendu).'
    )
    if error_message:
        return _json_error(error_message)

    expiration_date, error_message = _clean_iso_date_input(
        payload.get('expiration_date'), "Format de date d'expiration invalide (YYYY-MM-DD attendu)."
    )
    if error_message:
        return _json_error(error_message)

    base_date = date.today()
    if date_proposition:
        base_date = parse_iso_date(date_proposition)
        if base_date is None:
            return _json_error('date_proposition invalide.')

    if not expiration_date:
        expiration_date = (base_date + timedelta(days=DEFAULT_VALIDITY_DAYS)).isoformat()
    else:
        parsed_expiration_date = parse_iso_date(expiration_date)
        if parsed_expiration_date is None:
            return _json_error('expiration_date invalide.')
        if parsed_expiration_date < base_date:
            return _json_error("La date d'expiration ne peut pas être antérieure à la date de proposition.")

    include_tax_raw = payload.get('include_tax')
    if isinstance(include_tax_raw, bool):
        include_tax = include_tax_raw
    elif include_tax_raw is not None:
        include_tax = str(include_tax_raw).strip().lower() in ('1', 'true', 'yes', 'on')
    else:
        include_tax = True

    project_name = payload.get('project_name')
    installation_address = payload.get('installation_address')

    proposal_session = ProposalSession(request, edit)
    proposal_session.set('client_id', client_id)
    proposal_session.set('date_proposition', date_proposition)
    proposal_session.set('expiration_date', expiration_date)
    proposal_session.set('include_tva', include_tax)
    proposal_session.set('project_name', project_name.strip() if isinstance(project_name, str) else '')
    proposal_session.set('installation_address', installation_address.strip() if isinstance(installation_address, str) else '')
    proposal_session.set('no_included', encode_multiline(payload.get('no_included')))
    proposal_session.set('cgv', encode_multiline(payload.get('cgv')))

    return JsonResponse({
        'success': True,
        'message': 'Options de la proposition enregistrées avec succès.',
        'proposal_client_id': client_id,
        'proposal_date_proposition': date_proposition,
        'proposal_expiration_date': expiration_date,
        'proposal_include_tva': include_tax,
    })


def _render_proposal_form(request, edit):
    """Page de saisie d'une proposition (création ou modification d'un brouillon)."""
    proposal_session = ProposalSession(request, edit)
    summary_categories, proposal_total = build_summary(proposal_session.lines)

    no_included = decode_multiline(proposal_session.get('no_included'))
    cgv = decode_multiline(proposal_session.get('cgv'))
    if not edit:
        no_included = no_included or DEFAULT_NO_INCLUDED
        cgv = cgv or DEFAULT_CGV

    url_suffix = '_edit' if edit else ''
    api_urls = {
        'selected_products': reverse(f'save_selected_products{url_suffix}_api'),
        'remove_product': reverse(f'remove_selected_product{url_suffix}_api'),
        'options': reverse(f'save_proposal_options{url_suffix}_api'),
        'preview': reverse(proposal_session.preview_url_name),
    }

    return render(
        request,
        "views/proposition_form.html",
        {
            "is_edit": edit,
            "clients": Client.objects.all(),
            "categories": Category.objects.all(),
            "proposal": proposal_session.items,
            "selected_client_id": proposal_session.client_id,
            "proposal_date_proposition": proposal_session.proposal_date.isoformat(),
            "proposal_expiration_date": proposal_session.expiration_date.isoformat(),
            "proposal_include_tva": proposal_session.include_tva,
            "proposal_total": proposal_total,
            "summary_categories": summary_categories,
            "proposal_project_name": proposal_session.get('project_name', ''),
            "proposal_installation_address": proposal_session.get('installation_address', ''),
            "no_included": no_included,
            "cgv": cgv,
            "preview_url_name": proposal_session.preview_url_name,
            "api_urls": api_urls,
        }
    )


def _render_proposal_preview(request, edit):
    """Aperçu du document de la proposition en session, avant enregistrement."""
    proposal_session = ProposalSession(request, edit)
    summary_categories, amount_ht = build_summary(proposal_session.lines)
    amount_tva = tva_amount(amount_ht, proposal_session.include_tva)
    client_id = proposal_session.client_id

    return render(
        request,
        "views/preview-proposition.html",
        {
            'is_edit': edit,
            'draft_id': proposal_session.draft_id,
            'doc_date': proposal_session.proposal_date,
            'commercial': request.user,
            'proposal_number': proposal_session.get('commercial_proposal_number', '') if edit else '',
            'client': Client.objects.filter(id=client_id).first() if client_id else None,
            'project_name': proposal_session.get('project_name', ''),
            'installation_address': proposal_session.get('installation_address', ''),
            'summary_categories': summary_categories,
            'amount_ht': amount_ht,
            'tva_amount': amount_tva,
            'amount_ttc': amount_ht + amount_tva,
            'no_included': multiline_items(proposal_session.get('no_included')),
            'cgv': multiline_items(proposal_session.get('cgv')),
        }
    )


def _finalize_proposal(request, edit, state, success_redirect_name):
    """Enregistre en base la proposition en session (brouillon si state=0, validée si state=1)."""
    proposal_session = ProposalSession(request, edit)
    back_to_preview = redirect(proposal_session.preview_url_name)

    lines = billable_lines(proposal_session.items)
    if not lines:
        return back_to_preview

    client_id = proposal_session.client_id
    selected_client = Client.objects.filter(id=client_id).first() if client_id else None
    if selected_client is None:
        return back_to_preview

    amount_ht = lines_total(lines)
    amount_ttc = amount_ht * (1 + TVA_RATE) if proposal_session.include_tva else amount_ht
    proposal_fields = {
        'date_proposal': proposal_session.proposal_date,
        'expiration_date': proposal_session.expiration_date,
        'amount_ht': amount_ht,
        'amount_ttc': amount_ttc,
        'client': selected_client,
        'commercial': request.user,
        'state': state,
        'project_name': proposal_session.get('project_name', ''),
        'installation_address': proposal_session.get('installation_address', ''),
        'no_included': proposal_session.get('no_included', ''),
        'cgv': proposal_session.get('cgv', ''),
    }
    products_by_id = Product.objects.in_bulk([line['product_id'] for line in lines if line['product_id'] > 0])

    with transaction.atomic():
        commercial_proposal = None
        if proposal_session.draft_id:
            commercial_proposal = CommercialProposal.objects.filter(
                id=proposal_session.draft_id, commercial=request.user
            ).first()

        if commercial_proposal is None:
            commercial_proposal = CommercialProposal.objects.create(**proposal_fields)
        else:
            for field_name, value in proposal_fields.items():
                setattr(commercial_proposal, field_name, value)
            commercial_proposal.save(update_fields=list(proposal_fields))
            commercial_proposal.proposal_products.all().delete()

        ProposalProduct.objects.bulk_create([
            ProposalProduct(
                coefficient=line['coefficient'],
                quantity=line['quantity'],
                sale_unit_price=line['sale_unit_price'],
                purchase_unit_price=line['purchase_unit_price'],
                commercial_proposal=commercial_proposal,
                product=products_by_id.get(line['product_id']),
                explanation=line['explanation'],
            )
            for line in lines
        ])

    proposal_session.clear()

    if state == 0:
        messages.success(request, 'Brouillon enregistré avec succès.')
    else:
        messages.success(request, 'Proposition validée avec succès.')

    return redirect(success_redirect_name)


# ────────── Création d'une proposition ──────────

@require_GET
@user_required
@ensure_csrf_cookie
def new_proposition_page(request):
    return _render_proposal_form(request, edit=False)

@require_POST
@user_required
def save_selected_products_api(request):
    return _save_selected_products(request, edit=False)

@require_POST
@user_required
def remove_selected_product_api(request):
    return _remove_selected_product(request, edit=False)

@require_POST
@user_required
def save_proposal_options_api(request):
    return _save_proposal_options(request, edit=False)

@require_GET
@user_required
def appercu_proposition_page(request):
    return _render_proposal_preview(request, edit=False)

@require_POST
@user_required
def save_draft_proposition_page(request):
    return _finalize_proposal(request, edit=False, state=0, success_redirect_name='propositions_page')

@require_GET
@user_required
def validate_proposition_page(request):
    return _finalize_proposal(request, edit=False, state=1, success_redirect_name='new_proposition_page')


# ────────── Modification d'un brouillon ──────────

@require_GET
@user_required
@ensure_csrf_cookie
def edit_draft_proposition_page(request):
    proposal_id = request.GET.get('proposal_id', '').strip()
    if not proposal_id.isdigit():
        return redirect('propositions_page')

    commercial_proposal = CommercialProposal.objects.filter(id=proposal_id, commercial=request.user).first()
    if commercial_proposal is None or commercial_proposal.state == 1:
        return redirect('propositions_page')

    # On ne recharge depuis la base que si un autre brouillon était en cours de modification
    if str(request.session.get(ProposalSession.DRAFT_ID_KEY, '') or '') != proposal_id:
        ProposalSession(request, edit=True).load_from_proposal(commercial_proposal)

    return _render_proposal_form(request, edit=True)

@require_POST
@user_required
def save_selected_products_edit_api(request):
    return _save_selected_products(request, edit=True)

@require_POST
@user_required
def remove_selected_product_edit_api(request):
    return _remove_selected_product(request, edit=True)

@require_POST
@user_required
def save_proposal_options_edit_api(request):
    return _save_proposal_options(request, edit=True)

@require_GET
@user_required
def appercu_proposition_page_edit(request):
    return _render_proposal_preview(request, edit=True)

@require_POST
@user_required
def save_draft_proposition_edit_page(request):
    return _finalize_proposal(request, edit=True, state=0, success_redirect_name='propositions_page')

@require_GET
@user_required
def validate_proposition_edit_page(request):
    return _finalize_proposal(request, edit=True, state=1, success_redirect_name='new_proposition_page')


# ────────── Propositions enregistrées ──────────

@require_GET
@user_required
def propositions_page(request):
    client_id= request.GET.get('client_id', '').strip()
    if client_id:
        client_id_int = int(client_id)
        all_proposals = CommercialProposal.objects.filter(client_id=client_id_int, commercial=request.user)
    else:
        all_proposals = CommercialProposal.objects.filter(commercial=request.user)
    all_clients=Client.objects.all()

    return render(
        request,
        "views/propositions.html",
        {
            'proposals': all_proposals,
            'clients': all_clients
        }
    )

@require_GET
@user_required
def proposition_detail(request):
    proposal_id = request.GET.get('proposal_id', '').strip()

    commercial_proposal = (
        CommercialProposal.objects.select_related('client', 'commercial').filter(id=proposal_id).first()
        if proposal_id.isdigit() else None
    )
    if commercial_proposal is None:
        return redirect('propositions_page')

    summary_categories, _ = build_summary(proposal_lines(commercial_proposal))
    amount_ht = float(commercial_proposal.amount_ht or 0)
    amount_ttc = float(commercial_proposal.amount_ttc or 0)

    return render(
        request,
        "views/proposition_detail.html",
        {
            'proposal': commercial_proposal,
            'doc_date': commercial_proposal.date_proposal,
            'commercial': commercial_proposal.commercial,
            'ref_chantier': f'VA 2600{commercial_proposal.id} ANN',
            'proposal_number': commercial_proposal.commercial_proposal_number,
            'client': commercial_proposal.client,
            'project_name': commercial_proposal.project_name,
            'installation_address': commercial_proposal.installation_address,
            'summary_categories': summary_categories,
            'amount_ht': amount_ht,
            'tva_amount': max(0.0, amount_ttc - amount_ht),
            'amount_ttc': amount_ttc,
            'no_included': multiline_items(commercial_proposal.no_included),
            'cgv': multiline_items(commercial_proposal.cgv),
        }
    )

@require_GET
@user_required
def send_proposal_mail_page(request):
    """Interface de rédaction du mail d'envoi d'une proposition commerciale."""
    proposal_id = request.GET.get('proposal_id', '').strip()

    # Mêmes règles que l'API d'envoi : uniquement les propositions validées du commercial connecté
    proposal = (
        CommercialProposal.objects.select_related('client', 'commercial')
        .filter(id=proposal_id, commercial=request.user, state=1)
        .first()
    ) if proposal_id.isdigit() else None
    if proposal is None:
        return redirect('propositions_page')

    client = proposal.client
    commercial = proposal.commercial

    sender_name = f"{commercial.first_name or ''} {commercial.last_name or ''}".strip() or commercial.username
    proposal_reference = f"PROP-2026-{proposal.id}"

    default_subject = f"Votre proposition commerciale {proposal_reference} - Vienne Agencement"
    default_body = (
        f"Bonjour {client.name},\n\n"
        "Nous vous remercions pour la confiance que vous accordez à Vienne Agencement.\n\n"
        f"Vous trouverez en pièce jointe la proposition commerciale {proposal_reference}"
        f"{' concernant le projet « ' + proposal.project_name + ' »' if proposal.project_name else ''}, "
        f"pour un montant de {float(proposal.amount_ttc or 0):.2f} € TTC.\n\n"
        "Cette proposition reste valable jusqu'au "
        f"{proposal.expiration_date.strftime('%d/%m/%Y') if proposal.expiration_date else '—'}.\n\n"
        "Nous restons à votre entière disposition pour toute précision ou ajustement.\n\n"
        "Bien cordialement,\n"
        f"{sender_name}\n"
        "Vienne Agencement"
    )

    return render(
        request,
        "views/send_proposal_mail.html",
        {
            'proposal': proposal,
            'client': client,
            'sender_name': sender_name,
            'sender_email': commercial.email,
            'proposal_reference': proposal_reference,
            'default_subject': default_subject,
            'default_body': default_body,
        }
    )
