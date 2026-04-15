from django.db import connection, transaction
from django.views.decorators.http import require_GET, require_POST
from django.shortcuts import render, redirect
from django.contrib import messages
from openpyxl import load_workbook
import io
import re
from authentification.decoratos import admin_required
from commercial.metier.Category import Category
from commercial.metier.Product import Product
from unidecode import unidecode

@require_GET
@admin_required
def import_page(request):
    return render(
        request, 
        "views/import.html"
    )

@require_POST
@admin_required
def read_excel_file(request):
    excel_file = request.FILES.get('excel_file')
    
    if not excel_file:
        messages.error(request, "Aucun fichier sélectionné")
        return redirect('import_page')
    
    if not excel_file.name.lower().endswith(('.xlsx', '.xlsm')):
        messages.error(request, "Format non supporté. Utilisez un fichier .xlsx ou .xlsm")
        return redirect('import_page')
    
    try:
        workbook = load_workbook(filename=io.BytesIO(excel_file.read()), data_only=True)
        sheet = workbook.active

        raw_category = sheet.cell(row=2, column=9).value
        if not isinstance(raw_category, str) or not raw_category.strip():
            messages.error(request, "La catégorie est introuvable (cellule I2 vide ou invalide).")
            return redirect('import_page')

        category_name = ' '.join(raw_category.strip().split()[:-1]).strip()
        if not category_name:
            category_name = raw_category.strip()

        nb_vide = 0
        products_to_insert = []  # Liste pour stocker toutes les données
        row_errors = []
        invalid_rows = set()
        
        for excel_row in range(7, sheet.max_row + 1):
            has_data = False
            
            # Vérifier si la ligne a des données
            for col_idx in range(1, 13):
                cell = sheet.cell(row=excel_row, column=col_idx)
                cell_value = cell.value
                
                if isinstance(cell_value, str):
                    cell_value = cell_value.strip()
                
                if cell_value is not None and cell_value != '' and str(cell_value).strip() != '' and cell_value != 0:
                    has_data = True
            
            if has_data:
                nb_vide = 0
                try:
                    designation_raw = sheet.cell(row=excel_row, column=2).value
                    unite_raw = sheet.cell(row=excel_row, column=7).value
                    quantite = sheet.cell(row=excel_row, column=9).value
                    prixAchat = sheet.cell(row=excel_row, column=10).value
                    coefficient = sheet.cell(row=excel_row, column=11).value
                    prixVente = sheet.cell(row=excel_row, column=12).value

                    if not isinstance(designation_raw, str) or not designation_raw.strip():
                        raise ValueError("désignation vide")
                    if not isinstance(unite_raw, str) or not unite_raw.strip():
                        raise ValueError("unité vide")
                    if prixAchat is None:
                        raise ValueError("prix d'achat manquant")
                    if coefficient is None:
                        raise ValueError("coefficient manquant")
                    if prixVente is None:
                        raise ValueError("prix de vente manquant")

                    designation = unidecode(designation_raw.strip()).lower()
                    unite = unidecode(unite_raw.strip()).lower()

                    try:
                        if quantite is not None and str(quantite).strip() != '':
                            quantite = float(quantite)
                    except (TypeError, ValueError):
                        raise ValueError("quantité invalide")

                    try:
                        prixAchat = float(prixAchat)
                    except (TypeError, ValueError):
                        raise ValueError("prix d'achat invalide")

                    try:
                        coefficient = float(coefficient)
                    except (TypeError, ValueError):
                        raise ValueError("coefficient invalide")

                    try:
                        prixVente = float(prixVente)
                    except (TypeError, ValueError):
                        raise ValueError("prix de vente invalide")

                    products_to_insert.append({
                        'excel_row': excel_row,
                        'designation': designation,
                        'unite': unite,
                        'quantite': quantite,
                        'prixAchat': prixAchat,
                        'coefficient': coefficient,
                        'prixVente': prixVente,
                    })
                except Exception as row_error:
                    row_errors.append(f"Ligne Excel {excel_row}: {row_error}")
                    invalid_rows.add(excel_row)
            else:
                nb_vide += 1
            
            if nb_vide >= 2:
                break

        seen_designations = {}
        for product in products_to_insert:
            designation = product['designation']
            excel_row = product['excel_row']

            if designation in seen_designations:
                first_row = seen_designations[designation]
                row_errors.append(
                    f"Ligne Excel {excel_row}: désignation dupliquée dans le fichier "
                    f"(déjà présente à la ligne {first_row}) -> '{designation}'."
                )
                invalid_rows.add(excel_row)
            else:
                seen_designations[designation] = excel_row

        candidate_products = [
            product for product in products_to_insert
            if product['excel_row'] not in invalid_rows
        ]

        if candidate_products:
            candidate_designations = [product['designation'] for product in candidate_products]
            existing_designations = set(
                Product.objects.filter(designation__in=candidate_designations)
                .values_list('designation', flat=True)
            )

            for product in candidate_products:
                if product['designation'] in existing_designations:
                    row_errors.append(
                        f"Ligne Excel {product['excel_row']}: désignation déjà existante en base -> "
                        f"'{product['designation']}'."
                    )
                    invalid_rows.add(product['excel_row'])

        products_to_insert = [
            product for product in candidate_products
            if product['excel_row'] not in invalid_rows
        ]

        if row_errors:
            messages.error(
                request,
                f"Import annulé: {len(row_errors)} erreur(s) détectée(s). Corrigez-les puis réimportez."
            )
            for row_error in row_errors:
                messages.error(request, row_error, extra_tags='excel-row-error')
            return redirect('import_page')
        
        # Insertion en masse dans PostgreSQL
        if products_to_insert:
            with transaction.atomic():
                category = Category.objects.get_or_create(name=category_name)[0]

                with connection.cursor() as cursor:
                    # Créer la table temporaire
                    cursor.execute("""
                        CREATE TEMP TABLE temp_catalogue_import (
                            designation VARCHAR(500),
                            unite VARCHAR(50),
                            quantite DECIMAL,
                            prix_achat DECIMAL,
                            coefficient DECIMAL,
                            prix_vente DECIMAL,
                            category_id INTEGER
                        )
                    """)
                    
                    cursor.execute("""
                        CREATE TEMP VIEW temp_import_with_units AS
                        SELECT 
                            tci.designation,
                            tci.unite,
                            tci.quantite,
                            tci.prix_achat,
                            tci.coefficient,
                            tci.prix_vente,
                            tci.category_id,
                            u.id as unite_id
                        FROM temp_catalogue_import tci
                        JOIN unit u ON u.name = tci.unite
                        WHERE tci.designation IS NOT NULL
                    """)
                    
                    # Préparer les données pour executemany
                    temp_data = []
                    for product in products_to_insert:
                        temp_data.append((
                            product['designation'],
                            product['unite'],
                            product['quantite'],
                            product['prixAchat'],
                            product['coefficient'],
                            product['prixVente'],
                            category.id,
                        ))
                    
                    # Insertion en masse dans la table temporaire
                    cursor.executemany("""
                        INSERT INTO temp_catalogue_import 
                        (designation, unite, quantite, prix_achat, coefficient, prix_vente, category_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, temp_data)
                    
                    cursor.execute("""
                        INSERT INTO unit (name)
                        SELECT DISTINCT unite
                        FROM temp_catalogue_import
                        WHERE unite IS NOT NULL 
                        AND unite != ''
                        AND NOT EXISTS (
                            SELECT 1 FROM unit WHERE unit.name = temp_catalogue_import.unite
                        )
                    """)
                    
                    cursor.execute("""
                        INSERT INTO product (designation, purchase_unit_price, sale_unit_price, coefficient, unit_id, category_id)
                        SELECT designation, prix_achat, prix_vente, coefficient, unite_id, category_id
                        FROM temp_import_with_units
                        WHERE NOT EXISTS (
                            SELECT 1 FROM product 
                            WHERE product.designation = temp_import_with_units.designation 
                            AND product.category_id = temp_import_with_units.category_id
                        )
                    """)
                    
                    # Récupérer le nombre de produits insérés
                    cursor.execute("SELECT COUNT(*) FROM temp_catalogue_import")
                    count = cursor.fetchone()[0]
                    print(request, f"Import réussi - {count} produits ajoutés dans la catégorie {category.name}")
                    
                    messages.success(request, f"Import réussi - {count} produits ajoutés dans la catégorie {category.name}")
                    
                    # La table temporaire est automatiquement supprimée à la fin du with
        else:
            messages.warning(request, "Aucune donnée valide à importer")
            return redirect('import_page')
        
    except Exception as e:
        print(f"Erreur: {e}")
        error_message = str(e)

        if "product_designation_key" in error_message or "(designation)=" in error_message:
            duplicate_match = re.search(r"\(designation\)=\((.*?)\)", error_message)
            duplicate_designation = duplicate_match.group(1) if duplicate_match else None

            if duplicate_designation:
                messages.error(
                    request,
                    f"Erreur d'import: la désignation '{duplicate_designation}' existe déjà. "
                    f"Supprimez-la du fichier ou modifiez-la avant de réimporter."
                )
            else:
                messages.error(
                    request,
                    "Erreur d'import: une désignation existe déjà en base. "
                    "Corrigez les doublons puis réessayez."
                )
        else:
            messages.error(request, f"Erreur de lecture: {error_message}")
        return redirect('import_page')
    
    return redirect('liste_product_page')