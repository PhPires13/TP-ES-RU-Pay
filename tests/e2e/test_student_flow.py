"""E2E: aluno se cadastra, faz login, recarrega online e confere o extrato (US1, US3, US4)."""
from decimal import Decimal

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from rupayapp.models import Transaction, User

from ._helpers import BaseE2ETest


class StudentFlowE2ETest(BaseE2ETest):
    def test_cadastro_login_e_recarga_online(self):
        driver = self.selenium

        # 1) Aluno abre a pagina de cadastro e preenche o formulario
        driver.get(f'{self.live_server_url}/aluno/cadastro/')
        driver.find_element(By.ID, 'id_username').send_keys('mariae2e')
        driver.find_element(By.ID, 'id_name').send_keys('Maria E2E Teste')
        driver.find_element(By.ID, 'id_card_number').send_keys('11122233')
        driver.find_element(By.ID, 'id_password').send_keys('senha123')
        driver.find_element(By.ID, 'id_password_confirm').send_keys('senha123')
        submit_btn = self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'form.form-panel button[type="submit"]'))
        )
        driver.execute_script("arguments[0].click();", submit_btn)  # Clica em cadastrar

        # Cadastro valido redireciona para a area do aluno e cria o usuario no banco
        self.wait.until(EC.url_contains('/aluno/consulta/'))
        self.assertTrue(
            User._default_manager.filter(username='mariae2e', card_number='11122233').exists(),
            'Usuário deveria ter sido criado no banco após o cadastro.',
        )

        # 2) Aluno faz login com o usuario e senha recem-criados
        driver.find_element(By.ID, 'id_username').send_keys('mariae2e')
        driver.find_element(By.ID, 'id_password').send_keys('senha123')
        submit_btn = self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'form.form-panel button[type="submit"]'))
        )
        driver.execute_script("arguments[0].click();", submit_btn)  # Clica em entrar

        # Apos o login, o nome do aluno e o saldo (R$ 0) aparecem na tela
        self.wait.until(
            EC.text_to_be_present_in_element((By.CSS_SELECTOR, 'body'), 'Maria E2E Teste')
        )
        self.assertIn('R$ 0', driver.page_source)  # Saldo inicial zerado

        # 3) Aluno digita R$75 e confirma a recarga online
        valor_input = self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="amount"]'))
        )
        valor_input.clear()
        valor_input.send_keys('75.00')
        recharge_form = driver.find_element(By.XPATH, '//form[.//input[@name="recharge"]]')  # Formulario de recarga
        recharge_btn = recharge_form.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
        driver.execute_script("arguments[0].click();", recharge_btn)  # Confirma a recarga

        # 4) A tela mostra a mensagem de sucesso e o novo saldo
        self.wait.until(
            EC.text_to_be_present_in_element((By.CSS_SELECTOR, 'body'), 'Recarga online de R$ 75')
        )
        self.assertIn('R$ 75', driver.page_source)

        # Confirma que a transacao foi gravada no banco corretamente
        student = User._default_manager.get(username='mariae2e')
        transactions = Transaction._default_manager.filter(user=student)
        self.assertEqual(transactions.count(), 1)
        self.assertEqual(transactions.first().amount, Decimal('75.00'))
        self.assertEqual(transactions.first().type, Transaction.TransactionType.RECHARGE)
        self.assertEqual(transactions.first().recharge_method, Transaction.MethodType.ONLINE)

        # E o extrato na tela lista a recarga feita (US4)
        extrato_table = driver.find_element(By.CSS_SELECTOR, 'table.data')
        self.assertIn('Recarga', extrato_table.text)
        self.assertIn('75', extrato_table.text)
