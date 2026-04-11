from django.contrib import messages
from django.db import transaction as db_transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

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


def receipt_history(request):
    u = _get_student_from_request(request)
    if not u:
        messages.info(request, 'Entre com usuário e senha para ver os comprovantes.')
        return redirect('rupayapp:student_lookup')

    receipts = u.transactions.filter(type=Transaction.TransactionType.MEAL).order_by('-created_at')  # type: ignore
    return render(
        request,
        'rupayapp/receipt_history.html',
        {
            'user_obj': u,
            'receipts': receipts,
            'balance': user_balance(u),
        },
    )


def home(request):
    return render(request, 'rupayapp/home.html', {'meal_price': meal_price()})


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
    if request.method == 'POST' and 'logout' in request.POST:
        request.session.pop(STUDENT_SESSION_KEY, None)
        messages.success(request, 'Você saiu da área do aluno.')
        return redirect('rupayapp:student_lookup')

    if user_obj:
        form = StudentLoginForm(initial={'username': user_obj.username})
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
        },
    )


@require_http_methods(['GET', 'POST'])
def student_recharge_online(request):
    user_obj = _get_student_from_request(request)
    if request.method == 'POST':
        form = OnlineRechargeForm(request.POST)
        if form.is_valid():
            u = user_obj
            if u is None:
                try:
                    u = User.objects.get(card_number=form.cleaned_data['card_number'])  # type: ignore
                except User.DoesNotExist:  # type: ignore
                    messages.error(request, 'Carteirinha não encontrada.')
            if u is None:
                pass
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
                return redirect('rupayapp:student_lookup')
    else:
        initial = {}
        if user_obj:
            initial['card_number'] = user_obj.card_number
        if cn := request.GET.get('card_number', '').strip():
            initial['card_number'] = cn
        form = OnlineRechargeForm(initial=initial)

    return render(request, 'rupayapp/student_recharge_online.html', {'form': form})


def student_history(request):
    u = _get_student_from_request(request)
    if not u:
        messages.info(request, 'Entre com usuário e senha para ver o extrato.')
        return redirect('rupayapp:student_lookup')

    txs = u.transactions.order_by('-created_at')
    return render(
        request,
        'rupayapp/student_history.html',
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
            method = recharge_form.cleaned_data['method']
            amount = recharge_form.cleaned_data['amount']
            Transaction.objects.create(  # type: ignore
                user=user_obj,
                type=Transaction.TransactionType.RECHARGE,
                amount=amount,
                recharge_method=method,
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
        'rupayapp/operator_panel.html',
        {
            'lookup_form': lookup_form,
            'user_obj': user_obj,
            'balance': balance,
            'recharge_form': recharge_form,
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
                        return redirect('rupayapp:receipt', transaction_id=transaction.id)
            except User.DoesNotExist:  # type: ignore
                messages.error(request, 'Carteirinha não cadastrada.')
                form = TurnstileForm(request.POST)
    else:
        form = TurnstileForm()

    return render(
        request,
        'rupayapp/turnstile.html',
        {
            'form': form,
            'result': result,
            'meal_price': meal_price(),
        },
    )