# views.py
import json
from datetime import date

from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.db import transaction

from commercial.metier.Category import Category
from commercial.metier.Client import Client
from commercial.metier.CommercialProposal import CommercialProposal
from commercial.metier.Product import Product
from commercial.metier.ProposalProduct import ProposalProduct


def _compute_proposal_total(list_proposal):
    total = 0.0

    if not isinstance(list_proposal, list):
        return total

    for item in list_proposal:
        if not isinstance(item, dict):
            continue

        product = item.get('product', {})
        product_total = 0.0

        if isinstance(product, dict):
            try:
                product_total = float(product.get('total', 0))
            except (TypeError, ValueError):
                product_total = 0.0

        if product_total <= 0:
            try:
                quantity = float(item.get('quantity', 0))
                coefficient = float(item.get('coefficient', 0))
                sale_unit_price = float(product.get('prix_unitaire_vente', 0)) if isinstance(product, dict) else 0.0
                product_total = sale_unit_price * coefficient * quantity
            except (TypeError, ValueError):
                product_total = 0.0

        total += max(0.0, product_total)

    return total

@require_GET
@login_required(login_url='login_user_page')
def catalogue_page(request):
    list_proposal = request.session.get('proposal', [])
    nom = request.GET.get('nom', '').strip()
    category_id = request.GET.get('category_id', '').strip()
    allCategory = Category.objects.all()
    allProducts = Product.objects.all()

    if nom:
        allProducts = allProducts.filter(designation__icontains=nom)

    if category_id:
        allProducts = allProducts.filter(category_id=category_id)

    proposal_by_product = {}
    if isinstance(list_proposal, list):
        for proposal_item in list_proposal:
            if not isinstance(proposal_item, dict):
                continue

            try:
                product_value = proposal_item.get('product', proposal_item.get('product_id', 0))
                if isinstance(product_value, dict):
                    product_value = product_value.get('id', product_value.get('product_id', 0))

                product_id = int(product_value)
                coefficient = float(proposal_item.get('coefficient', 0))
                quantity = float(proposal_item.get('quantity', 0))
            except (TypeError, ValueError):
                continue

            if product_id <= 0:
                continue

            proposal_by_product[product_id] = {
                'coefficient': max(0.0, coefficient),
                'quantity': max(0.0, quantity),
            }

    for product in allProducts:
        existing_value = proposal_by_product.get(product.id)
        if existing_value:
            product.catalogue_coefficient = existing_value['coefficient']
            product.catalogue_quantity = existing_value['quantity']
        else:
            product.catalogue_coefficient = float(product.coefficient)
            product.catalogue_quantity = 0.0

    return render(
        request, 
        "views/catalogue.html",
        {
            "categories": allCategory,
            "products": allProducts,
            "nom": nom,
            "category_id": category_id,
            "list_proposal": list_proposal,
        }
    )


@require_GET
@login_required(login_url='login_user_page')
def get_products_api(request):
    nom = request.GET.get('nom', '').strip()
    category_id = request.GET.get('category_id', '').strip()
    list_proposal = request.session.get('proposal', [])

    proposal_by_product = {}
    if isinstance(list_proposal, list):
        for proposal_item in list_proposal:
            if not isinstance(proposal_item, dict):
                continue

            try:
                product_value = proposal_item.get('product', proposal_item.get('product_id', 0))
                if isinstance(product_value, dict):
                    product_value = product_value.get('id', product_value.get('product_id', 0))

                product_id = int(product_value)
                coefficient = float(proposal_item.get('coefficient', 0))
                quantity = float(proposal_item.get('quantity', 0))
            except (TypeError, ValueError):
                continue

            if product_id <= 0:
                continue

            proposal_by_product[product_id] = {
                'coefficient': max(0.0, coefficient),
                'quantity': max(0.0, quantity),
            }
    
    products = Product.objects.all()
    
    if nom:
        products = products.filter(designation__icontains=nom)
    
    if category_id:
        products = products.filter(category_id=category_id)
    
    data = [
        {
            'id': p.id,
            'designation': p.designation,
            'category_id': p.category_id,
            'category_name': p.category.name,
            'unit_name': p.unit.name,
            'sale_unit_price': float(p.sale_unit_price),
            'coefficient': proposal_by_product.get(p.id, {}).get('coefficient', float(p.coefficient)),
            'quantity': proposal_by_product.get(p.id, {}).get('quantity', 0.0),
        }
        for p in products
    ]
    
    return JsonResponse({'products': data})


