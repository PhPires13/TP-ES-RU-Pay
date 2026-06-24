from decimal import Decimal
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase, Client
from django.contrib.auth.hashers import check_password

from .forms import (
	CardNumberForm,
	StudentLoginForm,
	UserRegistrationForm,
	OnlineRechargeForm,
	OperatorRechargeForm,
	TurnstileForm,
)
from .models import User, Transaction
from .utils import meal_price, user_balance


class UserModelTests(TestCase):
	def setUp(self):
		self.user = User.objects.create(
			username='testuser',
			name='Test User',
			card_number='12345678'
		)

	def test_user_creation(self):
		self.assertEqual(self.user.username, 'testuser')
		self.assertEqual(self.user.name, 'Test User')
		self.assertEqual(self.user.card_number, '12345678')

	def test_user_str_representation(self):
		self.assertEqual(str(self.user), 'Test User')

	def test_set_password_hashes_password(self):
		self.user.set_password('mypassword')
		self.assertNotEqual(self.user.password_hash, 'mypassword')
		self.assertTrue(check_password('mypassword', self.user.password_hash))

	def test_check_password_validates_correctly(self):
		self.user.set_password('mypassword')
		self.assertTrue(self.user.check_password('mypassword'))
		self.assertFalse(self.user.check_password('wrongpassword'))

	def test_card_number_must_be_unique(self):
		with self.assertRaises(Exception):
			User.objects.create(
				username='another',
				name='Another User',
				card_number='12345678'
			)

	def test_username_must_be_unique(self):
		with self.assertRaises(Exception):
			User.objects.create(
				username='testuser',
				name='Another User',
				card_number='87654321'
			)

	def test_card_number_validation_8_digits_only(self):
		invalid_user = User(
			username='invalid',
			name='Invalid User',
			card_number='1234567'
		)
		with self.assertRaises(ValidationError):
			invalid_user.full_clean()

	def test_card_number_validation_rejects_non_digits(self):
		invalid_user = User(
			username='invalid',
			name='Invalid User',
			card_number='1234567a'
		)
		with self.assertRaises(ValidationError):
			invalid_user.full_clean()


class TransactionModelTests(TestCase):
	def setUp(self):
		self.user = User.objects.create(
			username='testuser',
			name='Test User',
			card_number='12345678'
		)

	def test_transaction_creation(self):
		transaction = Transaction.objects.create(
			user=self.user,
			type=Transaction.TransactionType.RECHARGE,
			amount=Decimal('50.00')
		)
		self.assertEqual(transaction.user, self.user)
		self.assertEqual(transaction.type, Transaction.TransactionType.RECHARGE)
		self.assertEqual(transaction.amount, Decimal('50.00'))

	def test_transaction_str_representation(self):
		transaction = Transaction.objects.create(
			user=self.user,
			type=Transaction.TransactionType.MEAL,
			amount=Decimal('5.60')
		)
		self.assertEqual(str(transaction), 'MEAL - 5.60')

	def test_meal_transaction_type(self):
		transaction = Transaction.objects.create(
			user=self.user,
			type=Transaction.TransactionType.MEAL,
			amount=Decimal('5.60')
		)
		self.assertEqual(transaction.type, Transaction.TransactionType.MEAL)

	def test_recharge_transaction_types(self):
		for method in [Transaction.MethodType.ONLINE, Transaction.MethodType.CASH, Transaction.MethodType.CARD]:
			transaction = Transaction.objects.create(
				user=self.user,
				type=Transaction.TransactionType.RECHARGE,
				amount=Decimal('10.00'),
				recharge_method=method
			)
			self.assertEqual(transaction.recharge_method, method)

	def test_transaction_cascade_delete(self):
		Transaction.objects.create(
			user=self.user,
			type=Transaction.TransactionType.RECHARGE,
			amount=Decimal('50.00')
		)
		user_id = self.user.id
		self.user.delete()
		self.assertEqual(Transaction.objects.filter(user_id=user_id).count(), 0)


