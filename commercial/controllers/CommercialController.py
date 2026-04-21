# views.py
import json
from datetime import date, timedelta

from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_POST
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.db import transaction

from authentification.decoratos import user_required
from commercial.metier.Category import Category
from commercial.metier.Client import Client
from commercial.metier.CommercialProposal import CommercialProposal
from commercial.metier.Product import Product
from commercial.metier.ProposalProduct import ProposalProduct


def _product_category_label(product):
    if product is None:
        return 'Non catégorisé'

    category_names = getattr(product, 'category_names', '')
    if category_names:
        return category_names

    category = getattr(product, 'category', None)
    if category is not None and getattr(category, 'name', ''):
        return category.name

    return 'Non catégorisé'


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
                sale_unit_price = 0.0
                if isinstance(product, dict):
                    sale_unit_price = float(
                        product.get('sale_unit_price', product.get('prix_unitaire_vente', 0))
                    )
                product_total = sale_unit_price * coefficient * quantity
            except (TypeError, ValueError):
                product_total = 0.0

        total += max(0.0, product_total)

    return total


def _proposal_item_from_proposal_product(proposal_product):
    product = getattr(proposal_product, 'product', None)
    sale_unit_price = max(0.0, float(getattr(proposal_product, 'sale_unit_price', 0) or 0))
    purchase_unit_price = max(0.0, float(getattr(proposal_product, 'purchase_unit_price', 0) or 0))
    coefficient = max(0.0, float(getattr(proposal_product, 'coefficient', 0) or 0))
    quantity = max(0.0, float(getattr(proposal_product, 'quantity', 0) or 0))
    product_id = 0
    designation = ''
    category_name = 'Non catégorisé'

    if product is not None:
        try:
            product_id = int(getattr(product, 'id', 0) or 0)
        except (TypeError, ValueError):
            product_id = 0

        designation = str(getattr(product, 'designation', '') or '').strip()
        category_name = _product_category_label(product)

    if not designation:
        designation = f'Produit {getattr(proposal_product, "id", 0)}'

    return {
        'product': {
            'id': product_id,
            'designation': designation,
            'category_name': category_name,
            'sale_unit_price': sale_unit_price,
            'purchase_unit_price': purchase_unit_price,
            'prix_unitaire_vente': sale_unit_price,
            'prix_unitaire_achat': purchase_unit_price,
            'total': sale_unit_price * coefficient * quantity,
        },
        'coefficient': coefficient,
        'quantity': quantity,
    }


def _proposal_rows_from_session(session_proposal):
    proposal_rows = []

    if not isinstance(session_proposal, list):
        return proposal_rows

    for item in session_proposal:
        if not isinstance(item, dict):
            continue

        product = item.get('product', {})

        try:
            coefficient = float(item.get('coefficient', 0))
            quantity = float(item.get('quantity', 0))
            product_id = int(product.get('id', 0)) if isinstance(product, dict) else 0
        except (TypeError, ValueError):
            continue

        if quantity <= 0:
            continue

        sale_unit_price = 0.0
        purchase_unit_price = 0.0
        if isinstance(product, dict):
            try:
                sale_unit_price = float(product.get('sale_unit_price', product.get('prix_unitaire_vente', 0)))
                purchase_unit_price = float(product.get('purchase_unit_price', product.get('prix_unitaire_achat', 0)))
            except (TypeError, ValueError):
                sale_unit_price = 0.0
                purchase_unit_price = 0.0

        if sale_unit_price <= 0 and coefficient > 0:
            try:
                computed_total = float(product.get('total', 0)) if isinstance(product, dict) else 0.0
                sale_unit_price = computed_total / (coefficient * quantity)
            except (TypeError, ValueError, ZeroDivisionError):
                sale_unit_price = 0.0

        if purchase_unit_price < 0:
            purchase_unit_price = 0.0

        proposal_rows.append({
            'coefficient': max(0.0, coefficient),
            'quantity': max(0.0, quantity),
            'sale_unit_price': max(0.0, sale_unit_price),
            'purchase_unit_price': max(0.0, purchase_unit_price),
            'product_id': product_id if product_id > 0 else None,
        })

    return proposal_rows


