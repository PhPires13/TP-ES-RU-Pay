"""Testes de unidade dos formulários (validação, sem acesso a views)."""
from decimal import Decimal

from django.test import TestCase

from rupayapp.forms import (
    CardNumberForm,
    StudentLoginForm,
    UserRegistrationForm,
    OnlineRechargeForm,
    OperatorRechargeForm,
    TurnstileForm,
)
from rupayapp.models import User, Transaction


class CardNumberFormTests(TestCase):
    def test_accepts_exactly_8_digits(self):
        form = CardNumberForm({'card_number': '12345678'})  # Carteirinha valida (8 digitos)
        self.assertTrue(form.is_valid())  # Deve passar

    def test_rejects_7_digits(self):
        form = CardNumberForm({'card_number': '2024010'})  # So 7 digitos
        self.assertFalse(form.is_valid())  # Deve reprovar
        self.assertIn('card_number', form.errors)  # Com erro no campo da carteirinha

    def test_rejects_9_digits(self):
        form = CardNumberForm({'card_number': '123456789'})  # 9 digitos
        self.assertFalse(form.is_valid())

    def test_rejects_letters(self):
        form = CardNumberForm({'card_number': '1234567a'})  # Contem letra
        self.assertFalse(form.is_valid())

    def test_rejects_empty(self):
        form = CardNumberForm({'card_number': ''})  # Campo vazio
        self.assertFalse(form.is_valid())


class StudentLoginFormTests(TestCase):
    def test_accepts_valid_data(self):
        form = StudentLoginForm({'username': 'aluno', 'password': 'segredo'})  # Usuario e senha preenchidos
        self.assertTrue(form.is_valid())

    def test_requires_username(self):
        form = StudentLoginForm({'username': '', 'password': 'segredo'})  # Sem usuario
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

    def test_requires_password(self):
        form = StudentLoginForm({'username': 'aluno', 'password': ''})  # Sem senha
        self.assertFalse(form.is_valid())
        self.assertIn('password', form.errors)

    def test_empty(self):
        form = StudentLoginForm({})  # Formulario vazio
        self.assertFalse(form.is_valid())


class UserRegistrationFormTests(TestCase):
    BASE = {  # Dados validos de cadastro reutilizados nos testes
        'username': 'aluno',
        'name': 'Aluno Teste',
        'card_number': '12345678',
        'password': 'segredo123',
        'password_confirm': 'segredo123',
    }

    def test_valid(self):
        form = UserRegistrationForm(self.BASE)  # Cadastro com tudo certo
        self.assertTrue(form.is_valid())

    def test_hashes_password(self):
        form = UserRegistrationForm(self.BASE)
        self.assertTrue(form.is_valid())
        user = form.save(commit=False)  # Monta o aluno sem salvar no banco
        self.assertNotEqual(user.password_hash, 'segredo123')  # Senha guardada como hash
        self.assertTrue(user.check_password('segredo123'))  # E confere corretamente

    def test_passwords_must_match(self):
        data = {**self.BASE, 'password_confirm': 'diferentes'}  # Confirmacao diferente
        form = UserRegistrationForm(data)
        self.assertFalse(form.is_valid())  # Deve reprovar
        self.assertIn('password_confirm', form.errors)

    def test_requires_all_fields(self):
        data = {k: v for k, v in self.BASE.items() if k != 'password_confirm'}  # Falta a confirmacao
        form = UserRegistrationForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn('password_confirm', form.errors)

    def test_saves_user(self):
        form = UserRegistrationForm(self.BASE)
        self.assertTrue(form.is_valid())
        user = form.save()  # Salva o aluno no banco
        self.assertEqual(User.objects.count(), 1)  # Aluno foi criado
        self.assertEqual(user.username, 'aluno')
        self.assertTrue(user.check_password('segredo123'))

    def test_invalid_card_number(self):
        data = {**self.BASE, 'card_number': '1234567'}  # Carteirinha invalida
        form = UserRegistrationForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn('card_number', form.errors)


class OnlineRechargeFormTests(TestCase):
    def test_valid(self):
        form = OnlineRechargeForm({'amount': '50.00'})  # Valor valido
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['amount'], Decimal('50.00'))

    def test_minimum_amount(self):
        form = OnlineRechargeForm({'amount': '0.01'})  # Valor minimo aceito
        self.assertTrue(form.is_valid())

    def test_rejects_zero(self):
        form = OnlineRechargeForm({'amount': '0.00'})  # Zero nao e permitido
        self.assertFalse(form.is_valid())

    def test_rejects_negative(self):
        form = OnlineRechargeForm({'amount': '-10.00'})  # Valor negativo
        self.assertFalse(form.is_valid())

    def test_accepts_integer_amount_string(self):
        form = OnlineRechargeForm({'amount': '10'})  # Aceita inteiro sem casas decimais
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['amount'], Decimal('10'))

    def test_rejects_non_numeric(self):
        form = OnlineRechargeForm({'amount': 'abc'})  # Texto nao numerico
        self.assertFalse(form.is_valid())


class OperatorRechargeFormTests(TestCase):
    def test_valid_cash(self):
        form = OperatorRechargeForm({'amount': '50.00', 'method': Transaction.MethodType.CASH})  # Em dinheiro
        self.assertTrue(form.is_valid())

    def test_valid_card(self):
        form = OperatorRechargeForm({'amount': '50.00', 'method': Transaction.MethodType.CARD})  # No cartao
        self.assertTrue(form.is_valid())

    def test_requires_method(self):
        form = OperatorRechargeForm({'amount': '50.00', 'method': ''})  # Sem metodo de pagamento
        self.assertFalse(form.is_valid())

    def test_rejects_zero(self):
        form = OperatorRechargeForm({'amount': '0.00', 'method': Transaction.MethodType.CASH})  # Valor zero
        self.assertFalse(form.is_valid())

    def test_rejects_negative(self):
        form = OperatorRechargeForm({'amount': '-5.00', 'method': Transaction.MethodType.CASH})  # Valor negativo
        self.assertFalse(form.is_valid())


class TurnstileFormTests(TestCase):
    def test_valid(self):
        form = TurnstileForm({'card_number': '12345678'})  # Carteirinha valida na catraca
        self.assertTrue(form.is_valid())

    def test_invalid_card_number(self):
        form = TurnstileForm({'card_number': '1234567'})  # Carteirinha invalida
        self.assertFalse(form.is_valid())
