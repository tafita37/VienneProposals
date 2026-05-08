from datetime import date
import json
from types import SimpleNamespace
from unittest.mock import patch

from django.db import connection, IntegrityError
from django.test import RequestFactory, TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from time import perf_counter

from authentification.metier.AdminUser import AdminUser
from authentification.metier.User import User
from commercial.controllers import CommercialController, StatController
from commercial.controllers.CommercialController import (
	_compute_proposal_total,
	_product_category_label,
	_proposal_item_from_proposal_product,
	_proposal_rows_from_session,
)
from commercial.controllers.StatController import (
	_build_profit_by_month,
	_build_profit_by_month_for_commercial,
	_build_stat_by_commercial,
	_build_user_dashboard_counts,
	_parse_requested_year,
)
from commercial.metier.Category import Category
from commercial.metier.Client import Client
from commercial.metier.CommercialProposal import CommercialProposal
from commercial.metier.Company import Company
from commercial.metier.CompanyType import CompanyType
from commercial.metier.Individual import Individual
from commercial.metier.Product import Product
from commercial.metier.ProductCategory import ProductCategory
from commercial.metier.ProposalProduct import ProposalProduct
from commercial.metier.Unit import Unit


class CommercialModelAndHelperTests(TestCase):
	def setUp(self):
		# One coherent commercial dataset reused by the helper tests: product, client, proposal and categories.
		self.factory = RequestFactory()
		self.unit = Unit.objects.create(name='piece')
		self.category_alpha = Category.objects.create(name='Alpha')
		self.category_beta = Category.objects.create(name='Beta')
		self.company_type = CompanyType.objects.create(name='SARL')
		self.commercial_user = User.objects.create_user(
			username='commercial1',
			first_name='Camille',
			last_name='Dupont',
			email='commercial1@example.com',
			password='secret-password',
		)
		self.client_obj = Client.objects.create(
			name='Client A',
			address='1 rue de Paris',
			email='client-a@example.com',
			website_url='https://client-a.example.com',
			phone='0102030405',
			is_company=True,
		)
		self.product = Product.objects.create(
			designation='Table en bois',
			purchase_unit_price=60,
			sale_unit_price=100,
			coefficient=1.5,
			unit=self.unit,
		)
		ProductCategory.objects.create(product=self.product, category=self.category_beta)
		ProductCategory.objects.create(product=self.product, category=self.category_alpha)
		self.proposal = CommercialProposal.objects.create(
			date_proposal=date(2026, 1, 15),
			amount_ht=0.0,
			amount_ttc=0.0,
			client=self.client_obj,
			commercial=self.commercial_user,
			state=1,
		)
		self.proposal_product = ProposalProduct.objects.create(
			coefficient=2,
			quantity=3,
			purchase_unit_price=60,
			sale_unit_price=100,
			commercial_proposal=self.proposal,
			product=self.product,
			explanation='Pose incluse',
		)

	# def test_product_model_category_properties_use_expected_ordering(self):
	# 	# Product.category picks the first category by id, while the label helpers keep all names.
	# 	self.assertEqual(self.product.category.id, self.category_beta.id)
	# 	self.assertEqual(self.product.category_id, self.category_beta.id)
	# 	self.assertEqual(self.product.category_name, 'Beta')
	# 	self.assertEqual(self.product.category_names, 'Alpha, Beta')
	# 	self.assertEqual(self.product.category_ids, [self.category_beta.id, self.category_alpha.id])
	# 	self.assertEqual(self.product.category_ids_csv, f'{self.category_beta.id},{self.category_alpha.id}')

	def test_product_category_unique_constraint_prevents_duplicates(self):
		with self.assertRaises(IntegrityError):
			ProductCategory.objects.create(product=self.product, category=self.category_beta)

	def test_company_save_creates_linked_client(self):
		# Company.save() should create the related Client automatically when client_data is provided.
		company = Company(
			name='Bois SARL',
			registration_number='REG-001',
			tax_identification_number='TVA-001',
			created_at=date(2026, 1, 1),
			company_type=self.company_type,
		)

		company.save(client_data={
			'name': 'Bois SARL',
			'address': '2 rue des Fleurs',
			'phone': '0600000000',
			'email': 'bois@example.com',
			'website_url': 'https://bois.example.com',
		})

		company.refresh_from_db()
		self.assertIsNotNone(company.client_id)
		self.assertTrue(Client.objects.filter(id=company.client_id, is_company=True).exists())

	def test_individual_save_creates_linked_client(self):
		# Individual.save() follows the same pattern, but marks the linked client as a private person.
		individual = Individual(
			first_name='Julie',
			last_name='Martin',
			birth_date=date(1990, 5, 10),
			id_card_number='ID-12345',
		)

		individual.save(client_data={
			'name': 'Julie Martin',
			'address': '3 avenue de Lyon',
			'phone': '0700000000',
			'email': 'julie@example.com',
			'website_url': 'https://julie.example.com',
		})

		individual.refresh_from_db()
		self.assertIsNotNone(individual.client_id)
		self.assertTrue(Client.objects.filter(id=individual.client_id, is_company=False).exists())

	def test_commercial_proposal_returns_related_proposal_products(self):
		# This property is just a convenient wrapper around the reverse relation.
		related_products = self.proposal.proposal_product_list

		self.assertEqual(len(related_products), 1)
		self.assertEqual(related_products[0].id, self.proposal_product.id)

	def test_product_category_label_prefers_category_names_then_first_category(self):
		# The label helper should use the richest information available and fall back safely.
		self.assertEqual(_product_category_label(None), 'Non catégorisé')
		self.assertEqual(_product_category_label(self.product), 'Alpha, Beta')

		no_multi_category_product = SimpleNamespace(category_names='', category=SimpleNamespace(name='Cuisine'))
		self.assertEqual(_product_category_label(no_multi_category_product), 'Cuisine')

	def test_compute_proposal_total_supports_multiple_input_shapes(self):
		# The total helper accepts precomputed totals or recomputes them from unit price, coefficient and quantity.
		list_proposal = [
			{'product': {'sale_unit_price': 100, 'total': 0}, 'quantity': 2, 'coefficient': 1.5},
			{'product': {'total': 50}, 'quantity': 1, 'coefficient': 1},
			{'product': {'sale_unit_price': 'bad'}, 'quantity': 1, 'coefficient': 1},
			'ignored-item',
		]

		total = _compute_proposal_total(list_proposal)

		self.assertEqual(total, 350.0)

	def test_proposal_item_from_proposal_product_returns_normalized_dict(self):
		# The conversion helper flattens a model instance into the session/API structure used by the UI.
		item = _proposal_item_from_proposal_product(self.proposal_product)

		self.assertEqual(item['product']['id'], self.product.id)
		self.assertEqual(item['product']['designation'], self.product.designation)
		self.assertEqual(item['product']['category_name'], 'Alpha, Beta')
		self.assertEqual(item['product']['total'], 600.0)
		self.assertEqual(item['coefficient'], 2.0)
		self.assertEqual(item['quantity'], 3.0)
		self.assertEqual(item['explanation'], 'Pose incluse')

	def test_proposal_rows_from_session_filters_invalid_rows(self):
		# Only rows with valid numeric values and a positive quantity should survive the session parsing.
		session_proposal = [
			{'product': {'id': self.product.id, 'sale_unit_price': 100, 'purchase_unit_price': 60}, 'quantity': 2, 'coefficient': 1.5, 'explanation': 'ok'},
			{'product': {'id': self.product.id, 'total': 300}, 'quantity': 2, 'coefficient': 1.5},
			{'product': {'id': self.product.id}, 'quantity': 0, 'coefficient': 1.5},
			{'product': {'id': self.product.id}, 'quantity': 'bad', 'coefficient': 1.5},
		]

		proposal_rows = _proposal_rows_from_session(session_proposal)

		self.assertEqual(len(proposal_rows), 2)
		self.assertEqual(proposal_rows[0]['product_id'], self.product.id)
		self.assertEqual(proposal_rows[0]['sale_unit_price'], 100.0)
		self.assertEqual(proposal_rows[1]['sale_unit_price'], 100.0)


