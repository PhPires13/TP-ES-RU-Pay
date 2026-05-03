from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Transaction
from .utils import user_balance
from rupay.notifications import notificar_saldo_baixo

LIMITE_SALDO = 5.60

@receiver(post_save, sender=Transaction)
def verificar_saldo_baixo(sender, instance, **kwargs):
    user = instance.user
    saldo = user_balance(user)
    if saldo < LIMITE_SALDO:
        notificar_saldo_baixo(user, saldo)