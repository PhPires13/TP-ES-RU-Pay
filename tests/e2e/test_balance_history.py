"""E2E: aluno consulta saldo e histórico de transações (US3 e US4)."""
from decimal import Decimal

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from rupayapp.models import Transaction, User

from ._helpers import BaseE2ETest


class BalanceAndHistoryE2ETest(BaseE2ETest):
    def setUp(self):
        super().setUp()
        # Aluno já cadastrado e com histórico: 1 recarga e 1 refeição
        self.student = User._default_manager.create(
            username='historicoe2e',
            name='Historico E2E',
            card_number='66677788',
        )
        self.student.set_password('senha123')
        self.student.save()
        Transaction._default_manager.create(
            user=self.student,
            type=Transaction.TransactionType.RECHARGE,
            amount=Decimal('50.00'),
            recharge_method=Transaction.MethodType.ONLINE,
        )
        Transaction._default_manager.create(
            user=self.student,
            type=Transaction.TransactionType.MEAL,
            amount=Decimal('5.60'),
        )

    def test_aluno_consulta_saldo_e_historico(self):
        driver = self.selenium

        # 1) Aluno faz login na área de consulta
        driver.get(f'{self.live_server_url}/aluno/consulta/')
        driver.find_element(By.ID, 'id_username').send_keys('historicoe2e')
        driver.find_element(By.ID, 'id_password').send_keys('senha123')
        submit_btn = self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'form.form-panel button[type="submit"]'))
        )
        driver.execute_script("arguments[0].click();", submit_btn)

        # 2) Nome e saldo atual (50,00 - 5,60 = 44,40) devem aparecer na tela
        self.wait.until(
            EC.text_to_be_present_in_element((By.CSS_SELECTOR, 'body'), 'Historico E2E')
        )
        self.assertIn('44,40', driver.page_source)

        # 3) O extrato deve listar tanto a recarga quanto a refeição (US4)
        extrato_table = self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'table.data'))
        )
        self.assertIn('Recarga', extrato_table.text)
        self.assertIn('Refeição', extrato_table.text)
        self.assertIn('50', extrato_table.text)
        self.assertIn('5', extrato_table.text)
