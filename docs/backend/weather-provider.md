# ADR 0001 — Provedor meteorológico

## Status

Aceito.

## Contexto

O Wardrobe AI precisa utilizar informações meteorológicas para
melhorar recomendações de roupas.

A integração precisa atender:

- Uso gratuito.
- Possibilidade de uso comercial.
- Cobertura geográfica global.
- Previsões estruturadas em JSON.
- Ausência de dependência de chave de API.

## Decisão

Utilizar MET Norway Locationforecast 2.0.

## Justificativa

O serviço disponibiliza previsões globais e dados abertos sob
licença Creative Commons Attribution 4.0, respeitando seus
termos de identificação, atribuição e cache.

## Arquitetura

O backend consulta o provedor.

O frontend não acessa diretamente a API meteorológica.

As respostas são armazenadas no PostgreSQL e reutilizadas
conforme a validade indicada pelo provedor.

## Segurança e privacidade

- Não enviar coordenadas arbitrárias do cliente.
- Utilizar as coordenadas do perfil autenticado.
- Não expor dados internos do cache.
- Identificar a aplicação pelo User-Agent.
- Utilizar HTTPS.

## Limitações

- Não existe SLA.
- A disponibilidade do provedor não é garantida.
- A precisão e frequência de atualização variam por região.
- O cache deve respeitar os cabeçalhos e termos do serviço.

## Licença e atribuição

Fonte: MET Norway.

Licença: CC BY 4.0.

https://creativecommons.org/licenses/by/4.0/