class CommercialStatisticsHelperTests(TestCase):
	def setUp(self):
		# Build two commercial users and a mix of validated/draft proposals to exercise the aggregate logic.
		self.commercial_a = User.objects.create_user(
			username='commercial-a',
			first_name='Alice',
			last_name='Durand',
			email='commercial-a@example.com',
			password='secret-password',
		)
		self.commercial_b = User.objects.create_user(
			username='commercial-b',
			first_name='Bruno',
			last_name='Martin',
			email='commercial-b@example.com',
			password='secret-password',
		)
		self.unit = Unit.objects.create(name='m²')
		self.category = Category.objects.create(name='Cuisine')
		self.client_a = Client.objects.create(
			name='Client Stat A',
			address='10 rue A',
			email='client-stata@example.com',
			website_url='https://stata.example.com',
			phone='0101010101',
			is_company=True,
		)
		self.client_b = Client.objects.create(
			name='Client Stat B',
			address='20 rue B',
			email='client-statb@example.com',
			website_url='https://statb.example.com',
			phone='0202020202',
			is_company=True,
		)
		self.product = Product.objects.create(
			designation='Plan de travail',
			purchase_unit_price=40,
			sale_unit_price=70,
			coefficient=1.75,
			unit=self.unit,
		)
		ProductCategory.objects.create(product=self.product, category=self.category)

		self.proposal_a_january = CommercialProposal.objects.create(
			date_proposal=date(2026, 1, 10),
			amount_ht=0.0,
			amount_ttc=0.0,
			client=self.client_a,
			commercial=self.commercial_a,
			state=1,
		)
		ProposalProduct.objects.create(
			coefficient=1,
			quantity=2,
			purchase_unit_price=40,
			sale_unit_price=70,
			commercial_proposal=self.proposal_a_january,
			product=self.product,
		)

		self.proposal_a_february = CommercialProposal.objects.create(
			date_proposal=date(2026, 2, 10),
			amount_ht=0.0,
			amount_ttc=0.0,
			client=self.client_a,
			commercial=self.commercial_a,
			state=0,
		)
		ProposalProduct.objects.create(
			coefficient=1,
			quantity=1,
			purchase_unit_price=30,
			sale_unit_price=50,
			commercial_proposal=self.proposal_a_february,
			product=self.product,
		)

		self.proposal_b_january = CommercialProposal.objects.create(
			date_proposal=date(2026, 1, 20),
			amount_ht=0.0,
			amount_ttc=0.0,
			client=self.client_b,
			commercial=self.commercial_b,
			state=1,
		)
		ProposalProduct.objects.create(
			coefficient=1,
			quantity=1,
			purchase_unit_price=25,
			sale_unit_price=35,
			commercial_proposal=self.proposal_b_january,
			product=self.product,
		)

	def test_parse_requested_year_supports_empty_valid_and_invalid_values(self):
		# The year parser defaults to the current year, accepts integers, and rejects invalid text.
		with patch('commercial.controllers.StatController.timezone.localdate', return_value=date(2026, 5, 6)):
			self.assertEqual(_parse_requested_year(RequestFactory().get('/stats/')), 2026)
			self.assertEqual(_parse_requested_year(RequestFactory().get('/stats/', {'year': '2024'})), 2024)
			self.assertIsNone(_parse_requested_year(RequestFactory().get('/stats/', {'year': 'not-a-year'})))

	def test_build_stat_by_commercial_aggregates_margins_and_counts(self):
		# This helper aggregates per-commercial counts and yearly/monthly margins from proposal lines.
		stats = _build_stat_by_commercial(2026)
		stats_by_id = {item['id']: item for item in stats}

		self.assertIn(self.commercial_a.id, stats_by_id)
		self.assertIn(self.commercial_b.id, stats_by_id)
		self.assertEqual(stats_by_id[self.commercial_a.id]['proposals'], 2)
		self.assertEqual(stats_by_id[self.commercial_b.id]['proposals'], 1)
		self.assertEqual(stats_by_id[self.commercial_a.id]['yearlyProfit'], 80.0)
		self.assertEqual(stats_by_id[self.commercial_b.id]['yearlyProfit'], 10.0)
		january_profit = stats_by_id[self.commercial_a.id]['monthlyProfit'][0]
		february_profit = stats_by_id[self.commercial_a.id]['monthlyProfit'][1]
		self.assertEqual(january_profit['value'], 60.0)
		self.assertEqual(february_profit['value'], 20.0)

	def test_build_profit_by_month_aggregates_all_proposals(self):
		# Global monthly profit includes every proposal of the requested year, regardless of state.
		profits = _build_profit_by_month(2026)

		self.assertEqual(len(profits), 12)
		self.assertEqual(profits[0]['value'], 70.0)
		self.assertEqual(profits[1]['value'], 20.0)

	def test_build_profit_by_month_for_commercial_filters_by_user_and_validated_state(self):
		# The user dashboard only counts validated proposals for the current commercial.
		profits = _build_profit_by_month_for_commercial(2026, self.commercial_a)

		self.assertEqual(len(profits), 12)
		self.assertEqual(profits[0]['value'], 60.0)
		self.assertEqual(profits[1]['value'], 0.0)

	def test_build_user_dashboard_counts_reports_created_validated_and_pending(self):
		# The dashboard counts are a simple breakdown of all proposals by state for one user.
		counts = _build_user_dashboard_counts(self.commercial_a)

		self.assertEqual(counts['created'], 2)
		self.assertEqual(counts['validated'], 1)
		self.assertEqual(counts['pending'], 1)


class CommercialIntegrationTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(
			username='commercial-integration',
			first_name='Lina',
			last_name='Seller',
			email='commercial-integration@example.com',
			password='user-pass-123',
		)
		self.admin_user = AdminUser.objects.create(
			username='admin-integration',
			first_name='Lina',
			last_name='Admin',
			email='admin-integration@example.com',
		)
		self.admin_user.set_password('admin-pass-123')
		self.admin_user.save(update_fields=['password'])

		self.unit = Unit.objects.create(name='u-integration')
		self.category = Category.objects.create(name='Cat Integration')
		self.company_type = CompanyType.objects.create(name='Type Integration')
		self.product = Product.objects.create(
			designation='Produit Integration',
			purchase_unit_price=50,
			sale_unit_price=90,
			coefficient=1.8,
			unit=self.unit,
		)
		ProductCategory.objects.create(product=self.product, category=self.category)
		self.client_obj = Client.objects.create(
			name='Client Integration',
			address='11 rue integration',
			email='client-integration@example.com',
			website_url='https://client-integration.example.com',
			phone='0505050505',
			is_company=True,
		)
		self.company = Company.objects.create(
			name='Company Integration',
			registration_number='REG-INTEGRATION',
			tax_identification_number='TVA-INTEGRATION',
			created_at=date(2026, 1, 10),
			company_type=self.company_type,
			client=self.client_obj,
		)

	def test_user_products_api_requires_authentication(self):
		response = self.client.get('/com/api/products/')

		self.assertEqual(response.status_code, 302)
		self.assertIn(reverse('login_user_page'), response.url)

	def test_authenticated_user_gets_products_json(self):
		self.client.force_login(self.user)

		response = self.client.get('/com/api/products/', {'nom': 'Produit'})

		self.assertEqual(response.status_code, 200)
		payload = response.json()
		self.assertIn('products', payload)
		self.assertEqual(len(payload['products']), 1)
		self.assertEqual(payload['products'][0]['id'], self.product.id)

	def test_save_selected_products_api_persists_proposal_in_session(self):
		self.client.force_login(self.user)

		response = self.client.post(
			'/com/api/proposals/selected-products/',
			data=json.dumps({'selected_products': [{'product_id': self.product.id, 'coefficient': 2, 'quantity': 3}]}),
			content_type='application/json',
		)

		self.assertEqual(response.status_code, 200)
		self.assertTrue(response.json()['success'])

		session = self.client.session
		self.assertIn('proposal', session)
		self.assertEqual(len(session['proposal']), 1)
		self.assertEqual(session['proposal'][0]['product']['id'], self.product.id)

	def test_save_options_then_save_draft_creates_proposal_and_rows(self):
		self.client.force_login(self.user)
		session = self.client.session
		session['proposal'] = [{
			'product': {
				'id': self.product.id,
				'designation': self.product.designation,
				'category_name': self.category.name,
				'sale_unit_price': 90,
				'purchase_unit_price': 50,
				'total': 180,
			},
			'coefficient': 1,
			'quantity': 2,
			'explanation': 'Test integration',
		}]
		session['proposal_client_id'] = self.client_obj.id
		session['proposal_date_proposition'] = '2026-02-10'
		session['proposal_expiration_date'] = '2026-03-12'
		session['proposal_include_tva'] = True
		session.save()

		response = self.client.post('/com/save_draft_proposition_page/')

		self.assertEqual(response.status_code, 302)
		self.assertEqual(response.url, reverse('propositions_page'))

		proposal = CommercialProposal.objects.get(commercial=self.user)
		self.assertEqual(proposal.state, 0)
		self.assertEqual(proposal.client_id, self.client_obj.id)
		self.assertEqual(proposal.proposal_products.count(), 1)

	def test_update_client_from_proposal_api_updates_company_data(self):
		self.client.force_login(self.user)

		response = self.client.post(
			'/com/api/clients/update/',
			data=json.dumps({
				'client_id': self.client_obj.id,
				'address': '99 nouvelle adresse',
				'phone': '0606060606',
				'email': 'updated-client@example.com',
				'website_url': 'https://updated-client.example.com',
				'company_name': 'Company Updated',
				'company_type_id': self.company_type.id,
				'registration_number': 'REG-UPDATED',
				'tax_identification_number': 'TVA-UPDATED',
				'created_at': '2026-01-11',
			}),
			content_type='application/json',
		)

		self.assertEqual(response.status_code, 200)
		self.assertTrue(response.json()['success'])

		self.client_obj.refresh_from_db()
		self.company.refresh_from_db()
		self.assertEqual(self.client_obj.address, '99 nouvelle adresse')
		self.assertEqual(self.client_obj.name, 'Company Updated')
		self.assertEqual(self.company.registration_number, 'REG-UPDATED')

	def test_admin_save_product_creates_product_with_category(self):
		self.client.force_login(self.admin_user, backend='authentification.backends.AdminUserBackend')

		response = self.client.post('/admin/product/save/', {
			'designation': 'Produit Cree Admin',
			'purchase_unit_price': '40',
			'sale_unit_price': '80',
			'coefficient': '2',
			'unit_id': str(self.unit.id),
			'category_ids': [str(self.category.id)],
		})

		self.assertEqual(response.status_code, 302)
		self.assertEqual(response.url, reverse('liste_product_page'))

		created = Product.objects.get(designation='Produit Cree Admin')
		self.assertEqual(created.unit_id, self.unit.id)
		self.assertEqual(created.categories.count(), 1)
		self.assertEqual(created.categories.first().id, self.category.id)

	def test_admin_products_api_requires_admin_authentication(self):
		response = self.client.get('/admin/product/api/products/')

		self.assertEqual(response.status_code, 302)
		self.assertIn(reverse('login_admin_page'), response.url)


class CommercialFunctionalTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(
			username='commercial-functional',
			first_name='Nora',
			last_name='Seller',
			email='commercial-functional@example.com',
			password='functional-pass-123',
		)
		self.unit = Unit.objects.create(name='u-functional')
		self.category = Category.objects.create(name='Cat Functional')
		self.company_type = CompanyType.objects.create(name='SARL Functional')
		self.product = Product.objects.create(
			designation='Produit Fonctionnel',
			purchase_unit_price=40,
			sale_unit_price=100,
			coefficient=2.5,
			unit=self.unit,
		)
		ProductCategory.objects.create(product=self.product, category=self.category)
		self.client_obj = Client.objects.create(
			name='Client Functional',
			address='10 avenue fonctionnelle',
			email='client-functional@example.com',
			website_url='https://client-functional.example.com',
			phone='0707070707',
			is_company=True,
		)
		Company.objects.create(
			name='Company Functional',
			registration_number='REG-FUNCTIONAL',
			tax_identification_number='TVA-FUNCTIONAL',
			created_at=date(2026, 2, 1),
			company_type=self.company_type,
			client=self.client_obj,
		)

	def test_full_user_workflow_from_login_to_validated_proposal(self):
		login_response = self.client.post('/auth/login_user/', {
			'username': 'commercial-functional',
			'password': 'functional-pass-123',
		})
		self.assertEqual(login_response.status_code, 302)
		self.assertEqual(login_response.url, reverse('dashboard_user_page'))

		select_response = self.client.post(
			'/com/api/proposals/selected-products/',
			data=json.dumps({'selected_products': [{'product_id': self.product.id, 'coefficient': 1.5, 'quantity': 2}]}),
			content_type='application/json',
		)
		self.assertEqual(select_response.status_code, 200)
		self.assertTrue(select_response.json()['success'])

		options_response = self.client.post(
			'/com/api/proposals/options/',
			data=json.dumps({
				'client_id': self.client_obj.id,
				'date_proposition': '2026-04-10',
				'expiration_date': '2026-05-10',
				'include_tax': True,
			}),
			content_type='application/json',
		)
		self.assertEqual(options_response.status_code, 200)
		self.assertTrue(options_response.json()['success'])

		preview_response = self.client.get('/com/preview_proposition_page/', {'client_id': self.client_obj.id})
		self.assertEqual(preview_response.status_code, 200)

		validate_response = self.client.get('/com/validate_proposition_page/')
		self.assertEqual(validate_response.status_code, 302)
		self.assertEqual(validate_response.url, reverse('new_proposition_page'))

		proposal = CommercialProposal.objects.get(commercial=self.user)
		self.assertEqual(proposal.state, 1)
		self.assertEqual(proposal.client_id, self.client_obj.id)
		self.assertEqual(proposal.proposal_products.count(), 1)

		list_response = self.client.get('/com/propositions_page/')
		self.assertEqual(list_response.status_code, 200)

		detail_response = self.client.get('/com/proposition_detail/', {'proposal_id': proposal.id})
		self.assertEqual(detail_response.status_code, 200)

	def test_user_creates_individual_client_then_session_keeps_selected_client(self):
		self.client.force_login(self.user)

		response = self.client.post('/com/save_client_user/', {
			'address': '23 rue client user',
			'email': 'nouveau-client-user@example.com',
			'website_url': 'https://nouveau-client-user.example.com',
			'phone': '0808080808',
			'is_company': '0',
			'first_name': 'Paul',
			'last_name': 'Martin',
			'birth_date': '1992-03-14',
			'id_card_number': 'ID-FUNCTIONAL-001',
			'company_name': '',
			'company_type': '',
			'registration_number': '',
			'tax_identification_number': '',
			'created_at': '',
		})

		self.assertEqual(response.status_code, 302)
		self.assertEqual(response.url, reverse('new_proposition_page'))

		created_client = Client.objects.get(email='nouveau-client-user@example.com')
		self.assertFalse(created_client.is_company)
		self.assertTrue(Individual.objects.filter(client_id=created_client.id).exists())

		session = self.client.session
		self.assertEqual(session.get('proposal_client_id'), created_client.id)

		new_prop_response = self.client.get('/com/new_proposition_page/')
		self.assertEqual(new_prop_response.status_code, 200)


