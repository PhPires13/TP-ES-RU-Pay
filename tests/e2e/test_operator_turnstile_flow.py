"""E2E: operador registra recarga presencial e a catraca libera a refeição (US6, US7, US5)."""
from decimal import Decimal

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from rupayapp.models import Transaction, User

from ._helpers import BaseE2ETest


class OperatorAndTurnstileFlowE2ETest(BaseE2ETest):
    def setUp(self):
        super().setUp()
        # Aluno já existe no sistema, mas ainda sem saldo
        self.student = User._default_manager.create(
            username='joaoe2e',
            name='Joao E2E Teste',
            card_number='99988877',
        )

    def test_operador_recarrega_e_catraca_libera_refeicao(self):
        driver = self.selenium

        # 1) Operador acessa o painel e lê a carteirinha do aluno
        driver.get(f'{self.live_server_url}/operador/')
        driver.find_element(By.ID, 'id_lookup-card_number').send_keys('99988877')
        lookup_btn = self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'button[type="submit"][name="lookup"]'))
        )
        driver.execute_script("arguments[0].click();", lookup_btn)

        # Dados do aluno (nome) devem aparecer na tela após a leitura
        self.wait.until(
            EC.text_to_be_present_in_element((By.CSS_SELECTOR, 'body'), 'Joao E2E Teste')
        )

        # 2) Operador registra uma recarga presencial em dinheiro de R$ 40,00
        valor_input = self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="amount"]'))
        )
        valor_input.clear()
        valor_input.send_keys('40.00')

        metodo_select = driver.find_element(By.CSS_SELECTOR, 'select[name="method"]')
        for option in metodo_select.find_elements(By.TAG_NAME, 'option'):
            if option.get_attribute('value') == Transaction.MethodType.CASH:
                option.click()
                break

        recharge_btn = self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'button[type="submit"][name="recharge"]'))
        )
        driver.execute_script("arguments[0].click();", recharge_btn)

        # Mensagem de sucesso confirma a recarga presencial
        self.wait.until(
            EC.text_to_be_present_in_element((By.CSS_SELECTOR, 'body'), 'Recarga de R$ 40')
        )
        recharge_tx = Transaction._default_manager.get(user=self.student, type=Transaction.TransactionType.RECHARGE)
        self.assertEqual(recharge_tx.amount, Decimal('40.00'))
        self.assertEqual(recharge_tx.recharge_method, Transaction.MethodType.CASH)

        # 3) Aluno (já com saldo) vai até a catraca para fazer uma refeição
        driver.get(f'{self.live_server_url}/catraca/')
        driver.find_element(By.ID, 'id_card_number').send_keys('99988877')
        lookup_btn = self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'button[type="submit"][name="lookup"]'))
        )
        driver.execute_script("arguments[0].click();", lookup_btn)

        # A tela deve mostrar o nome do aluno e o botão de confirmar entrada
        self.wait.until(
            EC.text_to_be_present_in_element((By.CSS_SELECTOR, 'body'), 'Joao E2E Teste')
        )
        confirm_button = self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'button[type="submit"][name="confirm"]'))
        )
        driver.execute_script("arguments[0].click();", confirm_button)

        # 4) Acesso deve ser liberado: mensagem de sucesso e débito do valor da refeição
        self.wait.until(
            EC.text_to_be_present_in_element((By.CSS_SELECTOR, 'body'), 'Acesso liberado')
        )

        meal_tx = Transaction._default_manager.get(user=self.student, type=Transaction.TransactionType.MEAL)
        self.assertEqual(meal_tx.amount, Decimal('5.60'))

        # Saldo final esperado: 40.00 (recarga) - 5.60 (refeição) = 34.40
        self.assertIn('34.40', driver.page_source)
