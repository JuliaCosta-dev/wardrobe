# Infraestrutura do Banco de Dados — Wardrobe AI

**Versão:** 1.0  
**Etapa:** Fase 0 — Fundação  
**Status:** Infraestrutura implementada e validada  
**Branch:** `feature/database-foundation`

---

## 1. Objetivo

Este documento registra a implementação da infraestrutura de persistência do Wardrobe AI, incluindo a configuração do PostgreSQL, execução em Docker, integração com Python por meio do SQLAlchemy, gerenciamento de sessões, verificação de disponibilidade do banco e configuração do Alembic.

O objetivo desta etapa é preparar uma estrutura confiável para armazenar os dados da aplicação e permitir sua evolução por meio de migrações controladas.

Esta etapa não contempla ainda a criação das tabelas de usuários, peças de roupa, looks ou outras entidades de negócio.

## 2. Tecnologias utilizadas

| Tecnologia | Responsabilidade |
|---|---|
| PostgreSQL 18 | Sistema gerenciador do banco de dados relacional. |
| Docker | Execução isolada do PostgreSQL em um container. |
| Docker Compose | Definição e gerenciamento do serviço do banco. |
| SQLAlchemy 2 | ORM e gerenciamento das conexões e sessões. |
| psycopg 3 | Driver de comunicação entre Python e PostgreSQL. |
| Alembic | Versionamento e gerenciamento de migrações. |
| Pydantic Settings | Carregamento e validação das configurações da aplicação. |
| FastAPI | Disponibilização da API e verificação de disponibilidade. |
| Pytest | Execução dos testes automatizados. |
| Ruff | Análise estática e organização do código Python. |

## 3. Organização dos arquivos

A estrutura implementada para esta etapa é:

```text
backend/
├── app/
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py
│   ├── __init__.py
│   ├── database.py
│   └── main.py
├── migrations/
│   ├── versions/
│   ├── env.py
│   ├── README
│   └── script.py.mako
├── tests/
│   └── test_main.py
├── .env
├── .env.example
├── alembic.ini
├── docker-compose.yml
└── pyproject.toml
```

Os arquivos `__pycache__`, `.pyc` e outros arquivos temporários são gerados automaticamente durante a execução do Python e não fazem parte da estrutura versionada.

### 3.1. Responsabilidade dos arquivos

**`app/core/config.py`**

Centraliza as configurações da aplicação e carrega as variáveis de ambiente.

**`app/database.py`**

Centraliza a URL de conexão, o engine SQLAlchemy, a fábrica de sessões, a classe-base dos modelos e a dependência de acesso ao banco.

**`app/main.py`**

Contém os endpoints iniciais da API, incluindo a verificação de disponibilidade do banco.

**`migrations/env.py`**

Conecta o Alembic à configuração do banco e aos metadados dos modelos SQLAlchemy.

**`alembic.ini`**

Contém as configurações gerais do Alembic. A URL de conexão não fica armazenada diretamente nesse arquivo.

**`docker-compose.yml`**

Define o serviço PostgreSQL executado pelo Docker.

## 4. Configuração do PostgreSQL com Docker

O PostgreSQL é executado em um container independente da aplicação FastAPI.

Essa separação permite desenvolver o backend pelo ambiente Python local, enquanto o banco permanece isolado no Docker.

### 4.1. Configuração do serviço

Arquivo: `backend/docker-compose.yml`

```yaml
services:
  db:
    image: postgres:18-alpine
    container_name: wardrobe-ai-db
    restart: unless-stopped

    environment:
      POSTGRES_DB: ${POSTGRES_DB:?POSTGRES_DB is required}
      POSTGRES_USER: ${POSTGRES_USER:?POSTGRES_USER is required}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?POSTGRES_PASSWORD is required}

    ports:
      - "127.0.0.1:${POSTGRES_PORT:-5432}:5432"

    volumes:
      - postgres_data:/var/lib/postgresql

    healthcheck:
      test:
        - CMD-SHELL
        - pg_isready -U "$$POSTGRES_USER" -d "$$POSTGRES_DB"
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 10s

volumes:
  postgres_data:
```

### 4.2. Explicação das configurações

