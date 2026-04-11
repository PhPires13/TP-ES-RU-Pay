from django.contrib import messages
from django.db import transaction as db_transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from .forms import (
    CardNumberForm,
    OnlineRechargeForm,
    OperatorRechargeForm,
    TurnstileForm,
    UserRegistrationForm,
)
from .models import Operator, Transaction, User  # type: ignore
from .utils import meal_price, user_balance


def receipt(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id)  # type: ignore
    return render(
        request,
        'rupay/receipt.html',
        {
            'transaction': transaction,
            'user': transaction.user,
            'balance': user_balance(transaction.user),
        },
    )


def receipt_history(request):
    card_number = request.GET.get('card_number', '').strip()
    if not card_number:
        messages.info(request, 'Informe o número da carteirinha para ver os comprovantes.')
        return redirect('rupay:student_lookup')

    u = get_object_or_404(User, card_number=card_number)  # type: ignore
    receipts = u.transactions.filter(type=Transaction.TransactionType.MEAL).order_by('-created_at')  # type: ignore
    return render(
        request,
        'rupay/receipt_history.html',
        {
            'user_obj': u,
            'receipts': receipts,
            'balance': user_balance(u),
        },
    )


def home(request):
    return render(request, 'rupay/home.html', {'meal_price': meal_price()})


@require_http_methods(['GET', 'POST'])
def student_register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cadastro realizado. Você já pode consultar saldo e recarregar.')
            return redirect('rupay:student_lookup')
    else:
        form = UserRegistrationForm()
    return render(request, 'rupay/student_register.html', {'form': form})


@require_http_methods(['GET', 'POST'])
def student_lookup(request):
    user_obj = None
    balance = None
    card_number = request.GET.get('card_number', '').strip()
    if request.method == 'POST':
        form = CardNumberForm(request.POST)
        if form.is_valid():
            card_number = form.cleaned_data['card_number']
            try:
                user_obj = User.objects.get(card_number=card_number)  # type: ignore
                balance = user_balance(user_obj)
            except User.DoesNotExist:  # type: ignore
                messages.error(request, 'Carteirinha não encontrada. Verifique o número ou cadastre-se.')
    else:
        form = CardNumberForm(initial={'card_number': card_number} if card_number else None)
        if card_number:
            try:
                user_obj = User.objects.get(card_number=card_number)  # type: ignore
                balance = user_balance(user_obj)
            except User.DoesNotExist:  # type: ignore
                messages.warning(request, 'Carteirinha não encontrada.')

    return render(
        request,
        'rupay/student_lookup.html',
        {
            'form': form,
            'user_obj': user_obj,
            'balance': balance,
            'meal_price': meal_price(),
        },
    )


@require_http_methods(['GET', 'POST'])
def student_recharge_online(request):
    if request.method == 'POST':
        form = OnlineRechargeForm(request.POST)
        if form.is_valid():
            card = form.cleaned_data['card_number']
            try:
                u = User.objects.get(card_number=card)  # type: ignore
            except User.DoesNotExist:  # type: ignore
                messages.error(request, 'Carteirinha não encontrada.')
            else:
                Transaction.objects.create(  # type: ignore
                    user=u,
                    type=Transaction.TransactionType.RECHARGE,
                    amount=form.cleaned_data['amount'],
                    recharge_method=Transaction.MethodType.ONLINE,
                )
                messages.success(
                    request,
                    f'Recarga online de R$ {form.cleaned_data["amount"]} registrada com sucesso.',
                )
                return redirect(f'{reverse("rupay:student_lookup")}?card_number={u.card_number}')
    else:
        initial = {}
        if cn := request.GET.get('card_number', '').strip():
            initial['card_number'] = cn
        form = OnlineRechargeForm(initial=initial)

    return render(request, 'rupay/student_recharge_online.html', {'form': form})


