# Relatório de Testes — RU Pay (TP2)

Divisão do trabalho de testes por integrante, com a funcionalidade coberta e o
tipo de teste (**Unidade**, **Integração** ou **E2E**). A autoria está
registrada nos commits do repositório.

> Legenda de tipo: 🟦 Unidade · 🟩 Integração · 🟧 E2E
> US = História de usuário do README.

---

## Como rodar os testes

> Todos os comandos são rodados a partir da raiz do projeto.

```bash
# 0) Instalar dependências (Django, coverage e selenium)
make install

# 1) ENTREGA: roda unidade + integração e mostra a cobertura (gera coverage-report.txt + htmlcov/)
make coverage

# 2) Abrir o relatório visual de cobertura no navegador
open htmlcov/index.html        # macOS

# Rodar por categoria
make unit                      # só testes de unidade
make integration               # só testes de integração
make e2e                       # 4 testes E2E (Selenium — requer Google Chrome instalado)

# Rodar tudo (unidade + integração + E2E)
make test-all
```

**Sem o `make`** (equivalente direto):

```bash
# Unidade + integração com cobertura
.venv/bin/python -m coverage run manage.py test tests.unit tests.integration
.venv/bin/python -m coverage report -m

# E2E (Selenium)
.venv/bin/python manage.py test tests.e2e

# Um teste específico (ex.: explicar na apresentação)
.venv/bin/python manage.py test tests.unit.test_utils.UtilsTests.test_user_balance_with_meal
```

| Comando | O que roda | Tipo |
|---|---|---|
| `make coverage` | unidade + integração + relatório de cobertura | 🟦 + 🟩 |
| `make unit` | `tests/unit/` | 🟦 |
| `make integration` | `tests/integration/` | 🟩 |
| `make e2e` | `tests/e2e/` (Selenium + Chrome) | 🟧 |
| `make test-all` | tudo | 🟦 + 🟩 + 🟧 |

---

## Resumo geral

| Integrante | Commit(s) principal(is) | Unidade | Integração | E2E | Foco |
|---|---|:--:|:--:|:--:|---|
| **João Pedro** | `c8f677f`, `080089b` | ✅ | ✅ | — | Base da suíte: modelos, saldo, formulários e views |
| **Júlia** | `5648eca` | — | — | ✅ | Testes E2E com Selenium (navegador real) |
| **Bárbara** | `a1d45ab`, `24a15e8`, `5d892e4` | ✅ | ✅ | ✅* | 3 funcionalidades + fluxo completo + reorganização |
| **Pedro** | `9defcc9` | — | ✅ | ✅ | Complemento de cobertura + 2 cenários E2E |

\* E2E "in-process" (Django Client, sem navegador) — hoje em `tests/integration/test_full_flow.py`.

**Cobertura final:** 99% (unidade + integração) · **Total de testes:** 89 (unid./integr.) + 4 E2E Selenium.

---

## João Pedro — Base da suíte (Unidade + Integração)

Criou a fundação dos testes: modelos, regra de saldo, validação de formulários
e as quatro views principais.

| Funcionalidade | O que testou | Tipo |
|---|---|---|
| Cadastro / Modelo de usuário | criação, unicidade de usuário e carteirinha, hash de senha, validação de 8 dígitos (US8 dados do aluno) | 🟦 Unidade |
| Consulta de saldo (US3) | `user_balance` com recarga, refeição, múltiplas transações e saldo negativo | 🟦 Unidade |
| Validação de formulários | login, cadastro, recarga online, recarga do operador e catraca | 🟦 Unidade |
| Recarga online (US1) | view de consulta criando transação online | 🟩 Integração |
| Recarga presencial (US2, US7) | painel do operador registrando dinheiro/cartão | 🟩 Integração |
| Login / Consulta (US3, US6) | login válido/inválido, leitura de carteirinha | 🟩 Integração |
| Catraca / Controle de acesso (US5, US9) | refeição com saldo suficiente, insuficiente e zerado | 🟩 Integração |

**Arquivos hoje:** `tests/unit/test_models.py`, `test_utils.py`, `test_forms.py` e as views em `tests/integration/`.

