"""Testes de unidade dos modelos User e Transaction."""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.contrib.auth.hashers import check_password

from rupayapp.models import User, Transaction


class UserModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(  # Cria um aluno base para os testes
            username='testuser',
            name='Test User',
            card_number='12345678',
        )

    def test_user_creation(self):
        # Verifica que os dados do aluno foram salvos corretamente
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.name, 'Test User')
        self.assertEqual(self.user.card_number, '12345678')

    def test_user_str_representation(self):
        # O texto do aluno deve ser o nome dele
        self.assertEqual(str(self.user), 'Test User')

    def test_set_password_hashes_password(self):
        self.user.set_password('mypassword')  # Define a senha
        self.assertNotEqual(self.user.password_hash, 'mypassword')  # Senha nao fica em texto puro
        self.assertTrue(check_password('mypassword', self.user.password_hash))  # Mas confere com o hash

    def test_check_password_validates_correctly(self):
        self.user.set_password('mypassword')
        self.assertTrue(self.user.check_password('mypassword'))  # Senha certa passa
        self.assertFalse(self.user.check_password('wrongpassword'))  # Senha errada falha

    def test_card_number_must_be_unique(self):
        # Nao pode existir outro aluno com a mesma carteirinha
        with self.assertRaises(Exception):
            User.objects.create(
                username='another',
                name='Another User',
                card_number='12345678',
            )

    def test_username_must_be_unique(self):
        # Nao pode existir outro aluno com o mesmo usuario
        with self.assertRaises(Exception):
            User.objects.create(
                username='testuser',
                name='Another User',
                card_number='87654321',
            )

    def test_card_number_validation_8_digits_only(self):
        invalid_user = User(username='invalid', name='Invalid User', card_number='1234567')  # So 7 digitos
        with self.assertRaises(ValidationError):
            invalid_user.full_clean()  # Validacao deve reprovar

    def test_card_number_validation_rejects_non_digits(self):
        invalid_user = User(username='invalid', name='Invalid User', card_number='1234567a')  # Tem uma letra
        with self.assertRaises(ValidationError):
            invalid_user.full_clean()  # Validacao deve reprovar


class TransactionModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(  # Aluno dono das transacoes
            username='testuser',
            name='Test User',
            card_number='12345678',
        )

    def test_transaction_creation(self):
        transaction = Transaction.objects.create(  # Cria uma recarga
            user=self.user,
            type=Transaction.TransactionType.RECHARGE,
            amount=Decimal('50.00'),
        )
        # Verifica que os campos foram gravados como esperado
        self.assertEqual(transaction.user, self.user)
        self.assertEqual(transaction.type, Transaction.TransactionType.RECHARGE)
        self.assertEqual(transaction.amount, Decimal('50.00'))

    def test_transaction_str_representation(self):
        transaction = Transaction.objects.create(  # Cria uma refeicao
            user=self.user,
            type=Transaction.TransactionType.MEAL,
            amount=Decimal('5.60'),
        )
        self.assertEqual(str(transaction), 'MEAL - 5.60')  # Texto no formato tipo - valor

    def test_meal_transaction_type(self):
        transaction = Transaction.objects.create(
            user=self.user,
            type=Transaction.TransactionType.MEAL,
            amount=Decimal('5.60'),
        )
        self.assertEqual(transaction.type, Transaction.TransactionType.MEAL)  # Tipo refeicao gravado

    def test_recharge_transaction_types(self):
        # A recarga aceita os tres metodos de pagamento (online, dinheiro, cartao)
        for method in [Transaction.MethodType.ONLINE, Transaction.MethodType.CASH, Transaction.MethodType.CARD]:
            transaction = Transaction.objects.create(
                user=self.user,
                type=Transaction.TransactionType.RECHARGE,
                amount=Decimal('10.00'),
                recharge_method=method,
            )
            self.assertEqual(transaction.recharge_method, method)

    def test_transaction_cascade_delete(self):
        Transaction.objects.create(  # Cria uma transacao do aluno
            user=self.user,
            type=Transaction.TransactionType.RECHARGE,
            amount=Decimal('50.00'),
        )
        user_id = self.user.id
        self.user.delete()  # Apaga o aluno
        self.assertEqual(Transaction.objects.filter(user_id=user_id).count(), 0)  # Transacoes somem junto