class UtilsTests(TestCase):
	def setUp(self):
		self.user = User.objects.create(
			username='testuser',
			name='Test User',
			card_number='12345678'
		)

	def test_meal_price(self):
		price = meal_price()
		self.assertEqual(price, Decimal('5.60'))

	def test_user_balance_no_transactions(self):
		balance = user_balance(self.user)
		self.assertEqual(balance, Decimal('0'))

	def test_user_balance_with_recharge(self):
		Transaction.objects.create(
			user=self.user,
			type=Transaction.TransactionType.RECHARGE,
			amount=Decimal('50.00')
		)
		balance = user_balance(self.user)
		self.assertEqual(balance, Decimal('50.00'))

	def test_user_balance_with_meal(self):
		Transaction.objects.create(
			user=self.user,
			type=Transaction.TransactionType.RECHARGE,
			amount=Decimal('100.00')
		)
		Transaction.objects.create(
			user=self.user,
			type=Transaction.TransactionType.MEAL,
			amount=Decimal('5.60')
		)
		balance = user_balance(self.user)
		self.assertEqual(balance, Decimal('94.40'))

	def test_user_balance_multiple_transactions(self):
		Transaction.objects.create(
			user=self.user,
			type=Transaction.TransactionType.RECHARGE,
			amount=Decimal('50.00')
		)
		Transaction.objects.create(
			user=self.user,
			type=Transaction.TransactionType.RECHARGE,
			amount=Decimal('30.00')
		)
		Transaction.objects.create(
			user=self.user,
			type=Transaction.TransactionType.MEAL,
			amount=Decimal('5.60')
		)
		Transaction.objects.create(
			user=self.user,
			type=Transaction.TransactionType.MEAL,
			amount=Decimal('5.60')
		)
		balance = user_balance(self.user)
		self.assertEqual(balance, Decimal('68.80'))

	def test_user_balance_negative(self):
		Transaction.objects.create(
			user=self.user,
			type=Transaction.TransactionType.RECHARGE,
			amount=Decimal('5.00')
		)
		Transaction.objects.create(
			user=self.user,
			type=Transaction.TransactionType.MEAL,
			amount=Decimal('5.60')
		)
		balance = user_balance(self.user)
		self.assertEqual(balance, Decimal('-0.60'))


class CardNumberValidationTests(TestCase):
	def test_card_number_form_accepts_exactly_8_digits(self):
		form = CardNumberForm({'card_number': '12345678'})
		self.assertTrue(form.is_valid())

	def test_card_number_form_rejects_non_8_digit_values(self):
		form = CardNumberForm({'card_number': '2024010'})
		self.assertFalse(form.is_valid())
		self.assertIn('card_number', form.errors)

	def test_card_number_form_rejects_9_digits(self):
		form = CardNumberForm({'card_number': '123456789'})
		self.assertFalse(form.is_valid())

	def test_card_number_form_rejects_letters(self):
		form = CardNumberForm({'card_number': '1234567a'})
		self.assertFalse(form.is_valid())

	def test_card_number_form_empty(self):
		form = CardNumberForm({'card_number': ''})
		self.assertFalse(form.is_valid())

	def test_user_model_rejects_non_8_digit_card_numbers(self):
		user = User(username='teste', name='Teste', card_number='2024010')
		with self.assertRaises(ValidationError):
			user.full_clean()


class StudentLoginFormTests(TestCase):
	def test_student_login_form_accepts_valid_data(self):
		form = StudentLoginForm({'username': 'aluno', 'password': 'segredo'})
		self.assertTrue(form.is_valid())

	def test_student_login_form_requires_username(self):
		form = StudentLoginForm({'username': '', 'password': 'segredo'})
		self.assertFalse(form.is_valid())
		self.assertIn('username', form.errors)

	def test_student_login_form_requires_password(self):
		form = StudentLoginForm({'username': 'aluno', 'password': ''})
		self.assertFalse(form.is_valid())
		self.assertIn('password', form.errors)

	def test_student_login_form_empty(self):
		form = StudentLoginForm({})
		self.assertFalse(form.is_valid())


