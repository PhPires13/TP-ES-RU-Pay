"""
Testes E2E (ponta a ponta) do RU Pay usando Selenium + Django LiveServerTestCase.

Diferente dos testes em `tests.py` (que usam o Client de testes do Django e
não renderizam JS/CSS nem executam um navegador real), estes testes sobem o
servidor Django de fato (LiveServerTestCase) e dirigem um navegador Chrome
headless de verdade, simulando o usuário: abrir página, preencher campo,
clicar em botão, conferir o que aparece na tela.

Como executar:
    pip install selenium
    (é necessário ter o Google Chrome / Chromium e o chromedriver compatível
     instalados e disponíveis no PATH, ou o Selenium Manager fará o download
     automaticamente na primeira execução)

    python manage.py test rupayapp.test_e2e

Cenários cobertos:
    1) Fluxo do aluno: cadastro -> login -> recarga online -> saldo e
       extrato atualizados na tela.
    2) Fluxo do operador + catraca: operador lê a carteirinha e registra
       uma recarga presencial em dinheiro; em seguida, na catraca, o aluno
       passa o cartão e tem a refeição debitada com sucesso (saldo
       suficiente).
"""
from decimal import Decimal

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from rupayapp.models import Transaction, User
from rupayapp.utils import user_balance


def _build_headless_chrome():
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1280,1024')
    return webdriver.Chrome(options=options)


class StudentFlowE2ETest(StaticLiveServerTestCase):
    """E2E: aluno se cadastra, faz login, recarrega online e confere extrato."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.selenium = _build_headless_chrome()
        cls.selenium.implicitly_wait(5)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def setUp(self):
        self.wait = WebDriverWait(self.selenium, 10)

    def test_cadastro_login_e_recarga_online(self):
        driver = self.selenium

        # 1) Aluno acessa a página de cadastro e cria sua conta
        driver.get(f'{self.live_server_url}/aluno/cadastro/')

        driver.find_element(By.ID, 'id_username').send_keys('mariae2e')
        driver.find_element(By.ID, 'id_name').send_keys('Maria E2E Teste')
        driver.find_element(By.ID, 'id_card_number').send_keys('11122233')
        driver.find_element(By.ID, 'id_password').send_keys('senha123')
        driver.find_element(By.ID, 'id_password_confirm').send_keys('senha123')
        submit_btn = self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'form.form-panel button[type="submit"]'))
        )
        driver.execute_script("arguments[0].click();", submit_btn)

        # Cadastro válido redireciona para a área do aluno (consulta)
        self.wait.until(EC.url_contains('/aluno/consulta/'))
        self.assertTrue(
            User._default_manager.filter(username='mariae2e', card_number='11122233').exists(),
            'Usuário deveria ter sido criado no banco após o cadastro.',
        )

        # 2) Aluno faz login com usuário e senha recém-criados
        driver.find_element(By.ID, 'id_username').send_keys('mariae2e')
        driver.find_element(By.ID, 'id_password').send_keys('senha123')
        submit_btn = self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'form.form-panel button[type="submit"]'))
        )
        driver.execute_script("arguments[0].click();", submit_btn)

        # Após login, o nome do aluno e o saldo (R$ 0) devem aparecer na tela
        self.wait.until(
            EC.text_to_be_present_in_element((By.CSS_SELECTOR, 'body'), 'Maria E2E Teste')
        )
        self.assertIn('R$ 0', driver.page_source)

        # 3) Aluno faz uma recarga online de R$ 75,00
        valor_input = self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="amount"]'))
        )
        valor_input.clear()
        valor_input.send_keys('75.00')

        # Localiza o botão "Confirmar recarga" dentro do formulário de recarga
        recharge_form = driver.find_element(
            By.XPATH, '//form[.//input[@name="recharge"]]'
        )
        recharge_btn = recharge_form.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
        driver.execute_script("arguments[0].click();", recharge_btn)

        # 4) Mensagem de sucesso, novo saldo e extrato devem refletir a recarga
        self.wait.until(
            EC.text_to_be_present_in_element(
                (By.CSS_SELECTOR, 'body'), 'Recarga online de R$ 75'
            )
        )
        self.assertIn('R$ 75', driver.page_source)

        student = User._default_manager.get(username='mariae2e')
        transactions = Transaction._default_manager.filter(user=student)
        self.assertEqual(transactions.count(), 1)
        self.assertEqual(transactions.first().amount, Decimal('75.00'))
        self.assertEqual(transactions.first().type, Transaction.TransactionType.RECHARGE)
        self.assertEqual(transactions.first().recharge_method, Transaction.MethodType.ONLINE)

        # O extrato (tabela de transações) deve listar a recarga feita
        extrato_table = driver.find_element(By.CSS_SELECTOR, 'table.data')
        self.assertIn('Recarga', extrato_table.text)
        self.assertIn('75', extrato_table.text)


class OperatorAndTurnstileFlowE2ETest(StaticLiveServerTestCase):
    """E2E: operador registra recarga presencial e a catraca libera a refeição."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.selenium = _build_headless_chrome()
        cls.selenium.implicitly_wait(5)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def setUp(self):
        self.wait = WebDriverWait(self.selenium, 10)
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
            EC.text_to_be_present_in_element(
                (By.CSS_SELECTOR, 'body'), 'Recarga de R$ 40'
            )
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
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'button[type="submit"][name="confirm"]')
            )
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


class TurnstileAccessDeniedE2ETest(StaticLiveServerTestCase):
    """E2E: catraca bloqueia o acesso de aluno com saldo insuficiente (US9)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.selenium = _build_headless_chrome()
        cls.selenium.implicitly_wait(5)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def setUp(self):
        self.wait = WebDriverWait(self.selenium, 10)
        # Aluno com saldo de apenas R$ 2,00 (abaixo do preço da refeição de R$ 5,60)
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
        driver.execute_script("arguments[0].click();", lookup_btn)

        # A tela deve mostrar o nome do aluno e o botão de confirmar entrada
        self.wait.until(
            EC.text_to_be_present_in_element((By.CSS_SELECTOR, 'body'), 'Sem Saldo E2E')
        )
        confirm_button = self.wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'button[type="submit"][name="confirm"]')
            )
        )
        driver.execute_script("arguments[0].click();", confirm_button)

        # 2) Acesso deve ser NEGADO por saldo insuficiente
        self.wait.until(
            EC.text_to_be_present_in_element((By.CSS_SELECTOR, 'body'), 'Acesso negado')
        )

        # Nenhuma transação de refeição deve ter sido criada; saldo permanece R$ 2,00
        self.assertFalse(
            Transaction._default_manager.filter(
                user=self.student, type=Transaction.TransactionType.MEAL
            ).exists(),
            'Não deveria existir refeição quando o saldo é insuficiente.',
        )
        self.assertEqual(user_balance(self.student), Decimal('2.00'))


class BalanceAndHistoryE2ETest(StaticLiveServerTestCase):
    """E2E: aluno consulta saldo e histórico de transações (US3 e US4)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.selenium = _build_headless_chrome()
        cls.selenium.implicitly_wait(5)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def setUp(self):
        self.wait = WebDriverWait(self.selenium, 10)
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