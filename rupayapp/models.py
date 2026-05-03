from django.core.validators import RegexValidator
from django.contrib.auth.hashers import check_password, make_password
from django.db import models
from django.conf import settings
import uuid


CARD_NUMBER_VALIDATOR = RegexValidator(
    regex=r'^\d{10}$',
    message='Use exatamente 10 dígitos (ex.: 1234567890).',
)


class User(models.Model):
    THEME_CHOICES = [
        ('light', 'Claro'),
        ('dark', 'Escuro'),
        ('high_contrast', 'Alto Contraste'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=50, unique=True)
    password_hash = models.CharField(max_length=32)
    name = models.CharField(max_length=100)
    card_number = models.CharField(max_length=10, unique=True, validators=[CARD_NUMBER_VALIDATOR])
    created_at = models.DateTimeField(auto_now_add=True)
    photo = models.ImageField(upload_to='photos/', null=True, blank=True)
    theme_preference = models.CharField(max_length=15, choices=THEME_CHOICES, default='light')

    def __str__(self):
        return self.name

    def set_password(self, raw_password):
        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password_hash)


class Transaction(models.Model):

    class TransactionType(models.TextChoices):
        RECHARGE = 'RECHARGE', 'Recharge'
        MEAL = 'MEAL', 'Meal'

    class MethodType(models.TextChoices):
        ONLINE = 'ONLINE', 'Online'
        CASH = 'CASH', 'Cash'
        CARD = 'CARD', 'Card'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    type = models.CharField(max_length=20, choices=TransactionType.choices)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    recharge_method = models.CharField(
        max_length=20,
        choices=MethodType.choices,
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.type} - {self.amount}'