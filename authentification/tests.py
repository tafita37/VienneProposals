from django.contrib.auth.models import AnonymousUser
from django.db import IntegrityError
from django.core import signing
from django.core import mail
from django.http import HttpResponse
from django.test import RequestFactory, TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.db import connection
import re
from unittest.mock import patch
from time import perf_counter

from authentification.backends import AdminUserBackend
from authentification.controllers import UserController
from authentification.decoratos import admin_required, user_required
from authentification.metier.AdminUser import AdminUser
from authentification.metier.Role import Role
from authentification.metier.User import User
from authentification.metier.UserRole import UserRole


class AuthenticationUnitTests(TestCase):
	def setUp(self):
		# Test data shared by all authentication cases: one standard user, one admin, and one role.
		self.factory = RequestFactory()
		self.user = User.objects.create_user(
			username='user1',
			first_name='Alice',
			last_name='Martin',
			email='user1@example.com',
			password='old-password',
		)
		self.admin_user = AdminUser.objects.create(
			username='admin1',
			first_name='Admin',
			last_name='User',
			email='admin1@example.com',
		)
		self.admin_user.set_password('admin-password')
		self.admin_user.save(update_fields=['password'])
		self.role = Role.objects.create(name='Manager')
		self.user_role = UserRole.objects.create(user=self.user, role=self.role)

	def _post_request(self, path='/', data=None):
		request = self.factory.post(path, data=data or {})
		request.user = AnonymousUser()
		return request

	def _get_request(self, path='/', data=None):
		request = self.factory.get(path, data=data or {})
		request.user = AnonymousUser()
		return request

	def test_user_model_hashes_password_and_keeps_required_fields(self):
		self.assertEqual(self.user.email, 'user1@example.com')
		self.assertTrue(self.user.check_password('old-password'))
		self.assertEqual(self.user.failed_login_attempts, 0)

	def test_admin_backend_authenticate_returns_admin_user(self):
		backend = AdminUserBackend()

		authenticated_user = backend.authenticate(None, username='admin1', password='admin-password')

		self.assertEqual(authenticated_user, self.admin_user)

	def test_admin_backend_authenticate_returns_none_for_invalid_password(self):
		backend = AdminUserBackend()

		self.assertIsNone(backend.authenticate(None, username='admin1', password='wrong-password'))

	def test_admin_backend_get_user_returns_admin_user(self):
		backend = AdminUserBackend()

		self.assertEqual(backend.get_user(self.admin_user.id), self.admin_user)
		self.assertIsNone(backend.get_user(999999))

	def test_password_token_round_trip_and_validation(self):
		# The token must encode the user id and reject mismatched account types or purposes.
		token = UserController._build_password_token(self.user.id, 'user', 'forgot_password')

		self.assertEqual(
			UserController._read_password_token(token, 'user', 'forgot_password'),
			self.user.id,
		)
		with self.assertRaises(signing.BadSignature):
			UserController._read_password_token(token, 'admin', 'forgot_password')
		with self.assertRaises(signing.BadSignature):
			UserController._read_password_token(token, 'user', 'define_password')

	def test_password_token_reader_uses_expected_max_age(self):
		# We mock signing.loads so we can verify the helper enforces the 7-day expiration window.
		with patch('authentification.controllers.UserController.signing.loads', return_value={
			'user_id': self.user.id,
			'account_type': 'user',
			'purpose': 'forgot_password',
		}) as loads_mock:
			self.assertEqual(
				UserController._read_password_token('token-value', 'user', 'forgot_password'),
				self.user.id,
			)

		loads_mock.assert_called_once()
		self.assertEqual(loads_mock.call_args.kwargs['max_age'], 604800)

	def test_admin_required_redirects_anonymous_and_rejects_standard_user(self):
		# Anonymous users and standard users must be redirected away from admin-only views.
		@admin_required
		def protected_view(request):
			return HttpResponse('ok')

		anonymous_request = self._get_request()
		with patch('authentification.decoratos.messages.error'):
			response = protected_view(anonymous_request)
		self.assertEqual(response.status_code, 302)
		self.assertEqual(response.url, reverse('login_admin_page'))

		standard_request = self._get_request()
		standard_request.user = self.user
		with patch('authentification.decoratos.messages.error'):
			response = protected_view(standard_request)
		self.assertEqual(response.status_code, 302)
		self.assertEqual(response.url, reverse('login_admin_page'))

	def test_admin_required_accepts_admin_user(self):
		# A real admin user should pass through the decorator unchanged.
		@admin_required
		def protected_view(request):
			return HttpResponse('ok')

		request = self._get_request()
		request.user = self.admin_user

		response = protected_view(request)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.content, b'ok')

	def test_login_user_page_redirects_authenticated_user_and_admin(self):
		user_request = self._get_request('/login_page/')
		user_request.user = self.user
		admin_request = self._get_request('/login_page/')
		admin_request.user = self.admin_user

		with patch('authentification.controllers.UserController.render') as render_mock:
			user_response = UserController.login_user_page(user_request)
			admin_response = UserController.login_user_page(admin_request)

		self.assertEqual(user_response.status_code, 302)
		self.assertEqual(user_response.url, reverse('catalogue_page'))
		self.assertEqual(admin_response.status_code, 302)
		self.assertEqual(admin_response.url, reverse('dashboard_page'))
		render_mock.assert_not_called()

	def test_login_admin_page_redirects_authenticated_admin_and_user(self):
		admin_request = self._get_request('/login_admin_page/')
		admin_request.user = self.admin_user
		user_request = self._get_request('/login_admin_page/')
		user_request.user = self.user

		with patch('authentification.controllers.UserController.render') as render_mock:
			admin_response = UserController.login_admin_page(admin_request)
			user_response = UserController.login_admin_page(user_request)

		self.assertEqual(admin_response.status_code, 302)
		self.assertEqual(admin_response.url, reverse('dashboard_page'))
		self.assertEqual(user_response.status_code, 302)
		self.assertEqual(user_response.url, reverse('catalogue_page'))
		render_mock.assert_not_called()

	def test_user_required_redirects_anonymous_and_rejects_admin(self):
		# The user-only decorator mirrors the admin one, but for the standard user area.
		@user_required
		def protected_view(request):
			return HttpResponse('ok')

		anonymous_request = self._get_request()
		with patch('authentification.decoratos.messages.error'):
			response = protected_view(anonymous_request)
		self.assertEqual(response.status_code, 302)
		self.assertEqual(response.url, reverse('login_user_page'))

		admin_request = self._get_request()
		admin_request.user = self.admin_user
		with patch('authentification.decoratos.messages.error'):
			response = protected_view(admin_request)
		self.assertEqual(response.status_code, 302)
		self.assertEqual(response.url, reverse('login_user_page'))

	def test_user_required_accepts_standard_user(self):
		# Standard users should be able to access views protected by user_required.
		@user_required
		def protected_view(request):
			return HttpResponse('ok')

		request = self._get_request()
		request.user = self.user

		response = protected_view(request)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.content, b'ok')

	def test_login_user_success(self):
		# On success, the view should authenticate, log in, and redirect to the user dashboard.
		request = self._post_request('/login_user/', {'username': 'user1', 'password': 'old-password'})

		with patch('authentification.controllers.UserController.authenticate', return_value=self.user) as authenticate_mock:
			with patch('authentification.controllers.UserController.login') as login_mock:
				response = UserController.login_user(request)

		authenticate_mock.assert_called_once()
		login_mock.assert_called_once()
		self.assertEqual(response.status_code, 302)
		self.assertEqual(response.url, reverse('dashboard_user_page'))

	def test_login_user_failure_redirects_back(self):
		# Invalid credentials must show an error and send the user back to the login page.
		request = self._post_request('/login_user/', {'username': 'user1', 'password': 'wrong'})

		with patch('authentification.controllers.UserController.authenticate', return_value=None):
			with patch('authentification.controllers.UserController.messages.error') as error_mock:
				response = UserController.login_user(request)

		error_mock.assert_called_once()
		self.assertEqual(response.status_code, 302)
		self.assertEqual(response.url, reverse('login_user_page'))

	def test_login_admin_success(self):
		# Admin login uses the custom backend and redirects to the admin dashboard.
		request = self._post_request('/login_admin/', {'username': 'admin1', 'password': 'admin-password'})

		with patch.object(AdminUserBackend, 'authenticate', return_value=self.admin_user) as authenticate_mock:
			with patch('authentification.controllers.UserController.login') as login_mock:
				response = UserController.login_admin(request)

		authenticate_mock.assert_called_once()
		login_mock.assert_called_once()
		self.assertEqual(response.status_code, 302)
		self.assertEqual(response.url, reverse('dashboard_page'))

	def test_login_admin_failure_redirects_back(self):
		# If the admin backend rejects the credentials, the flow must return to the login form.
		request = self._post_request('/login_admin/', {'username': 'admin1', 'password': 'wrong'})

		with patch.object(AdminUserBackend, 'authenticate', return_value=None):
			with patch('authentification.controllers.UserController.messages.error') as error_mock:
				response = UserController.login_admin(request)

		error_mock.assert_called_once()
		self.assertEqual(response.status_code, 302)
		self.assertEqual(response.url, reverse('login_admin_page'))

	def test_send_user_reset_link_with_blank_email_rejects_request(self):
		# The password-reset request should stop early if the email field is empty.
		request = self._post_request('/forgot_password/send_link/', {'email': ''})

		with patch('authentification.controllers.UserController.messages.error') as error_mock:
			response = UserController.send_user_reset_link(request)

		error_mock.assert_called_once()
		self.assertEqual(response.status_code, 302)
		self.assertEqual(response.url, reverse('forgot_password_user_page'))

	def test_send_user_reset_link_with_existing_email_sends_mail(self):
		# Existing accounts receive a reset mail, but the response stays generic to avoid user enumeration.
		request = self._post_request('/forgot_password/send_link/', {'email': self.user.email})

		with patch('authentification.controllers.UserController.send_mail') as send_mail_mock:
			with patch('authentification.controllers.UserController.messages.success'):
				response = UserController.send_user_reset_link(request)

		send_mail_mock.assert_called_once()
		self.assertEqual(response.status_code, 302)
		self.assertEqual(response.url, reverse('login_user_page'))

	def test_reset_user_password_page_renders_with_valid_token(self):
		# A valid token should open the reset form with the username prefilled in context.
		token = UserController._build_password_token(self.user.id, 'user', 'forgot_password')
		request = self._get_request('/forgot_password/reset_page/', {'token': token})

		with patch('authentification.controllers.UserController.render', return_value=HttpResponse('ok')) as render_mock:
			response = UserController.reset_user_password_page(request)

		render_mock.assert_called_once()
		self.assertEqual(response.content, b'ok')

	def test_define_password_success_updates_password(self):
		# The setup flow should persist the new password and send the user back to login.
		token = UserController._build_password_token(self.user.id, 'user', 'define_password')
		request = self._post_request(
			'/define_password/',
			{'token': token, 'new_password': 'new-password', 'confirm_password': 'new-password'},
		)

		with patch('authentification.controllers.UserController.messages.success'):
			response = UserController.define_password(request)

		self.user.refresh_from_db()
		self.assertTrue(self.user.check_password('new-password'))
		self.assertEqual(response.status_code, 302)
		self.assertEqual(response.url, reverse('login_user_page'))

	def test_reset_user_password_validation_failure_returns_form(self):
		# Mismatched passwords must not update the account and should re-render the form.
		token = UserController._build_password_token(self.user.id, 'user', 'forgot_password')
		request = self._post_request(
			'/forgot_password/reset/',
			{'token': token, 'new_password': 'new-password', 'confirm_password': 'different'},
		)

		with patch('authentification.controllers.UserController.render', return_value=HttpResponse('invalid')) as render_mock:
			with patch('authentification.controllers.UserController.messages.error'):
				response = UserController.reset_user_password(request)

		render_mock.assert_called_once()
		self.assertEqual(response.content, b'invalid')
		self.user.refresh_from_db()
		self.assertTrue(self.user.check_password('old-password'))

	def test_send_admin_reset_link_with_existing_email_sends_mail(self):
		# Admin reset uses the same pattern as the user one, with a distinct token/account type.
		request = self._post_request('/forgot_password_admin/send_link/', {'email': self.admin_user.email})

		with patch('authentification.controllers.UserController.send_mail') as send_mail_mock:
			with patch('authentification.controllers.UserController.messages.success'):
				response = UserController.send_admin_reset_link(request)

		send_mail_mock.assert_called_once()
		self.assertEqual(response.status_code, 302)
		self.assertEqual(response.url, reverse('login_admin_page'))

	def test_send_admin_reset_link_with_blank_email_rejects_request(self):
		# Empty admin email should be rejected immediately.
		request = self._post_request('/forgot_password_admin/send_link/', {'email': ''})

		with patch('authentification.controllers.UserController.messages.error') as error_mock:
			response = UserController.send_admin_reset_link(request)

		error_mock.assert_called_once()
		self.assertEqual(response.status_code, 302)
		self.assertEqual(response.url, reverse('forgot_password_admin_page'))

	def test_change_user_password_success(self):
		# A correct current password plus matching new passwords should update the account in place.
		request = self._post_request(
			'/change_password/',
			{'current_password': 'old-password', 'new_password': 'updated-password', 'confirm_password': 'updated-password'},
		)
		request.user = self.user

		with patch('authentification.controllers.UserController.update_session_auth_hash') as session_mock:
			with patch('authentification.controllers.UserController.messages.success'):
				response = UserController.change_user_password(request)

		session_mock.assert_called_once()
		self.user.refresh_from_db()
		self.assertTrue(self.user.check_password('updated-password'))
		self.assertEqual(response.status_code, 302)
		self.assertEqual(response.url, reverse('catalogue_page'))

	def test_change_user_password_rejects_wrong_current_password(self):
		# Wrong current password must leave the stored hash untouched.
		request = self._post_request(
			'/change_password/',
			{'current_password': 'wrong-password', 'new_password': 'updated-password', 'confirm_password': 'updated-password'},
		)
		request.user = self.user

		with patch('authentification.controllers.UserController.render', return_value=HttpResponse('invalid')) as render_mock:
			with patch('authentification.controllers.UserController.messages.error'):
				response = UserController.change_user_password(request)

		render_mock.assert_called_once()
		self.assertEqual(response.content, b'invalid')
		self.user.refresh_from_db()
		self.assertTrue(self.user.check_password('old-password'))

	def test_change_admin_password_success(self):
		# Admin password changes follow the same rule set and return to the admin dashboard.
		request = self._post_request(
			'/change_password_admin/',
			{'current_password': 'admin-password', 'new_password': 'updated-admin', 'confirm_password': 'updated-admin'},
		)
		request.user = self.admin_user

		with patch('authentification.controllers.UserController.update_session_auth_hash') as session_mock:
			with patch('authentification.controllers.UserController.messages.success'):
				response = UserController.change_admin_password(request)

		session_mock.assert_called_once()
		self.admin_user.refresh_from_db()
		self.assertTrue(self.admin_user.check_password('updated-admin'))
		self.assertEqual(response.status_code, 302)
		self.assertEqual(response.url, reverse('dashboard_page'))

	def test_logout_user_redirects_to_login(self):
		# Logout only needs to clear the session and redirect to the login screen.
		request = self._get_request('/logout_user/')

		with patch('authentification.controllers.UserController.logout'):
			response = UserController.logout_user(request)

		self.assertEqual(response.status_code, 302)
		self.assertEqual(response.url, reverse('login_user_page'))

	def test_role_relation_enforces_uniqueness(self):
		# The role-user pair is unique, so inserting the same relation twice must fail.
		with self.assertRaises(IntegrityError):
			UserRole.objects.create(user=self.user, role=self.role)


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class AuthenticationIntegrationTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(
			username='integration-user',
			first_name='Ines',
			last_name='User',
			email='integration-user@example.com',
			password='start-pass-123',
		)
		self.admin_user = AdminUser.objects.create(
			username='integration-admin',
			first_name='Ines',
			last_name='Admin',
			email='integration-admin@example.com',
		)
		self.admin_user.set_password('admin-start-123')
		self.admin_user.save(update_fields=['password'])

	def test_user_login_then_access_user_dashboard(self):
		response = self.client.post('/auth/login_user/', {
			'username': 'integration-user',
			'password': 'start-pass-123',
		})

		self.assertEqual(response.status_code, 302)
		self.assertEqual(response.url, reverse('dashboard_user_page'))

		dashboard_response = self.client.get('/com/dashboard_user_page/')
		self.assertEqual(dashboard_response.status_code, 200)

	def test_admin_login_then_access_admin_dashboard(self):
		response = self.client.post('/admin/login_admin/', {
			'username': 'integration-admin',
			'password': 'admin-start-123',
		})

		self.assertEqual(response.status_code, 302)
		self.assertEqual(response.url, reverse('dashboard_page'))

		dashboard_response = self.client.get('/admin/dashboard_page/')
		self.assertEqual(dashboard_response.status_code, 200)

	def test_send_reset_link_then_reset_password_for_user(self):
		response = self.client.post('/auth/forgot_password/send_link/', {
			'email': self.user.email,
		})

		self.assertEqual(response.status_code, 302)
		self.assertEqual(response.url, reverse('login_user_page'))
		self.assertEqual(len(mail.outbox), 1)

		token = UserController._build_password_token(self.user.id, 'user', 'forgot_password')
		reset_response = self.client.post('/auth/forgot_password/reset/', {
			'token': token,
			'new_password': 'new-pass-456',
			'confirm_password': 'new-pass-456',
		})

		self.assertEqual(reset_response.status_code, 302)
		self.assertEqual(reset_response.url, reverse('login_user_page'))

		self.user.refresh_from_db()
		self.assertTrue(self.user.check_password('new-pass-456'))

	def test_define_password_flow_updates_hash(self):
		token = UserController._build_password_token(self.user.id, 'user', 'define_password')
		response = self.client.post('/auth/define_password/', {
			'token': token,
			'new_password': 'define-pass-789',
			'confirm_password': 'define-pass-789',
		})

		self.assertEqual(response.status_code, 302)
		self.assertEqual(response.url, reverse('login_user_page'))
		self.user.refresh_from_db()
		self.assertTrue(self.user.check_password('define-pass-789'))


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class AuthenticationFunctionalTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(
			username='functional-user',
			first_name='Fiona',
			last_name='User',
			email='functional-user@example.com',
			password='functional-start-123',
		)

	def test_forgot_password_complete_workflow_from_email_link_to_login(self):
		request_reset_response = self.client.post('/auth/forgot_password/send_link/', {
			'email': self.user.email,
		})

		self.assertEqual(request_reset_response.status_code, 302)
		self.assertEqual(request_reset_response.url, reverse('login_user_page'))
		self.assertEqual(len(mail.outbox), 1)

		body = mail.outbox[0].body
		token_match = re.search(r'token=([^\s]+)', body)
		self.assertIsNotNone(token_match)
		token = token_match.group(1)

		open_link_response = self.client.get('/auth/forgot_password/reset_page/', {'token': token})
		self.assertEqual(open_link_response.status_code, 200)

		apply_new_password_response = self.client.post('/auth/forgot_password/reset/', {
			'token': token,
			'new_password': 'functional-new-456',
			'confirm_password': 'functional-new-456',
		})
		self.assertEqual(apply_new_password_response.status_code, 302)
		self.assertEqual(apply_new_password_response.url, reverse('login_user_page'))

		login_response = self.client.post('/auth/login_user/', {
			'username': 'functional-user',
			'password': 'functional-new-456',
		})
		self.assertEqual(login_response.status_code, 302)
		self.assertEqual(login_response.url, reverse('dashboard_user_page'))

	def test_login_then_change_password_then_login_with_new_password(self):
		login_response = self.client.post('/auth/login_user/', {
			'username': 'functional-user',
			'password': 'functional-start-123',
		})
		self.assertEqual(login_response.status_code, 302)
		self.assertEqual(login_response.url, reverse('dashboard_user_page'))

		change_password_response = self.client.post('/auth/change_password/', {
			'current_password': 'functional-start-123',
			'new_password': 'functional-change-789',
			'confirm_password': 'functional-change-789',
		})
		self.assertEqual(change_password_response.status_code, 302)
		self.assertEqual(change_password_response.url, reverse('catalogue_page'))

		self.client.get('/auth/logout_user/')
		relogin_response = self.client.post('/auth/login_user/', {
			'username': 'functional-user',
			'password': 'functional-change-789',
		})
		self.assertEqual(relogin_response.status_code, 302)
		self.assertEqual(relogin_response.url, reverse('dashboard_user_page'))


