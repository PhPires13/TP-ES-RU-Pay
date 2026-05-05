from django.contrib import messages
from django.db import transaction as db_transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
import urllib.request
import json
from datetime import date

from .forms import (
    CardNumberForm,
    OnlineRechargeForm,
    OperatorRechargeForm,
    StudentLoginForm,
    TurnstileForm,
    UserRegistrationForm,
)
from .models import Transaction, User  # type: ignore
from .utils import meal_price, user_balance


STUDENT_SESSION_KEY = 'student_user_id'


def _get_student_from_session(request):
    student_id = request.session.get(STUDENT_SESSION_KEY)
    if not student_id:
        return None
    try:
        return User.objects.get(id=student_id)  # type: ignore
    except User.DoesNotExist:  # type: ignore
        request.session.pop(STUDENT_SESSION_KEY, None)
        return None


def _get_student_from_request(request):
    card_number = request.GET.get('card_number', '').strip() or request.POST.get('card_number', '').strip()
    if card_number:
        return get_object_or_404(User, card_number=card_number)  # type: ignore
    return _get_student_from_session(request)


def receipt(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id)  # type: ignore
    return render(
        request,
        'rupayapp/receipt.html',
        {
            'transaction': transaction,
            'user': transaction.user,
            'balance': user_balance(transaction.user),
        },
    )



def home(request):
    return render(request, 'rupayapp/home.html', {'meal_price': meal_price()})


FUMP_API = 'https://fump.ufmg.br:3003/cardapios'


def _fump_get(path):
    try:
        with urllib.request.urlopen(f'{FUMP_API}{path}', timeout=5) as r:
            return json.loads(r.read().decode())
    except Exception:
        return None


def cardapio(request):
    restaurantes = _fump_get('/restaurantes') or []
    cardapio_data = None
    erro = None
    restaurante_id = request.GET.get('restaurante', '')
    data_consulta = request.GET.get('data', date.today().isoformat())

    if restaurante_id and data_consulta:
        result = _fump_get(f'/cardapio?id={restaurante_id}&dataInicio={data_consulta}&dataFim={data_consulta}')
        if result is None:
            erro = 'Não foi possível conectar ao serviço da FUMP.'
        elif not result.get('cardapios'):
            erro = 'Nenhum cardápio encontrado para essa data.'
        else:
            cardapio_data = result

    return render(request, 'rupayapp/cardapio.html', {
        'restaurantes': restaurantes,
        'cardapio_data': cardapio_data,
        'restaurante_id': restaurante_id,
        'data_consulta': data_consulta,
        'erro': erro,
    })


@require_http_methods(['GET', 'POST'])
def student_register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cadastro realizado. Você já pode consultar saldo e recarregar.')
            return redirect('rupayapp:student_lookup')
    else:
        form = UserRegistrationForm()
    return render(request, 'rupayapp/student_register.html', {'form': form})


