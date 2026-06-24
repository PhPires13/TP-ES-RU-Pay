"""E2E: catraca bloqueia o acesso de aluno com saldo insuficiente (US9)."""
from decimal import Decimal

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from rupayapp.models import Transaction, User
from rupayapp.utils import user_balance

from ._helpers import BaseE2ETest


class TurnstileAccessDeniedE2ETest(BaseE2ETest):
    def setUp(self):
        super().setUp()
        # Aluno com saldo de apenas R$2,00 (abaixo do preco da refeicao de R$5,60)
        self.student = User._default_manager.create(
            username='semsaldoe2e',
            name='Sem Saldo E2E',
            card_number='55544433',
        )
        Transaction._default_manager.create(
            user=self.student,
            type=Transaction.TransactionType.RECHARGE,
            amount=Decimal('2.00'),
            recharge_method=Transaction.MethodType.ONLINE,
        )

    def test_catraca_bloqueia_saldo_insuficiente(self):
        driver = self.selenium

        # 1) Aluno passa a carteirinha na catraca
        driver.get(f'{self.live_server_url}/catraca/')
        driver.find_element(By.ID, 'id_card_number').send_keys('55544433')
        lookup_btn = self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'button[type="submit"][name="lookup"]'))
        )
        driver.execute_script("arguments[0].click();", lookup_btn)  # Busca o aluno

        # Tela mostra o aluno e o botao de confirmar entrada
        self.wait.until(
            EC.text_to_be_present_in_element((By.CSS_SELECTOR, 'body'), 'Sem Saldo E2E')
        )
        confirm_button = self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'button[type="submit"][name="confirm"]'))
        )
        driver.execute_script("arguments[0].click();", confirm_button)  # Tenta confirmar a entrada

        # 2) Acesso e NEGADO por saldo insuficiente
        self.wait.until(
            EC.text_to_be_present_in_element((By.CSS_SELECTOR, 'body'), 'Acesso negado')
        )

        # Nenhuma refeicao foi criada e o saldo continua R$2,00
        self.assertFalse(
            Transaction._default_manager.filter(
                user=self.student, type=Transaction.TransactionType.MEAL
            ).exists(),
            'Não deveria existir refeição quando o saldo é insuficiente.',
        )
        self.assertEqual(user_balance(self.student), Decimal('2.00'))
