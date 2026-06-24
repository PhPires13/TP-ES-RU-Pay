"""Testes de unidade das funções utilitárias (saldo e preço da refeição)."""
from decimal import Decimal

from django.test import TestCase

from rupayapp.models import User, Transaction
from rupayapp.utils import meal_price, user_balance


class UtilsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(  # Aluno usado no calculo de saldo
            username='testuser',
            name='Test User',
            card_number='12345678',
        )

    def test_meal_price(self):
        self.assertEqual(meal_price(), Decimal('5.60'))  # Preco da refeicao vem das configuracoes

    def test_user_balance_no_transactions(self):
        self.assertEqual(user_balance(self.user), Decimal('0'))  # Sem transacoes, saldo zero

    def test_user_balance_with_recharge(self):
        Transaction.objects.create(  # Uma recarga de R$50
            user=self.user,
            type=Transaction.TransactionType.RECHARGE,
            amount=Decimal('50.00'),
        )
        self.assertEqual(user_balance(self.user), Decimal('50.00'))  # Recarga soma no saldo

    def test_user_balance_with_meal(self):
        Transaction.objects.create(  # Recarrega R$100
            user=self.user,
            type=Transaction.TransactionType.RECHARGE,
            amount=Decimal('100.00'),
        )
        Transaction.objects.create(  # Consome uma refeicao de R$5,60
            user=self.user,
            type=Transaction.TransactionType.MEAL,
            amount=Decimal('5.60'),
        )
        self.assertEqual(user_balance(self.user), Decimal('94.40'))  # Saldo = recargas - refeicoes

    def test_user_balance_multiple_transactions(self):
        # Mistura de recargas e refeicoes: 50 + 30 - 5,60 - 5,60 = 68,80
        Transaction.objects.create(user=self.user, type=Transaction.TransactionType.RECHARGE, amount=Decimal('50.00'))
        Transaction.objects.create(user=self.user, type=Transaction.TransactionType.RECHARGE, amount=Decimal('30.00'))
        Transaction.objects.create(user=self.user, type=Transaction.TransactionType.MEAL, amount=Decimal('5.60'))
        Transaction.objects.create(user=self.user, type=Transaction.TransactionType.MEAL, amount=Decimal('5.60'))
        self.assertEqual(user_balance(self.user), Decimal('68.80'))

    def test_user_balance_negative(self):
        # Refeicao maior que a recarga deixa o saldo negativo (5,00 - 5,60)
        Transaction.objects.create(user=self.user, type=Transaction.TransactionType.RECHARGE, amount=Decimal('5.00'))
        Transaction.objects.create(user=self.user, type=Transaction.TransactionType.MEAL, amount=Decimal('5.60'))
        self.assertEqual(user_balance(self.user), Decimal('-0.60'))