@require_GET
@login_required(login_url='login_user_page')
def get_client_by_id_api(request, client_id):
    client = Client.objects.filter(id=client_id).first()

    if client is None:
        return JsonResponse({'success': False, 'message': 'Client introuvable.'}, status=404)

    return JsonResponse({
        'success': True,
        'client': {
            'id': client.id,
            'name': client.name,
            'address': client.address,
            'phone': client.phone,
            'email': client.email,
            'website_url': client.website_url,
        }
    })


@require_POST
@login_required(login_url='login_user_page')
def save_selected_products_api(request):
    try:
        payload = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Payload JSON invalide.'}, status=400)

    raw_selected_products = payload.get('selected_products', [])
    if not isinstance(raw_selected_products, list):
        return JsonResponse({'success': False, 'message': 'Le champ selected_products doit être une liste.'}, status=400)

    proposal_by_product = {}

    def upsert_item(raw_item, product_key='product'):
        if not isinstance(raw_item, dict):
            return

        try:
            product_value = raw_item.get(product_key, raw_item.get('product_id', 0))
            if isinstance(product_value, dict):
                product_id = int(product_value.get('id', product_value.get('product_id', 0)))
                designation = str(product_value.get('designation', '')).strip()
                category_name = str(product_value.get('category_name', '')).strip()
                prix_unitaire_vente = float(product_value.get('prix_unitaire_vente', 0))
            else:
                product_id = int(product_value)
                designation = ''
                category_name = ''
                prix_unitaire_vente = float(raw_item.get('prix_unitaire_vente', 0))

            coefficient = float(raw_item.get('coefficient', 0))
            quantity = float(raw_item.get('quantity', 0))
        except (TypeError, ValueError, AttributeError):
            return

        if product_id <= 0 or quantity <= 0:
            return

        proposal_by_product[product_id] = {
            'product': {
                'id': product_id,
                'designation': designation,
                'category_name': category_name,
                'prix_unitaire_vente': prix_unitaire_vente,
                'total': prix_unitaire_vente * max(0.0, coefficient) * max(0.0, quantity),
            },
            'coefficient': max(0.0, coefficient),
            'quantity': max(0.0, quantity),
        }

    existing_proposal = request.session.get('proposal', [])
    if isinstance(existing_proposal, list):
        for existing_item in existing_proposal:
            if isinstance(existing_item, list):
                for nested_item in existing_item:
                    upsert_item(nested_item, product_key='product')
                continue

            upsert_item(existing_item, product_key='product')

    for item in raw_selected_products:
        if not isinstance(item, dict):
            continue

        try:
            product_id = int(item.get('product_id', item.get('product', 0)))
            coefficient = float(item.get('coefficient', 0))
            quantity = float(item.get('quantity', 0))
        except (TypeError, ValueError):
            continue

        if product_id <= 0 or quantity <= 0:
            continue

        product = Product.objects.filter(id=product_id).only('id', 'designation', 'category', 'sale_unit_price').first()
        if not product:
            continue

        proposal_by_product[product_id] = {
            'product': {
                'id': product.id,
                'designation': product.designation,
                'category_name': product.category.name,
                'prix_unitaire_vente': float(product.sale_unit_price),
                'total': float(product.sale_unit_price) * max(0.0, coefficient) * max(0.0, quantity),
            },
            'coefficient': max(0.0, coefficient),
            'quantity': max(0.0, quantity),
        }

    request.session['proposal'] = list(proposal_by_product.values())
    request.session.modified = True

    return JsonResponse({
        'success': True,
        'message': 'Produits enregistrés avec succès.',
        'proposal': request.session['proposal'],
    })


@require_POST
@login_required(login_url='login_user_page')
def remove_selected_product_api(request):
    try:
        payload = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Payload JSON invalide.'}, status=400)

    try:
        product_id = int(payload.get('product_id', 0))
    except (TypeError, ValueError):
        product_id = 0

    if product_id <= 0:
        return JsonResponse({'success': False, 'message': 'product_id invalide.'}, status=400)

    existing_proposal = request.session.get('proposal', [])
    if not isinstance(existing_proposal, list):
        existing_proposal = []

    filtered_proposal = []
    for item in existing_proposal:
        if not isinstance(item, dict):
            continue

        product = item.get('product', {})
        current_product_id = 0

        if isinstance(product, dict):
            try:
                current_product_id = int(product.get('id', 0))
            except (TypeError, ValueError):
                current_product_id = 0

        if current_product_id != product_id:
            filtered_proposal.append(item)

    request.session['proposal'] = filtered_proposal
    request.session.modified = True

    return JsonResponse({
        'success': True,
        'message': 'Produit supprimé avec succès.',
        'proposal': filtered_proposal,
        'proposal_total': _compute_proposal_total(filtered_proposal),
    })