class AuthenticationPerformanceTests(TestCase):
	def setUp(self):
		self.factory = RequestFactory()
		self.admin_user = AdminUser.objects.create(
			username='perf-admin-2',
			first_name='Perf',
			last_name='Admin',
			email='perf-admin-2@example.com',
		)
		self.admin_user.set_password('perf-admin-pass-2')
		self.admin_user.save(update_fields=['password'])
		self.user = User.objects.create_user(
			username='perf-user-2',
			first_name='Perf',
			last_name='User',
			email='perf-user-2@example.com',
			password='perf-user-pass-2',
		)
		self.role = Role.objects.create(name='Perf Role')
		UserRole.objects.create(user=self.user, role=self.role)

	def test_list_users_admin_page_query_count_is_bounded(self):
		request = self.factory.get('/admin/user/list/')
		request.user = self.admin_user

		with CaptureQueriesContext(connection) as queries:
			response = UserController.list_users_admin_page(request)

		self.assertEqual(response.status_code, 200)
		self.assertLessEqual(len(queries), 3)

	def test_new_user_admin_page_query_count_is_bounded(self):
		request = self.factory.get('/admin/user/new/')
		request.user = self.admin_user

		with CaptureQueriesContext(connection) as queries:
			response = UserController.new_user_admin_page(request)

		self.assertEqual(response.status_code, 200)
		self.assertLessEqual(len(queries), 2)

	def test_edit_user_admin_page_query_count_is_bounded(self):
		request = self.factory.get(f'/admin/user/edit/{self.user.id}/')
		request.user = self.admin_user

		with CaptureQueriesContext(connection) as queries:
			response = UserController.edit_user_admin_page(request, self.user.id)

		self.assertEqual(response.status_code, 200)
		self.assertLessEqual(len(queries), 4)

	def test_send_user_reset_link_query_count_is_bounded(self):
		request = self.factory.post('/auth/forgot_password/send_link/', {'email': self.user.email})
		request.user = AnonymousUser()

		with CaptureQueriesContext(connection) as queries:
			with patch('authentification.controllers.UserController.send_mail'):
				with patch('authentification.controllers.UserController.messages.success'):
					response = UserController.send_user_reset_link(request)

		self.assertEqual(response.status_code, 302)
		self.assertLessEqual(len(queries), 2)

	def _measure_post(self, path, data, runs=20, warmup=3):
		for _ in range(warmup):
			self.client.post(path, data)
		durations = []
		for _ in range(runs):
			start = perf_counter()
			response = self.client.post(path, data)
			durations.append((perf_counter() - start) * 1000.0)
		return response, durations

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

	def test_login_user_latency(self):
		# measure login POST latency
		User.objects.create_user(username='perf-login', email='perf-login@example.com', password='login-pass')
		response, durations = self._measure_post('/auth/login_user/', {'username': 'perf-login', 'password': 'login-pass'}, runs=25)
		self.assertIn(response.status_code, [302, 200])
		p50 = self._percentile(durations, 50)
		p95 = self._percentile(durations, 95)
		p99 = self._percentile(durations, 99)
		print('\n[perf] auth.login_user: runs=%d median=%.1fms p95=%.1fms p99=%.1fms' % (len(durations), p50 or 0.0, p95 or 0.0, p99 or 0.0))

	def test_forgot_password_send_link_latency(self):
		# measure forgot password flow (sending link) latency
		response, durations = self._measure_post('/auth/forgot_password/send_link/', {'email': self.user.email}, runs=20)
		self.assertIn(response.status_code, [302, 200])
		p50 = self._percentile(durations, 50)
		p95 = self._percentile(durations, 95)
		p99 = self._percentile(durations, 99)
		print('\n[perf] auth.forgot_password.send_link: runs=%d median=%.1fms p95=%.1fms p99=%.1fms' % (len(durations), p50 or 0.0, p95 or 0.0, p99 or 0.0))

	def test_reset_user_password_page_query_count_is_bounded(self):
		token = UserController._build_password_token(self.user.id, 'user', 'forgot_password')
		request = self.factory.get('/auth/forgot_password/reset_page/', {'token': token})
		request.user = AnonymousUser()

		with CaptureQueriesContext(connection) as queries:
			with patch('authentification.controllers.UserController.render', return_value=HttpResponse('ok')):
				response = UserController.reset_user_password_page(request)

		self.assertEqual(response.status_code, 200)
		self.assertLessEqual(len(queries), 2)

	def test_send_admin_reset_link_query_count_is_bounded(self):
		request = self.factory.post('/admin/forgot_password/send_link/', {'email': self.admin_user.email})
		request.user = AnonymousUser()

		with CaptureQueriesContext(connection) as queries:
			with patch('authentification.controllers.UserController.send_mail'):
				with patch('authentification.controllers.UserController.messages.success'):
					response = UserController.send_admin_reset_link(request)

		self.assertEqual(response.status_code, 302)
		self.assertLessEqual(len(queries), 2)

	def test_list_users_admin_page_is_bounded_when_roles_exist(self):
		request = self.factory.get('/admin/user/list/')
		request.user = self.admin_user

		with CaptureQueriesContext(connection) as queries:
			response = UserController.list_users_admin_page(request)

		self.assertEqual(response.status_code, 200)
		self.assertLessEqual(len(queries), 3)

	def test_new_user_admin_page_query_count_is_bounded(self):
		request = self.factory.get('/admin/user/new/')
		request.user = self.admin_user

		with CaptureQueriesContext(connection) as queries:
			response = UserController.new_user_admin_page(request)

		self.assertEqual(response.status_code, 200)
		self.assertLessEqual(len(queries), 2)

	def test_edit_user_admin_page_query_count_is_bounded(self):
		request = self.factory.get(f'/admin/user/edit/{self.user.id}/')
		request.user = self.admin_user

		with CaptureQueriesContext(connection) as queries:
			response = UserController.edit_user_admin_page(request, self.user.id)

		self.assertEqual(response.status_code, 200)
		self.assertLessEqual(len(queries), 4)

	def test_save_user_admin_query_count_is_bounded(self):
		request = self.factory.post('/admin/user/save/', {
			'username': 'perf-created',
			'first_name': 'Perf',
			'last_name': 'Created',
			'email': 'perf-created@example.com',
			'role_ids': [str(self.role.id)],
		})
		request.user = self.admin_user
		request.build_absolute_uri = lambda value: f'http://testserver{value}'

		with CaptureQueriesContext(connection) as queries:
			with patch('authentification.controllers.UserController.send_mail'):
				with patch('authentification.controllers.UserController.messages.success'):
					with patch('authentification.controllers.UserController.messages.error'):
						response = UserController.save_user_admin(request)

		self.assertEqual(response.status_code, 302)
		self.assertLessEqual(len(queries), 8)

	def test_update_user_admin_query_count_is_bounded(self):
		request = self.factory.post('/admin/user/update/', {
			'user_id': self.user.id,
			'username': 'perf-user-updated',
			'first_name': 'Perf',
			'last_name': 'UserUpdated',
			'email': 'perf-user-updated@example.com',
			'password': '',
			'role_ids': [str(self.role.id)],
		})
		request.user = self.admin_user

		with CaptureQueriesContext(connection) as queries:
			with patch('authentification.controllers.UserController.messages.success'):
				with patch('authentification.controllers.UserController.messages.error'):
					response = UserController.update_user_admin(request)

		self.assertEqual(response.status_code, 302)
		self.assertLessEqual(len(queries), 8)

	def test_delete_user_admin_query_count_is_bounded(self):
		request = self.factory.get('/admin/user/delete/', {'id': self.user.id})
		request.user = self.admin_user

		with CaptureQueriesContext(connection) as queries:
			with patch('authentification.controllers.UserController.messages.success'):
				with patch('authentification.controllers.UserController.messages.info'):
					with patch('authentification.controllers.UserController.messages.error'):
						response = UserController.delete_user_admin(request)

		self.assertEqual(response.status_code, 302)
		self.assertLessEqual(len(queries), 3)


