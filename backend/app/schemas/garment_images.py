from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, computed_field


class GarmentImageRead(BaseModel):
    """
    Metadados públicos de uma imagem de peça.

    Não expõe storage_key nem caminhos internos
    do armazenamento.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    garment_id: UUID
    mime_type: str
    width: int | None
    height: int | None
    is_primary: bool
    created_at: datetime

    @computed_field
    @property
    def url(self) -> str:
        """
        Retorna a rota de leitura dos bytes da imagem.
        """
        return f"/api/v1/garments/{self.garment_id}/images/{self.id}"
