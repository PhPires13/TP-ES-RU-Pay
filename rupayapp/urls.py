from django.urls import path

from . import views

app_name = 'rupayapp'

urlpatterns = [
    path('', views.home, name='home'),
    path('cardapio/', views.cardapio, name='cardapio'),
    path('aluno/cadastro/', views.student_register, name='student_register'),
    path('aluno/consulta/', views.student_lookup, name='student_lookup'),
    path('aluno/recarga-online/', views.student_recharge_online, name='student_recharge_online'),
    path('aluno/extrato/', views.student_history, name='student_history'),
    path('operador/', views.operator_panel, name='operator_panel'),
    path('catraca/', views.turnstile, name='turnstile'),
    path('comprovante/<uuid:transaction_id>/', views.receipt, name='receipt'),
    path('comprovantes/', views.receipt_history, name='receipt_history'),
]