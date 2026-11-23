from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class GarmentImageRead(BaseModel):
    """Metadados públicos de uma imagem de peça."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    garment_id: UUID
    mime_type: str
    width: int | None
    height: int | None
    is_primary: bool
    created_at: datetime
