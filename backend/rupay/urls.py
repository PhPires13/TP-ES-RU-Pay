from django.urls import path

from .views import (
    CardLookupView,
    OnlineRechargeView,
    OperatorRechargeView,
    TurnstileValidationView,
    UserBalanceView,
    UserTransactionHistoryView,
)

urlpatterns = [
    path('recharges/online/', OnlineRechargeView.as_view(), name='recharge-online'),
    path('recharges/operator/', OperatorRechargeView.as_view(), name='recharge-operator'),
    path('users/<uuid:user_id>/balance/', UserBalanceView.as_view(), name='user-balance'),
    path(
        'users/<uuid:user_id>/transactions/',
        UserTransactionHistoryView.as_view(),
        name='user-transactions',
    ),
    path('turnstile/validate/', TurnstileValidationView.as_view(), name='turnstile-validate'),
    path('cards/<str:card_number>/', CardLookupView.as_view(), name='card-lookup'),
]

