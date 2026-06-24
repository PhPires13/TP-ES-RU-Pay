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
        form = CardNumberForm({'card_number': '12345678'})
        self.assertTrue(form.is_valid())

    def test_rejects_7_digits(self):
        form = CardNumberForm({'card_number': '2024010'})
        self.assertFalse(form.is_valid())
        self.assertIn('card_number', form.errors)

    def test_rejects_9_digits(self):
        form = CardNumberForm({'card_number': '123456789'})
        self.assertFalse(form.is_valid())

    def test_rejects_letters(self):
        form = CardNumberForm({'card_number': '1234567a'})
        self.assertFalse(form.is_valid())

    def test_rejects_empty(self):
        form = CardNumberForm({'card_number': ''})
        self.assertFalse(form.is_valid())


class StudentLoginFormTests(TestCase):
    def test_accepts_valid_data(self):
        form = StudentLoginForm({'username': 'aluno', 'password': 'segredo'})
        self.assertTrue(form.is_valid())

    def test_requires_username(self):
        form = StudentLoginForm({'username': '', 'password': 'segredo'})
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

    def test_requires_password(self):
        form = StudentLoginForm({'username': 'aluno', 'password': ''})
        self.assertFalse(form.is_valid())
        self.assertIn('password', form.errors)

    def test_empty(self):
        form = StudentLoginForm({})
        self.assertFalse(form.is_valid())


class UserRegistrationFormTests(TestCase):
    BASE = {
        'username': 'aluno',
        'name': 'Aluno Teste',
        'card_number': '12345678',
        'password': 'segredo123',
        'password_confirm': 'segredo123',
    }

    def test_valid(self):
        form = UserRegistrationForm(self.BASE)
        self.assertTrue(form.is_valid())

    def test_hashes_password(self):
        form = UserRegistrationForm(self.BASE)
        self.assertTrue(form.is_valid())
        user = form.save(commit=False)
        self.assertNotEqual(user.password_hash, 'segredo123')
        self.assertTrue(user.check_password('segredo123'))

    def test_passwords_must_match(self):
        data = {**self.BASE, 'password_confirm': 'diferentes'}
        form = UserRegistrationForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn('password_confirm', form.errors)

    def test_requires_all_fields(self):
        data = {k: v for k, v in self.BASE.items() if k != 'password_confirm'}
        form = UserRegistrationForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn('password_confirm', form.errors)

    def test_saves_user(self):
        form = UserRegistrationForm(self.BASE)
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(user.username, 'aluno')
        self.assertTrue(user.check_password('segredo123'))

    def test_invalid_card_number(self):
        data = {**self.BASE, 'card_number': '1234567'}
        form = UserRegistrationForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn('card_number', form.errors)


class OnlineRechargeFormTests(TestCase):
    def test_valid(self):
        form = OnlineRechargeForm({'amount': '50.00'})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['amount'], Decimal('50.00'))

    def test_minimum_amount(self):
        form = OnlineRechargeForm({'amount': '0.01'})
        self.assertTrue(form.is_valid())

    def test_rejects_zero(self):
        form = OnlineRechargeForm({'amount': '0.00'})
        self.assertFalse(form.is_valid())

    def test_rejects_negative(self):
        form = OnlineRechargeForm({'amount': '-10.00'})
        self.assertFalse(form.is_valid())

    def test_accepts_integer_amount_string(self):
        form = OnlineRechargeForm({'amount': '10'})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['amount'], Decimal('10'))

    def test_rejects_non_numeric(self):
        form = OnlineRechargeForm({'amount': 'abc'})
        self.assertFalse(form.is_valid())


class OperatorRechargeFormTests(TestCase):
    def test_valid_cash(self):
        form = OperatorRechargeForm({'amount': '50.00', 'method': Transaction.MethodType.CASH})
        self.assertTrue(form.is_valid())

    def test_valid_card(self):
        form = OperatorRechargeForm({'amount': '50.00', 'method': Transaction.MethodType.CARD})
        self.assertTrue(form.is_valid())

    def test_requires_method(self):
        form = OperatorRechargeForm({'amount': '50.00', 'method': ''})
        self.assertFalse(form.is_valid())

    def test_rejects_zero(self):
        form = OperatorRechargeForm({'amount': '0.00', 'method': Transaction.MethodType.CASH})
        self.assertFalse(form.is_valid())

    def test_rejects_negative(self):
        form = OperatorRechargeForm({'amount': '-5.00', 'method': Transaction.MethodType.CASH})
        self.assertFalse(form.is_valid())


class TurnstileFormTests(TestCase):
    def test_valid(self):
        form = TurnstileForm({'card_number': '12345678'})
        self.assertTrue(form.is_valid())

    def test_invalid_card_number(self):
        form = TurnstileForm({'card_number': '1234567'})
        self.assertFalse(form.is_valid())