@require_POST
@login_required(login_url='login_user_page')
def save_proposal_options_api(request):
    try:
        payload = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Payload JSON invalide.'}, status=400)

    client_id_raw = payload.get('client_id')
    date_proposition_raw = payload.get('date_proposition')

    client_id = None
    if client_id_raw not in (None, '', 0):
        try:
            client_id = int(client_id_raw)
        except (TypeError, ValueError):
            return JsonResponse({'success': False, 'message': 'client_id invalide.'}, status=400)

        if client_id <= 0:
            return JsonResponse({'success': False, 'message': 'client_id invalide.'}, status=400)

    if date_proposition_raw in (None, ''):
        date_proposition = ''
    else:
        try:
            date_proposition = str(date_proposition_raw).strip()
        except (TypeError, ValueError):
            return JsonResponse({'success': False, 'message': 'date_proposition invalide.'}, status=400)

        if len(date_proposition) != 10 or date_proposition[4] != '-' or date_proposition[7] != '-':
            return JsonResponse({'success': False, 'message': 'Format de date invalide (YYYY-MM-DD attendu).'}, status=400)

    request.session['proposal_client_id'] = client_id
    request.session['proposal_date_proposition'] = date_proposition
    request.session.modified = True

    return JsonResponse({
        'success': True,
        'message': 'Options de la proposition enregistrées avec succès.',
        'proposal_client_id': client_id,
        'proposal_date_proposition': date_proposition,
    })
    
@require_GET
@login_required(login_url='login_user_page')
@ensure_csrf_cookie
def new_proposition_page(request):
    list_proposal= request.session.get('proposal', [])
    selected_client_id_raw = request.session.get('proposal_client_id')
    try:
        selected_client_id = int(selected_client_id_raw) if selected_client_id_raw not in (None, '') else None
    except (TypeError, ValueError):
        selected_client_id = None
    proposal_date_proposition = request.session.get('proposal_date_proposition', '')
    proposal_total = 0.0
    summary_by_category = {}

    if isinstance(list_proposal, list):
        for item in list_proposal:
            if not isinstance(item, dict):
                continue

            product = item.get('product', {})
            category_name = ''
            designation = ''
            quantity = 0.0
            coefficient = 0.0
            sale_unit_price = 0.0
            product_total = 0.0

            if isinstance(product, dict):
                try:
                    category_name = str(product.get('category_name', '')).strip() or 'Non catégorisé'
                    designation = str(product.get('designation', '')).strip()
                    sale_unit_price = float(product.get('prix_unitaire_vente', 0))
                    quantity = float(item.get('quantity', 0))
                    coefficient = float(item.get('coefficient', 0))
                    product_total = float(product.get('total', 0))
                except (TypeError, ValueError):
                    product_total = 0.0

            if product_total <= 0:
                try:
                    quantity = float(item.get('quantity', 0))
                    coefficient = float(item.get('coefficient', 0))
                    sale_unit_price = float(product.get('prix_unitaire_vente', 0)) if isinstance(product, dict) else 0.0
                    product_total = sale_unit_price * coefficient * quantity
                except (TypeError, ValueError):
                    product_total = 0.0

            product_total = max(0.0, product_total)
            proposal_total += product_total

            if not category_name:
                category_name = 'Non catégorisé'

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
            })
            summary_by_category[category_name]['total'] += product_total

    summary_categories = list(summary_by_category.values())
    proposal_table_rows = []
    for category in summary_categories:
        proposal_table_rows.append({
            'is_category': True,
            'category_name': category['name'],
        })

        for item in category['items']:
            proposal_table_rows.append({
                'is_category': False,
                'designation': item['designation'],
                'quantity': item['quantity'],
                'sale_unit_price': item['sale_unit_price'],
                'coefficient': item['coefficient'],
                'total': item['total'],
            })

    allClient= Client.objects.all()
    allCategory = Category.objects.all()
    return render(
        request, 
        "views/newProposition.html", 
        {
            "clients": allClient, 
            "categories": allCategory, 
            "proposal": list_proposal,
            "selected_client_id": selected_client_id,
            "proposal_date_proposition": proposal_date_proposition,
            "proposal_total": proposal_total,
            "summary_categories": summary_categories,
            "proposal_table_rows": proposal_table_rows,
        }
    )
    