def _finalize_proposal_from_session(request, state, success_redirect_name):
    session_proposal = request.session.get('proposal', [])
    session_client_id = request.session.get('proposal_client_id')
    session_date_proposition = request.session.get('proposal_date_proposition')
    session_include_tva = request.session.get('proposal_include_tva', True)
    draft_id_raw = request.session.get('proposal_draft_id')

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

    proposal_rows = _proposal_rows_from_session(session_proposal)
    if len(proposal_rows) == 0:
        return redirect('appercu_proposition_page')

    include_tva = bool(session_include_tva)
    amount_ht = _compute_proposal_total(session_proposal)
    amount_ttc = amount_ht * 1.2 if include_tva else amount_ht

    product_ids = [row['product_id'] for row in proposal_rows if row['product_id'] is not None]
    products_by_id = {
        product.id: product
        for product in Product.objects.filter(id__in=product_ids).select_related('unit').prefetch_related('categories')
    }

    with transaction.atomic():
        commercial_proposal = None
        if draft_id_raw not in (None, ''):
            try:
                draft_id = int(draft_id_raw)
            except (TypeError, ValueError):
                draft_id = 0

            if draft_id > 0:
                commercial_proposal = CommercialProposal.objects.filter(id=draft_id, commercial=request.user).first()

        if commercial_proposal is not None:
            commercial_proposal.date_proposal = proposal_date
            commercial_proposal.amount_ht = amount_ht
            commercial_proposal.amount_ttc = amount_ttc
            commercial_proposal.client = selected_client
            commercial_proposal.commercial = request.user
            commercial_proposal.state = state
            commercial_proposal.save(update_fields=['date_proposal', 'amount_ht', 'amount_ttc', 'client', 'commercial', 'state'])
            commercial_proposal.proposal_products.all().delete()
        else:
            commercial_proposal = CommercialProposal.objects.create(
                date_proposal=proposal_date,
                amount_ht=amount_ht,
                amount_ttc=amount_ttc,
                client=selected_client,
                commercial=request.user,
                state=state,
                validity_period=30,
            )

        proposal_product_objects = []
        for row in proposal_rows:
            product_obj = products_by_id.get(row['product_id']) if row['product_id'] is not None else None
            proposal_product_objects.append(
                ProposalProduct(
                    coefficient=row['coefficient'],
                    quantity=row['quantity'],
                    sale_unit_price=row['sale_unit_price'],
                    purchase_unit_price=row['purchase_unit_price'],
                    commercial_proposal=commercial_proposal,
                    product=product_obj,
                )
            )

        ProposalProduct.objects.bulk_create(proposal_product_objects)

    for session_key in ('proposal', 'proposal_client_id', 'proposal_date_proposition', 'proposal_include_tva', 'proposal_draft_id'):
        if session_key in request.session:
            del request.session[session_key]
    request.session.modified = True

    if state == 0:
        messages.success(request, 'Brouillon enregistré avec succès.')
    else:
        messages.success(request, 'Proposition validée avec succès.')

    return redirect(success_redirect_name)


def _build_session_from_draft(request, commercial_proposal):
    proposal_items = []

    proposal_products = commercial_proposal.proposal_products.select_related('product').prefetch_related('product__categories').all()
    for proposal_product in proposal_products:
        proposal_items.append(_proposal_item_from_proposal_product(proposal_product))

    request.session['proposal'] = proposal_items
    request.session['proposal_client_id'] = commercial_proposal.client_id
    request.session['proposal_date_proposition'] = commercial_proposal.date_proposal.isoformat() if commercial_proposal.date_proposal else ''
    request.session['proposal_include_tva'] = float(commercial_proposal.amount_ttc or 0) > float(commercial_proposal.amount_ht or 0)
    request.session['proposal_draft_id'] = commercial_proposal.id
    request.session.modified = True

