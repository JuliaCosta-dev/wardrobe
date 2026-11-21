from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_profile
from app.models.garment import Garment
from app.models.profile import Profile
from app.schemas.garments import (
    GarmentCreate,
    GarmentList,
    GarmentRead,
    GarmentUpdate,
)

router = APIRouter(prefix="/garments", tags=["Garments"])


# Cria uma peça no closet do perfil autenticado.
@router.post(
    "",
    response_model=GarmentRead,
    status_code=status.HTTP_201_CREATED,
)
def create_garment(
    data: GarmentCreate,
    profile: Annotated[Profile, Depends(get_current_profile)],
    db: Annotated[Session, Depends(get_db)],
):
    garment = Garment(
        **data.model_dump(),
        profile_id=profile.id,
    )

    db.add(garment)
    db.commit()
    db.refresh(garment)

    return garment


# Lista as peças pertencentes ao perfil autenticado.
@router.get("", response_model=GarmentList)
def list_garments(
    profile: Annotated[Profile, Depends(get_current_profile)],
    db: Annotated[Session, Depends(get_db)],
    category: str | None = None,
    item_status: str | None = Query(default=None, alias="status"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
):
    statement = select(Garment).where(Garment.profile_id == profile.id)

    if category:
        statement = statement.where(Garment.category == category)

    if item_status:
        statement = statement.where(Garment.status == item_status)

    total_statement = select(func.count()).select_from(statement.order_by(None).subquery())

    total = db.scalar(total_statement) or 0

    items = db.scalars(
        statement.order_by(Garment.created_at.desc()).offset(skip).limit(limit)
    ).all()

    return GarmentList(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
    )


# Consulta uma peça específica do perfil autenticado.
@router.get("/{garment_id}", response_model=GarmentRead)
def get_garment(
    garment_id: UUID,
    profile: Annotated[Profile, Depends(get_current_profile)],
    db: Annotated[Session, Depends(get_db)],
):
    garment = db.scalar(
        select(Garment).where(
            Garment.id == garment_id,
            Garment.profile_id == profile.id,
        )
    )

    if garment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Peça não encontrada.",
        )

    return garment


# Atualiza somente os campos enviados pelo usuário.
@router.patch("/{garment_id}", response_model=GarmentRead)
def update_garment(
    garment_id: UUID,
    data: GarmentUpdate,
    profile: Annotated[Profile, Depends(get_current_profile)],
    db: Annotated[Session, Depends(get_db)],
):
    garment = db.scalar(
        select(Garment).where(
            Garment.id == garment_id,
            Garment.profile_id == profile.id,
        )
    )

    if garment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Peça não encontrada.",
        )

    updates = data.model_dump(exclude_unset=True)

    for field, value in updates.items():
        setattr(garment, field, value)

    db.commit()
    db.refresh(garment)

    return garment


# Exclui uma peça pertencente ao perfil autenticado.
@router.delete(
    "/{garment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_garment(
    garment_id: UUID,
    profile: Annotated[Profile, Depends(get_current_profile)],
    db: Annotated[Session, Depends(get_db)],
):
    garment = db.scalar(
        select(Garment).where(
            Garment.id == garment_id,
            Garment.profile_id == profile.id,
        )
    )

    if garment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Peça não encontrada.",
        )

    db.delete(garment)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