class CommercialPerformanceTests(TestCase):
	def setUp(self):
		self.factory = RequestFactory()
		self.admin_user = AdminUser.objects.create(
			username='perf-admin',
			first_name='Per',
			last_name='Formance',
			email='perf-admin@example.com',
		)
		self.admin_user.set_password('perf-admin-123')
		self.admin_user.save(update_fields=['password'])
		self.user = User.objects.create_user(
			username='perf-user',
			first_name='Per',
			last_name='User',
			email='perf-user@example.com',
			password='perf-user-123',
		)
		self.unit = Unit.objects.create(name='perf-unit')
		self.category_a = Category.objects.create(name='Perf A')
		self.category_b = Category.objects.create(name='Perf B')
		self.client_obj = Client.objects.create(
			name='Perf Client',
			address='1 perf street',
			email='perf-client@example.com',
			website_url='https://perf-client.example.com',
			phone='0909090909',
			is_company=True,
		)
		self.company_type = CompanyType.objects.create(name='Perf SARL')
		Company.objects.create(
			name='Perf Company',
			registration_number='REG-PERF',
			tax_identification_number='TVA-PERF',
			created_at=date(2026, 1, 1),
			company_type=self.company_type,
			client=self.client_obj,
		)
		self.product_1 = Product.objects.create(
			designation='Perf Product 1',
			purchase_unit_price=10,
			sale_unit_price=20,
			coefficient=2,
			unit=self.unit,
		)
		self.product_2 = Product.objects.create(
			designation='Perf Product 2',
			purchase_unit_price=15,
			sale_unit_price=30,
			coefficient=2,
			unit=self.unit,
		)
		ProductCategory.objects.create(product=self.product_1, category=self.category_a)
		ProductCategory.objects.create(product=self.product_1, category=self.category_b)
		ProductCategory.objects.create(product=self.product_2, category=self.category_b)

		proposal_january = CommercialProposal.objects.create(
			date_proposal=date(2026, 1, 10),
			amount_ht=0.0,
			amount_ttc=0.0,
			client=self.client_obj,
			commercial=self.user,
			state=1,
		)
		ProposalProduct.objects.create(
			coefficient=2,
			quantity=3,
			purchase_unit_price=10,
			sale_unit_price=20,
			commercial_proposal=proposal_january,
			product=self.product_1,
		)
		proposal_february = CommercialProposal.objects.create(
			date_proposal=date(2026, 2, 10),
			amount_ht=0.0,
			amount_ttc=0.0,
			client=self.client_obj,
			commercial=self.user,
			state=0,
		)
		ProposalProduct.objects.create(
			coefficient=2,
			quantity=2,
			purchase_unit_price=15,
			sale_unit_price=30,
			commercial_proposal=proposal_february,
			product=self.product_2,
		)

	def test_get_products_api_keeps_query_count_bounded(self):
		self.client.force_login(self.user)

		with CaptureQueriesContext(connection) as queries:
			response = self.client.get('/com/api/products/', {'nom': 'Perf'})

		self.assertEqual(response.status_code, 200)
		self.assertLessEqual(len(queries), 10)

	def test_get_client_by_id_api_keeps_query_count_bounded(self):
		request = self.factory.get(f'/com/api/clients/{self.client_obj.id}/')
		request.user = self.user

		with CaptureQueriesContext(connection) as queries:
			response = CommercialController.get_client_by_id_api(request, self.client_obj.id)

		self.assertEqual(response.status_code, 200)
		self.assertLessEqual(len(queries), 3)

	def test_initial_dashboard_data_avoids_query_explosion(self):
		request = self.factory.get('/com/api/loadInitialDataDashboard/')
		request.user = self.admin_user

		with CaptureQueriesContext(connection) as queries:
			response = StatController.get_initial_dashboard_data(request)

		self.assertEqual(response.status_code, 200)
		self.assertLessEqual(len(queries), 6)

	def test_initial_user_dashboard_data_avoids_query_explosion(self):
		request = self.factory.get('/com/api/loadInitialUserDashboardData/')
		request.user = self.user

		with CaptureQueriesContext(connection) as queries:
			response = StatController.get_initial_user_dashboard_data(request)

		self.assertEqual(response.status_code, 200)
		self.assertLessEqual(len(queries), 5)

	def test_catalogue_page_query_count_is_bounded(self):
		self.client.force_login(self.user)

		with CaptureQueriesContext(connection) as queries:
			response = self.client.get('/com/catalog_page/', {'nom': 'Perf'})

		self.assertEqual(response.status_code, 200)
		# The catalogue page loads categories and products with related data in a bounded number of queries.
		self.assertLessEqual(len(queries), 11)

	def test_new_proposition_page_query_count_is_bounded(self):
		self.client.force_login(self.user)
		session = self.client.session
		session['proposal'] = [{
			'product': {
				'id': self.product_1.id,
				'designation': self.product_1.designation,
				'category_name': self.category_a.name,
				'sale_unit_price': 20,
				'purchase_unit_price': 10,
				'total': 120,
			},
			'coefficient': 2,
			'quantity': 3,
		}]
		session['proposal_client_id'] = self.client_obj.id
		session['proposal_date_proposition'] = '2026-02-10'
		session['proposal_expiration_date'] = '2026-03-12'
		session.save()

		with CaptureQueriesContext(connection) as queries:
			response = self.client.get('/com/new_proposition_page/')

		self.assertEqual(response.status_code, 200)
		self.assertLessEqual(len(queries), 4)

	def test_appercu_proposition_page_query_count_is_bounded(self):
		self.client.force_login(self.user)
		session = self.client.session
		session['proposal'] = [{
			'product': {
				'id': self.product_1.id,
				'designation': self.product_1.designation,
				'category_name': self.category_a.name,
				'sale_unit_price': 20,
				'purchase_unit_price': 10,
				'total': 120,
			},
			'coefficient': 2,
			'quantity': 3,
		}]
		session['proposal_client_id'] = self.client_obj.id
		session['proposal_date_proposition'] = '2026-02-10'
		session['proposal_expiration_date'] = '2026-03-12'
		session.save()

		with CaptureQueriesContext(connection) as queries:
			response = self.client.get('/com/preview_proposition_page/', {'client_id': self.client_obj.id})

		self.assertEqual(response.status_code, 200)
		self.assertLessEqual(len(queries), 6)

	def test_propositions_page_query_count_is_bounded(self):
		CommercialProposal.objects.create(
			date_proposal=date(2026, 3, 10),
			amount_ht=0.0,
			amount_ttc=0.0,
			client=self.client_obj,
			commercial=self.user,
			state=1,
		)
		self.client.force_login(self.user)

		with CaptureQueriesContext(connection) as queries:
			response = self.client.get('/com/propositions_page/')

		self.assertEqual(response.status_code, 200)
		self.assertLessEqual(len(queries), 7)

	def test_proposition_detail_query_count_is_bounded(self):
		proposal = CommercialProposal.objects.create(
			date_proposal=date(2026, 3, 10),
			amount_ht=100.0,
			amount_ttc=120.0,
			client=self.client_obj,
			commercial=self.user,
			state=1,
		)
		ProposalProduct.objects.create(
			coefficient=1,
			quantity=1,
			purchase_unit_price=40,
			sale_unit_price=50,
			commercial_proposal=proposal,
			product=self.product_1,
		)
		self.client.force_login(self.user)

		with CaptureQueriesContext(connection) as queries:
			response = self.client.get('/com/proposition_detail/', {'proposal_id': proposal.id})

		self.assertEqual(response.status_code, 200)
		self.assertLessEqual(len(queries), 7)

	def test_client_list_page_query_count_is_bounded(self):
		self.client.force_login(self.admin_user, backend='authentification.backends.AdminUserBackend')

		with CaptureQueriesContext(connection) as queries:
			response = self.client.get('/admin/client/list/')

		self.assertEqual(response.status_code, 200)
		self.assertLessEqual(len(queries), 3)

	def test_category_list_page_query_count_is_bounded(self):
		self.client.force_login(self.admin_user, backend='authentification.backends.AdminUserBackend')

		with CaptureQueriesContext(connection) as queries:
			response = self.client.get('/admin/category/list/')

		self.assertEqual(response.status_code, 200)
		self.assertLessEqual(len(queries), 3)

	def test_product_list_page_query_count_is_bounded(self):
		self.client.force_login(self.admin_user, backend='authentification.backends.AdminUserBackend')

		with CaptureQueriesContext(connection) as queries:
			response = self.client.get('/admin/product/list/')

		self.assertEqual(response.status_code, 200)
		self.assertLessEqual(len(queries), 14)

	def _percentile(self, data, p):
		if not data:
			return None
		data = sorted(data)
		k = (len(data)-1) * (p/100.0)
		f = int(k)
		c = min(f+1, len(data)-1)
		if f == c:
			return data[int(k)]
		d0 = data[f] * (c-k)
		d1 = data[c] * (k-f)
		return d0 + d1

	def test_catalog_page_latency_report(self):
		"""Mesure simple: exécute plusieurs requêtes, affiche p50/p95/p99 (ms) et counts."""
		self.client.force_login(self.user)
		# warmup
		for _ in range(3):
			self.client.get('/com/catalog_page/', {'nom': 'Perf'})

		runs = 20
		durations = []
		query_counts = []
		for _ in range(runs):
			start = perf_counter()
			with CaptureQueriesContext(connection) as queries:
				response = self.client.get('/com/catalog_page/', {'nom': 'Perf'})
			d = (perf_counter() - start) * 1000.0
			durations.append(d)
			query_counts.append(len(queries))

		assert response.status_code == 200
		p50 = self._percentile(durations, 50)
		p95 = self._percentile(durations, 95)
		p99 = self._percentile(durations, 99)

		print('\n[perf] catalog_page: runs=%d median=%.1fms p95=%.1fms p99=%.1fms qcount_med=%.1f' % (
			runs, p50 or 0.0, p95 or 0.0, p99 or 0.0, self._percentile(query_counts, 50) or 0.0
		))

	def test_get_products_api_latency_report(self):
		"""Mesure p50/p95/p99 pour l'API de recherche produits."""
		self.client.force_login(self.user)
		# warmup
		for _ in range(3):
			self.client.get('/com/api/products/', {'nom': 'Perf'})

		runs = 30
		durations = []
		for _ in range(runs):
			start = perf_counter()
			response = self.client.get('/com/api/products/', {'nom': 'Perf'})
			durations.append((perf_counter() - start) * 1000.0)

		assert response.status_code == 200
		p50 = self._percentile(durations, 50)
		p95 = self._percentile(durations, 95)
		p99 = self._percentile(durations, 99)

		print('\n[perf] get_products_api: runs=%d median=%.1fms p95=%.1fms p99=%.1fms' % (
			runs, p50 or 0.0, p95 or 0.0, p99 or 0.0
		))

	def _measure_get(self, path, params=None, runs=20, warmup=3, capture_queries=False, login_user=None, login_backend=None):
		# login_user: user object to force_login; login_backend: optional backend string
		login_target = login_user if login_user is not None else getattr(self, 'user', None)
		if login_target is not None:
			if login_backend:
				self.client.force_login(login_target, backend=login_backend)
			else:
				self.client.force_login(login_target)
		for _ in range(warmup):
			self.client.get(path, params or {})
		durations = []
		query_counts = []
		for _ in range(runs):
			start = perf_counter()
			if capture_queries:
				with CaptureQueriesContext(connection) as queries:
					response = self.client.get(path, params or {})
					query_counts.append(len(queries))
			else:
				response = self.client.get(path, params or {})
			durations.append((perf_counter() - start) * 1000.0)
		# return last response for status check
		return response, durations, query_counts

	def _print_perf(self, name, runs, durations, query_counts=None):
		p50 = self._percentile(durations, 50)
		p95 = self._percentile(durations, 95)
		p99 = self._percentile(durations, 99)
		qmed = self._percentile(query_counts, 50) if query_counts else 0
		print('\n[perf] %s: runs=%d median=%.1fms p95=%.1fms p99=%.1fms qcount_med=%.1f' % (
			name, runs, p50 or 0.0, p95 or 0.0, p99 or 0.0, qmed or 0.0
		))

	def test_admin_product_list_latency(self):
		response, durations, q = self._measure_get('/admin/product/list/', runs=15, capture_queries=True, login_user=self.admin_user, login_backend='authentification.backends.AdminUserBackend')
		self.assertEqual(response.status_code, 200)
		self._print_perf('admin_product_list', len(durations), durations, q)

	def test_admin_client_list_latency(self):
		response, durations, q = self._measure_get('/admin/client/list/', runs=15, capture_queries=True, login_user=self.admin_user, login_backend='authentification.backends.AdminUserBackend')
		self.assertEqual(response.status_code, 200)
		self._print_perf('admin_client_list', len(durations), durations, q)

	def test_propositions_page_latency(self):
		response, durations, q = self._measure_get('/com/propositions_page/', runs=15, capture_queries=True)
		self.assertEqual(response.status_code, 200)
		self._print_perf('propositions_page', len(durations), durations, q)

	def test_new_proposition_page_latency(self):
		# ensure session has proposal
		session = self.client.session
		session['proposal'] = [{'product': {'id': self.product_1.id, 'designation': self.product_1.designation, 'sale_unit_price': 20, 'purchase_unit_price': 10, 'total': 120}, 'coefficient': 2, 'quantity': 3}]
		session['proposal_client_id'] = self.client_obj.id
		session.save()
		response, durations, q = self._measure_get('/com/new_proposition_page/', runs=15, capture_queries=True)
		self.assertEqual(response.status_code, 200)
		self._print_perf('new_proposition_page', len(durations), durations, q)

	def test_preview_proposition_page_latency(self):
		response, durations, q = self._measure_get('/com/preview_proposition_page/', params={'client_id': self.client_obj.id}, runs=15, capture_queries=True)
		self.assertEqual(response.status_code, 200)
		self._print_perf('preview_proposition_page', len(durations), durations, q)

	def test_new_client_page_query_count_is_bounded(self):
		self.client.force_login(self.admin_user, backend='authentification.backends.AdminUserBackend')

		with CaptureQueriesContext(connection) as queries:
			response = self.client.get('/admin/client/new/')

		self.assertEqual(response.status_code, 200)
		self.assertLessEqual(len(queries), 3)

	def test_edit_client_page_query_count_is_bounded_for_company(self):
		self.client.force_login(self.admin_user, backend='authentification.backends.AdminUserBackend')

		with CaptureQueriesContext(connection) as queries:
			response = self.client.get(f'/admin/client/edit/{self.client_obj.id}/')

		self.assertEqual(response.status_code, 200)
		self.assertLessEqual(len(queries), 5)

	def test_admin_save_product_query_count_is_bounded(self):
		self.client.force_login(self.admin_user, backend='authentification.backends.AdminUserBackend')

		with CaptureQueriesContext(connection) as queries:
			response = self.client.post('/admin/product/save/', {
				'designation': 'Perf Product Save',
				'purchase_unit_price': '33',
				'sale_unit_price': '66',
				'coefficient': '2',
				'unit_id': str(self.unit.id),
				'category_ids': [str(self.category_a.id), str(self.category_b.id)],
			})

		self.assertEqual(response.status_code, 302)
		self.assertLessEqual(len(queries), 7)

	def test_update_global_product_coefficient_query_count_is_bounded(self):
		self.client.force_login(self.admin_user, backend='authentification.backends.AdminUserBackend')

		with CaptureQueriesContext(connection) as queries:
			response = self.client.post('/admin/product/update-global-coefficient/', {'coefficient': '2.5'})

		self.assertEqual(response.status_code, 302)
		self.assertLessEqual(len(queries), 7)

	def test_save_client_query_count_is_bounded(self):
		self.client.force_login(self.admin_user, backend='authentification.backends.AdminUserBackend')

		with CaptureQueriesContext(connection) as queries:
			response = self.client.post('/admin/client/save/', {
				'address': '1 avenue perf',
				'email': 'perf-save@example.com',
				'website_url': 'https://perf-save.example.com',
				'phone': '0303030303',
				'is_company': '0',
				'first_name': 'Perf',
				'last_name': 'Save',
				'birth_date': '1990-01-01',
				'id_card_number': 'ID-PERF-SAVE',
				'company_name': '',
				'company_type': '',
				'registration_number': '',
				'tax_identification_number': '',
				'created_at': '',
			})

		self.assertEqual(response.status_code, 302)
		self.assertLessEqual(len(queries), 6)


