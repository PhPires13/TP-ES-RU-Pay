"""Testes de integração da catraca (controle de acesso por saldo)."""
from decimal import Decimal

from django.test import TestCase, Client

from rupayapp.models import User, Transaction
from rupayapp.utils import user_balance


class TurnstileViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.turnstile_url = '/catraca/'
        self.user = User.objects.create(username='student', name='Student', card_number='12345678')

    def test_get(self):
        response = self.client.get(self.turnstile_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)

    def test_lookup_valid_card(self):
        response = self.client.post(self.turnstile_url, {'card_number': '12345678', 'lookup': 'true'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context.get('user_obj'), self.user)
        self.assertEqual(response.context.get('balance'), Decimal('0'))

    def test_lookup_invalid_card(self):
        response = self.client.post(self.turnstile_url, {'card_number': '99999999', 'lookup': 'true'})
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context.get('user_obj'))

    def test_lookup_invalid_card_format(self):
        response = self.client.post(self.turnstile_url, {'card_number': '1234567', 'lookup': 'true'})
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context.get('user_obj'))

    def test_meal_purchase_sufficient_balance(self):
        Transaction.objects.create(
            user=self.user,
            type=Transaction.TransactionType.RECHARGE,
            amount=Decimal('50.00'),
        )
        response = self.client.post(self.turnstile_url, {'card_number': '12345678', 'confirm': 'true'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Transaction.objects.count(), 2)
        meal = Transaction.objects.filter(type=Transaction.TransactionType.MEAL).first()
        self.assertEqual(meal.amount, Decimal('5.60'))

    def test_meal_purchase_insufficient_balance(self):
        Transaction.objects.create(
            user=self.user,
            type=Transaction.TransactionType.RECHARGE,
            amount=Decimal('2.00'),
        )
        response = self.client.post(self.turnstile_url, {'card_number': '12345678', 'confirm': 'true'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Transaction.objects.count(), 1)

    def test_meal_purchase_zero_balance(self):
        response = self.client.post(self.turnstile_url, {'card_number': '12345678', 'confirm': 'true'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Transaction.objects.count(), 0)

    def test_meal_purchase_exact_balance_allowed(self):
        # Saldo exatamente igual ao preço da refeição deve liberar o acesso (US9)
        Transaction.objects.create(
            user=self.user,
            type=Transaction.TransactionType.RECHARGE,
            amount=Decimal('5.60'),
        )
        response = self.client.post(self.turnstile_url, {'card_number': '12345678', 'confirm': 'true'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Transaction.objects.filter(type=Transaction.TransactionType.MEAL).count(), 1)
        self.assertEqual(user_balance(self.user), Decimal('0.00'))

    def test_confirm_nonexistent_card(self):
        response = self.client.post(self.turnstile_url, {'card_number': '99999999', 'confirm': 'true'})
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context.get('user_obj'))
        self.assertEqual(Transaction.objects.count(), 0)
