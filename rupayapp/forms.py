from decimal import Decimal

from django import forms

from .models import CARD_NUMBER_VALIDATOR, Transaction, User


class StudentLoginForm(forms.Form):
    username = forms.CharField(label='Usuário', max_length=50)
    password = forms.CharField(label='Senha', widget=forms.PasswordInput())


class CardNumberForm(forms.Form):
    card_number = forms.CharField(
        label='Número da carteirinha',
        max_length=8,
        validators=[CARD_NUMBER_VALIDATOR],
        widget=forms.TextInput(attrs={'autocomplete': 'off', 'placeholder': '12345678'}),
    )


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(label='Senha', widget=forms.PasswordInput())
    password_confirm = forms.CharField(label='Confirmar senha', widget=forms.PasswordInput())

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

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', 'As senhas não conferem.')
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.set_password(self.cleaned_data['password'])
        if commit:
            instance.save()
        return instance


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
