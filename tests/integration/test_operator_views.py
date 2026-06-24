"""Testes de integração do painel do operador (leitura e recarga presencial)."""
from decimal import Decimal

from django.test import TestCase, Client

from rupayapp.models import User, Transaction


class OperatorPanelViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.panel_url = '/operador/'
        self.user = User.objects.create(username='student', name='Student', card_number='12345678')

    def test_get(self):
        response = self.client.get(self.panel_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('lookup_form', response.context)

    def test_lookup_valid_card(self):
        response = self.client.post(self.panel_url, {'lookup-card_number': '12345678', 'lookup': 'true'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context.get('user_obj'), self.user)

    def test_lookup_invalid_card(self):
        response = self.client.post(self.panel_url, {'lookup-card_number': '99999999', 'lookup': 'true'})
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context.get('user_obj'))

    def test_recharge_cash(self):
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

    def test_recharge_card(self):
        response = self.client.post(self.panel_url, {
            'card_number': '12345678',
            'recharge': 'true',
            'amount': '50.00',
            'method': Transaction.MethodType.CARD,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Transaction.objects.count(), 1)
        self.assertEqual(Transaction.objects.first().recharge_method, Transaction.MethodType.CARD)

    def test_query_string_lookup(self):
        response = self.client.get(self.panel_url, {'card_number': '12345678'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context.get('user_obj'), self.user)

    def test_query_string_nonexistent_card(self):
        response = self.client.get(self.panel_url, {'card_number': '99999999'})
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context.get('user_obj'))

    def test_recharge_invalid_amount(self):
        response = self.client.post(self.panel_url, {
            'card_number': '12345678',
            'recharge': 'true',
            'amount': '0.00',
            'method': Transaction.MethodType.CASH,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Transaction.objects.count(), 0)

    def test_recharge_nonexistent_card_returns_404(self):
        response = self.client.post(self.panel_url, {
            'card_number': '99999999',
            'recharge': 'true',
            'amount': '50.00',
            'method': Transaction.MethodType.CASH,
        })
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Transaction.objects.count(), 0)

    def test_recharge_without_card_no_transaction(self):
        response = self.client.post(self.panel_url, {
            'card_number': '',
            'recharge': 'true',
            'amount': '10.00',
            'method': Transaction.MethodType.CASH,
        })
        self.assertIn(response.status_code, (200, 302, 404))
        self.assertEqual(Transaction.objects.count(), 0)
