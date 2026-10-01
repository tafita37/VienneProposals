from django.views.decorators.http import require_GET, require_POST
from django.shortcuts import render, redirect
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.http import JsonResponse
from django.urls import reverse
from decimal import Decimal, InvalidOperation
from django.db.models import OuterRef, Subquery
from authentification.decoratos import admin_required
from commercial.metier.Category import Category
from commercial.metier.CompanyType import CompanyType
from commercial.metier.Individual import Individual
from commercial.metier.Client import Client
from commercial.metier.Company import Company
from commercial.metier.Product import Product
from commercial.metier.ProductMovement import ProductMovement
from commercial.metier.ProductsCoefficientHistory import ProductsCoefficientHistory
from commercial.metier.Supplier import Supplier
from commercial.metier.Unit import Unit

@require_GET
@admin_required
def liste_client_page(request):
    all_clients = Client.objects.all()
    return render(
        request, 
        "views/clients.html",
        {"clients": all_clients}
    )
    
@require_GET
@admin_required
def liste_categorie_page(request):
    all_categories = Category.objects.all()
    return render(
        request, 
        "views/categories.html",
        {"categories": all_categories}
    )
    
def _admin_products_queryset():
    """Produits avec unité, catégories et fournisseur de la dernière entrée de stock."""
    last_entry = ProductMovement.objects.filter(
        product_id=OuterRef('pk'),
        movement_type=ProductMovement.MOVEMENT_TYPE_ENTRY,
    ).order_by('-movement_date', '-id')

    return (
        Product.objects
        .select_related('unit')
        .prefetch_related('categories')
        .annotate(
            last_supplier_id=Subquery(last_entry.values('supplier_id')[:1]),
            last_supplier_name=Subquery(last_entry.values('supplier__name')[:1]),
        )
        .order_by('designation')
    )


def _serialize_admin_product(product):
    # Lecture via le prefetch : les propriétés category_* de Product refont une requête par produit
    categories = list(product.categories.all())
    return {
        'id': product.id,
        'designation': product.designation,
        'category_ids': sorted(category.id for category in categories),
        'category_names': ', '.join(sorted(category.name for category in categories)),
        'unit_id': product.unit_id,
        'unit_name': product.unit.name,
        'supplier_id': product.last_supplier_id,
        'supplier_name': product.last_supplier_name,
        'purchase_unit_price': float(product.purchase_unit_price),
        'sale_unit_price': float(product.sale_unit_price),
        'explanation': product.explanation or '',
    }


@require_GET
@admin_required
def liste_product_page(request):
    product_coefficient_history = ProductsCoefficientHistory.objects.order_by('-date_change', '-id').first()
    global_coefficient = product_coefficient_history.coefficient if product_coefficient_history else Decimal('1.30')
    return render(
        request,
        "views/products.html",
        {
            "products": [_serialize_admin_product(product) for product in _admin_products_queryset()],
            "categories": Category.objects.order_by('name'),
            "units": Unit.objects.order_by('name'),
            "suppliers": Supplier.objects.order_by('name'),
            "global_coefficient": global_coefficient,
            "error": request.GET.get('error', ''),
        }
    )


@require_GET
@admin_required
def get_products_api(request):
    nom = request.GET.get('nom', '').strip()
    category_id = request.GET.get('category_id', '').strip()

    products = _admin_products_queryset()

    if nom:
        products = products.filter(designation__icontains=nom)

    if category_id.isdigit():
        products = products.filter(categories__id=category_id).distinct()

    return JsonResponse({'products': [_serialize_admin_product(product) for product in products]})

@require_GET
@admin_required
def new_client_page(request):
    allCompanyTypes = CompanyType.objects.all()
    return render(
        request, 
        "views/newClient.html",
        {"company_types": allCompanyTypes}
    )
    