@require_GET
@user_required
def catalogue_page(request):
    list_proposal = request.session.get('proposal', [])
    nom = request.GET.get('nom', '').strip()
    category_id = request.GET.get('category_id', '').strip()
    allCategory = Category.objects.all()
    allProducts = Product.objects.select_related('unit').prefetch_related('categories').all()

    if nom:
        allProducts = allProducts.filter(designation__icontains=nom)

    if category_id:
        allProducts = allProducts.filter(categories__id=category_id).distinct()

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
@user_required
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
            'category_name': _product_category_label(p),
            'unit_name': p.unit.name,
            'sale_unit_price': float(p.sale_unit_price),
            'coefficient': proposal_by_product.get(p.id, {}).get('coefficient', float(p.coefficient)),
            'quantity': proposal_by_product.get(p.id, {}).get('quantity', 0.0),
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
@user_required
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
                prix_unitaire_vente = float(product_value.get('sale_unit_price', product_value.get('prix_unitaire_vente', 0)))
                prix_unitaire_achat = float(product_value.get('purchase_unit_price', product_value.get('prix_unitaire_achat', 0)))
            else:
                product_id = int(product_value)
                designation = ''
                category_name = ''
                prix_unitaire_vente = float(raw_item.get('sale_unit_price', raw_item.get('prix_unitaire_vente', 0)))
                prix_unitaire_achat = float(raw_item.get('purchase_unit_price', raw_item.get('prix_unitaire_achat', 0)))

            coefficient = float(raw_item.get('coefficient', 0))
            quantity = float(raw_item.get('quantity', 0))
        except (TypeError, ValueError, AttributeError):
            return

        if product_id <= 0 or quantity <= 0:
            return

            if prix_unitaire_achat <= 0 or not designation or not category_name:
                product = Product.objects.select_related('unit').prefetch_related('categories').filter(
                    id=product_id
                ).first()
            if product is not None:
                designation = designation or str(product.designation)
                category_name = category_name or _product_category_label(product)
                if prix_unitaire_vente <= 0:
                    prix_unitaire_vente = float(product.sale_unit_price)
                if prix_unitaire_achat <= 0:
                    prix_unitaire_achat = float(product.purchase_unit_price)

        proposal_by_product[product_id] = {
            'product': {
                'id': product_id,
                'designation': designation,
                'category_name': category_name,
                'prix_unitaire_vente': prix_unitaire_vente,
                'prix_unitaire_achat': prix_unitaire_achat,
                'total': prix_unitaire_vente * max(0.0, coefficient) * max(0.0, quantity),
                'sale_unit_price': prix_unitaire_vente,
                'purchase_unit_price': prix_unitaire_achat,
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

        product = Product.objects.select_related('unit').prefetch_related('categories').filter(
            id=product_id
        ).first()
        if not product:
            continue

        sale_unit_price = max(0.0, float(product.sale_unit_price))
        purchase_unit_price = max(0.0, float(product.purchase_unit_price))
        product_total = sale_unit_price * max(0.0, coefficient) * max(0.0, quantity)

        proposal_by_product[product_id] = {
            'product': {
                'id': product.id,
                'designation': product.designation,
                'category_name': _product_category_label(product),
                'sale_unit_price': sale_unit_price,
                'purchase_unit_price': purchase_unit_price,
                'prix_unitaire_vente': sale_unit_price,
                'prix_unitaire_achat': purchase_unit_price,
                'total': product_total,
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


@require_GET
@user_required
def edit_draft_proposition_page(request):
    proposal_id = request.GET.get('proposal_id', '').strip()
    if not proposal_id:
        return redirect('propositions_page')

    commercial_proposal = CommercialProposal.objects.filter(id=proposal_id, commercial=request.user).first()
    if commercial_proposal is None or commercial_proposal.state == 1:
        return redirect('propositions_page')

    _build_session_from_draft(request, commercial_proposal)
    return new_proposition_page(request)


@require_POST
@user_required
def save_draft_proposition_page(request):
    return _finalize_proposal_from_session(request, state=0, success_redirect_name='propositions_page')


@require_POST
@user_required
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
@user_required
def save_proposal_options_api(request):
    try:
        payload = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Payload JSON invalide.'}, status=400)

    client_id_raw = payload.get('client_id')
    date_proposition_raw = payload.get('date_proposition')
    include_tax_raw = payload.get('include_tax')

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

    include_tax = True
    if isinstance(include_tax_raw, bool):
        include_tax = include_tax_raw
    elif include_tax_raw is not None:
        include_tax = str(include_tax_raw).strip().lower() in ('1', 'true', 'yes', 'on')

    request.session['proposal_client_id'] = client_id
    request.session['proposal_date_proposition'] = date_proposition
    request.session['proposal_include_tva'] = include_tax
    request.session.modified = True

    return JsonResponse({
        'success': True,
        'message': 'Options de la proposition enregistrées avec succès.',
        'proposal_client_id': client_id,
        'proposal_date_proposition': date_proposition,
        'proposal_include_tva': include_tax,
    })
    
@require_GET
@user_required
@ensure_csrf_cookie
def new_proposition_page(request):
    list_proposal= request.session.get('proposal', [])
    selected_client_id_raw = request.session.get('proposal_client_id')
    try:
        selected_client_id = int(selected_client_id_raw) if selected_client_id_raw not in (None, '') else None
    except (TypeError, ValueError):
        selected_client_id = None
    proposal_date_proposition = request.session.get('proposal_date_proposition', '')
    proposal_include_tva = bool(request.session.get('proposal_include_tva', True))
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
                    sale_unit_price = float(product.get('sale_unit_price', product.get('prix_unitaire_vente', 0)))
                    quantity = float(item.get('quantity', 0))
                    coefficient = float(item.get('coefficient', 0))
                    product_total = float(product.get('total', 0))
                except (TypeError, ValueError):
                    product_total = 0.0

            if product_total <= 0:
                try:
                    quantity = float(item.get('quantity', 0))
                    coefficient = float(item.get('coefficient', 0))
                    sale_unit_price = 0.0
                    if isinstance(product, dict):
                        sale_unit_price = float(product.get('sale_unit_price', product.get('prix_unitaire_vente', 0)))
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
            "proposal_include_tva": proposal_include_tva,
            "proposal_total": proposal_total,
            "summary_categories": summary_categories,
            "proposal_table_rows": proposal_table_rows,
        }
    )
    
@require_GET
@user_required
def appercu_proposition_page(request):
    proposal_id = request.GET.get('proposal_id', '').strip()
    client_id = request.GET.get('client_id', '').strip()
    if not client_id:
        session_client_id = request.session.get('proposal_client_id')
        client_id = str(session_client_id).strip() if session_client_id not in (None, '') else ''

    proposal_date_proposition = request.session.get('proposal_date_proposition', '')
    include_tva = bool(request.session.get('proposal_include_tva', True))
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
                    sale_unit_price = float(product.get('sale_unit_price', product.get('prix_unitaire_vente', 0)))
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
    tva_amount = proposal_total * 0.2 if include_tva else 0.0
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
            'include_tva': include_tva,
            'validity_period': 30,
            'selected_client': selected_client,
            'proposal_date_proposition': proposal_date_proposition,
        }
    )