@require_GET
@login_required(login_url='login_user_page')
def appercu_proposition_page(request):
    proposal_id = request.GET.get('proposal_id', '').strip()
    client_id = request.GET.get('client_id', '').strip()
    if not client_id:
        session_client_id = request.session.get('proposal_client_id')
        client_id = str(session_client_id).strip() if session_client_id not in (None, '') else ''

    proposal_date_proposition = request.session.get('proposal_date_proposition', '')
    list_proposal = request.session.get('proposal', [])

    proposal_total = 0.0
    summary_by_category = {}

    if isinstance(list_proposal, list):
        for item in list_proposal:
            if not isinstance(item, dict):
                continue

            product = item.get('product', {})
            category_name = 'Non catégorisé'
            designation = ''
            quantity = 0.0
            coefficient = 0.0
            sale_unit_price = 0.0
            product_total = 0.0

            if isinstance(product, dict):
                try:
                    category_name = str(product.get('category_name', '')).strip() or 'Non catégorisé'
                    designation = str(product.get('designation', '')).strip()
                    quantity = float(item.get('quantity', 0))
                    coefficient = float(item.get('coefficient', 0))
                    sale_unit_price = float(product.get('prix_unitaire_vente', 0))
                    product_total = float(product.get('total', 0))
                except (TypeError, ValueError):
                    product_total = 0.0

            if product_total <= 0:
                product_total = max(0.0, sale_unit_price) * max(0.0, coefficient) * max(0.0, quantity)

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
            })
            summary_by_category[category_name]['total'] += product_total

    summary_categories = list(summary_by_category.values())
    tva_amount = proposal_total * 0.2
    total_ttc = proposal_total + tva_amount

    selected_client = None
    if client_id:
        try:
            selected_client = Client.objects.filter(id=int(client_id)).first()
        except (TypeError, ValueError):
            selected_client = None

    return render(
        request, 
        "views/preview-proposition.html",
        {
            'proposal_id': proposal_id,
            'summary_categories': summary_categories,
            'proposal_total': proposal_total,
            'tva_amount': tva_amount,
            'total_ttc': total_ttc,
            'selected_client': selected_client,
            'proposal_date_proposition': proposal_date_proposition,
        }
    )


@require_GET
@login_required(login_url='login_user_page')
def validate_proposition_page(request):
    session_proposal = request.session.get('proposal', [])
    session_client_id = request.session.get('proposal_client_id')
    session_date_proposition = request.session.get('proposal_date_proposition')

    if not isinstance(session_proposal, list) or len(session_proposal) == 0:
        return redirect('appercu_proposition_page')

    if session_client_id in (None, ''):
        return redirect('appercu_proposition_page')

    try:
        client_id = int(session_client_id)
    except (TypeError, ValueError):
        return redirect('appercu_proposition_page')

    selected_client = Client.objects.filter(id=client_id).first()
    if selected_client is None:
        return redirect('appercu_proposition_page')

    if session_date_proposition in (None, ''):
        proposal_date = date.today()
    else:
        try:
            proposal_date = date.fromisoformat(str(session_date_proposition))
        except (TypeError, ValueError):
            return redirect('appercu_proposition_page')

    amount_ht = _compute_proposal_total(session_proposal)
    amount_ttc = amount_ht * 1.2

    proposal_rows = []
    for item in session_proposal:
        if not isinstance(item, dict):
            continue

        product = item.get('product', {})

        try:
            coefficient = float(item.get('coefficient', 0))
            quantity = float(item.get('quantity', 0))
        except (TypeError, ValueError):
            continue

        if quantity <= 0:
            continue

        unit_price = 0.0
        if isinstance(product, dict):
            try:
                unit_price = float(product.get('prix_unitaire_vente', 0))
            except (TypeError, ValueError):
                unit_price = 0.0

        if unit_price <= 0 and coefficient > 0:
            try:
                computed_total = float(product.get('total', 0)) if isinstance(product, dict) else 0.0
                unit_price = computed_total / (coefficient * quantity)
            except (TypeError, ValueError, ZeroDivisionError):
                unit_price = 0.0

        proposal_rows.append({
            'coefficient': max(0.0, coefficient),
            'quantity': max(0.0, quantity),
            'unit_price': max(0.0, unit_price),
        })

    if len(proposal_rows) == 0:
        return redirect('appercu_proposition_page')

    with transaction.atomic():
        commercial_proposal = CommercialProposal.objects.create(
            date_proposal=proposal_date,
            amount_ht=amount_ht,
            amount_ttc=amount_ttc,
            client=selected_client,
        )

        ProposalProduct.objects.bulk_create([
            ProposalProduct(
                coefficient=row['coefficient'],
                quantity=row['quantity'],
                unit_price=row['unit_price'],
                commercial_proposal=commercial_proposal,
            )
            for row in proposal_rows
        ])

    for session_key in ('proposal', 'proposal_client_id', 'proposal_date_proposition'):
        if session_key in request.session:
            del request.session[session_key]
    request.session.modified = True

    return redirect('new_proposition_page')