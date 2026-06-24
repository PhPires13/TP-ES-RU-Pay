from decimal import Decimal
from django.test import TestCase, Client

from .forms import OnlineRechargeForm, OperatorRechargeForm, TurnstileForm, StudentLoginForm
from .models import User, Transaction
from .utils import user_balance


class OnlineRechargeTests(TestCase):
	def setUp(self):
		self.client = Client()
		self.lookup_url = '/aluno/consulta/'
		self.user = User.objects.create(username='student', name='Student', card_number='12345678')
		self.user.set_password('password123')
		self.user.save()

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

	def test_student_lookup_recharge_creates_online_transaction(self):
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
		self.assertEqual(transaction.recharge_method, Transaction.MethodType.ONLINE)

	def test_student_lookup_recharge_requires_session(self):
		response = self.client.post(self.lookup_url, {
			'recharge': 'true',
			'amount': '50.00',
		})
		# without session student_user_id, no transaction created
		self.assertEqual(response.status_code, 200)
		self.assertEqual(Transaction.objects.count(), 0)

	def test_user_balance_updated_after_online_recharge(self):
		Transaction.objects.create(user=self.user, type=Transaction.TransactionType.RECHARGE, amount=Decimal('20.00'))
		balance = user_balance(self.user)
		self.assertEqual(balance, Decimal('20.00'))

	def test_online_recharge_accepts_integer_amount_string(self):
		form = OnlineRechargeForm({'amount': '10'})
		self.assertTrue(form.is_valid())
		self.assertEqual(form.cleaned_data['amount'], Decimal('10'))

	def test_online_recharge_form_rejects_non_numeric(self):
		form = OnlineRechargeForm({'amount': 'abc'})
		self.assertFalse(form.is_valid())


class InPersonRechargeTests(TestCase):
	def setUp(self):
		self.client = Client()
		self.panel_url = '/operador/'
		self.user = User.objects.create(username='student', name='Student', card_number='12345678')

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

	def test_operator_panel_lookup_valid_card(self):
		response = self.client.post(self.panel_url, {
			'lookup-card_number': '12345678',
			'lookup': 'true',
		})
		self.assertEqual(response.status_code, 200)
		self.assertIsNotNone(response.context.get('user_obj'))

	def test_operator_panel_lookup_invalid_card(self):
		response = self.client.post(self.panel_url, {
			'lookup-card_number': '99999999',
			'lookup': 'true',
		})
		self.assertEqual(response.status_code, 200)
		self.assertIsNone(response.context.get('user_obj'))

	def test_operator_recharge_form_valid(self):
		form = OperatorRechargeForm({'amount': '50.00', 'method': Transaction.MethodType.CASH})
		self.assertTrue(form.is_valid())

	def test_operator_recharge_form_requires_method(self):
		form = OperatorRechargeForm({'amount': '50.00', 'method': ''})
		self.assertFalse(form.is_valid())

	def test_operator_panel_query_string_lookup(self):
		response = self.client.get(self.panel_url, {'card_number': '12345678'})
		self.assertEqual(response.status_code, 200)
		self.assertIsNotNone(response.context.get('user_obj'))

	def test_operator_recharge_form_rejects_zero(self):
		form = OperatorRechargeForm({'amount': '0.00', 'method': Transaction.MethodType.CASH})
		self.assertFalse(form.is_valid())

	def test_operator_recharge_form_rejects_negative(self):
		form = OperatorRechargeForm({'amount': '-5.00', 'method': Transaction.MethodType.CASH})
		self.assertFalse(form.is_valid())

	def test_operator_panel_recharge_without_card_no_transaction(self):
		response = self.client.post(self.panel_url, {
			'card_number': '',
			'recharge': 'true',
			'amount': '10.00',
			'method': Transaction.MethodType.CASH,
		})
		self.assertIn(response.status_code, (200, 302, 404))
		self.assertEqual(Transaction.objects.count(), 0)


class BalanceInquiryTests(TestCase):
	def setUp(self):
		self.client = Client()
		self.lookup_url = '/aluno/consulta/'
		self.turnstile_url = '/catraca/'
		self.user = User.objects.create(username='student', name='Student', card_number='12345678')
		self.user.set_password('password123')
		self.user.save()

	def test_student_lookup_get_no_session(self):
		response = self.client.get(self.lookup_url)
		self.assertEqual(response.status_code, 200)
		self.assertIsNone(response.context.get('user_obj'))

	def test_student_lookup_login_valid_shows_balance(self):
		response = self.client.post(self.lookup_url, {'username': 'student', 'password': 'password123'})
		self.assertEqual(response.status_code, 200)
		self.assertIsNotNone(response.context.get('user_obj'))
		self.assertEqual(response.context.get('balance'), Decimal('0'))

	def test_student_lookup_login_invalid_password(self):
		response = self.client.post(self.lookup_url, {'username': 'student', 'password': 'wrong'})
		self.assertEqual(response.status_code, 200)
		self.assertIsNone(response.context.get('user_obj'))

	def test_student_lookup_login_nonexistent_user(self):
		response = self.client.post(self.lookup_url, {'username': 'nope', 'password': 'password123'})
		self.assertEqual(response.status_code, 200)
		self.assertIsNone(response.context.get('user_obj'))

	def test_turnstile_lookup_valid_card(self):
		response = self.client.post(self.turnstile_url, {'card_number': '12345678', 'lookup': 'true'})
		self.assertEqual(response.status_code, 200)
		self.assertIsNotNone(response.context.get('user_obj'))

	def test_turnstile_lookup_invalid_card(self):
		response = self.client.post(self.turnstile_url, {'card_number': '99999999', 'lookup': 'true'})
		self.assertEqual(response.status_code, 200)
		self.assertIsNone(response.context.get('user_obj'))

	def test_user_balance_no_transactions(self):
		self.assertEqual(user_balance(self.user), Decimal('0'))

	def test_user_balance_with_recharge(self):
		Transaction.objects.create(user=self.user, type=Transaction.TransactionType.RECHARGE, amount=Decimal('50.00'))
		self.assertEqual(user_balance(self.user), Decimal('50.00'))

	def test_user_balance_with_meal(self):
		Transaction.objects.create(user=self.user, type=Transaction.TransactionType.RECHARGE, amount=Decimal('20.00'))
		Transaction.objects.create(user=self.user, type=Transaction.TransactionType.MEAL, amount=Decimal('5.60'))
		self.assertEqual(user_balance(self.user), Decimal('14.40'))

	def test_turnstile_meal_purchase_sufficient_balance(self):
		Transaction.objects.create(user=self.user, type=Transaction.TransactionType.RECHARGE, amount=Decimal('50.00'))
		response = self.client.post(self.turnstile_url, {'card_number': '12345678', 'confirm': 'true'})
		self.assertEqual(response.status_code, 200)
		self.assertEqual(Transaction.objects.filter(type=Transaction.TransactionType.MEAL).count(), 1)

	def test_turnstile_meal_purchase_insufficient_balance(self):
		Transaction.objects.create(user=self.user, type=Transaction.TransactionType.RECHARGE, amount=Decimal('2.00'))
		response = self.client.post(self.turnstile_url, {'card_number': '12345678', 'confirm': 'true'})
		self.assertEqual(response.status_code, 200)
		self.assertEqual(Transaction.objects.filter(type=Transaction.TransactionType.MEAL).count(), 0)

