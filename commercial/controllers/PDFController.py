import os
import io
from weasyprint import HTML, CSS
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.clickjacking import xframe_options_sameorigin
from pypdf import PdfReader, PdfWriter

from commercial.controllers.ProposalService import build_summary, multiline_items, proposal_lines, tva_amount
from commercial.metier.CommercialProposal import CommercialProposal
from proposal import settings


def build_proposal_pdf(proposal, base_url):
    """Génère le PDF complet d'une proposition (page générée + PDF annexe) et renvoie ses octets."""
    summary_categories, proposal_total = build_summary(proposal_lines(proposal))
    include_tva = float(proposal.amount_ttc or 0) > float(proposal.amount_ht or 0)
    amount_tva = tva_amount(proposal_total, include_tva)

    context = {
        'proposal': proposal,
        'summary_categories': summary_categories,
        'proposal_total': proposal_total,
        'tva_amount': amount_tva,
        'total_ttc': proposal_total + amount_tva,
        'include_tva': include_tva,
        'no_included': multiline_items(proposal.no_included),
        'cgv': multiline_items(proposal.cgv),
    }

    # Génération du PDF principal (page 1)
    html_string = render_to_string('pdf/template.html', context)
    css_path = os.path.join(settings.BASE_DIR, 'static', 'css', 'pages', 'preview-proposition.css')
    css = CSS(filename=css_path)
    main_pdf_bytes = HTML(string=html_string, base_url=base_url).write_pdf(stylesheets=[css])

    # Fusion avec le PDF existant (page 2)
    second_pdf_path = os.path.join(settings.BASE_DIR, 'static', 'pdf', 'facture_FA02015-4.pdf')  # adapte le chemin

    writer = PdfWriter()

    # Ajout de la page 1 (PDF généré)
    main_reader = PdfReader(io.BytesIO(main_pdf_bytes))
    for page in main_reader.pages:
        writer.add_page(page)

    # Ajout de la page 2 (fichier PDF existant)
    second_reader = PdfReader(second_pdf_path)
    for page in second_reader.pages:
        writer.add_page(page)

    # Numérotation de toutes les pages (PDF généré + pages ajoutées)
    # Pages générées : numéro au-dessus du footer ; pages ajoutées (CGV) : numéro plus bas
    main_pages_count = len(main_reader.pages)
    second_pages_count = len(second_reader.pages)
    overlay_html = (
        '<div class="page"></div>' * main_pages_count
        + '<div class="page annex"></div>' * second_pages_count
    )
    overlay_css = CSS(string='''
        @page {
            size: A4;
            margin: 0 0 20mm 0;
            @bottom-center {
                content: "Page " counter(page) " / " counter(pages);
                vertical-align: top;
                font-family: 'DejaVu Sans', Arial, sans-serif;
                font-size: 12px;
            }
        }
        @page annex {
            margin: 0 0 10mm 0;
        }
        .page + .page { break-before: page; }
        .annex { page: annex; }
    ''')
    overlay_bytes = HTML(string=overlay_html).write_pdf(stylesheets=[overlay_css])
    overlay_reader = PdfReader(io.BytesIO(overlay_bytes))

    for page, overlay_page in zip(writer.pages, overlay_reader.pages):
        page.merge_page(overlay_page)

    # Écriture du résultat final
    output_buffer = io.BytesIO()
    writer.write(output_buffer)
    return output_buffer.getvalue()


# SAMEORIGIN : autorise l'affichage du PDF dans l'iframe d'aperçu de l'application (DENY par défaut)
@xframe_options_sameorigin
def proposition_pdf(request, pk):
    proposal = get_object_or_404(CommercialProposal, pk=pk)
    pdf_bytes = build_proposal_pdf(proposal, base_url=request.build_absolute_uri('/'))

    # `?inline=1` permet d'afficher le PDF directement dans un aperçu (iframe) au lieu de le telecharger
    disposition = 'inline' if request.GET.get('inline') else 'attachment'

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'{disposition}; filename="proposition_{pk}.pdf"'
    return response