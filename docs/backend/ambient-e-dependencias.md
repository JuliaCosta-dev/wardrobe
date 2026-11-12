# Wardrobe AI — Ambiente e Gerenciamento de Dependências

**Área:** Backend  
**Fase:** 0 — Fundação do Projeto  
**Status:** Em desenvolvimento  
**Última atualização:** 11/11/2026

---

## 1. Objetivo

Este documento descreve a configuração do ambiente de desenvolvimento Python do backend do Wardrobe AI, incluindo o ambiente virtual, o gerenciamento de dependências, a instalação de bibliotecas e a execução local da API.

O objetivo é padronizar a configuração do ambiente, facilitar a reprodução da instalação em outras máquinas e evitar dependências instaladas globalmente no sistema operacional.

## 2. Tecnologias utilizadas

| Tecnologia | Finalidade |
|---|---|
| Python | Linguagem de programação do backend. |
| FastAPI | Framework responsável pela construção da API REST. |
| Uvicorn | Servidor ASGI responsável por executar a aplicação. |
| Pydantic | Validação, estruturação e serialização de dados. |
| Pydantic Settings | Gerenciamento de configurações e variáveis de ambiente. |
| pip | Gerenciador de pacotes Python. |

### 2.1 Ferramentas de desenvolvimento previstas

| Ferramenta | Finalidade |
|---|---|
| pytest | Execução de testes automatizados. |
| HTTPX | Requisições HTTP durante os testes. |
| Ruff | Análise estática e padronização do código. |

Essas ferramentas serão instaladas como dependências opcionais de desenvolvimento.

## 3. Estrutura do backend

Estrutura inicial prevista:

```text
backend/
├── app/
│   ├── __init__.py
│   └── main.py
├── .venv/
└── pyproject.toml
```

**Descrição:**

- `app/`: contém o código-fonte principal da aplicação.
- `__init__.py`: identifica a pasta como um pacote Python.
- `main.py`: ponto de entrada da aplicação FastAPI.
- `.venv/`: ambiente virtual local, não versionado no Git.
- `pyproject.toml`: centraliza os metadados e as dependências do projeto.

## 4. Requisitos do ambiente

Configuração utilizada durante a fase inicial:

| Requisito | Versão |
|---|---|
| Python | 3.15.0 |
| pip | 26.2.1 na validação inicial; posteriormente 26.3 |
| Git | 2.55.0 |
| Docker | 29.8.2 |
| Docker Compose | 5.5.1 |

As versões acima representam o ambiente utilizado durante a configuração inicial, não necessariamente versões mínimas obrigatórias.

## 5. Ambiente virtual Python

### 5.1 O que é?

O ambiente virtual é um espaço isolado que permite instalar bibliotecas específicas para um projeto sem interferir nas instalações globais do Python.

No Wardrobe AI, utilizamos o módulo `venv`, disponibilizado pelo próprio Python.

### 5.2 Criar o ambiente virtual

Na pasta `backend`, execute:

```powershell
py -m venv .venv
```

Esse comando cria o diretório `.venv` com uma instalação isolada do Python e os recursos necessários para gerenciar pacotes.

### 5.3 Ativar o ambiente virtual

No Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Após a ativação, o terminal deverá apresentar `(.venv)` antes do caminho atual.

### 5.4 Verificar a ativação

Execute:

```powershell
python --version
python -m pip --version
```

O caminho apresentado pelo pip deve apontar para dentro de `backend\.venv`.

### 5.5 Desativar o ambiente virtual

Para encerrar o uso do ambiente virtual:

```powershell
deactivate
```

A desativação não remove os pacotes instalados.

## 6. Gerenciamento de dependências

### 6.1 Arquivo pyproject.toml

O arquivo `pyproject.toml` é utilizado para declarar os metadados e as dependências do backend.

Ele diferencia dois grupos:

- Dependências principais: necessárias para executar a aplicação.
- Dependências de desenvolvimento: utilizadas para testes, análise e manutenção do código.

O arquivo será a referência oficial para a instalação das dependências do projeto.

### 6.2 Dependências principais

| Biblioteca | Responsabilidade |
|---|---|
| FastAPI | Construção dos endpoints da API. |
| Uvicorn | Execução do servidor ASGI. |
| Pydantic | Validação e estruturação dos dados recebidos e enviados. |
| Pydantic Settings | Carregamento e gerenciamento das configurações. |

### 6.3 Dependências de desenvolvimento

| Biblioteca | Responsabilidade |
|---|---|
| pytest | Testes automatizados. |
| HTTPX | Cliente HTTP para testes da API. |
| Ruff | Verificação de qualidade e padronização do código. |

### 6.4 Instalação das dependências

