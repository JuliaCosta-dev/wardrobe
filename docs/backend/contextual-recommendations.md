
# Contextual Outfit Recommendations

## Objetivo

Implementar recomendações automáticas de looks considerando:

- Peças disponíveis no closet.
- Preferências cadastradas no perfil.
- Ocasião desejada.
- Estação informada.
- Formalidade desejada.
- Previsão meteorológica da localização do perfil.

## Arquitetura

### Integração externa

O sistema utiliza o MET Norway Locationforecast 2.0.

Endpoint:

https://api.met.no/weatherapi/locationforecast/2.0/compact

A integração fica em:

app/integrations/weather/met_no_client.py

Responsabilidades:

- Enviar requisições HTTP.
- Identificar a aplicação pelo User-Agent.
- Interpretar respostas HTTP.
- Suportar respostas 304.
- Respeitar o cabeçalho Expires.

### Cache meteorológico

O cache fica na tabela weather_cache.

As coordenadas são normalizadas para quatro casas decimais.

O sistema reutiliza previsões válidas e consulta novamente o provedor
quando necessário.

Quando o provedor está indisponível, uma previsão antiga pode ser
utilizada, desde que esteja armazenada. A resposta informa is_stale.

### Recomendação

O motor de recomendação fica em:

app/services/contextual_outfit_generator.py

Ele não acessa banco de dados nem serviços externos.

Recebe as peças disponíveis, preferências e dados meteorológicos.

As estruturas básicas são:

- top + bottom + shoes
- one_piece + shoes

Complementos opcionais:

- bags
- accessories
- jewelry
- hair_accessories

A seleção utiliza pontuação determinística.

## Pontuação

A pontuação considera:

- Cores preferidas.
- Cores evitadas.
- Preferência de caimento.
- Formalidade.
- Peças favoritas.
- Compatibilidade entre temperatura e nível de aquecimento.

A pontuação final é limitada entre 0 e 100.

O sistema não afirma que uma peça é impermeável, pois essa
informação ainda não existe no modelo Garment.

## Histórico

Cada combinação é identificada por uma assinatura SHA-256.

O histórico de looks continua utilizando a validade de 30 dias.

As recomendações são armazenadas na tabela outfits.

Os campos adicionais são:

- recommendation_score
- recommendation_reasons
- weather_snapshot

## Endpoint

POST /api/v1/recommendations/outfit

Autenticação obrigatória.

Exemplo de solicitação:

{
  "occasion": "work",
  "season": "summer",
  "formality": 3
}

Não são aceitos IDs de peças ou coordenadas enviados pelo cliente.

## Resposta

A resposta inclui:

- Look gerado.
- Peças utilizadas.
- Pontuação.
- Justificativas.
- Previsão meteorológica considerada.

## Segurança

- A localização vem do perfil autenticado.
- O closet é filtrado pelo profile_id.
- A API externa é acessada exclusivamente pelo backend.
- O User-Agent identifica a aplicação.
- O timeout limita o tempo de espera.
- A resposta externa é validada antes de ser utilizada.
- Dados internos do cache não são expostos.

## Limitações conhecidas

- A recomendação é baseada em regras, não em aprendizado de máquina.
- preferred_styles ainda não é aplicado porque Garment não possui
  um atributo de estilo.
- Não existe atributo de impermeabilidade.
- A previsão meteorológica é aproximada.
- A API externa não oferece garantia de disponibilidade.
- O cache é atualizado sob demanda, sem um agendador independente.

## Licenciamento

Os dados meteorológicos devem ser atribuídos ao MET Norway.

Fonte:
https://api.met.no/

Licença:
https://creativecommons.org/licenses/by/4.0/

A aplicação deve indicar a fonte e a licença sempre que apresentar
os dados meteorológicos ao usuário.

## Decisões futuras

- Adicionar estilos às peças.
- Adicionar atributos de proteção contra chuva e vento.
- Implementar preferências de temperatura.
- Adicionar histórico de avaliações dos looks.
- Melhorar a diversidade das recomendações.
- Considerar um modelo de aprendizado de máquina após reunir dados
  suficientes e consentidos.
