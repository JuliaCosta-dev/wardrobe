
# Sistema de Feedback das Recomendações

## 1. Objetivo

Armazenar avaliações dos looks gerados pelo motor de recomendações
contextuais do Wardrobe AI.

O feedback será utilizado futuramente para analisar a qualidade
das recomendações e aprimorar as regras de pontuação.

## 2. Arquitetura

O módulo segue a arquitetura em camadas:

- API: recebe as requisições HTTP.
- Schemas: validam os dados de entrada e saída.
- Service: aplica as regras de negócio.
- Repository: executa as operações de persistência.
- Model: representa a tabela no PostgreSQL.

## 3. Modelo de dados

Tabela: recommendation_feedback

Campos:

- id: UUID, chave primária.
- profile_id: UUID, perfil proprietário.
- outfit_id: UUID, look avaliado.
- rating: positive ou negative.
- reason: motivo estruturado opcional.
- comment: comentário opcional, até 500 caracteres.
- created_at: data de criação.
- updated_at: data da última atualização.

Cada look pode possuir somente um feedback.

A restrição UNIQUE em outfit_id impede registros duplicados.

## 4. Regras de negócio

1. Somente usuários autenticados podem avaliar.
2. O perfil é identificado pelo token de autenticação.
3. O look precisa pertencer ao perfil autenticado.
4. Somente looks de recomendações contextuais podem ser avaliados.
5. Uma nova avaliação atualiza a anterior.
6. O usuário pode consultar e excluir sua avaliação.
7. Um look removido também remove seu feedback por CASCADE.

## 5. Segurança

- Não aceitar profile_id do cliente.
- Não aceitar outfit_id no corpo da requisição.
- Validar rating e reason com valores controlados.
- Limitar comentários a 500 caracteres.
- Filtrar looks pelo profile_id autenticado.
- Aplicar restrições no PostgreSQL.
- Não retornar informações de outros perfis.

## 6. Endpoints

PUT /api/v1/recommendations/outfit/{outfit_id}/feedback

Cria ou atualiza uma avaliação.

GET /api/v1/recommendations/outfit/{outfit_id}/feedback

Consulta a avaliação do perfil autenticado.

DELETE /api/v1/recommendations/outfit/{outfit_id}/feedback

Remove a avaliação.

## 7. Decisões técnicas

O método PUT foi escolhido para tornar a operação de criação
e atualização idempotente.

O feedback utiliza valores estruturados para permitir análises
e métricas futuras.

A implementação não altera automaticamente o algoritmo
de recomendação. Os dados serão coletados primeiro e poderão
ser utilizados em uma etapa posterior.

## 8. Evoluções futuras

- Painel de métricas de satisfação.
- Análise dos motivos mais frequentes.
- Ajuste de pesos do algoritmo.
- Preferências aprendidas a partir das avaliações.
- Experimentos controlados de recomendação.
