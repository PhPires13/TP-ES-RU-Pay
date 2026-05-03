"""
Context processors for rupayapp templates
Provides global context variables available to all templates
"""

from .views import get_user_theme
from .views import _get_student_from_session
from .models import Notificacao


def theme_context(request):
    """
    Provides user_theme to all templates
    """
    # adiciona tema e notificações do aluno (se houver sessão de aluno)
    aluno = _get_student_from_session(request)
    notificacoes = []
    notificacoes_count = 0
    if aluno:
        qs = Notificacao.objects.filter(aluno=aluno, lida=False)
        notificacoes = list(qs)
        notificacoes_count = qs.count()

    return {
        'user_theme': get_user_theme(request),
        'notificacoes': notificacoes,
        'notificacoes_count': notificacoes_count,
    }
