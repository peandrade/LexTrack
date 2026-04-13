# LexTrack — Gestão de Contratos e Vencimentos Jurídicos

## Estado Atual do Projeto
- **Etapa em execução:** 1 - SETUP
- **Branch atual:** feature/setup
- **Última etapa concluída:** —

## Etapas do Plano

| # | Etapa | Status |
|---|-------|--------|
| 1 | SETUP - Estrutura de pastas, virtualenv, dependências | 🔄 Em andamento |
| 2 | MODELS - Modelos SQLAlchemy | ⏳ Pendente |
| 3 | ROUTES - Blueprint contracts CRUD | ⏳ Pendente |
| 4 | SCHEDULER - APScheduler para alertas | ⏳ Pendente |
| 5 | PDF - Extração de datas com pdfplumber | ⏳ Pendente |
| 6 | FRONTEND - Dashboard com Chart.js | ⏳ Pendente |
| 7 | AUTH - Login com Flask-Login | ⏳ Pendente |
| 8 | TESTES - pytest com fixtures | ⏳ Pendente |
| 9 | DOCKER - Dockerfile + docker-compose | ⏳ Pendente |
| 10 | DOCS - README.md final | ⏳ Pendente |

## Comandos Úteis

```bash
# Criar e ativar virtualenv
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
cp .env.example .env

# Rodar aplicação
flask run

# Rodar testes
pytest
```

## Stack
- Python 3.11+
- Flask 3.0
- SQLAlchemy + Flask-Migrate
- APScheduler
- pdfplumber
- Jinja2 + TailwindCSS + Chart.js
