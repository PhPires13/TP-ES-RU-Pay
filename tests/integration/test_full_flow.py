"""Teste de integração de ponta a ponta usando o Django test client (sem navegador).

Cobre o fluxo completo em processo: cadastro -> login -> recarga online ->
recarga presencial pelo operador -> refeição na catraca, validando os efeitos
no banco e o saldo a cada etapa.
"""
from decimal import Decimal

from django.test import TestCase, Client

from rupayapp.models import User, Transaction
from rupayapp.utils import user_balance, meal_price


class FullFlowIntegrationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = '/aluno/cadastro/'
        self.lookup_url = '/aluno/consulta/'
        self.panel_url = '/operador/'
        self.turnstile_url = '/catraca/'

    def test_full_user_flow_online_and_inperson_recharge_and_meal(self):
        # 1) Aluno se cadastra no sistema
        resp = self.client.post(self.register_url, {
            'username': 'e2estudent',
            'name': 'E2E Student',
            'card_number': '87654321',
            'password': 'e2epass',
            'password_confirm': 'e2epass',
        })
        self.assertIn(resp.status_code, (200, 302))
        user = User.objects.filter(username='e2estudent').first()
        self.assertIsNotNone(user)  # Aluno foi criado

        # 2) Aluno faz login na area de consulta
        resp = self.client.post(self.lookup_url, {'username': 'e2estudent', 'password': 'e2epass'})
        self.assertEqual(resp.status_code, 200)
        session = self.client.session  # Mantem o aluno logado para a recarga
        session['student_user_id'] = str(user.id)
        session.save()

        # 3) Aluno faz uma recarga online de R$30
        resp = self.client.post(self.lookup_url, {'recharge': 'true', 'amount': '30.00'})
        self.assertEqual(resp.status_code, 200)
        tx_online = Transaction.objects.filter(
            user=user, type=Transaction.TransactionType.RECHARGE, amount=Decimal('30.00')
        ).first()
        self.assertIsNotNone(tx_online)  # Recarga online registrada
        self.assertEqual(user_balance(user), Decimal('30.00'))  # Saldo = 30

        # 4) Operador registra uma recarga presencial em dinheiro de R$20
        resp = self.client.post(self.panel_url, {
            'card_number': '87654321',
            'recharge': 'true',
            'amount': '20.00',
            'method': Transaction.MethodType.CASH,
        })
        self.assertEqual(resp.status_code, 200)
        tx_cash = Transaction.objects.filter(
            user=user, type=Transaction.TransactionType.RECHARGE, amount=Decimal('20.00')
        ).first()
        self.assertIsNotNone(tx_cash)  # Recarga presencial registrada
        self.assertEqual(user_balance(user), Decimal('50.00'))  # Saldo = 30 + 20

        # 5) Aluno passa na catraca e a refeicao e debitada
        current_balance = user_balance(user)
        meal = meal_price()
        resp = self.client.post(self.turnstile_url, {'card_number': '87654321', 'confirm': 'true'})
        self.assertEqual(resp.status_code, 200)
        meal_tx = Transaction.objects.filter(user=user, type=Transaction.TransactionType.MEAL).first()
        self.assertIsNotNone(meal_tx)  # Refeicao debitada
        self.assertEqual(user_balance(user), current_balance - meal)  # Saldo cai o valor da refeicao