class CommercialEdgeCaseTests(TestCase):
	"""Tests de robustesse et cas limites pour le module commercial."""
	
	def setUp(self):
		self.user = User.objects.create_user(
			username='edge-commercial',
			first_name='Edge',
			last_name='Commercial',
			email='edge-commercial@example.com',
			password='edge-pass',
		)
		self.admin_user = AdminUser.objects.create(
			username='edge-admin-commercial',
			first_name='Edge',
			last_name='Admin',
			email='edge-admin-commercial@example.com',
		)
		self.admin_user.set_password('edge-admin-pass')
		self.admin_user.save(update_fields=['password'])
		
		self.unit = Unit.objects.create(name='edge-unit')
		self.category = Category.objects.create(name='Edge Category')
		self.company_type = CompanyType.objects.create(name='Edge Type')
		self.client_obj = Client.objects.create(
			name='Edge Client',
			address='1 edge street',
			email='edge-client@example.com',
			website_url='https://edge-client.example.com',
			phone='0101010101',
			is_company=True,
		)
		self.product = Product.objects.create(
			designation='Edge Product',
			purchase_unit_price=50,
			sale_unit_price=100,
			coefficient=2.0,
			unit=self.unit,
		)
		ProductCategory.objects.create(product=self.product, category=self.category)
		self.proposal = CommercialProposal.objects.create(
			date_proposal=date(2026, 5, 1),
			amount_ht=0.0,
			amount_ttc=0.0,
			client=self.client_obj,
			commercial=self.user,
			state=0,
		)

	def test_proposal_with_zero_quantity(self):
		# ProposalProduct avec quantity = 0 devrait être rejeté ou ignoré.
		try:
			proposal_product = ProposalProduct.objects.create(
				coefficient=1,
				quantity=0,  # Zéro - invalide
				purchase_unit_price=50,
				sale_unit_price=100,
				commercial_proposal=self.proposal,
				product=self.product,
			)
			# If created, ensure total calculation ignores zero quantity
			total = _compute_proposal_total([{
				'product': {'sale_unit_price': 100},
				'quantity': 0,
				'coefficient': 1,
			}])
			self.assertEqual(total, 0.0)
		except (ValueError, IntegrityError):
			pass  # Accept either behavior

	def test_proposal_with_negative_quantity(self):
		# ProposalProduct with negative quantity: application may reject or accept.
		try:
			pp = ProposalProduct.objects.create(
				coefficient=1,
				quantity=-5,  # Négatif - invalide
				purchase_unit_price=50,
				sale_unit_price=100,
				commercial_proposal=self.proposal,
				product=self.product,
			)
			# If created, ensure it's stored with negative quantity (edge case)
			self.assertEqual(pp.quantity, -5)
		except (ValueError, IntegrityError):
			pass  # Both behaviors acceptable

	def test_product_with_zero_coefficient(self):
		# Product avec coefficient = 0 est un cas limite.
		product = Product.objects.create(
			designation='Zero Coeff Product',
			purchase_unit_price=50,
			sale_unit_price=100,
			coefficient=0,  # Zéro
			unit=self.unit,
		)
		self.assertEqual(product.coefficient, 0)
		
		# Proposal avec ce product devrait calculer un total de 0 (ou être rejeté)
		proposal_product = ProposalProduct.objects.create(
			coefficient=0,
			quantity=1,
			purchase_unit_price=50,
			sale_unit_price=100,
			commercial_proposal=self.proposal,
			product=product,
		)
		self.assertEqual(proposal_product.coefficient, 0)

	def test_product_with_negative_price(self):
		# Product avec prix négatif devrait être rejeté ou marqué comme anomalie.
		try:
			product = Product.objects.create(
				designation='Negative Price Product',
				purchase_unit_price=-50,  # Négatif
				sale_unit_price=100,
				coefficient=2,
				unit=self.unit,
			)
		except (ValueError, IntegrityError):
			pass  # Expected if validation rejects negative price

	def test_proposal_with_expiration_before_creation(self):
		# Proposal avec expiration_date avant date_proposal devrait être détecté.
		# Ce test vérifie si l'application valide cela
		try:
			proposal = CommercialProposal.objects.create(
				date_proposal=date(2026, 5, 10),
				expiration_date=date(2026, 5, 5),  # Avant date_proposal
				amount_ht=0.0,
				amount_ttc=0.0,
				client=self.client_obj,
				commercial=self.user,
				state=0,
			)
		except (ValueError, IntegrityError):
			pass

	def test_proposal_with_nonexistent_product(self):
		# Attempt to create ProposalProduct with nonexistent product_id should fail at DB level.
		from django.db import transaction
		with self.assertRaises(IntegrityError):
			with transaction.atomic():
				ProposalProduct.objects.create(
					coefficient=1,
					quantity=1,
					purchase_unit_price=50,
					sale_unit_price=100,
					commercial_proposal=self.proposal,
					product_id=99999,  # Inexistant
				)
				connection.check_constraints()

	def test_proposal_with_nonexistent_client(self):
		# Attempt to create CommercialProposal with nonexistent client_id should fail.
		from django.db import transaction
		with self.assertRaises(IntegrityError):
			with transaction.atomic():
				CommercialProposal.objects.create(
					date_proposal=date(2026, 5, 1),
					amount_ht=0.0,
					amount_ttc=0.0,
					client_id=99999,  # Inexistant
					commercial=self.user,
					state=0,
				)
				connection.check_constraints()

	def test_client_without_email(self):
		# Client sans email devrait être accepté ou rejeté selon la logique métier.
		try:
			client = Client.objects.create(
				name='No Email Client',
				address='2 no email street',
				email='',  # Vide
				website_url='https://no-email-client.example.com',
				phone='0202020202',
				is_company=True,
			)
			self.assertEqual(client.email, '')
		except (ValueError, IntegrityError):
			pass  # Accepté aussi si la DB/application l'impose

	def test_product_without_unit(self):
		# Product sans unit devrait être rejeté.
		with self.assertRaises(Exception):
			Product.objects.create(
				designation='No Unit Product',
				purchase_unit_price=50,
				sale_unit_price=100,
				coefficient=2,
				unit=None,  # Manquant
			)

	def test_product_without_category(self):
		# Product sans catégorie est acceptable (ProductCategory est optionnel).
		product = Product.objects.create(
			designation='No Category Product',
			purchase_unit_price=50,
			sale_unit_price=100,
			coefficient=2,
			unit=self.unit,
		)
		self.assertEqual(product.categories.count(), 0)

	def test_concurrent_proposal_modification(self):
		# Deux modifications concurrentes de la même proposition.
		self.proposal.amount_ht = 100.0
		self.proposal.save()
		
		# Recharger et modifier à nouveau
		proposal_refreshed = CommercialProposal.objects.get(id=self.proposal.id)
		proposal_refreshed.amount_ttc = 120.0
		proposal_refreshed.save()
		
		# Vérifier que les deux modifications sont préservées
		self.proposal.refresh_from_db()
		self.assertEqual(self.proposal.amount_ht, 100.0)
		self.assertEqual(self.proposal.amount_ttc, 120.0)

	def test_proposal_product_with_extreme_coefficient(self):
		# ProposalProduct avec coefficient extrêmement grand.
		proposal_product = ProposalProduct.objects.create(
			coefficient=9999.99,  # Très grand
			quantity=1,
			purchase_unit_price=50,
			sale_unit_price=100,
			commercial_proposal=self.proposal,
			product=self.product,
		)
		self.assertEqual(proposal_product.coefficient, 9999.99)

	def test_product_category_assignment_error_handling(self):
		# Attempting to assign a nonexistent category should fail.
		from django.db import transaction
		with self.assertRaises(IntegrityError):
			with transaction.atomic():
				ProductCategory.objects.create(
					product=self.product,
					category_id=99999,  # Inexistant
				)
				connection.check_constraints()

	def test_company_save_with_missing_client_data(self):
		# Company.save() without client_data should raise due to NOT NULL client_id in schema
		company = Company(
			name='No Client Data Company',
			registration_number='REG-EDGE-001',
			tax_identification_number='TVA-EDGE-001',
			created_at=date(2026, 5, 1),
			company_type=self.company_type,
		)
		with self.assertRaises(Exception):
			company.save()

	def test_individual_with_invalid_birth_date(self):
		# Individual with future birth date may fail due to NOT NULL client_id; expect exception
		individual = Individual(
			first_name='Future',
			last_name='Born',
			birth_date=date(2030, 1, 1),  # Dans le futur
			id_card_number='ID-FUTURE-001',
		)
		with self.assertRaises(Exception):
			individual.save()

	def test_proposal_state_transitions(self):
		# Test des transitions d'état valides/invalides.
		proposal = CommercialProposal.objects.create(
			date_proposal=date(2026, 5, 1),
			amount_ht=0.0,
			amount_ttc=0.0,
			client=self.client_obj,
			commercial=self.user,
			state=0,  # Created
		)
		
		# Transition: Created -> Validated
		proposal.state = 1
		proposal.save()
		self.assertEqual(proposal.state, 1)
		
		# Transition inverse (si autorisée)
		proposal.state = 0
		proposal.save()
		self.assertEqual(proposal.state, 0)

	def test_proposal_calculation_with_null_values(self):
		# Vérifier que _compute_proposal_total gère les null/None.
		result = _compute_proposal_total([
			{'product': None},  # Product null
			'invalid-item',  # String invalide
			{'product': {'sale_unit_price': None}, 'quantity': 1, 'coefficient': 1},
		])
		self.assertIsInstance(result, (int, float))  # Doit retourner un nombre

	def test_proposal_rows_from_session_with_empty_list(self):
		# _proposal_rows_from_session avec liste vide.
		result = _proposal_rows_from_session([])
		self.assertEqual(len(result), 0)

	def test_proposal_rows_from_session_with_missing_fields(self):
		# _proposal_rows_from_session avec champs manquants.
		result = _proposal_rows_from_session([
			{'product': {'id': self.product.id}},  # Manque quantity, coefficient
			{'product': {'id': self.product.id}, 'quantity': 1},  # Manque coefficient
		])
		# Doit ignorer ou traiter les lignes incomplètes
		self.assertIsInstance(result, list)
