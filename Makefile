PYTHON = ./.venv/bin/python
PIP = ./.venv/bin/pip
MANAGE = $(PYTHON) manage.py

.PHONY: test testes e2e coverage coverage-html install

install:
	$(PIP) install -r requirements.txt
	$(PIP) install coverage

test:
	$(MANAGE) test testes

testes:
	@echo "Running all testes with coverage..."
	@set +e; \
	$(PYTHON) -m coverage run --source=. manage.py test testes; \
	RESULT=$$?; \
	$(PYTHON) -m coverage report -m | tee coverage-report.txt; \
	$(PYTHON) -m coverage html >/dev/null 2>&1; \
	TOTAL=$$(grep TOTAL coverage-report.txt | awk '{print $$4}'); \
	if [ $$RESULT -eq 0 ]; then echo; echo "RESULTADO: TESTES PASSARAM"; else echo; echo "RESULTADO: TESTES FALHARAM"; fi; \
	echo "Cobertura total: $$TOTAL"; \
	echo "Relatório HTML gerado em htmlcov/index.html"; \
	exit $$RESULT

coverage:
	$(PYTHON) -m coverage run --source=. manage.py test testes
	$(PYTHON) -m coverage report -m

e2e:
	$(MANAGE) test testes.barbara_e2e_test

barbara:
	$(MANAGE) test testes.barbara_tests

coverage-html:
	$(PYTHON) -m coverage html
	@echo "HTML coverage report generated at htmlcov/index.html"
