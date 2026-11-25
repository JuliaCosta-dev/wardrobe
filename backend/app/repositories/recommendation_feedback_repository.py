from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.recommendation_feedback import RecommendationFeedback


def get_by_outfit(
    db: Session,
    outfit_id: UUID,
) -> RecommendationFeedback | None:
    """
    Busca a avaliação de um look.

    A restrição UNIQUE em outfit_id garante que exista
    no máximo um registro.
    """

    statement = select(RecommendationFeedback).where(
        RecommendationFeedback.outfit_id == outfit_id,
    )

    return db.scalar(statement)


def save(
    db: Session,
    feedback: RecommendationFeedback,
) -> RecommendationFeedback:
    """
    Adiciona ou atualiza uma avaliação na sessão atual.

    O commit fica sob responsabilidade do service,
    para que a camada de negócio controle a transação.
    """

    db.add(feedback)
    db.flush()

    return feedback


def delete(
    db: Session,
    feedback: RecommendationFeedback,
) -> None:
    """Marca uma avaliação para exclusão na sessão atual."""

    db.delete(feedback)
    db.flush()
