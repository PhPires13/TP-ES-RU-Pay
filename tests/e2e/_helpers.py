"""Infraestrutura compartilhada dos testes E2E (Selenium + Chrome headless).

Não é descoberto pelo runner (não casa com `test*.py`); serve apenas de base
para os arquivos de cenário em `tests/e2e/`.

Pré-requisitos para rodar os E2E:
    pip install selenium
    (Google Chrome/Chromium + chromedriver no PATH; o Selenium Manager baixa
     automaticamente o driver na primeira execução)
"""
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait


def build_headless_chrome():
    options = Options()
    # options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1280,1024')
    return webdriver.Chrome(options=options)


class BaseE2ETest(StaticLiveServerTestCase):
    """Sobe o servidor de teste e abre um Chrome headless por classe de teste."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.selenium = build_headless_chrome()
        cls.selenium.implicitly_wait(5)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def setUp(self):
        self.wait = WebDriverWait(self.selenium, 10)
