PYTHON = ./.venv/bin/python
PIP = ./.venv/bin/pip
MANAGE = $(PYTHON) manage.py

# Cobertura medida apenas sobre o código de produção (app rupayapp).
# Suíte de unidade + integração (não exige navegador/Selenium).
# A fonte/omissões da cobertura ficam em .coveragerc.
UNIT_INTEGRATION = tests.unit tests.integration

.PHONY: install test unit integration e2e coverage coverage-html test-all

install:
	$(PIP) install -r requirements.txt

# ---------------------------------------------------------------------------
# Alvo principal de entrega: roda unidade + integração e mostra a cobertura.
# ---------------------------------------------------------------------------
coverage:
	@echo "Rodando testes de unidade + integração com cobertura..."
	@set +e; \
	$(PYTHON) -m coverage run manage.py test $(UNIT_INTEGRATION); \
	RESULT=$$?; \
	$(PYTHON) -m coverage report -m | tee coverage-report.txt; \
	$(PYTHON) -m coverage html >/dev/null 2>&1; \
	TOTAL=$$(grep TOTAL coverage-report.txt | awk '{print $$4}'); \
	echo; \
	if [ $$RESULT -eq 0 ]; then echo "RESULTADO: TESTES PASSARAM"; else echo "RESULTADO: TESTES FALHARAM"; fi; \
	echo "Cobertura total: $$TOTAL"; \
	echo "Relatorio HTML em htmlcov/index.html"; \
	exit $$RESULT

# Apenas roda a suíte (sem cobertura).
test:
	$(MANAGE) test $(UNIT_INTEGRATION)

# Alvos por categoria.
unit:
	$(MANAGE) test tests.unit

integration:
	$(MANAGE) test tests.integration

# Testes E2E (Selenium + Chrome). Requer `pip install selenium` e Chrome no PATH.
e2e:
	$(MANAGE) test tests.e2e

# Tudo: unidade + integração + e2e (precisa de Selenium/Chrome).
test-all:
	$(MANAGE) test tests

coverage-html:
	$(PYTHON) -m coverage html
	@echo "Relatorio HTML em htmlcov/index.html"
