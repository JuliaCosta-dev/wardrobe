
# Módulo de Looks (Outfits)

## 1. Objetivo

O módulo de Looks é responsável por gerar combinações de roupas
automaticamente a partir das peças disponíveis no closet de cada perfil.

O usuário não cadastra manualmente as peças de um look.
Ele pode informar filtros opcionais, como ocasião, estação e formalidade.

A seleção das peças é responsabilidade do backend.

## 2. Arquitetura

O módulo segue a arquitetura:

API -> Service -> Generator / Repository -> Database

### API

Arquivo: `app/api/v1/outfits.py`

Responsabilidades:
- Receber solicitações HTTP.
- Validar autenticação.
- Validar os parâmetros recebidos.
- Converter erros de negócio em respostas HTTP.
- Retornar os dados do look.

### Schemas

Arquivo: `app/schemas/outfits.py`

Responsabilidades:
- Validar os filtros de geração.
- Definir o formato de resposta dos looks.
- Impedir campos não permitidos na solicitação.

### Generator

Arquivo: `app/services/outfit_generator.py`

Responsabilidades:
- Filtrar peças por ocasião, estação e formalidade.
- Selecionar peças compatíveis.
- Criar uma combinação de roupas.
- Gerar uma assinatura SHA-256 da combinação.
- Evitar assinaturas já utilizadas.

### Service

Arquivo: `app/services/outfit_service.py`

Responsabilidades:
- Coordenar a geração.
- Bloquear o perfil durante a geração.
- Limpar registros vencidos.
- Consultar o histórico.
- Persistir o look e seus itens.
- Controlar a validade de 30 dias.

### Repository

Arquivo: `app/repositories/outfit_repository.py`

Responsabilidades:
- Consultar peças disponíveis.
- Consultar histórico de combinações.
- Persistir looks e itens.
- Consultar looks pertencentes ao perfil.
- Excluir registros vencidos.

## 3. Modelagem

### Outfit

Representa um look gerado.

Campos principais:
- id
- profile_id
- occasion
- season
- formality
- signature
- generated_at
- expires_at

### OutfitItem

Representa uma peça associada ao look.

Campos principais:
- id
- outfit_id
- garment_id
- role
- created_at

Um look pode possuir vários itens.

## 4. Regras de geração

Estruturas obrigatórias:

- tops + bottoms + shoes
- one_piece + shoes

Complementos opcionais:

- bags
- accessories
- jewelry
- hair_accessories

A categoria makeup não participa da composição nesta versão.

Somente peças com status `available` são elegíveis.

## 5. Compatibilidade

Quando um filtro é informado:

- Se a peça possui tags de ocasião, deve incluir a ocasião solicitada.
- Se a peça possui tags de estação, deve incluir a estação solicitada.
- Se a peça possui formalidade, pode ter diferença máxima de um nível.

Peças sem tags de ocasião ou estação não são descartadas somente
pela ausência desses dados.

## 6. Prevenção de repetição

A assinatura SHA-256 é calculada com os IDs das peças do look.

Os IDs são ordenados antes do cálculo, evitando que a ordem de
apresentação altere a identificação da combinação.

A assinatura é única por perfil.

Os looks possuem validade de 30 dias.

Registros vencidos são removidos durante as operações de geração
e consulta do módulo.

A limpeza física não é executada por um agendador nesta versão.
Se o sistema ficar sem receber requisições, registros vencidos
poderão permanecer no banco até a próxima operação do módulo.

## 7. Segurança

- Todos os endpoints exigem autenticação.
- O perfil é obtido pelo token autenticado.
- O cliente não pode enviar IDs de peças para montar looks.
- As consultas de peças são filtradas pelo profile_id.
- A consulta de looks também verifica o profile_id.
- As constraints do banco protegem a integridade das associações.
- A geração bloqueia a linha do perfil para reduzir concorrência.
- As respostas não expõem caminhos de armazenamento de imagens.

## 8. Endpoints

### Gerar look

POST /api/v1/outfits/generate

Exemplo:

{
  "occasion": "casual",
  "season": "summer",
  "formality": 1
}

Todos os filtros são opcionais.

### Listar looks

GET /api/v1/outfits

Parâmetros:
- skip
- limit

### Consultar look

GET /api/v1/outfits/{outfit_id}

## 9. Respostas e erros

- 201: look gerado.
- 200: consulta realizada.
- 401: autenticação ausente ou inválida.
- 404: look não encontrado para o perfil.
- 409: não existe combinação inédita ou faltam peças compatíveis.
- 422: parâmetros inválidos.

## 10. Limitações desta versão

- O gerador é baseado em regras, não em inteligência artificial.
- A seleção é probabilística.
- A compatibilidade visual avançada de cores ainda não é avaliada.
- A previsão do tempo não é consultada.
- Não há agendador para limpeza física independente de requisições.
- Não há edição manual de looks.

## 11. Evoluções futuras

- Pontuação de compatibilidade de cores.
- Integração com preferências pessoais do perfil.
- Recomendações baseadas em clima.
- Histórico de uso e avaliação dos looks.
- Agendamento automático da limpeza de registros vencidos.
- Motor de recomendações mais avançado.

---

# 12. `backend/app/docs/outfits.md`

Se esse documento já existe, adicione a seguinte seção:

```markdown
## Imagens das peças nos looks

Os endpoints:

- GET /api/v1/outfits
- GET /api/v1/outfits/{outfit_id}
- POST /api/v1/outfits/generate

Retornam os metadados da imagem principal de cada peça
dentro de `items[].garment.primary_image`.

A imagem é recuperada separadamente pela URL fornecida
nos metadados.

Os bytes não são incorporados à resposta JSON.