class UserRegistrationFormTests(TestCase):
	def test_user_registration_form_valid(self):
		form = UserRegistrationForm({
			'username': 'aluno',
			'name': 'Aluno Teste',
			'card_number': '12345678',
			'password': 'segredo123',
			'password_confirm': 'segredo123',
		})
		self.assertTrue(form.is_valid())

	def test_user_registration_form_hashes_password(self):
		form = UserRegistrationForm({
			'username': 'aluno',
			'name': 'Aluno Teste',
			'card_number': '12345678',
			'password': 'segredo123',
			'password_confirm': 'segredo123',
		})
		self.assertTrue(form.is_valid())
		user = form.save(commit=False)
		self.assertNotEqual(user.password_hash, 'segredo123')
		self.assertTrue(user.check_password('segredo123'))

	def test_user_registration_passwords_must_match(self):
		form = UserRegistrationForm({
			'username': 'aluno',
			'name': 'Aluno Teste',
			'card_number': '12345678',
			'password': 'segredo123',
			'password_confirm': 'diferentes',
		})
		self.assertFalse(form.is_valid())
		self.assertIn('password_confirm', form.errors)

	def test_user_registration_form_requires_all_fields(self):
		form = UserRegistrationForm({
			'username': 'aluno',
			'name': 'Aluno Teste',
			'card_number': '12345678',
			'password': 'segredo123',
		})
		self.assertFalse(form.is_valid())
		self.assertIn('password_confirm', form.errors)

	def test_user_registration_form_saves_user(self):
		form = UserRegistrationForm({
			'username': 'aluno',
			'name': 'Aluno Teste',
			'card_number': '12345678',
			'password': 'segredo123',
			'password_confirm': 'segredo123',
		})
		self.assertTrue(form.is_valid())
		user = form.save()
		self.assertEqual(User.objects.count(), 1)
		self.assertEqual(user.username, 'aluno')
		self.assertTrue(user.check_password('segredo123'))

	def test_user_registration_form_invalid_card_number(self):
		form = UserRegistrationForm({
			'username': 'aluno',
			'name': 'Aluno Teste',
			'card_number': '1234567',
			'password': 'segredo123',
			'password_confirm': 'segredo123',
		})
		self.assertFalse(form.is_valid())
		self.assertIn('card_number', form.errors)


class RechargeFormsTests(TestCase):
	def test_online_recharge_form_valid(self):
		form = OnlineRechargeForm({'amount': '50.00'})
		self.assertTrue(form.is_valid())
		self.assertEqual(form.cleaned_data['amount'], Decimal('50.00'))

	def test_online_recharge_form_minimum_amount(self):
		form = OnlineRechargeForm({'amount': '0.01'})
		self.assertTrue(form.is_valid())

	def test_online_recharge_form_rejects_zero(self):
		form = OnlineRechargeForm({'amount': '0.00'})
		self.assertFalse(form.is_valid())

	def test_online_recharge_form_rejects_negative(self):
		form = OnlineRechargeForm({'amount': '-10.00'})
		self.assertFalse(form.is_valid())

	def test_operator_recharge_form_valid(self):
		form = OperatorRechargeForm({
			'amount': '50.00',
			'method': Transaction.MethodType.CASH
		})
		self.assertTrue(form.is_valid())

	def test_operator_recharge_form_card_method(self):
		form = OperatorRechargeForm({
			'amount': '50.00',
			'method': Transaction.MethodType.CARD
		})
		self.assertTrue(form.is_valid())

	def test_operator_recharge_form_requires_method(self):
		form = OperatorRechargeForm({'amount': '50.00', 'method': ''})
		self.assertFalse(form.is_valid())

	def test_turnstile_form_valid(self):
		form = TurnstileForm({'card_number': '12345678'})
		self.assertTrue(form.is_valid())

	def test_turnstile_form_invalid_card_number(self):
		form = TurnstileForm({'card_number': '1234567'})
		self.assertFalse(form.is_valid())


