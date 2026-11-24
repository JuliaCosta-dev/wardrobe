## Imagem principal na listagem de peças

Os endpoints:

- GET /api/v1/garments
- GET /api/v1/garments/{garment_id}

Retornam o objeto `primary_image` dentro de cada peça.

Quando a peça não possui imagem principal, o valor será `null`.

Exemplo:

```json
{
  "primary_image": {
    "id": "UUID",
    "garment_id": "UUID",
    "mime_type": "image/webp",
    "width": 800,
    "height": 1000,
    "url": "/api/v1/garments/UUID/images/UUID"
  }
}