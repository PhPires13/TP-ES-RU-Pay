"""Testes de integração da catraca (controle de acesso por saldo)."""
from decimal import Decimal

from django.test import TestCase, Client

from rupayapp.models import User, Transaction
from rupayapp.utils import user_balance


class TurnstileViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.turnstile_url = '/catraca/'
        self.user = User.objects.create(username='student', name='Student', card_number='12345678')  # Aluno que usa a catraca

    def test_get(self):
        response = self.client.get(self.turnstile_url)  # Abre a tela da catraca
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)  # Traz o campo da carteirinha

    def test_lookup_valid_card(self):
        response = self.client.post(self.turnstile_url, {'card_number': '12345678', 'lookup': 'true'})  # Passa a carteirinha
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context.get('user_obj'), self.user)  # Identifica o aluno
        self.assertEqual(response.context.get('balance'), Decimal('0'))  # E mostra o saldo

    def test_lookup_invalid_card(self):
        response = self.client.post(self.turnstile_url, {'card_number': '99999999', 'lookup': 'true'})  # Carteirinha inexistente
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context.get('user_obj'))  # Nao identifica ninguem

    def test_lookup_invalid_card_format(self):
        response = self.client.post(self.turnstile_url, {'card_number': '1234567', 'lookup': 'true'})  # Formato invalido (7 digitos)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context.get('user_obj'))  # Reprovado na validacao

    def test_meal_purchase_sufficient_balance(self):
        Transaction.objects.create(  # Aluno com saldo suficiente (R$50)
            user=self.user,
            type=Transaction.TransactionType.RECHARGE,
            amount=Decimal('50.00'),
        )
        response = self.client.post(self.turnstile_url, {'card_number': '12345678', 'confirm': 'true'})  # Confirma a entrada
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Transaction.objects.count(), 2)  # Recarga + refeicao debitada
        meal = Transaction.objects.filter(type=Transaction.TransactionType.MEAL).first()
        self.assertEqual(meal.amount, Decimal('5.60'))  # Debitou o preco da refeicao

    def test_meal_purchase_insufficient_balance(self):
        Transaction.objects.create(  # Cria transacao recarga insuficiente
            user=self.user,
            type=Transaction.TransactionType.RECHARGE,
            amount=Decimal('2.00'),
        )
        response = self.client.post(self.turnstile_url, {'card_number': '12345678', 'confirm': 'true'})  # Passa o cartao na catraca
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Transaction.objects.count(), 1)  # Verifica que uma transacao de refeicao nao foi criada

    def test_meal_purchase_zero_balance(self):
        # Aluno sem nenhum saldo tenta entrar
        response = self.client.post(self.turnstile_url, {'card_number': '12345678', 'confirm': 'true'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Transaction.objects.count(), 0)  # Acesso negado, nada criado

    def test_meal_purchase_exact_balance_allowed(self):
        Transaction.objects.create(  # Saldo exatamente igual ao preco da refeicao (US9)
            user=self.user,
            type=Transaction.TransactionType.RECHARGE,
            amount=Decimal('5.60'),
        )
        response = self.client.post(self.turnstile_url, {'card_number': '12345678', 'confirm': 'true'})  # Confirma a entrada
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Transaction.objects.filter(type=Transaction.TransactionType.MEAL).count(), 1)  # Libera e debita
        self.assertEqual(user_balance(self.user), Decimal('0.00'))  # Saldo zera

    def test_confirm_nonexistent_card(self):
        # Confirma entrada com carteirinha que nao existe
        response = self.client.post(self.turnstile_url, {'card_number': '99999999', 'confirm': 'true'})
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context.get('user_obj'))  # Ninguem identificado
        self.assertEqual(Transaction.objects.count(), 0)  # Nada e debitado