| Configuração | Finalidade |
|---|---|
| `image` | Define a imagem oficial do PostgreSQL. |
| `container_name` | Define um nome identificável para o container. |
| `restart` | Permite reiniciar o serviço automaticamente. |
| `environment` | Recebe o nome do banco, usuário e senha. |
| `ports` | Publica a porta do banco somente para conexões locais. |
| `volumes` | Preserva os dados do PostgreSQL entre recriações do container. |
| `healthcheck` | Verifica se o banco está pronto para receber conexões. |

O volume nomeado `postgres_data` mantém os dados fora do ciclo de vida do container.

**Observação:** a remoção do container não implica necessariamente a remoção do volume. Entretanto, comandos como `docker compose down -v` removem também o volume e, consequentemente, os dados armazenados nele.

### 4.3. Portas utilizadas

A configuração atual utiliza:

| Local | Porta |
|---|---:|
| Host Windows | 5433 |
| Container PostgreSQL | 5432 |

O mapeamento permite que a aplicação Python, executada no Windows, acesse o banco por `127.0.0.1:5433`.

A porta interna do PostgreSQL permanece em 5432.

## 5. Variáveis de ambiente e proteção das credenciais

As credenciais do banco são mantidas em um arquivo `.env`, fora do versionamento do Git.

### 5.1. Arquivo `.env`

Local: `backend/.env`

Exemplo de estrutura:

```env
POSTGRES_DB=wardrobe_ai
POSTGRES_USER=wardrobe_user
POSTGRES_PASSWORD=SENHA_LOCAL_SEGURA
POSTGRES_PORT=5433
```

O arquivo real contém a senha utilizada no ambiente local e não deve ser compartilhado ou enviado ao repositório.

### 5.2. Arquivo `.env.example`

Local: `backend/.env.example`

```env
POSTGRES_DB=wardrobe_ai
POSTGRES_USER=wardrobe_user
POSTGRES_PASSWORD=replace_with_a_secure_password
POSTGRES_PORT=5433
```

Esse arquivo serve como referência para outras pessoas configurarem o ambiente.

### 5.3. Proteção pelo Git

O `.gitignore` da raiz do projeto contém as regras:

```gitignore
.env
.env.*
!.env.example
```

Assim:

- `.env` é ignorado.
- `.env.example` pode ser versionado.
- As credenciais reais não devem aparecer nos commits.

Também foi adicionada a regra:

```gitignore
*.egg-info/
```

Ela evita versionar metadados gerados automaticamente durante a instalação do pacote Python.

A proteção foi conferida com:

```powershell
git check-ignore -v backend/.env
```

Resultado confirmado: o arquivo `backend/.env` está sendo ignorado.

## 6. Configuração centralizada com Pydantic Settings

Arquivo: `backend/app/core/config.py`

```python
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    postgres_db: str
    postgres_user: str
    postgres_password: str
    postgres_host: str = "127.0.0.1"
    postgres_port: int = 5433

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
```

### 6.1. Responsabilidades

O `BaseSettings` permite carregar configurações a partir de variáveis de ambiente e validá-las conforme os tipos definidos.

O caminho `BACKEND_DIR` localiza a pasta `backend` a partir da localização do próprio arquivo, evitando depender do diretório atual do terminal.

As credenciais são obrigatórias. Já o host e a porta possuem valores padrão.

A configuração utiliza:

- `postgres_db`: nome do banco.
- `postgres_user`: usuário de conexão.
- `postgres_password`: senha.
- `postgres_host`: endereço do PostgreSQL.
- `postgres_port`: porta publicada no host.

O objeto `settings` disponibiliza essas configurações para os demais módulos.

## 7. Conexão e sessões com SQLAlchemy

Arquivo: `backend/app/database.py`

```python
from collections.abc import Generator

from sqlalchemy import URL, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


DATABASE_URL = URL.create(
    drivername="postgresql+psycopg",
    username=settings.postgres_user,
    password=settings.postgres_password,
    host=settings.postgres_host,
    port=settings.postgres_port,
    database=settings.postgres_db,
)


engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
```

### 7.1. URL de conexão

A função `URL.create()` monta a URL de conexão utilizando os valores das configurações.

O driver escolhido é:

```text
postgresql+psycopg
```

Isso indica que o SQLAlchemy utilizará o driver psycopg 3 para se comunicar com PostgreSQL.

A utilização de `URL.create()` também evita problemas com caracteres especiais presentes nas senhas.

### 7.2. Engine

O `engine` gerencia as conexões entre a aplicação e o banco de dados.

A opção:

```python
pool_pre_ping=True
```

