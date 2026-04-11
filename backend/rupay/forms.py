from decimal import Decimal

from django import forms
from django.core.validators import RegexValidator

from .models import Operator, Transaction, User

CARD_NUMBER_VALIDATOR = RegexValidator(
    regex=r'^\d{10}$',
    message='Use exatamente 10 dígitos (ex.: 2024010250).',
)


class CardNumberForm(forms.Form):
    card_number = forms.CharField(
        label='Número da carteirinha',
        max_length=50,
        validators=[CARD_NUMBER_VALIDATOR],
        widget=forms.TextInput(attrs={'autocomplete': 'off', 'placeholder': '2024010250'}),
    )


class UserRegistrationForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'name', 'card_number', 'photo')
        labels = {
            'username': 'Usuário (login)',
            'name': 'Nome completo',
            'card_number': 'Número da carteirinha (10 dígitos)',
            'photo': 'Foto',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['card_number'].validators.append(CARD_NUMBER_VALIDATOR)
        self.fields['card_number'].widget.attrs.setdefault('placeholder', '2024010250')


class OnlineRechargeForm(forms.Form):
    card_number = forms.CharField(
        label='Número da carteirinha',
        max_length=50,
        validators=[CARD_NUMBER_VALIDATOR],
        widget=forms.TextInput(attrs={'placeholder': '2024010250'}),
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
    operator = forms.ModelChoiceField(
        label='Operador',
        queryset=Operator.objects.all().order_by('name'),
        empty_label='Selecione…',
    )


class TurnstileForm(forms.Form):
    card_number = forms.CharField(
        label='Número da carteirinha',
        max_length=50,
        validators=[CARD_NUMBER_VALIDATOR],
        widget=forms.TextInput(attrs={'autocomplete': 'off', 'placeholder': '2024010250'}),
    )
