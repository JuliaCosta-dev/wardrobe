from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.outfit import Outfit
from app.models.profile import Profile
from app.models.recommendation_feedback import RecommendationFeedback
from app.repositories import recommendation_feedback_repository as repository
from app.schemas.recommendation_feedback import RecommendationFeedbackCreate


class RecommendationFeedbackError(Exception):
    """Erro de negócio relacionado à avaliação de recomendações."""


def _get_recommended_outfit(
    db: Session,
    profile_id: UUID,
    outfit_id: UUID,
) -> Outfit:
    """
    Confirma que o look existe, pertence ao perfil autenticado
    e foi criado pelo motor de recomendações contextuais.

    A consulta sempre filtra por profile_id para impedir
    acesso a looks de outros usuários.
    """

    statement = select(Outfit).where(
        Outfit.id == outfit_id,
        Outfit.profile_id == profile_id,
        Outfit.recommendation_score.is_not(None),
    )

    outfit = db.scalar(statement)

    if outfit is None:
        raise RecommendationFeedbackError("Recomendação não encontrada.")

    return outfit


def create_or_update_feedback(
    db: Session,
    profile: Profile,
    outfit_id: UUID,
    data: RecommendationFeedbackCreate,
) -> RecommendationFeedback:
    """
    Registra uma avaliação ou atualiza a avaliação existente.

    O bloqueio da linha do look evita que duas requisições
    simultâneas do mesmo look criem avaliações duplicadas.

    O UNIQUE no banco continua sendo a proteção definitiva.
    """

    try:
        # Verifica a propriedade do look e bloqueia sua linha
        # até o fim da transação.
        statement = (
            select(Outfit)
            .where(
                Outfit.id == outfit_id,
                Outfit.profile_id == profile.id,
                Outfit.recommendation_score.is_not(None),
            )
            .with_for_update()
        )

        outfit = db.scalar(statement)

        if outfit is None:
            raise RecommendationFeedbackError("Recomendação não encontrada.")

        feedback = repository.get_by_outfit(
            db=db,
            outfit_id=outfit.id,
        )

        if feedback is None:
            feedback = RecommendationFeedback(
                profile_id=profile.id,
                outfit_id=outfit.id,
                rating=data.rating,
                reason=data.reason,
                comment=data.comment,
            )
        else:
            # Reavaliação substitui os dados anteriores.
            feedback.rating = data.rating
            feedback.reason = data.reason
            feedback.comment = data.comment

        repository.save(db, feedback)

        db.commit()
        db.refresh(feedback)

        return feedback

    except RecommendationFeedbackError:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        raise


def get_feedback(
    db: Session,
    profile_id: UUID,
    outfit_id: UUID,
) -> RecommendationFeedback | None:
    """
    Consulta a avaliação de um look do perfil.

    A propriedade do look é validada antes de devolver
    qualquer informação de feedback.
    """

    _get_recommended_outfit(
        db=db,
        profile_id=profile_id,
        outfit_id=outfit_id,
    )

    feedback = repository.get_by_outfit(
        db=db,
        outfit_id=outfit_id,
    )

    # Defesa adicional contra inconsistência de propriedade.
    if feedback is not None and feedback.profile_id != profile_id:
        return None

    return feedback


def delete_feedback(
    db: Session,
    profile_id: UUID,
    outfit_id: UUID,
) -> None:
    """Remove a avaliação do usuário para aquele look."""

    try:
        _get_recommended_outfit(
            db=db,
            profile_id=profile_id,
            outfit_id=outfit_id,
        )

        feedback = repository.get_by_outfit(
            db=db,
            outfit_id=outfit_id,
        )

        if feedback is None or feedback.profile_id != profile_id:
            raise RecommendationFeedbackError("Avaliação não encontrada.")

        repository.delete(db, feedback)
        db.commit()

    except RecommendationFeedbackError:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        raise
