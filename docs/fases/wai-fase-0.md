# Wardrobe AI — Fase 0: Fundação do Projeto

**Versão:** 1.0  
**Etapa:** Fundação  
**Objetivo:** Preparar a estrutura do repositório e o ambiente de desenvolvimento para iniciar a construção do backend.

## 1. Objetivo da fase

A Fase 0 estabelece a infraestrutura técnica do Wardrobe AI.

Antes de desenvolver funcionalidades como cadastro de roupas, criação de looks e recomendações, precisamos garantir que o projeto tenha uma estrutura organizada, um ambiente reproduzível e uma base que permita evoluir com segurança.

Ao concluir esta fase, deveremos ter:

- Repositório Git inicializado e organizado.
- Ambiente Python configurado.
- API FastAPI inicializada.
- PostgreSQL executando por Docker Compose.
- Estrutura para controle de migrações.
- Ferramentas de qualidade e testes configuradas.
- Documentação inicial do projeto.

## 2. Organização do repositório

O repositório é o espaço central onde ficam os arquivos, códigos e documentos do projeto.

A organização inicial será:

```text
wardrobe-ai/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── repositories/
│   │   ├── services/
│   │   └── tests/
│   ├── alembic/
│   ├── pyproject.toml
│   └── .env.example
├── docs/
├── .gitignore
└── README.md
```

### Responsabilidade das principais pastas

| Diretório | Responsabilidade |
|---|---|
| backend/app/api | Receber e responder às requisições HTTP |
| backend/app/core | Configurações e recursos centrais |
| backend/app/models | Representar as entidades do banco |
| backend/app/schemas | Validar e estruturar os dados da API |
| backend/app/repositories | Centralizar o acesso aos dados |
| backend/app/services | Implementar regras de negócio |
| backend/app/tests | Armazenar testes automatizados |
| backend/alembic | Controlar as migrações do banco |
| docs | Armazenar documentação técnica |

A separação evita que toda a lógica do sistema fique concentrada nas rotas da API.

## 3. Ferramentas e tecnologias

### Python

Linguagem utilizada para implementar o backend. É onde desenvolveremos as regras de negócio, integrações e funcionalidades da API.

### FastAPI

Framework utilizado para construir a API HTTP. Ele permite definir endpoints, validar entradas e documentar as operações.

### PostgreSQL

Banco de dados relacional responsável por armazenar informações como usuários, peças de roupa, ocasiões e looks.

### SQLAlchemy

Biblioteca que permite trabalhar com o banco de dados utilizando objetos e estruturas Python.

### Alembic

Ferramenta para controlar as alterações na estrutura do banco de dados através de migrações versionadas.

### Docker Compose

Ferramenta para definir e executar os serviços necessários ao ambiente, como o PostgreSQL.

### Pytest

Framework utilizado para criar e executar testes automatizados.

### Git

Sistema de controle de versão. Permite acompanhar mudanças, recuperar versões anteriores e organizar o histórico de desenvolvimento.

## 4. Preparação do ambiente

O desenvolvimento será realizado inicialmente no Windows, utilizando o VS Code e o terminal.

### 4.1. Verificar as ferramentas

Execute:

```powershell
py --version
git --version
docker --version
docker compose version
```

Cada comando verifica a disponibilidade de uma ferramenta.

### 4.2. Criar o repositório

Crie a pasta principal:

```powershell
mkdir wardrobe-ai
cd wardrobe-ai
```

Inicialize o Git:

```powershell
git init
```

O Git começará a acompanhar as alterações do repositório, respeitando as regras definidas no `.gitignore`.

### 4.3. Criar o ambiente virtual Python

Entre na pasta do backend:

```powershell
mkdir backend
cd backend
```

Crie o ambiente virtual:

```powershell
py -m venv .venv
```

Ative-o no PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

O ambiente virtual isola as dependências Python deste projeto das dependências de outros projetos instalados na máquina.

Para verificar se está ativo:

```powershell
python --version
```

Para desativá-lo:

```powershell
deactivate
```

### 4.4. Instalar dependências

A instalação das bibliotecas será feita depois de definirmos o gerenciamento de dependências no `pyproject.toml`.

As dependências iniciais previstas incluem FastAPI, Uvicorn, Pydantic, SQLAlchemy, Alembic, Psycopg e Pytest.

Não devemos instalar bibliotecas aleatoriamente: cada dependência precisa ter uma finalidade no projeto.

## 5. Conceitos importantes

### Repositório

É o conjunto de arquivos e histórico de versões de um projeto controlado pelo Git.

### Ambiente virtual

É um ambiente isolado para instalar bibliotecas Python específicas de um projeto.

### Dependência

É uma biblioteca ou ferramenta externa utilizada pelo código para realizar determinada tarefa.

### Variável de ambiente

É uma configuração fornecida ao programa durante sua execução. Pode conter, por exemplo, o endereço do banco de dados.

### Migração

É uma alteração versionada na estrutura do banco de dados, como a criação de uma tabela ou de uma coluna.

### Endpoint

É um endereço disponibilizado pela API para realizar uma operação.

Exemplo:

```http
GET /health
```

### Teste automatizado

É um código que verifica se determinada funcionalidade apresenta o comportamento esperado.

## 6. Segurança desde o início

Algumas regras serão aplicadas desde a fundação:

- Não enviar arquivos `.env` para o GitHub.
- Não armazenar senhas ou tokens diretamente no código.
- Manter um `.env.example` sem credenciais reais.
- Utilizar `.gitignore` para excluir arquivos temporários e ambientes virtuais.
- Não permitir que dados de um usuário sejam acessados por outro.
- Manter imagens dos usuários em armazenamento apropriado e com acesso privado.

## 7. Primeiro resultado esperado

Ao concluir a configuração inicial, a API deverá responder:

```http
GET http://localhost:8000/health
```

Resposta esperada:

```json
{
  "status": "healthy",
  "service": "Wardrobe AI API"
}
```

Também será possível acessar a documentação interativa do FastAPI:

```text
http://localhost:8000/docs
```

Esse primeiro endpoint permitirá verificar se a aplicação está inicializando corretamente. A verificação do banco de dados será acrescentada quando a integração com PostgreSQL estiver configurada.

## 8. Critérios de conclusão

- [ ] Repositório inicializado.
- [ ] Estrutura de diretórios criada.
- [ ] Python e Git disponíveis.
- [ ] Docker e Docker Compose disponíveis.
- [ ] Ambiente virtual configurado.
- [ ] Dependências iniciais definidas.
- [ ] PostgreSQL executando.
- [ ] API FastAPI inicializada.
- [ ] Endpoint `/health` funcionando.
- [ ] Teste automatizado executado com sucesso.
- [ ] Documentação atualizada.

**Importante:** a conclusão da Fase 0 não significa que o sistema já possui funcionalidades de moda. Significa que a infraestrutura está preparada para que essas funcionalidades sejam desenvolvidas nas próximas etapas.