@require_GET
@user_required
def validate_proposition_page(request):
    return _finalize_proposal_from_session(request, state=1, success_redirect_name='new_proposition_page')

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

    for proposal in all_proposals:
        validity_days = int(getattr(proposal, 'validity_period', 30) or 30)
        validity_date = proposal.date_proposal + timedelta(days=validity_days)
        proposal.validity_date = validity_date
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

    commercialProposal = CommercialProposal.objects.filter(id=proposal_id).first()
    if commercialProposal is None:
        return redirect('propositions_page')

    summary_by_category = {}

    for proposal_product in commercialProposal.proposal_products.all():
        quantity = max(0.0, float(proposal_product.quantity))
        coefficient = max(0.0, float(proposal_product.coefficient))
        sale_unit_price = max(0.0, float(proposal_product.sale_unit_price))
        product_total = quantity * coefficient * sale_unit_price

        category_name = 'Non catégorisé'
        designation = f"Produit {proposal_product.id}"

        if proposal_product.product is not None:
            category_name = _product_category_label(proposal_product.product)
            designation = proposal_product.product.designation or designation

        if category_name not in summary_by_category:
            summary_by_category[category_name] = {
                'name': category_name,
                'items': [],
                'total': 0.0,
            }

        summary_by_category[category_name]['items'].append({
            'designation': designation,
            'quantity': quantity,
            'sale_unit_price': sale_unit_price,
            'coefficient': coefficient,
            'total': product_total,
        })
        summary_by_category[category_name]['total'] += product_total

    summary_categories = list(summary_by_category.values())

    proposal_total = float(commercialProposal.amount_ht or 0)
    tva_amount = max(0.0, float(commercialProposal.amount_ttc or 0) - proposal_total)
    total_ttc = float(commercialProposal.amount_ttc or 0)

    return render(
        request, 
        "views/proposition_detail.html",
        {
            'proposal': commercialProposal,
            'summary_categories': summary_categories,
            'proposal_total': proposal_total,
            'tva_amount': tva_amount,
            'total_ttc': total_ttc,
        }
    )