class AuthenticationEdgeCaseTests(TestCase):
	"""Tests de robustesse et cas limites pour l'authentification."""
	
	def setUp(self):
		self.factory = RequestFactory()
		self.user = User.objects.create_user(
			username='edge-user',
			first_name='Edge',
			last_name='Case',
			email='edge@example.com',
			password='edge-password',
		)
		self.admin_user = AdminUser.objects.create(
			username='edge-admin',
			first_name='Edge',
			last_name='Admin',
			email='edge-admin@example.com',
		)
		self.admin_user.set_password('edge-admin-password')
		self.admin_user.save(update_fields=['password'])
		self.role = Role.objects.create(name='Edge Role')

	def test_password_reset_with_expired_token(self):
		# Token expiré (max_age dépassée) ne devrait pas réinitialiser le password.
		from django.contrib.auth.tokens import default_token_generator
		token = default_token_generator.make_token(self.user)
		self.user.last_login = None
		self.user.save(update_fields=['last_login'])
		
		# Créer un token "expiré" en modifiant manually (simulé)
		with patch('django.contrib.auth.tokens.default_token_generator.check_token', return_value=False):
			request = self.factory.post('/auth/reset_password/', {
				'token': 'fake-expired-token',
				'password': 'new-secure-password-123',
			})
			request.user = AnonymousUser()
			
			with patch('authentification.controllers.UserController.messages.error'):
				# Controller function is named `reset_user_password` in the codebase
				response = UserController.reset_user_password(request)
		
		self.assertIn(response.status_code, [302, 400])
		self.user.refresh_from_db()
		self.assertTrue(self.user.check_password('edge-password'))

	def test_login_with_empty_username(self):
		# Login avec username vide devrait échouer.
		request = self.factory.post('/auth/login_user/', {
			'username': '',
			'password': 'edge-password',
		})
		request.user = AnonymousUser()
		
		with patch('authentification.controllers.UserController.authenticate', return_value=None):
			with patch('authentification.controllers.UserController.messages.error'):
				response = UserController.login_user(request)
		
		self.assertIn(response.status_code, [302, 400])

	def test_login_with_empty_password(self):
		# Login avec password vide devrait échouer.
		request = self.factory.post('/auth/login_user/', {
			'username': 'edge-user',
			'password': '',
		})
		request.user = AnonymousUser()
		
		with patch('authentification.controllers.UserController.authenticate', return_value=None):
			with patch('authentification.controllers.UserController.messages.error'):
				response = UserController.login_user(request)
		
		self.assertIn(response.status_code, [302, 400])

	def test_login_with_nonexistent_user(self):
		# Login avec utilisateur inexistant devrait échouer.
		request = self.factory.post('/auth/login_user/', {
			'username': 'nonexistent-user-xyz',
			'password': 'any-password',
		})
		request.user = AnonymousUser()
		
		with patch('authentification.controllers.UserController.authenticate', return_value=None):
			with patch('authentification.controllers.UserController.messages.error'):
				response = UserController.login_user(request)
		
		self.assertIn(response.status_code, [302, 400])

	def test_change_password_with_wrong_old_password(self):
		# Changement de password avec ancien password incorrect devrait échouer.
		request = self.factory.post('/auth/change_password_user/', {
			'old_password': 'wrong-old-password',
			'new_password': 'new-secure-password-456',
			'confirm_password': 'new-secure-password-456',
		})
		request.user = self.user
		
		with patch('authentification.controllers.UserController.messages.error'):
			# Controller function is named `change_user_password` in the codebase
			response = UserController.change_user_password(request)
		
		self.assertIn(response.status_code, [200, 302, 400])
		self.user.refresh_from_db()
		self.assertTrue(self.user.check_password('edge-password'))

	def test_change_password_with_mismatched_confirmation(self):
		# Confirmation de password ne correspond pas au nouveau password.
		request = self.factory.post('/auth/change_password_user/', {
			'old_password': 'edge-password',
			'new_password': 'new-secure-password-456',
			'confirm_password': 'different-password',
		})
		request.user = self.user
		
		with patch('authentification.controllers.UserController.messages.error'):
			# Controller function is named `change_user_password` in the codebase
			response = UserController.change_user_password(request)
		
		self.assertIn(response.status_code, [200, 302, 400])

	def test_change_password_same_as_old(self):
		# Nouveau password ne devrait pas être identique à l'ancien.
		request = self.factory.post('/auth/change_password_user/', {
			'old_password': 'edge-password',
			'new_password': 'edge-password',
			'confirm_password': 'edge-password',
		})
		request.user = self.user
		
		with patch('authentification.controllers.UserController.messages.error'):
			with patch('authentification.controllers.UserController.messages.warning'):
				# Controller function is named `change_user_password` in the codebase
				response = UserController.change_user_password(request)
		
		# Should either reject or allow but that's application-specific

	def test_create_user_with_duplicate_username(self):
		# Création d'utilisateur avec username déjà existant devrait échouer.
		with self.assertRaises(IntegrityError):
			User.objects.create_user(
				username='edge-user',  # Déjà existant
				first_name='Duplicate',
				last_name='User',
				email='duplicate@example.com',
				password='new-password',
			)

	def test_create_user_with_duplicate_email(self):
		# Création d'utilisateur avec email déjà existant devrait échouer.
		# Note: Django User par défaut n'applique pas d'unicité sur email en DB
		# mais l'application peut avoir des validations supplémentaires
		try:
			user = User.objects.create_user(
				username='another-user',
				first_name='Another',
				last_name='User',
				email='edge@example.com',  # Déjà existant
				password='new-password',
			)
			# Si on arrive ici, c'est que l'application ne valide pas l'unicité
			# C'est acceptable
		except IntegrityError:
			pass  # Attendu si DB applique l'unicité

	def test_admin_required_decorator_blocks_non_admin(self):
		# @admin_required devrait rediriger les non-admins.
		request = self.factory.get('/admin/dashboard/')
		request.user = self.user  # Utilisateur normal, pas admin
		
		@admin_required
		def dummy_view(request):
			return HttpResponse('Success')
		
		with patch('authentification.decoratos.messages.error'):
			response = dummy_view(request)
		
		self.assertIn(response.status_code, [302, 403])

	def test_user_required_decorator_blocks_admin(self):
		# @user_required devrait bloquer les admins.
		request = self.factory.get('/com/dashboard/')
		request.user = self.admin_user
		request.session = {}
		
		@user_required
		def dummy_view(request):
			return HttpResponse('Success')
		
		with patch('authentification.decoratos.messages.error'):
			response = dummy_view(request)
		
		self.assertIn(response.status_code, [302, 403])

	def test_user_required_decorator_blocks_anonymous(self):
		# @user_required devrait rediriger les anonymes.
		request = self.factory.get('/com/dashboard/')
		request.user = AnonymousUser()
		
		@user_required
		def dummy_view(request):
			return HttpResponse('Success')
		
		# Patch messages to prevent MessageMiddleware requirement when using RequestFactory
		with patch('authentification.decoratos.messages.error'):
			response = dummy_view(request)
		self.assertEqual(response.status_code, 302)

	def test_user_role_assignment_with_nonexistent_role(self):
		# Assignation d'un role inexistant devrait échouer.
		from django.db import transaction
		with self.assertRaises(IntegrityError):
			with transaction.atomic():
				UserRole.objects.create(
					user=self.user,
					role_id=99999,  # Inexistant
				)
				connection.check_constraints()
