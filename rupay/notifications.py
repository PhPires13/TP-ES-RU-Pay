'''from decimal import Decimal

LIMITE_SALDO = Decimal('5.60')

def notificar_saldo_baixo(aluno, saldo):
    """
    Cria uma notificação persistente para o aluno quando o saldo está abaixo do limite.
    """
    from rupayapp.models import Notificacao

    Notificacao.objects.get_or_create(
        aluno=aluno,
        tipo='SALDO_BAIXO',
        lida=False,
        defaults={
            'mensagem': (
                f'Atenção! Seu saldo está baixo: R$ {saldo:.2f}. '
                'Recarregue sua carteirinha para continuar usando o restaurante universitário.'
            )
        }
    )
    '''