class StudentRegisterViewTests(TestCase):
	def setUp(self):
		self.client = Client()
		self.register_url = '/aluno/cadastro/'

	def test_student_register_get(self):
		response = self.client.get(self.register_url)
		self.assertEqual(response.status_code, 200)
		self.assertIn('form', response.context)

	def test_student_register_post_valid(self):
		response = self.client.post(self.register_url, {
			'username': 'newstudent',
			'name': 'New Student',
			'card_number': '12345678',
			'password': 'password123',
			'password_confirm': 'password123',
		})
		self.assertEqual(response.status_code, 302)
		self.assertEqual(User.objects.count(), 1)

	def test_student_register_post_invalid(self):
		response = self.client.post(self.register_url, {
			'username': 'newstudent',
			'name': 'New Student',
			'card_number': '1234567',
			'password': 'password123',
			'password_confirm': 'password123',
		})
		self.assertEqual(response.status_code, 200)
		self.assertEqual(User.objects.count(), 0)
		self.assertIn('form', response.context)


class StudentLookupViewTests(TestCase):
	def setUp(self):
		self.client = Client()
		self.lookup_url = '/aluno/consulta/'
		self.user = User.objects.create(username='student', name='Student', card_number='12345678')
		self.user.set_password('password123')
		self.user.save()

	def test_student_lookup_get_no_session(self):
		response = self.client.get(self.lookup_url)
		self.assertEqual(response.status_code, 200)
		self.assertIsNone(response.context.get('user_obj'))

	def test_student_lookup_login_valid(self):
		response = self.client.post(self.lookup_url, {
			'username': 'student',
			'password': 'password123',
		})
		self.assertEqual(response.status_code, 200)
		self.assertIsNotNone(response.context.get('user_obj'))
		self.assertEqual(response.context.get('balance'), Decimal('0'))

	def test_student_lookup_login_invalid_password(self):
		response = self.client.post(self.lookup_url, {
			'username': 'student',
			'password': 'wrongpassword',
		})
		self.assertEqual(response.status_code, 200)
		self.assertIsNone(response.context.get('user_obj'))

	def test_student_lookup_login_nonexistent_user(self):
		response = self.client.post(self.lookup_url, {
			'username': 'nonexistent',
			'password': 'password123',
		})
		self.assertEqual(response.status_code, 200)
		self.assertIsNone(response.context.get('user_obj'))

	def test_student_lookup_recharge(self):
		session = self.client.session
		session['student_user_id'] = str(self.user.id)
		session.save()

		response = self.client.post(self.lookup_url, {
			'recharge': 'true',
			'amount': '50.00',
		})
		self.assertEqual(response.status_code, 200)
		self.assertEqual(Transaction.objects.count(), 1)
		transaction = Transaction.objects.first()
		self.assertEqual(transaction.amount, Decimal('50.00'))
		self.assertEqual(transaction.type, Transaction.TransactionType.RECHARGE)
		self.assertEqual(transaction.recharge_method, Transaction.MethodType.ONLINE)

	def test_student_lookup_logout(self):
		session = self.client.session
		session['student_user_id'] = str(self.user.id)
		session.save()

		response = self.client.post(self.lookup_url, {'logout': 'true'})
		self.assertEqual(response.status_code, 302)
		self.assertNotIn('student_user_id', self.client.session)

	def test_student_lookup_get_with_valid_session(self):
		# Aluno já autenticado (sessão ativa) vê saldo e extrato ao acessar a página
		Transaction.objects.create(
			user=self.user,
			type=Transaction.TransactionType.RECHARGE,
			amount=Decimal('25.00'),
		)
		session = self.client.session
		session['student_user_id'] = str(self.user.id)
		session.save()

		response = self.client.get(self.lookup_url)
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.context.get('user_obj'), self.user)
		self.assertEqual(response.context.get('balance'), Decimal('25.00'))
		self.assertIsNotNone(response.context.get('transactions'))
		self.assertEqual(len(response.context.get('transactions')), 1)

	def test_student_lookup_stale_session_is_cleared(self):
		# Sessão aponta para um id inexistente: deve ser limpa e tratada como anônimo
		session = self.client.session
		session['student_user_id'] = '00000000-0000-0000-0000-000000000000'
		session.save()

		response = self.client.get(self.lookup_url)
		self.assertEqual(response.status_code, 200)
		self.assertIsNone(response.context.get('user_obj'))
		self.assertNotIn('student_user_id', self.client.session)

	def test_student_lookup_recharge_invalid_amount(self):
		# Recarga online com valor inválido (zero) não deve criar transação
		session = self.client.session
		session['student_user_id'] = str(self.user.id)
		session.save()

		response = self.client.post(self.lookup_url, {
			'recharge': 'true',
			'amount': '0.00',
		})
		self.assertEqual(response.status_code, 200)
		self.assertEqual(Transaction.objects.count(), 0)


