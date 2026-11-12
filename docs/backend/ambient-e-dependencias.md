# Wardrobe AI — Ambiente e Gerenciamento de Dependências

**Área:** Backend  
**Fase:** 0 — Fundação do Projeto  
**Status:** Em desenvolvimento  
**Última atualização:** 12/11/2026

---

## 1. Objetivo

Este documento descreve a configuração do ambiente de desenvolvimento Python do backend do Wardrobe AI, incluindo o ambiente virtual, o gerenciamento de dependências, a instalação de bibliotecas, a execução local da API, os testes automatizados e a análise de qualidade do código.

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
| setuptools | Ferramenta responsável pelo processo de build e instalação do projeto. |

### 2.1 Ferramentas de desenvolvimento

| Ferramenta | Finalidade |
|---|---|
| pytest | Execução de testes automatizados. |
| HTTPX2 | Suporte às requisições HTTP simuladas durante os testes através do TestClient do FastAPI. |
| Ruff | Análise estática, organização de imports e formatação do código. |

Essas ferramentas são instaladas como dependências opcionais de desenvolvimento, separadas das dependências necessárias para executar a aplicação.

## 3. Estrutura do backend

Estrutura atual:

```text
backend/
├── app/
│   ├── __init__.py
│   └── main.py
├── tests/
│   └── test_main.py
├── .venv/
└── pyproject.toml
```

**Descrição:**

- `app/`: contém o código-fonte principal da aplicação.
- `__init__.py`: identifica a pasta como um pacote Python.
- `main.py`: ponto de entrada da aplicação FastAPI.
- `tests/`: contém os testes automatizados do backend.
- `test_main.py`: contém os primeiros testes dos endpoints da API.
- `.venv/`: ambiente virtual local, não versionado no Git.
- `pyproject.toml`: centraliza os metadados, as dependências e as configurações das ferramentas do projeto.

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

O arquivo `pyproject.toml` é utilizado para declarar os metadados, as dependências e as configurações das ferramentas do backend.

Ele diferencia dois grupos:

- **Dependências principais:** necessárias para executar a aplicação.
- **Dependências de desenvolvimento:** utilizadas para testes, análise e manutenção do código.

Também define o sistema de build utilizado para preparar e instalar o projeto.

O arquivo é a referência oficial para a instalação das dependências do projeto.

### 6.2 Sistema de build

A configuração utiliza o setuptools como ferramenta de build:

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"
```

**Responsabilidades:**

- `requires`: declara a ferramenta necessária para preparar o projeto.
- `build-backend`: identifica o mecanismo responsável pelo processo de build.

Essa configuração permite que o pip instale o projeto utilizando o padrão moderno de empacotamento Python.

### 6.3 Dependências principais

| Biblioteca | Responsabilidade |
|---|---|
| FastAPI | Construção dos endpoints da API. |
| Uvicorn | Execução do servidor ASGI. |
| Pydantic | Validação e estruturação dos dados recebidos e enviados. |
| Pydantic Settings | Carregamento e gerenciamento das configurações. |

### 6.4 Dependências de desenvolvimento

| Biblioteca | Responsabilidade |
|---|---|
| pytest | Execução de testes automatizados. |
| HTTPX2 | Suporte às requisições HTTP simuladas nos testes. |
| Ruff | Verificação de qualidade, organização de imports e formatação do código. |

### 6.5 Instalação das dependências

A instalação é realizada na pasta `backend`, com o ambiente virtual ativo.

Para instalar o projeto e suas dependências principais e de desenvolvimento:

```powershell
python -m pip install -e ".[dev]"
```

**Detalhes do comando:**

- `pip install`: instala o projeto e suas dependências.
- `-e`: instala o projeto em modo editável, permitindo alterações no código sem reinstalações constantes.
- `.`: indica que o projeto está no diretório atual.
- `[dev]`: solicita também a instalação das dependências opcionais de desenvolvimento.

Para instalar somente as dependências principais, pode-se utilizar:

```powershell
python -m pip install .
```

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

## 9. Testes automatizados

### 9.1 Objetivo

Os testes automatizados permitem verificar se os componentes da aplicação estão funcionando conforme o esperado.

Eles ajudam a identificar regressões e problemas introduzidos durante alterações no código, reduzindo a necessidade de verificações exclusivamente manuais.

### 9.2 Ferramentas utilizadas

**pytest**

Responsável por descobrir, executar e apresentar os resultados dos testes automatizados.

**HTTPX2 e TestClient**

O TestClient disponibilizado pelo FastAPI permite simular requisições HTTP diretamente na aplicação, sem precisar iniciar o servidor Uvicorn.

### 9.3 Estrutura dos testes

Os testes ficam no diretório `backend/tests/`.

Atualmente, o arquivo `test_main.py` contém verificações para:

- Endpoint raiz (`GET /`).
- Health Check (`GET /health`).

### 9.4 Executar os testes

Para executar todos os testes:

```powershell
python -m pytest -v
```

O parâmetro `-v` apresenta os nomes dos testes e seus respectivos resultados.

### 9.5 Resultado esperado

Na configuração inicial, são esperados dois testes aprovados:

```text
tests/test_main.py::test_root_endpoint PASSED
tests/test_main.py::test_health_endpoint PASSED