permite verificar se uma conexão reutilizada pelo pool ainda está válida antes de utilizá-la.

### 7.3. SessionLocal

O `sessionmaker` funciona como uma fábrica de sessões.

Cada sessão representa uma unidade de trabalho de acesso ao banco, permitindo executar consultas e operações transacionais.

Foram utilizadas as opções:

- `autoflush=False`: evita que o SQLAlchemy execute flush automaticamente antes de determinadas consultas.
- `autocommit=False`: mantém o controle transacional explícito.

### 7.4. Base

A classe `Base` será utilizada como classe-base dos futuros modelos ORM.

Ela disponibiliza os metadados que o Alembic utilizará para identificar as tabelas declaradas na aplicação.

### 7.5. get_db()

A função `get_db()` disponibiliza uma sessão para os endpoints do FastAPI.

O bloco `finally` garante que a sessão seja fechada mesmo quando ocorre uma exceção durante a execução.

Futuramente, poderá ser utilizada como dependência:

```python
from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db


def example_endpoint(db: Session = Depends(get_db)):
    ...
```

O exemplo é ilustrativo e não representa um endpoint de negócio já implementado.

## 8. Teste de conexão pelo Python

Antes da integração com o health check, foi realizada uma consulta diretamente pelo SQLAlchemy.

Com o container ativo e o ambiente virtual habilitado:

```powershell
python -c "from sqlalchemy import text; from app.database import engine; connection = engine.connect(); print(connection.execute(text('SELECT current_database(), current_user')).fetchone()); connection.close()"
```

A consulta utilizada foi:

```sql
SELECT current_database(), current_user;
```

Ela permite verificar o banco e o usuário da conexão.

A execução foi concluída com sucesso, confirmando que o Python conseguiu acessar o PostgreSQL por meio do SQLAlchemy e do psycopg.

## 9. Health check integrado ao banco

Arquivo: `backend/app/main.py`

O endpoint `/health` foi atualizado para verificar não apenas a aplicação FastAPI, mas também a disponibilidade do banco.

Implementação:

```python
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database import engine


app = FastAPI(
    title="Wardrobe AI",
    description="API para organização de guarda-roupa e recomendações de looks.",
    version="0.1.0"
)


@app.get("/")
def root():
    return {
        "message": "Wardrobe AI API está funcionando!",
        "status": "online"
    }


@app.get("/health")
def health_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "database": "connected"
        }

    except SQLAlchemyError:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "disconnected"
            }
        )
```

### 9.1. Comportamento esperado

| Situação | Código HTTP | Status |
|---|---:|---|
| API e banco disponíveis | 200 | healthy |
| API disponível, banco indisponível | 503 | unhealthy |

A consulta `SELECT 1` verifica se o banco aceita uma operação simples.

Quando ocorre uma exceção SQLAlchemy, o endpoint retorna HTTP 503 sem expor detalhes internos da conexão ao cliente.

**Limitação atual:** esse endpoint é uma verificação básica de disponibilidade. Não verifica latência, capacidade de armazenamento, integridade dos dados ou saúde de outros serviços.

## 10. Configuração do Alembic

O Alembic foi inicializado a partir da pasta `backend`:

```powershell
python -m alembic init migrations
```

A estrutura gerada contém:

```text
migrations/
├── versions/
├── env.py
├── README
└── script.py.mako
```

O arquivo `alembic.ini` permanece na raiz de `backend`.

### 10.1. alembic.ini

A propriedade `sqlalchemy.url` foi deixada vazia:

```ini
sqlalchemy.url =
```

A URL não fica armazenada diretamente no arquivo para evitar manter credenciais nele.

### 10.2. migrations/env.py

O arquivo `env.py` foi configurado para importar a URL e os metadados diretamente da aplicação:

```python
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.database import DATABASE_URL, Base

config = context.config


if config.config_file_name is not None:
    fileConfig(config.config_file_name)


database_url = DATABASE_URL.render_as_string(
    hide_password=False
)

config.set_main_option(
    "sqlalchemy.url",
    database_url.replace("%", "%%"),
)


target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()

    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### 10.3. Metadados dos modelos

A propriedade:

```python
target_metadata = Base.metadata
```

informa ao Alembic quais metadados deve utilizar para comparar os modelos ORM com a estrutura do banco.

Quando os primeiros modelos forem implementados e importados corretamente, será possível gerar migrações automáticas.

A opção:

```python
compare_type=True
```

permite detectar alterações nos tipos das colunas durante a comparação.

### 10.4. Estado das migrações

Até o encerramento desta etapa:

- O Alembic está inicializado.
- A conexão com PostgreSQL foi validada.
- A pasta `migrations/versions/` está preparada.
- Nenhuma tabela de negócio foi criada.
- Nenhuma migração inicial foi gerada.

A ausência de uma revisão atual é esperada neste momento.

## 11. Testes e validações realizados

### 11.1. Docker

Inicialização:

```powershell
docker compose -f backend/docker-compose.yml up -d
```

Verificação:

```powershell
docker compose -f backend/docker-compose.yml ps
```

Resultado observado:

| Item | Resultado |
|---|---|
| Container | wardrobe-ai-db |
| Imagem | postgres:18-alpine |
| Estado | Up |
| Healthcheck | healthy |
| Porta publicada | 5433 |

### 11.2. PostgreSQL

Foi realizada uma consulta SQL diretamente no container:

```powershell
docker compose -f backend/docker-compose.yml exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT current_database(), current_user;"'
```

A consulta foi executada com sucesso.

### 11.3. SQLAlchemy

A conexão pelo Python foi testada utilizando `engine.connect()` e uma consulta SQL.

Resultado: conexão estabelecida com sucesso.

### 11.4. Pytest

Os testes automatizados existentes foram executados após a atualização do health check.

Os testes do endpoint `/` e do endpoint `/health` passaram.

O teste do health check foi atualizado para validar também a resposta:

```json
{
  "status": "healthy",
  "database": "connected"
}
```

### 11.5. Alembic

Comando executado:

```powershell
python -m alembic current
```

Resultado observado:

```text
INFO [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO [alembic.runtime.migration] Will assume transactional DDL.
```

Isso confirma que o Alembic reconheceu o PostgreSQL e iniciou o contexto de migrações.

Ainda não existe uma revisão aplicada.

## 12. Decisões técnicas

As seguintes decisões foram adotadas nesta etapa:

1. O PostgreSQL será executado em container Docker.
2. O FastAPI continuará sendo executado pelo ambiente virtual Python durante o desenvolvimento local.
3. As credenciais serão armazenadas em variáveis de ambiente.
4. O `.env` real não será versionado.
5. O SQLAlchemy será responsável pelo acesso ao banco.
6. O psycopg 3 será o driver PostgreSQL.
7. As sessões serão disponibilizadas por uma dependência do FastAPI.
8. O Alembic será utilizado para versionar as alterações do esquema.
9. O Alembic utilizará os metadados da classe `Base`.
10. Nenhuma tabela de negócio será criada antes da definição dos modelos e das regras de relacionamento.

## 13. Segurança e cuidados

Alguns cuidados deverão ser mantidos durante a evolução do backend:

- Nunca versionar credenciais reais.
- Não retornar senhas ou URLs completas de conexão em respostas da API.
- Fechar sessões após o uso.
- Utilizar transações de forma explícita nas operações de escrita.
- Revisar migrações automáticas antes de aplicá-las.
- Não remover volumes Docker sem compreender que isso pode apagar os dados.
- Restringir o acesso aos dados por usuário autenticado.
- Não armazenar imagens pessoais diretamente no PostgreSQL; armazenar arquivos em local apropriado e manter somente metadados e identificadores no banco.

A estratégia de autorização, isolamento por usuário e proteção de dados pessoais será detalhada durante a implementação de autenticação e dos primeiros modelos.

## 14. Próximas etapas

Com a infraestrutura de persistência preparada, o desenvolvimento seguirá para a modelagem dos dados da aplicação.

| Ordem | Atividade |
|---:|---|
| 1 | Definir o modelo de usuário e autenticação. |
| 2 | Definir as entidades do closet. |
| 3 | Criar os primeiros modelos SQLAlchemy. |
| 4 | Criar a primeira migração com Alembic. |
| 5 | Implementar operações CRUD e testes. |

Antes da criação das tabelas, será necessário definir os relacionamentos, as chaves, as regras de exclusão e o isolamento dos dados por usuário.

A primeira migração deverá refletir os modelos efetivamente implementados, e não apenas uma estrutura hipotética.

---

**Documento:** Infraestrutura do Banco de Dados — Wardrobe AI  
**Local de armazenamento:** `docs/backend/infraestrutura-do-banco-de-dados.md`  
**Versão:** 1.0