class OperatorPanelViewTests(TestCase):
	def setUp(self):
		self.client = Client()
		self.panel_url = '/operador/'
		self.user = User.objects.create(username='student', name='Student', card_number='12345678')

	def test_operator_panel_get(self):
		response = self.client.get(self.panel_url)
		self.assertEqual(response.status_code, 200)
		self.assertIn('lookup_form', response.context)

	def test_operator_panel_lookup_valid_card(self):
		response = self.client.post(self.panel_url, {
			'lookup-card_number': '12345678',
			'lookup': 'true',
		})
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.context.get('user_obj'), self.user)

	def test_operator_panel_lookup_invalid_card(self):
		response = self.client.post(self.panel_url, {
			'lookup-card_number': '99999999',
			'lookup': 'true',
		})
		self.assertEqual(response.status_code, 200)
		self.assertIsNone(response.context.get('user_obj'))

	def test_operator_panel_recharge_cash(self):
		response = self.client.post(self.panel_url, {
			'card_number': '12345678',
			'recharge': 'true',
			'amount': '100.00',
			'method': Transaction.MethodType.CASH,
		})
		self.assertEqual(response.status_code, 200)
		self.assertEqual(Transaction.objects.count(), 1)
		transaction = Transaction.objects.first()
		self.assertEqual(transaction.amount, Decimal('100.00'))
		self.assertEqual(transaction.recharge_method, Transaction.MethodType.CASH)

	def test_operator_panel_recharge_card(self):
		response = self.client.post(self.panel_url, {
			'card_number': '12345678',
			'recharge': 'true',
			'amount': '50.00',
			'method': Transaction.MethodType.CARD,
		})
		self.assertEqual(response.status_code, 200)
		self.assertEqual(Transaction.objects.count(), 1)
		transaction = Transaction.objects.first()
		self.assertEqual(transaction.recharge_method, Transaction.MethodType.CARD)

	def test_operator_panel_query_string_lookup(self):
		response = self.client.get(self.panel_url, {'card_number': '12345678'})
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.context.get('user_obj'), self.user)

	def test_operator_panel_query_string_nonexistent_card(self):
		response = self.client.get(self.panel_url, {'card_number': '99999999'})
		self.assertEqual(response.status_code, 200)
		self.assertIsNone(response.context.get('user_obj'))

	def test_operator_panel_recharge_invalid_amount(self):
		# Valor inválido (zero) não deve gerar transação
		response = self.client.post(self.panel_url, {
			'card_number': '12345678',
			'recharge': 'true',
			'amount': '0.00',
			'method': Transaction.MethodType.CASH,
		})
		self.assertEqual(response.status_code, 200)
		self.assertEqual(Transaction.objects.count(), 0)

	def test_operator_panel_recharge_nonexistent_card_returns_404(self):
		response = self.client.post(self.panel_url, {
			'card_number': '99999999',
			'recharge': 'true',
			'amount': '50.00',
			'method': Transaction.MethodType.CASH,
		})
		self.assertEqual(response.status_code, 404)
		self.assertEqual(Transaction.objects.count(), 0)