@require_GET
@admin_required
def edit_client_page(request, client_id):
    client = Client.objects.get(id=client_id)
    if client.is_company :
        company = Company.objects.filter(client_id=client.id).first()
        allCompanyTypes = CompanyType.objects.all()
        return render(
            request, 
            "views/edit_client_company.html",
            {"company_types": allCompanyTypes, "client": client, "company": company}
        )
    else :
        individual = Individual.objects.filter(client_id=client.id).first()
        allCompanyTypes = CompanyType.objects.all()
        return render(
            request, 
            "views/edit_client_individual.html",
            {"company_types": allCompanyTypes, "client": client, "individual": individual}
        )
    
@require_GET
@admin_required
def new_client_page(request):
    allCompanyTypes = CompanyType.objects.all()
    return render(
        request, 
        "views/newClient.html",
        {"company_types": allCompanyTypes}
    )
    
@require_POST
@admin_required
def save_client(request):
    address = request.POST.get('address')
    email = request.POST.get('email')
    website_url = request.POST.get('website_url')
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
    
    name=company_name if is_company else f"{first_name} {last_name}"
    
    client_data = {
        'name': name,
        'address': address,
        'email': email,
        'website_url': website_url,
        'phone': phone
    }
    
    with transaction.atomic():
        if is_company:
            company = Company(
                name=company_name,
                registration_number=registration_number,
                tax_identification_number=tax_identification_number,
                created_at=created_at,
                company_type=CompanyType(id=company_type)
            )
            company.save(client_data=client_data)
        else:
            individual = Individual(
                first_name=first_name,
                last_name=last_name,
                birth_date=birth_date,
                id_card_number=id_card_number
            )
            individual.save(client_data=client_data)
    
    return redirect('liste_client_page')

@require_POST
@admin_required
def saveCategorie(request):
    id= request.POST.get('id')
    name = request.POST.get('name')
    if id:
        category = Category.objects.get(id=id)
        category.name = name
    else:
        category = Category(name=name)
    category.save()
    return redirect('liste_categorie_page')

def _parse_ids(raw_values):
    ids = []
    for raw_value in raw_values:
        try:
            ids.append(int(raw_value))
        except (TypeError, ValueError):
            continue
    return ids


def _record_purchase_entry(product, supplier_id):
    """Trace une entrée de stock si le fournisseur ou le prix d'achat a changé depuis la dernière entrée."""
    last_entry = (
        ProductMovement.objects
        .filter(product=product, movement_type=ProductMovement.MOVEMENT_TYPE_ENTRY)
        .order_by('-movement_date', '-id')
        .first()
    )
    if last_entry and last_entry.supplier_id == supplier_id and last_entry.price == product.purchase_unit_price:
        return

    ProductMovement.objects.create(
        product=product,
        supplier_id=supplier_id,
        price=product.purchase_unit_price,
        movement_type=ProductMovement.MOVEMENT_TYPE_ENTRY,
    )


@require_POST
@admin_required
def saveProduct(request):
    product_id = request.POST.get('id')
    product = Product() if not product_id else Product.objects.filter(id=product_id).first()
    if product is None:
        return redirect('liste_product_page')

    product.designation = request.POST.get('designation')
    product.purchase_unit_price = float(request.POST.get('purchase_unit_price'))
    product.sale_unit_price = float(request.POST.get('sale_unit_price'))
    product.coefficient = request.POST.get('coefficient')
    product.unit_id = request.POST.get('unit_id')

    category_ids = _parse_ids(request.POST.getlist('category_ids'))
    supplier_ids = _parse_ids([request.POST.get('supplier_id')])
    supplier_id = supplier_ids[0] if supplier_ids else None

    with transaction.atomic():
        product.save()
        product.categories.set(Category.objects.filter(id__in=category_ids))
        _record_purchase_entry(product, supplier_id)

    return redirect('liste_product_page')


