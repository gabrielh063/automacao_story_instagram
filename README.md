# Postagens Diárias

Sistema web para automação de Stories no Instagram, permitindo publicar imagens imediatamente, agendar publicações e acompanhar o histórico de execução.

O projeto utiliza um banco privado de imagens na AWS S3, backend em Flask, frontend em React e processamento automatizado por worker.

## 📌 Sobre o projeto

O objetivo é reduzir o trabalho manual de publicar Stories recorrentes no Instagram.

Com o sistema, o usuário pode selecionar uma imagem do banco de fotos, publicar imediatamente ou agendar para outro horário.

Fluxo principal:

```text
React
  ↓
Flask
  ↓
MariaDB
  ↓
AWS S3
  ↓
Instagram API
```

As publicações agendadas são processadas automaticamente por um `worker.py`.

## ✅ Funcionalidades

- Banco de fotos integrado à AWS S3
- Galeria visual de imagens
- Publicação imediata de Stories
- Agendamento por data e horário
- Cancelamento de agendamentos
- Histórico de publicações
- Histórico de eventos de cada postagem
- Tratamento de erros
- Retentativas automáticas
- Retentativa manual quando segura
- Controle de idempotência
- Fila de publicações
- Proteção contra publicações simultâneas
- URLs temporárias para imagens privadas da S3
- Interface baseada nas Heurísticas de Nielsen

Estados tratados pelo sistema:

```text
AGENDADO
PROCESSANDO
PUBLICADO
ERRO
CANCELADO
```

Também são registradas fases internas como:

```text
PENDENTE
PREPARANDO_IMAGEM
CONTAINER_CRIADO
MIDIA_PROCESSADA
PUBLICANDO
AGUARDANDO_FILA
CONCLUIDA
```

## 🛠 Tecnologias utilizadas

### Backend

- Python
- Flask
- Flask-SQLAlchemy
- Flask-Migrate
- Flask-CORS
- PyMySQL
- Requests
- boto3
- python-dotenv

### Frontend

- React
- Vite
- Axios
- React Router DOM
- Bootstrap
- Bootstrap Icons

### Infraestrutura

- MariaDB
- AWS S3
- AWS IAM
- AWS CLI
- Instagram API with Instagram Login
- Instagram Graph API v25.0

## 🏗 Arquitetura

```text
postagens-diarias/
├── backend/
│   ├── app.py
│   ├── worker.py
│   ├── config.py
│   ├── extensions.py
│   ├── models/
│   ├── routes/
│   └── services/
│
└── frontend/
    ├── src/
    │   ├── components/
    │   ├── pages/
    │   └── services/
    ├── package.json
    └── vite.config.js
```

O backend armazena os dados das postagens no MariaDB e mantém apenas a `s3_key` das imagens.

As imagens permanecem privadas na S3 e são disponibilizadas temporariamente por meio de **Presigned URLs**.

## 🚀 Instalação

### Backend

```bash
cd backend

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

Crie o arquivo:

```text
backend/.env
```

Exemplo:

```env
FLASK_ENV=development

DATABASE_URL=mysql+pymysql://postagens_app:[SENHA]@localhost/postagens_diarias

APP_TIMEZONE=America/Sao_Paulo

AWS_PROFILE=postagens-diarias
AWS_REGION=sa-east-1
AWS_S3_BUCKET=postagens-diarias
AWS_S3_PREFIX=banco-fotos/

INSTAGRAM_API_VERSION=v25.0
INSTAGRAM_USER_ID=[PREENCHER]
INSTAGRAM_ACCESS_TOKEN=[PREENCHER]
```

Execute as migrations:

```bash
flask --app app db upgrade
```

Inicie o backend:

```bash
python app.py
```

Em outro terminal, inicie o worker:

```bash
python worker.py
```

### Frontend

```bash
cd frontend
npm install
```

Crie:

```text
frontend/.env
```

```env
VITE_API_URL=http://localhost:5000
```

Execute:

```bash
npm run dev
```

A interface ficará disponível em:

```text
http://localhost:5173
```

## ▶️ Como usar

### Publicar agora

1. Acesse a tela de fotos
2. Selecione uma imagem
3. Clique em **Publicar agora**
4. Confirme a publicação

### Agendar

1. Selecione uma imagem
2. Clique em **Agendar**
3. Escolha data e horário
4. Confirme

O worker processará automaticamente a postagem no horário definido.

### Histórico

A tela de histórico permite acompanhar:

- publicações concluídas;
- erros;
- cancelamentos;
- tentativas;
- eventos da operação.

## 🧠 Decisões técnicas importantes

### S3 privado

As imagens não ficam públicas permanentemente.

O backend gera URLs temporárias apenas quando necessário.

### Idempotência

Cada solicitação recebe uma chave única para evitar publicações duplicadas.

### Fila de publicações

Durante os testes foi identificado que duas publicações simultâneas poderiam gerar erro na API.

Foi implementado controle de concorrência com:

```sql
GET_LOCK(...)
```

do MariaDB.

Assim, apenas uma publicação é enviada ao Instagram por vez.

### Tratamento de falhas

O sistema diferencia erros como:

```text
TOKEN
TEMPORARIO
META
IMAGEM
PUBLICACAO_AMBIGUA
```

Falhas temporárias podem gerar novas tentativas.

Quando não é possível confirmar se o Instagram já publicou o Story, o sistema evita repetir automaticamente para impedir duplicidade.

## 🗺 Roadmap

Próximas melhorias planejadas:

- Dashboard
- Aviso de imagem publicada recentemente
- Upload de novas imagens pelo frontend
- Gerenciamento das imagens
- Autenticação da aplicação
- Renovação/reconexão do token do Instagram
- Deploy de produção
- Gunicorn
- systemd para backend e worker
- HTTPS
- CORS restrito
- Logs de produção

## 👤 Autor

Gabriel Henrique Alves Cintra

GitHub: gabrielh063

Repositório: https://github.com/gabrielh063/automacao_story_instagram
