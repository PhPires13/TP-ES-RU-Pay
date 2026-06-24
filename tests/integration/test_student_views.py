"""Testes de integração das views do aluno (cadastro, login, recarga, extrato)."""
from decimal import Decimal

from django.test import TestCase, Client

from rupayapp.models import User, Transaction


class StudentRegisterViewTests(TestCase):
    def setUp(self):
        self.client = Client()  # Navegador simulado do Django
        self.register_url = '/aluno/cadastro/'

    def test_get(self):
        response = self.client.get(self.register_url)  # Abre a pagina de cadastro
        self.assertEqual(response.status_code, 200)  # Pagina carrega
        self.assertIn('form', response.context)  # E traz o formulario

    def test_post_valid(self):
        response = self.client.post(self.register_url, {  # Envia cadastro valido
            'username': 'newstudent',
            'name': 'New Student',
            'card_number': '12345678',
            'password': 'password123',
            'password_confirm': 'password123',
        })
        self.assertEqual(response.status_code, 302)  # Redireciona apos sucesso
        self.assertEqual(User.objects.count(), 1)  # Aluno foi criado

    def test_post_invalid(self):
        response = self.client.post(self.register_url, {  # Carteirinha invalida (7 digitos)
            'username': 'newstudent',
            'name': 'New Student',
            'card_number': '1234567',
            'password': 'password123',
            'password_confirm': 'password123',
        })
        self.assertEqual(response.status_code, 200)  # Continua na mesma pagina
        self.assertEqual(User.objects.count(), 0)  # Nenhum aluno criado
        self.assertIn('form', response.context)  # Formulario volta com erros


class StudentLookupViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.lookup_url = '/aluno/consulta/'
        self.user = User.objects.create(username='student', name='Student', card_number='12345678')  # Aluno ja cadastrado
        self.user.set_password('password123')
        self.user.save()

    def test_get_no_session(self):
        response = self.client.get(self.lookup_url)  # Acessa sem estar logado
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context.get('user_obj'))  # Ninguem logado ainda

    def test_login_valid(self):
        response = self.client.post(self.lookup_url, {'username': 'student', 'password': 'password123'})  # Login correto
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context.get('user_obj'))  # Aluno autenticado
        self.assertEqual(response.context.get('balance'), Decimal('0'))  # Saldo inicial zero

    def test_login_invalid_password(self):
        response = self.client.post(self.lookup_url, {'username': 'student', 'password': 'wrongpassword'})  # Senha errada
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context.get('user_obj'))  # Nao loga

    def test_login_nonexistent_user(self):
        response = self.client.post(self.lookup_url, {'username': 'nonexistent', 'password': 'password123'})  # Usuario inexistente
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context.get('user_obj'))  # Nao loga

    def test_recharge(self):
        session = self.client.session  # Simula aluno logado
        session['student_user_id'] = str(self.user.id)
        session.save()

        response = self.client.post(self.lookup_url, {'recharge': 'true', 'amount': '50.00'})  # Faz recarga online de R$50
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Transaction.objects.count(), 1)  # Criou uma transacao
        transaction = Transaction.objects.first()
        self.assertEqual(transaction.amount, Decimal('50.00'))  # No valor certo
        self.assertEqual(transaction.type, Transaction.TransactionType.RECHARGE)  # Do tipo recarga
        self.assertEqual(transaction.recharge_method, Transaction.MethodType.ONLINE)  # E pelo metodo online

    def test_recharge_requires_session(self):
        # Sem aluno logado, a recarga online nao deve criar transacao
        response = self.client.post(self.lookup_url, {'recharge': 'true', 'amount': '50.00'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Transaction.objects.count(), 0)  # Nada criado

    def test_recharge_invalid_amount(self):
        session = self.client.session  # Aluno logado
        session['student_user_id'] = str(self.user.id)
        session.save()

        response = self.client.post(self.lookup_url, {'recharge': 'true', 'amount': '0.00'})  # Valor invalido (zero)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Transaction.objects.count(), 0)  # Nao cria transacao

    def test_logout(self):
        session = self.client.session  # Aluno logado
        session['student_user_id'] = str(self.user.id)
        session.save()

        response = self.client.post(self.lookup_url, {'logout': 'true'})  # Clica em sair
        self.assertEqual(response.status_code, 302)  # Redireciona
        self.assertNotIn('student_user_id', self.client.session)  # Sessao foi encerrada

    def test_get_with_valid_session(self):
        Transaction.objects.create(  # Aluno ja tem uma recarga de R$25
            user=self.user,
            type=Transaction.TransactionType.RECHARGE,
            amount=Decimal('25.00'),
        )
        session = self.client.session  # E esta logado
        session['student_user_id'] = str(self.user.id)
        session.save()

        response = self.client.get(self.lookup_url)  # Abre a area do aluno
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context.get('user_obj'), self.user)  # Mostra o aluno
        self.assertEqual(response.context.get('balance'), Decimal('25.00'))  # Saldo correto
        self.assertEqual(len(response.context.get('transactions')), 1)  # Extrato com 1 lancamento

    def test_stale_session_is_cleared(self):
        session = self.client.session  # Sessao aponta para um id que nao existe mais
        session['student_user_id'] = '00000000-0000-0000-0000-000000000000'
        session.save()

        response = self.client.get(self.lookup_url)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context.get('user_obj'))  # Trata como anonimo
        self.assertNotIn('student_user_id', self.client.session)  # E limpa a sessao invalida