---

## Júlia — Testes E2E com Selenium (E2E)

Montou a infraestrutura E2E (Chrome headless + `LiveServerTestCase`) e os dois
fluxos de ponta a ponta com navegador real.

| Funcionalidade | Cenário E2E | Tipo |
|---|---|---|
| Recarga online + extrato (US1, US3, US4) | aluno se cadastra → faz login → recarrega R$75 → confere saldo e extrato na tela | 🟧 E2E |
| Operador + catraca (US6, US7, US2, US5) | operador lê a carteirinha, recarrega R$40 em dinheiro; aluno passa na catraca e a refeição é liberada | 🟧 E2E |

**Arquivos hoje:** `tests/e2e/test_student_flow.py`, `tests/e2e/test_operator_turnstile_flow.py`.

---

## Bárbara — Testes por funcionalidade + fluxo completo + reorganização (Unidade + Integração + E2E)

Escreveu 30 testes organizados em **3 funcionalidades**, um teste de fluxo
completo e fez a reorganização da pasta de testes + Makefile.

| Funcionalidade | O que testou | Tipo |
|---|---|---|
| Recarga online (US1) | validação do valor, criação da transação, exigência de sessão, saldo atualizado | 🟦 Unidade + 🟩 Integração |
| Recarga presencial (US2, US7) | formas de pagamento, recarga sem carteirinha, leitura no painel | 🟦 Unidade + 🟩 Integração |
| Consulta de saldo (US3) | login e exibição de saldo, leitura na catraca, cálculo do saldo | 🟦 Unidade + 🟩 Integração |
| Fluxo completo (US1→US5) | cadastro → recarga online → recarga presencial → refeição na catraca (via Django Client) | 🟧 E2E in-process |

**Arquivos hoje:** testes mesclados em `tests/unit/` e `tests/integration/` (mantidos os exclusivos dela) + `tests/integration/test_full_flow.py`. Também: reorganização em `tests/` e `Makefile`.

---

## Pedro — Complemento de cobertura + 2 cenários E2E (Integração + E2E)

Fechou as lacunas de cobertura (views e casos de borda) e adicionou dois
cenários E2E que faltavam.

| Funcionalidade | O que testou | Tipo |
|---|---|---|
| Página inicial | home renderiza com o preço da refeição | 🟩 Integração |
| Comprovante (US4) | recibo de transação existente e 404 para inexistente | 🟩 Integração |
| Cardápio do dia | integração com a API da FUMP usando *mock* (lista, sem cardápio, serviço fora do ar, erro de rede) | 🟩 Integração |
| Casos de borda | sessão expirada, recarga inválida, carteirinha inexistente (404), saldo exatamente igual ao preço (US9) | 🟩 Integração |
| Controle de acesso (US9) | E2E: catraca **bloqueia** aluno com saldo insuficiente | 🟧 E2E |
| Saldo + histórico (US3, US4) | E2E: aluno faz login e confere saldo e extrato com recarga e refeição | 🟧 E2E |

**Arquivos hoje:** `tests/integration/test_other_views.py` + casos de borda nas demais views; `tests/e2e/test_turnstile_access_denied.py`, `tests/e2e/test_balance_history.py`.

---

## Mapa funcionalidade × quem testou

| História de usuário | Unidade | Integração | E2E |
|---|---|---|---|
| US1 Recarga online | João, Bárbara | João, Bárbara | Júlia |
| US2 Recarga presencial | João, Bárbara | João, Bárbara | Júlia |
| US3 Consulta de saldo | João, Bárbara | João, Bárbara | Pedro |
| US4 Histórico de transações | — | Pedro (comprovante) | Júlia, Pedro |
| US5 Validação na catraca | João | João | Júlia |
| US6 Leitura da carteirinha | — | João, Bárbara | Júlia |
| US7 Processamento de recarga | João, Bárbara | João, Bárbara | Júlia |
| US8 Confirmação de identidade | João (dados/foto do aluno) | — | — |
| US9 Controle de acesso | João | João, Pedro | Pedro |