===================== 2 passed =====================
```

Um teste aprovado indica que o resultado obtido corresponde ao resultado esperado.

Um teste com falha indica que alguma verificação não foi satisfeita e precisa ser analisada.

## 10. Qualidade e padronização do código

### 10.1 Ruff

O Ruff é utilizado para analisar o código Python e identificar problemas de organização e possíveis erros.

A configuração inicial fica centralizada no `pyproject.toml`:

```toml
[tool.ruff]
line-length = 100
target-version = "py310"

[tool.ruff.lint]
select = ["E", "F", "I"]
```

**Configurações:**

| Configuração | Finalidade |
|---|---|
| `line-length` | Define o limite de caracteres por linha. |
| `target-version` | Define a versão mínima de Python considerada na análise. |
| `E` | Verifica problemas relacionados às regras de estilo e sintaxe do pycodestyle. |
| `F` | Identifica problemas como imports e variáveis não utilizados. |
| `I` | Verifica a organização dos imports. |

### 10.2 Comandos do Ruff

Analisar o código:

```powershell
python -m ruff check .
```

Corrigir automaticamente problemas identificados:

```powershell
python -m ruff check . --fix
```

Formatar o código:

```powershell
python -m ruff format .
```

A análise e a formatação são operações diferentes:

- `ruff check`: identifica problemas de qualidade e lint.
- `ruff format`: padroniza a formatação do código.

As correções automáticas devem ser verificadas antes de registrar alterações no Git.

### 10.3 Validação inicial

Durante a configuração inicial, o Ruff identificou dois problemas de organização de imports:

- Um no arquivo `app/main.py`.
- Um no arquivo `tests/test_main.py`.

Os dois problemas foram corrigidos automaticamente com `ruff check . --fix`.

Após a correção, a análise apresentou:

```text
All checks passed!
```

## 11. Boas práticas

- Utilizar o ambiente virtual para todas as instalações do projeto.
- Preferir `python -m pip` em vez de executar `pip` diretamente.
- Declarar as dependências no `pyproject.toml`.
- Separar dependências de execução e desenvolvimento.
- Não versionar a pasta `.venv`.
- Não versionar arquivos `.env` com credenciais ou informações privadas.
- Não instalar bibliotecas globalmente sem necessidade.
- Executar os testes após alterações relevantes.
- Executar a análise do Ruff antes de registrar commits.
- Validar alterações antes de registrá-las no Git.
- Atualizar a documentação quando houver mudanças relevantes na configuração.

## 12. Solução de problemas

### 12.1 PyYAML falha durante a instalação

Em versões recentes do Python, algumas bibliotecas podem ainda não disponibilizar pacotes pré-compilados compatíveis com o interpretador utilizado.

Quando isso acontece, o pip pode tentar compilar a biblioteca localmente.

Durante a configuração inicial do Wardrobe AI, foi necessário utilizar a seguinte variável temporária no PowerShell:

```powershell
$env:PYYAML_FORCE_LIBYAML = "0"
```

Em seguida, a instalação foi executada novamente.

Essa configuração foi utilizada como alternativa para evitar a compilação da extensão C do PyYAML. Ela não deve ser tratada como uma configuração obrigatória para todos os ambientes.

### 12.2 Verificar uma biblioteca instalada

Para consultar informações sobre uma dependência:

```powershell
python -m pip show nome-da-biblioteca
```

Para listar os pacotes instalados:

```powershell
python -m pip list
```

### 12.3 TestClient apresenta aviso de depreciação

Durante a configuração inicial, foi identificado um aviso relacionado à integração do HTTPX tradicional com o `TestClient` do Starlette.

A configuração de desenvolvimento foi atualizada para utilizar HTTPX2, conforme a integração recomendada pela versão utilizada do Starlette.

Quando esse aviso aparecer, é importante verificar a compatibilidade entre as versões do FastAPI, Starlette e da biblioteca de testes antes de modificar dependências.

## 13. Segurança e configurações

Configurações sensíveis não devem ser armazenadas diretamente no código-fonte.

Quando forem implementadas as conexões com o banco de dados e outros serviços, as credenciais deverão ser fornecidas por variáveis de ambiente.

O arquivo `.env.example` deverá apresentar apenas exemplos de variáveis, sem credenciais reais.

O arquivo `.env` deverá permanecer fora do controle de versão.

## 14. Histórico de evolução

| Etapa | Descrição | Situação |
|---|---|---|
| 1 | Instalação e verificação do Python. | Concluída |
| 2 | Criação e ativação do ambiente virtual. | Concluída |
| 3 | Instalação das dependências iniciais. | Concluída |
| 4 | Criação da aplicação FastAPI. | Concluída |
| 5 | Implementação da rota principal. | Concluída |
| 6 | Implementação do Health Check. | Concluída |
| 7 | Formalização das dependências no `pyproject.toml`. | Concluída |
| 8 | Configuração do sistema de build. | Concluída |
| 9 | Instalação das dependências de desenvolvimento. | Concluída |
| 10 | Configuração dos testes automatizados. | Concluída |
| 11 | Implementação dos primeiros testes dos endpoints. | Concluída |
| 12 | Configuração inicial do Ruff. | Concluída |
| 13 | Correção dos primeiros problemas de organização do código. | Concluída |
| 14 | Validação final dos testes e análise de qualidade. | Em validação |

---

**Documento de referência:** documentação técnica do backend do Wardrobe AI.  
**Manutenção:** atualizar este documento sempre que houver mudanças relevantes na configuração do ambiente, nas dependências ou no processo de execução da aplicação.