@require_http_methods(['GET', 'POST'])
def student_lookup(request):
    user_obj = _get_student_from_session(request)
    balance = user_balance(user_obj) if user_obj else None
    recharge_form = None
    transactions = None
    
    if request.method == 'POST' and 'logout' in request.POST:
        request.session.pop(STUDENT_SESSION_KEY, None)
        messages.success(request, 'Você saiu da área do aluno.')
        return redirect('rupayapp:student_lookup')

    if user_obj:
        form = StudentLoginForm(initial={'username': user_obj.username})
        recharge_form = OnlineRechargeForm()
        transactions = user_obj.transactions.order_by('-created_at')
        
        # Handle recharge form submission
        if request.method == 'POST' and 'recharge' in request.POST:
            recharge_form = OnlineRechargeForm(request.POST)
            if recharge_form.is_valid():
                Transaction.objects.create(  # type: ignore
                    user=user_obj,
                    type=Transaction.TransactionType.RECHARGE,
                    amount=recharge_form.cleaned_data['amount'],
                    recharge_method=Transaction.MethodType.ONLINE,
                )
                messages.success(
                    request,
                    f'Recarga online de R$ {recharge_form.cleaned_data["amount"]} registrada com sucesso.',
                )
                balance = user_balance(user_obj)
                recharge_form = OnlineRechargeForm()
                transactions = user_obj.transactions.order_by('-created_at')
    elif request.method == 'POST':
        form = StudentLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            try:
                user_obj = User.objects.get(username=username)  # type: ignore
            except User.DoesNotExist:  # type: ignore
                messages.error(request, 'Usuário ou senha inválidos.')
            else:
                if user_obj.check_password(password):
                    request.session[STUDENT_SESSION_KEY] = str(user_obj.id)
                    balance = user_balance(user_obj)
                    recharge_form = OnlineRechargeForm()
                    transactions = user_obj.transactions.order_by('-created_at')
                    messages.success(request, f'Bem-vindo, {user_obj.name}.')
                else:
                    user_obj = None
                    messages.error(request, 'Usuário ou senha inválidos.')
    else:
        form = StudentLoginForm()

    if not user_obj:
        balance = None

    return render(
        request,
        'rupayapp/student_lookup.html',
        {
            'form': form,
            'user_obj': user_obj,
            'balance': balance,
            'meal_price': meal_price(),
            'recharge_form': recharge_form,
            'transactions': transactions,
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
            method = recharge_form.cleaned_data['method']
            amount = recharge_form.cleaned_data['amount']
            Transaction.objects.create(  # type: ignore
                user=user_obj,
                type=Transaction.TransactionType.RECHARGE,
                amount=amount,
                recharge_method=method,
            )
            messages.success(request, f'Recarga de R$ {amount} registrada para {user_obj.name}.')
            # Clear the form and user data after successful recharge
            user_obj = None
            balance = None
            recharge_form = None
            lookup_form = CardNumberForm(prefix='lookup')
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
        'rupayapp/operator_panel.html',
        {
            'lookup_form': lookup_form,
            'user_obj': user_obj,
            'balance': balance,
            'recharge_form': recharge_form,
            'meal_price': meal_price(),
        },
    )


@require_http_methods(['GET', 'POST'])
def turnstile(request):
    user_obj = None
    result = None
    balance = None

    if request.method == 'POST':
        # ETAPA 1: Buscar usuário
        if 'lookup' in request.POST:
            form = TurnstileForm(request.POST)
            if form.is_valid():
                cn = form.cleaned_data['card_number']
                try:
                    user_obj = User.objects.get(card_number=cn)
                    balance = user_balance(user_obj)
                except User.DoesNotExist:
                    messages.error(request, 'Carteirinha não cadastrada.')

        # ETAPA 2: Confirmar entrada
        elif 'confirm' in request.POST:
            cn = request.POST.get('card_number')
            try:
                with db_transaction.atomic():
                    user_obj = User.objects.select_for_update().get(card_number=cn)
                    balance = user_balance(user_obj)
                    bal = balance
                    price = meal_price()

                    if bal < price:
                        messages.error(request, f'Acesso negado — saldo insuficiente (R$ {bal:.2f})')
                    else:
                        transaction = Transaction.objects.create(
                            user=user_obj,
                            type=Transaction.TransactionType.MEAL,
                            amount=price,
                        )
                        new_balance = user_balance(user_obj)
                        messages.success(request, f'Acesso liberado — saldo após débito: R$ {new_balance:.2f}')
                        # Clear the form after successful access
                        user_obj = None
                        balance = None
                        form = TurnstileForm()

            except User.DoesNotExist:
                messages.error(request, 'Carteirinha não cadastrada.')

    else:
        form = TurnstileForm()

    if 'form' not in locals():
        form = TurnstileForm()

    return render(request, 'rupayapp/turnstile.html', {
        'form': form,
        'user_obj': user_obj,
        'result': result,
        'meal_price': meal_price(),
        'balance': balance,
    })