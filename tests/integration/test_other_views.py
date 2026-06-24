"""Testes de integração das demais views (home, comprovante e cardápio)."""
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase, Client

from rupayapp.models import User, Transaction


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
    """Isola a API externa da FUMP via mock de `_fump_get`."""

    def setUp(self):
        self.client = Client()
        self.cardapio_url = '/cardapio/'

    @patch('rupayapp.views._fump_get')
    def test_lists_restaurantes(self, mock_fump):
        mock_fump.return_value = [{'id': 1, 'nome': 'RU Central'}]
        response = self.client.get(self.cardapio_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context.get('restaurantes'), [{'id': 1, 'nome': 'RU Central'}])
        self.assertIsNone(response.context.get('cardapio_data'))
        self.assertIsNone(response.context.get('erro'))

    @patch('rupayapp.views._fump_get')
    def test_with_menu_data(self, mock_fump):
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
    def test_no_menu_found(self, mock_fump):
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
    def test_service_unavailable(self, mock_fump):
        def side_effect(path):
            if path == '/restaurantes':
                return []
            return None

        mock_fump.side_effect = side_effect
        response = self.client.get(self.cardapio_url, {'restaurante': '1', 'data': '2026-06-24'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context.get('erro'), 'Não foi possível conectar ao serviço da FUMP.')

    def test_fump_get_returns_none_on_network_error(self):
        from rupayapp.views import _fump_get

        with patch('rupayapp.views.urllib.request.urlopen', side_effect=OSError('boom')):
            self.assertIsNone(_fump_get('/restaurantes'))

    def test_fump_get_parses_json_response(self):
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
