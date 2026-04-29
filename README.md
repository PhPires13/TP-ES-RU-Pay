# RU Pay

## Roles

- Bárbara Diniz Abreu
  - Backend
- João Pedro Figueiredo Bicalho
  - Frontend
- Júlia Souza Moura
  - Frontend
- Pedro Henrique Gonçalves Pires
  - Backend

## Objetivo do Sistema

O sistema tem como objetivo gerenciar o saldo digital do restaurante universitário, permitindo que usuários recarreguem sua carteirinha presencialmente ou pelo site. Ao acessar o restaurante, basta utilizar a carteirinha na catraca para liberação rápida da entrada. A plataforma busca reduzir filas, otimizar o fluxo de atendimento e oferecer mais praticidade no pagamento das refeições. Além disso, possibilita o acompanhamento do saldo e histórico de recargas de forma simples e acessível.

## Tecnologias

<table style="border: none;">
    <tr>
        <td align="center" colspan="2">
            <h3>Agents</h3>
            <a href="https://github.com/features/copilot" target="_blank" rel="noreferrer"> <img src="https://ai.nd.edu/assets/607853/300x/github_copilot_logo_4x.png" alt="copilot" height="40"/> </a>
            <a href="https://openai.com/codex/" target="_blank" rel="noreferrer"> <img src="https://raw.githubusercontent.com/lobehub/lobe-icons/refs/heads/master/packages/static-png/dark/codex-text.png" alt="codex" height="40"/> </a>
            <a href="https://claude.ai/login" target="_blank" rel="noreferrer"> <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/Claude_AI_logo.svg/960px-Claude_AI_logo.svg.png" alt="codex" height="40"/> </a>
        </td>
    </tr>
    <tr>
        <td align="center">
            <h3>Backend</h3>
            <a href="https://www.python.org" target="_blank" rel="noreferrer"> <img src="https://www.python.org/static/community_logos/python-logo-generic.svg" alt="python" height="40"/> </a> <br>
            <a href="https://www.django-rest-framework.org" target="_blank" rel="noreferrer"> <img src="https://www.django-rest-framework.org/img/logo-dark.png#only-dark" alt="djangorest" height="40"/> </a>
        </td>
        <td align="center">
            <h3>Frontend</h3>
            <a href="https://www.w3.org/html/" target="_blank" rel="noreferrer"> <img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/html5/html5-original-wordmark.svg" alt="html5" height="40"/> </a>
            <a href="https://www.w3schools.com/css/" target="_blank" rel="noreferrer"> <img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/css3/css3-original-wordmark.svg" alt="css3" height="40"/> </a>
            <a href="https://developer.mozilla.org/en-US/docs/Web/JavaScript" target="_blank" rel="noreferrer"> <img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/javascript/javascript-original.svg" alt="javascript" height="40"/> </a> <br>
            <a href="https://www.djangoproject.com/" target="_blank" rel="noreferrer"> <img src="https://static.djangoproject.com/img/logos/django-logo-negative.svg" alt="django" height="40"/> </a>
        </td>
    </tr>
    <tr>
        <td align="center">
            <h3>Database</h3>
            <a href="https://sqlite.org" target="_blank" rel="noreferrer"> <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/3/38/SQLite370.svg/1280px-SQLite370.svg.png" alt="sqlite" height="40"/> </a>
        </td>
        <td align="center">
            <h3>DevOps</h3>
            <a href="https://git-scm.com/" target="_blank" rel="noreferrer"> <img   src="https://upload.wikimedia.org/wikipedia/commons/thumb/e/e0/Git-logo.svg/3840px-Git-logo.svg.png" alt="git" height="40"/> </a>
        </td>
    </tr>
</table>

## Requerimentos

### Requerimentos técnicos

- Python 3.10+ instalado
- pip atualizado
- Ambiente virtual (recomendado)

Dependências Python do projeto (arquivo `requirements.txt`):

- Django==6.0.4
- django-extensions==4.1
- pillow==12.2.0

### Requerimentos funcionais

Os requerimentos funcionais resumidos também estão no arquivo `requisitos.txt`.

## Como rodar o código

1. Clone o repositório e entre na pasta do projeto.
2. Crie e ative um ambiente virtual.
3. Instale as dependências.
4. Rode as migrações.
5. Inicie o servidor Django.

### Linux/macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Windows (PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Após iniciar, acesse: `http://127.0.0.1:8000/`

## Histórias de Usuário

### 1. Recarga online

**Como** aluno
**Quero** recarregar o saldo da minha carteirinha pelo site
**Para** evitar filas e garantir crédito antes de chegar ao restaurante

---

### 2. Recarga presencial

**Como** aluno
**Quero** recarregar minha carteirinha no local de atendimento
**Para** conseguir adicionar saldo mesmo sem acesso ao site

---

### 3. Consulta de saldo

**Como** aluno
**Quero** consultar meu saldo disponível
**Para** saber se tenho crédito suficiente para realizar uma refeição

---

### 4. Histórico de transações

**Como** aluno
**Quero** visualizar o histórico de recargas e utilizações
**Para** acompanhar meus gastos no restaurante

---

### 5. Validação na catraca

**Como** aluno
**Quero** passar minha carteirinha na catraca e ter o acesso liberado automaticamente
**Para** entrar rapidamente no restaurante sem precisar realizar pagamentos na hora

---

### 6. Leitura da carteirinha

**Como** operador de caixa
**Quero** ler a carteirinha do aluno no sistema
**Para** identificar o usuário e acessar suas informações de saldo

---

### 7. Processamento de recarga

**Como** operador de caixa
**Quero** registrar recargas presenciais no sistema
**Para** atualizar imediatamente o saldo do aluno

---

### 8. Confirmação de identidade

**Como** operador de caixa
**Quero** visualizar a foto do aluno ao passar a carteirinha
**Para** validar que a pessoa utilizando o cartão é o próprio titular e garantir a segurança do acesso

---

### 9. Controle de acesso

**Como** sistema
**Quero** validar automaticamente se o aluno possui saldo suficiente ao passar na catraca
**Para** liberar ou bloquear o acesso de forma rápida e sem intervenção manual
