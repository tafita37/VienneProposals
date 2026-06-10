import os
import io
from weasyprint import HTML, CSS
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from pypdf import PdfReader, PdfWriter

from commercial.metier.CommercialProposal import CommercialProposal
from proposal import settings


def _build_summary_categories(proposal):
    proposal_total = 0.0
    summary_by_category = {}

    proposal_products = proposal.proposal_products.select_related('product').prefetch_related('product__categories').all()

    for proposal_product in proposal_products:
        product = proposal_product.product
        category_name = 'Non catégorisé'
        designation = ''
        quantity = 0.0
        coefficient = 0.0
        sale_unit_price = 0.0
        product_total = 0.0
        explanation = str(proposal_product.explanation or '').strip()

        if product is not None:
            try:
                category_name = str(product.category_names or product.category_name or '').strip() or 'Non catégorisé'
                designation = str(product.designation or '').strip()
                quantity = float(proposal_product.quantity or 0)
                coefficient = float(proposal_product.coefficient or 0)
                sale_unit_price = float(proposal_product.sale_unit_price or product.sale_unit_price or 0)
                product_total = float(proposal_product.quantity or 0) * float(proposal_product.coefficient or 0) * sale_unit_price
            except (TypeError, ValueError):
                product_total = 0.0

        product_total = max(0.0, product_total)
        proposal_total += product_total

        if category_name not in summary_by_category:
            summary_by_category[category_name] = {
                'name': category_name,
                'items': [],
                'total': 0.0,
            }

        summary_by_category[category_name]['items'].append({
            'designation': designation,
            'quantity': max(0.0, quantity),
            'sale_unit_price': max(0.0, sale_unit_price),
            'coefficient': max(0.0, coefficient),
            'total': product_total,
            'explanation': explanation,
        })
        summary_by_category[category_name]['total'] += product_total

    return list(summary_by_category.values()), proposal_total

def proposition_pdf(request, pk):
    proposal = get_object_or_404(CommercialProposal, pk=pk)
    summary_categories, proposal_total = _build_summary_categories(proposal)
    include_tva = float(proposal.amount_ttc or 0) > float(proposal.amount_ht or 0)
    tva_amount = proposal_total * 0.2 if include_tva else 0.0
    total_ttc = proposal_total + tva_amount
    no_included = proposal.no_included.replace('- ', '').split('\\n')
    cgv=proposal.cgv.replace('- ', '').split('\\n')

    context = {
        'proposal': proposal,
        'summary_categories': summary_categories,
        'proposal_total': proposal_total,
        'tva_amount': tva_amount,
        'total_ttc': total_ttc,
        'include_tva': include_tva,
        'no_included': no_included,
        'cgv': cgv,
    }

    # Génération du PDF principal (page 1)
    html_string = render_to_string('pdf/template.html', context)
    css_path = os.path.join(settings.BASE_DIR, 'static', 'css', 'pages', 'preview-proposition.css')
    css = CSS(filename=css_path)
    main_pdf_bytes = HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf(stylesheets=[css])

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

    # Écriture du résultat final
    output_buffer = io.BytesIO()
    writer.write(output_buffer)
    output_buffer.seek(0)

    response = HttpResponse(output_buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="proposition_{pk}.pdf"'
    return response