class TurnstileViewTests(TestCase):
	def setUp(self):
		self.client = Client()
		self.turnstile_url = '/catraca/'
		self.user = User.objects.create(username='student', name='Student', card_number='12345678')

	def test_turnstile_get(self):
		response = self.client.get(self.turnstile_url)
		self.assertEqual(response.status_code, 200)
		self.assertIn('form', response.context)

	def test_turnstile_lookup_valid_card(self):
		response = self.client.post(self.turnstile_url, {
			'card_number': '12345678',
			'lookup': 'true',
		})
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.context.get('user_obj'), self.user)
		self.assertEqual(response.context.get('balance'), Decimal('0'))

	def test_turnstile_lookup_invalid_card(self):
		response = self.client.post(self.turnstile_url, {
			'card_number': '99999999',
			'lookup': 'true',
		})
		self.assertEqual(response.status_code, 200)
		self.assertIsNone(response.context.get('user_obj'))

	def test_turnstile_meal_purchase_sufficient_balance(self):
		Transaction.objects.create(
			user=self.user,
			type=Transaction.TransactionType.RECHARGE,
			amount=Decimal('50.00')
		)
		response = self.client.post(self.turnstile_url, {
			'card_number': '12345678',
			'confirm': 'true',
		})
		self.assertEqual(response.status_code, 200)
		self.assertEqual(Transaction.objects.count(), 2)
		meal_transaction = Transaction.objects.filter(type=Transaction.TransactionType.MEAL).first()
		self.assertEqual(meal_transaction.amount, Decimal('5.60'))

	def test_turnstile_meal_purchase_insufficient_balance(self):
		Transaction.objects.create(
			user=self.user,
			type=Transaction.TransactionType.RECHARGE,
			amount=Decimal('2.00')
		)
		response = self.client.post(self.turnstile_url, {
			'card_number': '12345678',
			'confirm': 'true',
		})
		self.assertEqual(response.status_code, 200)
		self.assertEqual(Transaction.objects.count(), 1)

	def test_turnstile_meal_purchase_zero_balance(self):
		response = self.client.post(self.turnstile_url, {
			'card_number': '12345678',
			'confirm': 'true',
		})
		self.assertEqual(response.status_code, 200)
		self.assertEqual(Transaction.objects.count(), 0)

	def test_turnstile_meal_purchase_exact_balance_allowed(self):
		# Saldo exatamente igual ao preço da refeição deve liberar o acesso (US9)
		Transaction.objects.create(
			user=self.user,
			type=Transaction.TransactionType.RECHARGE,
			amount=Decimal('5.60'),
		)
		response = self.client.post(self.turnstile_url, {
			'card_number': '12345678',
			'confirm': 'true',
		})
		self.assertEqual(response.status_code, 200)
		self.assertEqual(
			Transaction.objects.filter(type=Transaction.TransactionType.MEAL).count(),
			1,
		)
		self.assertEqual(user_balance(self.user), Decimal('0.00'))

	def test_turnstile_confirm_nonexistent_card(self):
		# Confirmar entrada com carteirinha inexistente não cria transação
		response = self.client.post(self.turnstile_url, {
			'card_number': '99999999',
			'confirm': 'true',
		})
		self.assertEqual(response.status_code, 200)
		self.assertIsNone(response.context.get('user_obj'))
		self.assertEqual(Transaction.objects.count(), 0)

	def test_turnstile_lookup_invalid_card_format(self):
		# Carteirinha com formato inválido reprova na validação do formulário
		response = self.client.post(self.turnstile_url, {
			'card_number': '1234567',
			'lookup': 'true',
		})
		self.assertEqual(response.status_code, 200)
		self.assertIsNone(response.context.get('user_obj'))


class HomeViewTests(TestCase):
	def setUp(self):
		self.client = Client()

	def test_home_renders_with_meal_price(self):
		response = self.client.get('/')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.context.get('meal_price'), Decimal('5.60'))


