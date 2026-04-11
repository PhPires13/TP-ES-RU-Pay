from django.core.exceptions import ValidationError
from django.test import TestCase

from .forms import CardNumberForm
from .models import User


class CardNumberValidationTests(TestCase):
	def test_card_number_form_accepts_exactly_8_digits(self):
		form = CardNumberForm({'card_number': '12345678'})

		self.assertTrue(form.is_valid())

	def test_card_number_form_rejects_non_8_digit_values(self):
		form = CardNumberForm({'card_number': '2024010'})

		self.assertFalse(form.is_valid())
		self.assertIn('card_number', form.errors)

	def test_user_model_rejects_non_8_digit_card_numbers(self):
		user = User(username='teste', name='Teste', card_number='2024010')

		with self.assertRaises(ValidationError):
			user.full_clean()