Após a configuração do `pyproject.toml`, a instalação poderá ser realizada com:

Dependências principais:

```powershell
python -m pip install .
```

Dependências principais e ferramentas de desenvolvimento:

```powershell
python -m pip install ".[dev]"
```

Os comandos devem ser executados na pasta `backend`, com o ambiente virtual ativo.

## 7. Execução da API

### 7.1 Iniciar o servidor

Na pasta `backend`, execute:

```powershell
python -m uvicorn app.main:app --reload
```

**Parâmetros:**

- `app.main`: indica o módulo `main.py` dentro do pacote `app`.
- `:app`: identifica a variável que contém a aplicação FastAPI.
- `--reload`: reinicia o servidor automaticamente quando alterações no código são detectadas.

### 7.2 Endereços locais

| Endereço | Finalidade |
|---|---|
| `http://127.0.0.1:8000/` | Rota principal da API. |
| `http://127.0.0.1:8000/health` | Verificação básica de disponibilidade. |
| `http://127.0.0.1:8000/docs` | Documentação interativa Swagger UI. |
| `http://127.0.0.1:8000/redoc` | Documentação interativa ReDoc. |

Para encerrar o servidor, pressione `CTRL + C` no terminal.

## 8. Endpoints iniciais

### 8.1 Rota principal

**Método:** GET  
**Caminho:** `/`

Retorna uma mensagem de identificação da aplicação.

Resposta esperada:

```json
{
  "message": "Wardrobe AI API está funcionando!",
  "status": "online"
}
```

### 8.2 Health Check

**Método:** GET  
**Caminho:** `/health`

Verifica se a aplicação está respondendo às requisições.

Resposta esperada:

```json
{
  "status": "healthy"
}
```

**Limitação atual:** essa verificação não consulta o banco de dados nem outros serviços externos. Ela confirma somente que a aplicação FastAPI está respondendo.

## 9. Boas práticas

- Utilizar o ambiente virtual para todas as instalações do projeto.
- Preferir `python -m pip` em vez de executar `pip` diretamente.
- Declarar as dependências no `pyproject.toml`.
- Separar dependências de execução e desenvolvimento.
- Não versionar a pasta `.venv`.
- Não versionar arquivos `.env` com credenciais ou informações privadas.
- Não instalar bibliotecas globalmente sem necessidade.
- Validar alterações antes de registrar commits.
- Atualizar a documentação quando houver mudanças relevantes na configuração.

## 10. Solução de problemas

### 10.1 PyYAML falha durante a instalação

Em versões recentes do Python, algumas bibliotecas podem ainda não disponibilizar pacotes pré-compilados compatíveis com o interpretador utilizado.

Quando isso acontece, o pip pode tentar compilar a biblioteca localmente.

Durante a configuração inicial do Wardrobe AI, foi necessário utilizar a seguinte variável temporária no PowerShell:

```powershell
$env:PYYAML_FORCE_LIBYAML = "0"
```

Em seguida, a instalação foi executada novamente.

Essa configuração foi utilizada como alternativa para evitar a compilação da extensão C do PyYAML. Ela não deve ser tratada como uma configuração obrigatória para todos os ambientes.

### 10.2 Verificar uma biblioteca instalada

Para consultar informações sobre uma dependência:

```powershell
python -m pip show nome-da-biblioteca
```

Para listar os pacotes instalados:

```powershell
python -m pip list
```

## 11. Segurança e configurações

Configurações sensíveis não devem ser armazenadas diretamente no código-fonte.

Quando forem implementadas as conexões com o banco de dados e outros serviços, as credenciais deverão ser fornecidas por variáveis de ambiente.

O arquivo `.env.example` deverá apresentar apenas exemplos de variáveis, sem credenciais reais.

O arquivo `.env` deverá permanecer fora do controle de versão.

## 12. Histórico de evolução

| Etapa | Descrição | Situação |
|---|---|---|
| 1 | Instalação e verificação do Python. | Concluída |
| 2 | Criação e ativação do ambiente virtual. | Concluída |
| 3 | Instalação das dependências iniciais. | Concluída |
| 4 | Criação da aplicação FastAPI. | Concluída |
| 5 | Implementação da rota principal. | Concluída |
| 6 | Implementação do Health Check. | Concluída |
| 7 | Formalização das dependências no `pyproject.toml`. | Em andamento |
| 8 | Instalação das dependências de desenvolvimento. | Pendente |
| 9 | Configuração dos testes automatizados. | Pendente |

---

**Documento de referência:** documentação técnica do backend do Wardrobe AI.  
**Manutenção:** atualizar este documento sempre que houver mudanças relevantes na configuração do ambiente ou no processo de execução da aplicação.