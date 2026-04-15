from django.views.decorators.http import require_GET, require_POST
from django.shortcuts import render, redirect
from django.db import transaction
from django.http import JsonResponse
from decimal import Decimal, InvalidOperation

from authentification.decoratos import admin_required
from commercial.metier.Category import Category
from commercial.metier.CompanyType import CompanyType
from commercial.metier.Individual import Individual
from commercial.metier.Client import Client
from commercial.metier.Company import Company
from commercial.metier.Product import Product
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
    
@require_GET
@admin_required
def liste_product_page(request):
    all_products = Product.objects.all()
    all_categories = Category.objects.all()
    all_units = Unit.objects.all()
    return render(
        request, 
        "views/products.html",
        {"products": all_products, "categories": all_categories, "units": all_units}
    )


@require_GET
@admin_required
def get_products_api(request):
    nom = request.GET.get('nom', '').strip()
    category_id = request.GET.get('category_id', '').strip()

    products = Product.objects.select_related('category', 'unit').all()

    if nom:
        products = products.filter(designation__icontains=nom)

    if category_id:
        products = products.filter(category_id=category_id)

    data = [
        {
            'id': product.id,
            'designation': product.designation,
            'category_id': product.category_id,
            'category_name': product.category.name,
            'unit_id': product.unit_id,
            'unit_name': product.unit.name,
            'purchase_unit_price': float(product.purchase_unit_price),
            'sale_unit_price': float(product.sale_unit_price),
        }
        for product in products
    ]

    return JsonResponse({'products': data})
    
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
    
    if is_company:
        company = Company(
            name=company_name,
            registration_number=registration_number,
            tax_identification_number=tax_identification_number,
            created_at=created_at,
            company_type_id=CompanyType(id=company_type)
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

@require_POST
@admin_required
def saveProduct(request):
    id= request.POST.get('id')
    if id:
        product = Product.objects.get(id=id)
        product.designation = request.POST.get('designation')
        product.purchase_unit_price = request.POST.get('purchase_unit_price')
        product.sale_unit_price = request.POST.get('sale_unit_price')
        product.coefficient = request.POST.get('coefficient')
        product.unit_id = request.POST.get('unit_id')
    else:
        category_id = request.POST.get('category_id')
        product = Product(
            designation=request.POST.get('designation'),
            purchase_unit_price=request.POST.get('purchase_unit_price'),
            sale_unit_price=request.POST.get('sale_unit_price'),
            coefficient=request.POST.get('coefficient'),
            unit_id=request.POST.get('unit_id'),
            category_id=category_id
        )
    product.save()
    return redirect('liste_product_page')


@require_POST
@admin_required
def update_global_product_coefficient(request):
    raw_coefficient = request.POST.get('coefficient', '').strip()

    try:
        coefficient = Decimal(raw_coefficient)
    except (InvalidOperation, TypeError, ValueError):
        return redirect('liste_product_page')

    if coefficient < 0:
        return redirect('liste_product_page')

    with transaction.atomic():
        for product in Product.objects.all():
            product.coefficient = coefficient
            product.sale_unit_price = float(product.purchase_unit_price) * float(coefficient)
            product.save(update_fields=['coefficient', 'sale_unit_price'])

    return redirect('liste_product_page')

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
        product.delete()
    return redirect('liste_product_page')