@require_POST
@admin_required
def update_global_product_coefficient(request):
    raw_coefficient = request.POST.get('coefficient', '').strip()

    try:
        coefficient = Decimal(raw_coefficient)
    except (InvalidOperation, TypeError, ValueError):
        return JsonResponse({'success': False, 'message': 'Coefficient invalide.'}, status=400)

    if coefficient <= 0:
        return JsonResponse({'success': False, 'message': 'Le coefficient doit être supérieur à 0.'}, status=400)

    with transaction.atomic():
        products = list(Product.objects.all())
        for product in products:
            product.coefficient = coefficient
            product.sale_unit_price = float(Decimal(str(product.purchase_unit_price)) * coefficient)

        if products:
            Product.objects.bulk_update(products, ['coefficient', 'sale_unit_price'])

        ProductsCoefficientHistory.objects.create(coefficient=coefficient)

    return JsonResponse(
        {
            'success': True,
            'message': 'Le coefficient global a bien été modifié.',
            'coefficient': str(coefficient),
            'updated_products': len(products),
        }
    )

@require_POST
@admin_required
def update_client(request):
    client_id = request.POST.get('client_id')
    if not client_id:
        return redirect('liste_client_page')

    client = Client.objects.filter(id=client_id).first()
    if not client:
        return redirect('liste_client_page')

    address = request.POST.get('address')
    email = request.POST.get('email')
    website_url = request.POST.get('website_url')
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

    client.name = name
    client.address = address
    client.email = email
    client.website_url = website_url
    client.phone = phone
    client.is_company = is_company
    client.save()

    if is_company:
        company = Company.objects.filter(client_id=client.id).first()
        if company:
            company.name = company_name
            company.registration_number = registration_number
            company.tax_identification_number = tax_identification_number
            company.created_at = created_at
            company.company_type_id = int(company_type)
            company.save()
    else:
        individual = Individual.objects.filter(client_id=client.id).first()
        if individual:
            individual.first_name = first_name
            individual.last_name = last_name
            individual.birth_date = birth_date
            individual.id_card_number = id_card_number
            individual.save()

    return redirect('liste_client_page')

@require_GET
@admin_required
def delete_client(request):
    client_id= request.GET.get('client_id')
    client = Client.objects.filter(id=client_id).first()
    if client:
        client.delete()
    return redirect('liste_client_page')

@require_GET
@admin_required
def delete_category(request):
    category_id= request.GET.get('id')
    category = Category.objects.filter(id=category_id).first()
    if category:
        category.delete()
    return redirect('liste_categorie_page')

@require_GET
@admin_required
def delete_product(request):
    product_id= request.GET.get('id')
    product = Product.objects.filter(id=product_id).first()
    if product:
        try:
            product.delete()
        except ProtectedError:
            return redirect(f"{reverse('liste_product_page')}?error=used")
    return redirect('liste_product_page')

@require_GET
@admin_required
def liste_supplier_page(request):
    all_suppliers = Supplier.objects.order_by('name').all()
    return render(
        request,
        "views/suppliers.html",
        {
            "suppliers": all_suppliers,
            "error": request.GET.get('error', ''),
        }
    )

@require_POST
@admin_required
def save_supplier(request):
    id = request.POST.get('id')
    name = (request.POST.get('name') or '').strip()
    if not name:
        return redirect(f"{reverse('liste_supplier_page')}?error=empty")
    if id:
        supplier = Supplier.objects.filter(id=id).first()
        if not supplier:
            return redirect('liste_supplier_page')
        supplier.name = name
    else:
        supplier = Supplier(name=name)
    try:
        supplier.save()
    except IntegrityError:
        return redirect(f"{reverse('liste_supplier_page')}?error=duplicate")
    return redirect('liste_supplier_page')

@require_GET
@admin_required
def delete_supplier(request):
    supplier_id = request.GET.get('id')
    supplier = Supplier.objects.filter(id=supplier_id).first()
    if supplier:
        try:
            supplier.delete()
        except ProtectedError:
            return redirect(f"{reverse('liste_supplier_page')}?error=used")
    return redirect('liste_supplier_page')
