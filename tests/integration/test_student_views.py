"""Testes de integração das views do aluno (cadastro, login, recarga, extrato)."""
from decimal import Decimal

from django.test import TestCase, Client

from rupayapp.models import User, Transaction


class StudentRegisterViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = '/aluno/cadastro/'

    def test_get(self):
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)

    def test_post_valid(self):
        response = self.client.post(self.register_url, {
            'username': 'newstudent',
            'name': 'New Student',
            'card_number': '12345678',
            'password': 'password123',
            'password_confirm': 'password123',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(User.objects.count(), 1)

    def test_post_invalid(self):
        response = self.client.post(self.register_url, {
            'username': 'newstudent',
            'name': 'New Student',
            'card_number': '1234567',
            'password': 'password123',
            'password_confirm': 'password123',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.count(), 0)
        self.assertIn('form', response.context)


class StudentLookupViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.lookup_url = '/aluno/consulta/'
        self.user = User.objects.create(username='student', name='Student', card_number='12345678')
        self.user.set_password('password123')
        self.user.save()

    def test_get_no_session(self):
        response = self.client.get(self.lookup_url)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context.get('user_obj'))

    def test_login_valid(self):
        response = self.client.post(self.lookup_url, {'username': 'student', 'password': 'password123'})
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context.get('user_obj'))
        self.assertEqual(response.context.get('balance'), Decimal('0'))

    def test_login_invalid_password(self):
        response = self.client.post(self.lookup_url, {'username': 'student', 'password': 'wrongpassword'})
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context.get('user_obj'))

    def test_login_nonexistent_user(self):
        response = self.client.post(self.lookup_url, {'username': 'nonexistent', 'password': 'password123'})
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context.get('user_obj'))

    def test_recharge(self):
        session = self.client.session
        session['student_user_id'] = str(self.user.id)
        session.save()

        response = self.client.post(self.lookup_url, {'recharge': 'true', 'amount': '50.00'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Transaction.objects.count(), 1)
        transaction = Transaction.objects.first()
        self.assertEqual(transaction.amount, Decimal('50.00'))
        self.assertEqual(transaction.type, Transaction.TransactionType.RECHARGE)
        self.assertEqual(transaction.recharge_method, Transaction.MethodType.ONLINE)

    def test_recharge_requires_session(self):
        # Sem sessão ativa, a recarga online não deve criar transação
        response = self.client.post(self.lookup_url, {'recharge': 'true', 'amount': '50.00'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Transaction.objects.count(), 0)

    def test_recharge_invalid_amount(self):
        session = self.client.session
        session['student_user_id'] = str(self.user.id)
        session.save()

        response = self.client.post(self.lookup_url, {'recharge': 'true', 'amount': '0.00'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Transaction.objects.count(), 0)

    def test_logout(self):
        session = self.client.session
        session['student_user_id'] = str(self.user.id)
        session.save()

        response = self.client.post(self.lookup_url, {'logout': 'true'})
        self.assertEqual(response.status_code, 302)
        self.assertNotIn('student_user_id', self.client.session)

    def test_get_with_valid_session(self):
        Transaction.objects.create(
            user=self.user,
            type=Transaction.TransactionType.RECHARGE,
            amount=Decimal('25.00'),
        )
        session = self.client.session
        session['student_user_id'] = str(self.user.id)
        session.save()

        response = self.client.get(self.lookup_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context.get('user_obj'), self.user)
        self.assertEqual(response.context.get('balance'), Decimal('25.00'))
        self.assertEqual(len(response.context.get('transactions')), 1)

    def test_stale_session_is_cleared(self):
        session = self.client.session
        session['student_user_id'] = '00000000-0000-0000-0000-000000000000'
        session.save()

        response = self.client.get(self.lookup_url)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context.get('user_obj'))
        self.assertNotIn('student_user_id', self.client.session)
