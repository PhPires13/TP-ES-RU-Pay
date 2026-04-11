from decimal import Decimal

from django import forms

from .models import CARD_NUMBER_VALIDATOR, Transaction, User


class CardNumberForm(forms.Form):
    card_number = forms.CharField(
        label='Número da carteirinha',
        max_length=8,
        validators=[CARD_NUMBER_VALIDATOR],
        widget=forms.TextInput(attrs={'autocomplete': 'off', 'placeholder': '12345678'}),
    )


class UserRegistrationForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'name', 'card_number', 'photo')
        labels = {
            'username': 'Usuário (login)',
            'name': 'Nome completo',
            'card_number': 'Número da carteirinha (8 dígitos)',
            'photo': 'Foto',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['card_number'].validators.append(CARD_NUMBER_VALIDATOR)
        self.fields['card_number'].widget.attrs.setdefault('placeholder', '12345678')


class OnlineRechargeForm(forms.Form):
    card_number = forms.CharField(
        label='Número da carteirinha',
        max_length=8,
        validators=[CARD_NUMBER_VALIDATOR],
        widget=forms.TextInput(attrs={'placeholder': '12345678'}),
    )
    amount = forms.DecimalField(
        label='Valor (R$)',
        min_value=Decimal('0.01'),
        max_digits=10,
        decimal_places=2,
    )


class OperatorRechargeForm(forms.Form):
    amount = forms.DecimalField(
        label='Valor da recarga (R$)',
        min_value=Decimal('0.01'),
        max_digits=10,
        decimal_places=2,
    )
    method = forms.ChoiceField(
        label='Forma de pagamento',
        choices=Transaction.MethodType.choices,
        initial=Transaction.MethodType.CASH,
    )


class TurnstileForm(forms.Form):
    card_number = forms.CharField(
        label='Número da carteirinha',
        max_length=8,
        validators=[CARD_NUMBER_VALIDATOR],
        widget=forms.TextInput(attrs={'autocomplete': 'off', 'placeholder': '12345678'}),
    )
