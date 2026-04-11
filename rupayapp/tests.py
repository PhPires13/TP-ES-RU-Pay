from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .forms import CardNumberForm, StudentLoginForm, UserRegistrationForm
from .models import User


class CardNumberValidationTests(TestCase):
	def test_card_number_form_accepts_exactly_8_digits(self):
		form = CardNumberForm({'card_number': '12345678'})

		self.assertTrue(form.is_valid())

	def test_card_number_form_rejects_non_8_digit_values(self):
		form = CardNumberForm({'card_number': '2024010'})

		self.assertFalse(form.is_valid())
		self.assertIn('card_number', form.errors)

	def test_user_model_rejects_non_8_digit_card_numbers(self):
		user = User(username='teste', name='Teste', card_number='2024010')

		with self.assertRaises(ValidationError):
			user.full_clean()

	def test_student_login_form_accepts_username_and_password(self):
		form = StudentLoginForm({'username': 'aluno', 'password': 'segredo'})

		self.assertTrue(form.is_valid())

	def test_user_registration_form_hashes_password(self):
		form = UserRegistrationForm(
			{
				'username': 'aluno',
				'name': 'Aluno Teste',
				'card_number': '12345678',
				'password': 'segredo123',
				'password_confirm': 'segredo123',
			}
		)

		self.assertTrue(form.is_valid())
		user = form.save(commit=False)
		self.assertNotEqual(user.password_hash, 'segredo123')
		self.assertTrue(user.check_password('segredo123'))

	def test_user_registration_form_shows_password_mismatch_error(self):
		form = UserRegistrationForm(
			{
				'username': 'aluno2',
				'name': 'Aluno Teste 2',
				'card_number': '23456789',
				'password': 'segredo123',
				'password_confirm': 'diferente123',
			}
		)

		self.assertFalse(form.is_valid())
		self.assertIn('password_confirm', form.errors)
		self.assertIn('As senhas não conferem.', form.errors['password_confirm'])


class StudentLoginFlowTests(TestCase):
	def setUp(self):
		self.user = User.objects.create(
			username='aluno_teste',
			name='Aluno Teste',
			card_number='87654321',
		)
		self.user.set_password('senha123')
		self.user.save()

	def test_login_sets_session_and_redirects_to_dashboard(self):
		response = self.client.post(
			reverse('rupayapp:student_lookup'),
			{'username': 'aluno_teste', 'password': 'senha123'},
			follow=True,
		)

		self.assertContains(response, 'Aluno Teste')
		self.assertEqual(str(self.client.session.get('student_user_id')), str(self.user.id))

	def test_invalid_login_does_not_set_session(self):
		response = self.client.post(
			reverse('rupayapp:student_lookup'),
			{'username': 'aluno_teste', 'password': 'senha_errada'},
		)

		self.assertContains(response, 'Usuário ou senha inválidos.')
		self.assertIsNone(self.client.session.get('student_user_id'))

	def test_logout_clears_session(self):
		session = self.client.session
		session['student_user_id'] = str(self.user.id)
		session.save()

		response = self.client.post(reverse('rupayapp:student_lookup'), {'logout': '1'}, follow=True)

		self.assertContains(response, 'Você saiu da área do aluno.')
		self.assertIsNone(self.client.session.get('student_user_id'))

	def test_student_history_requires_login(self):
		response = self.client.get(reverse('rupayapp:student_history'), follow=True)

		self.assertContains(response, 'Entre com usuário e senha para ver o extrato.')

	def test_student_register_displays_password_mismatch_message(self):
		response = self.client.post(
			reverse('rupayapp:student_register'),
			{
				'username': 'novo_aluno',
				'name': 'Novo Aluno',
				'card_number': '34567890',
				'password': 'senha12345',
				'password_confirm': 'senha54321',
			},
		)

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'As senhas não conferem.')