def student_history(request):
    card_number = request.GET.get('card_number', '').strip()
    if not card_number:
        messages.info(request, 'Informe o número da carteirinha para ver o extrato.')
        return redirect('rupay:student_lookup')

    u = get_object_or_404(User, card_number=card_number)
    txs = u.transactions.select_related('operator').order_by('-created_at')
    return render(
        request,
        'rupay/student_history.html',
        {
            'user_obj': u,
            'transactions': txs,
            'balance': user_balance(u),
        },
    )


@require_http_methods(['GET', 'POST'])
def operator_panel(request):
    user_obj = None
    balance = None
    recharge_form = None
    lookup_form = CardNumberForm(prefix='lookup')

    if request.method == 'POST' and 'lookup' in request.POST:
        lookup_form = CardNumberForm(request.POST, prefix='lookup')
        if lookup_form.is_valid():
            cn = lookup_form.cleaned_data['card_number']
            try:
                user_obj = User.objects.get(card_number=cn)  # type: ignore
                balance = user_balance(user_obj)
                recharge_form = OperatorRechargeForm()
            except User.DoesNotExist:  # type: ignore
                messages.error(request, 'Carteirinha não encontrada.')
    elif request.method == 'POST' and 'recharge' in request.POST:
        cn = request.POST.get('card_number', '').strip()
        user_obj = get_object_or_404(User, card_number=cn)
        balance = user_balance(user_obj)
        recharge_form = OperatorRechargeForm(request.POST)
        lookup_form = CardNumberForm(prefix='lookup', initial={'card_number': cn})
        if recharge_form.is_valid():
            op = recharge_form.cleaned_data['operator']
            method = recharge_form.cleaned_data['method']
            amount = recharge_form.cleaned_data['amount']
            Transaction.objects.create(  # type: ignore
                user=user_obj,
                type=Transaction.TransactionType.RECHARGE,
                amount=amount,
                recharge_method=method,
                operator=op,
            )
            messages.success(request, f'Recarga de R$ {amount} registrada para {user_obj.name}.')
            balance = user_balance(user_obj)
            recharge_form = OperatorRechargeForm()
    else:
        cn = request.GET.get('card_number', '').strip()
        if cn:
            try:
                user_obj = User.objects.get(card_number=cn)  # type: ignore
                balance = user_balance(user_obj)
                recharge_form = OperatorRechargeForm()
                lookup_form = CardNumberForm(prefix='lookup', initial={'card_number': cn})
            except User.DoesNotExist:  # type: ignore
                messages.warning(request, 'Carteirinha não encontrada.')

    return render(
        request,
        'rupay/operator_panel.html',
        {
            'lookup_form': lookup_form,
            'user_obj': user_obj,
            'balance': balance,
            'recharge_form': recharge_form,
            'operators_exist': Operator.objects.exists(),  # type: ignore
        },
    )


@require_http_methods(['GET', 'POST'])
def turnstile(request):
    result = None
    if request.method == 'POST':
        form = TurnstileForm(request.POST)
        if form.is_valid():
            cn = form.cleaned_data['card_number']
            try:
                with db_transaction.atomic():  # type: ignore
                    u = User.objects.select_for_update().get(card_number=cn)  # type: ignore
                    bal = user_balance(u)
                    price = meal_price()
                    if bal < price:
                        result = {'allowed': False, 'user': u, 'balance': bal, 'price': price}
                    else:
                        transaction = Transaction.objects.create(  # type: ignore
                            user=u,
                            type=Transaction.TransactionType.MEAL,
                            amount=price,
                        )
                        return redirect('rupay:receipt', transaction_id=transaction.id)
            except User.DoesNotExist:  # type: ignore
                messages.error(request, 'Carteirinha não cadastrada.')
                form = TurnstileForm(request.POST)
    else:
        form = TurnstileForm()

    return render(
        request,
        'rupay/turnstile.html',
        {
            'form': form,
            'result': result,
            'meal_price': meal_price(),
        },
    )
