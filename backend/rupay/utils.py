from decimal import Decimal

from django.conf import settings

from .models import Transaction


def meal_price() -> Decimal:
    return Decimal(settings.RU_MEAL_PRICE)


def user_balance(user) -> Decimal:
    total = Decimal('0')
    for t in user.transactions.all():
        if t.type == Transaction.TransactionType.RECHARGE:
            total += t.amount
        elif t.type == Transaction.TransactionType.MEAL:
            total -= t.amount
    return total