class ReceiptViewTests(TestCase):
	def setUp(self):
		self.client = Client()
		self.user = User.objects.create(username='student', name='Student', card_number='12345678')
		self.transaction = Transaction.objects.create(
			user=self.user,
			type=Transaction.TransactionType.RECHARGE,
			amount=Decimal('50.00'),
			recharge_method=Transaction.MethodType.ONLINE,
		)

	def test_receipt_renders_for_existing_transaction(self):
		response = self.client.get(f'/comprovante/{self.transaction.id}/')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.context.get('transaction'), self.transaction)
		self.assertEqual(response.context.get('user'), self.user)
		self.assertEqual(response.context.get('balance'), Decimal('50.00'))

	def test_receipt_unknown_transaction_returns_404(self):
		response = self.client.get('/comprovante/00000000-0000-0000-0000-000000000000/')
		self.assertEqual(response.status_code, 404)


class CardapioViewTests(TestCase):
	"""Testa a view de cardápio isolando a API externa da FUMP via mock."""

	def setUp(self):
		self.client = Client()
		self.cardapio_url = '/cardapio/'

	@patch('rupayapp.views._fump_get')
	def test_cardapio_lists_restaurantes(self, mock_fump):
		# Sem restaurante selecionado: apenas lista restaurantes, sem buscar cardápio
		mock_fump.return_value = [{'id': 1, 'nome': 'RU Central'}]
		response = self.client.get(self.cardapio_url)
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.context.get('restaurantes'), [{'id': 1, 'nome': 'RU Central'}])
		self.assertIsNone(response.context.get('cardapio_data'))
		self.assertIsNone(response.context.get('erro'))

	@patch('rupayapp.views._fump_get')
	def test_cardapio_with_menu_data(self, mock_fump):
		# Restaurante + data selecionados e cardápio disponível
		def side_effect(path):
			if path == '/restaurantes':
				return [{'id': 1, 'nome': 'RU Central'}]
			return {'cardapios': [{'data': '2026-06-24', 'itens': ['Arroz', 'Feijão']}]}

		mock_fump.side_effect = side_effect
		response = self.client.get(self.cardapio_url, {'restaurante': '1', 'data': '2026-06-24'})
		self.assertEqual(response.status_code, 200)
		self.assertIsNotNone(response.context.get('cardapio_data'))
		self.assertIsNone(response.context.get('erro'))

	@patch('rupayapp.views._fump_get')
	def test_cardapio_no_menu_found(self, mock_fump):
		def side_effect(path):
			if path == '/restaurantes':
				return [{'id': 1, 'nome': 'RU Central'}]
			return {'cardapios': []}

		mock_fump.side_effect = side_effect
		response = self.client.get(self.cardapio_url, {'restaurante': '1', 'data': '2026-06-24'})
		self.assertEqual(response.status_code, 200)
		self.assertIsNone(response.context.get('cardapio_data'))
		self.assertEqual(response.context.get('erro'), 'Nenhum cardápio encontrado para essa data.')

	@patch('rupayapp.views._fump_get')
	def test_cardapio_service_unavailable(self, mock_fump):
		def side_effect(path):
			if path == '/restaurantes':
				return []
			return None

		mock_fump.side_effect = side_effect
		response = self.client.get(self.cardapio_url, {'restaurante': '1', 'data': '2026-06-24'})
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.context.get('erro'), 'Não foi possível conectar ao serviço da FUMP.')

	def test_fump_get_returns_none_on_network_error(self):
		# Falha de rede deve ser tratada e retornar None (sem propagar exceção)
		from rupayapp.views import _fump_get

		with patch('rupayapp.views.urllib.request.urlopen', side_effect=OSError('boom')):
			self.assertIsNone(_fump_get('/restaurantes'))

	def test_fump_get_parses_json_response(self):
		# Resposta HTTP válida deve ser decodificada como JSON
		from rupayapp.views import _fump_get

		class _FakeResponse:
			def __enter__(self):
				return self

			def __exit__(self, *args):
				return False

			def read(self):
				return b'[{"id": 1, "nome": "RU Central"}]'

		with patch('rupayapp.views.urllib.request.urlopen', return_value=_FakeResponse()):
			self.assertEqual(_fump_get('/restaurantes'), [{'id': 1, 'nome': 'RU Central'}])

