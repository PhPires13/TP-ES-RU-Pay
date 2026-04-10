from django.contrib import admin

from .models import Operator, Transaction, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('name', 'username', 'card_number', 'created_at')
    search_fields = ('name', 'username', 'card_number')


@admin.register(Operator)
class OperatorAdmin(admin.ModelAdmin):
    list_display = ('name', 'username', 'created_at')
    search_fields = ('name', 'username')


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'user', 'type', 'amount', 'recharge_method', 'operator')
    list_filter = ('type', 'recharge_method')
    search_fields = ('user__name', 'user__card_number')
    date_hierarchy = 'created_at'
