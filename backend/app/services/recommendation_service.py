from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.models.outfit import Outfit
from app.models.profile import Profile
from app.repositories import outfit_repository
from app.schemas.recommendations import OutfitRecommendationRequest
from app.schemas.weather import WeatherRead
from app.services import contextual_outfit_generator, weather_service

OUTFIT_RETENTION_DAYS = 30


class RecommendationError(Exception):
    """Erro de negócio durante a recomendação."""


def recommend_outfit(
    db: Session,
    profile: Profile,
    request: OutfitRecommendationRequest,
) -> tuple[Outfit, WeatherRead]:
    """
    Gera e persiste a melhor recomendação contextual.

    A previsão é consultada antes do bloqueio do perfil para evitar
    manter uma transação de banco aberta durante uma chamada HTTP.

    Em seguida:
    - verifica se as recomendações estão habilitadas;
    - bloqueia o perfil;
    - remove looks expirados;
    - busca peças disponíveis;
    - consulta combinações já utilizadas;
    - calcula a recomendação;
    - persiste o look e seus itens.
    """

    weather = weather_service.get_weather(
        db=db,
        profile=profile,
    )

    # Utiliza as preferências já armazenadas no perfil.
    preferences = profile.preferences or {}

    # Respeita a configuração de recomendações do usuário.
    if not preferences.get("recommendations_enabled", True):
        raise RecommendationError("As recomendações estão desativadas nas suas preferências.")

    now = datetime.now(UTC)

    try:
        locked_profile = outfit_repository.lock_profile(
            db,
            profile.id,
        )

        if locked_profile is None:
            raise RecommendationError("Perfil não encontrado.")

        outfit_repository.delete_expired(
            db=db,
            profile_id=profile.id,
            now=now,
        )

        garments = outfit_repository.list_available_garments(
            db=db,
            profile_id=profile.id,
        )

        used_signatures = outfit_repository.list_recent_signatures(
            db=db,
            profile_id=profile.id,
            now=now,
        )

        weather_data = weather.model_dump(mode="json")

        try:
            (
                combination,
                signature,
                score,
                reasons,
            ) = contextual_outfit_generator.generate_recommendation(
                garments=garments,
                used_signatures=used_signatures,
                preferences=preferences,
                weather=weather_data,
                occasion=request.occasion,
                season=request.season,
                formality=request.formality,
            )

        except contextual_outfit_generator.ContextualOutfitError as error:
            # Mantém a limpeza dos looks expirados mesmo se não houver
            # uma nova combinação disponível.
            db.commit()
            raise RecommendationError(str(error)) from None

        outfit = Outfit(
            profile_id=profile.id,
            occasion=request.occasion,
            season=request.season,
            formality=request.formality,
            signature=signature,
            generated_at=now,
            expires_at=now + timedelta(days=OUTFIT_RETENTION_DAYS),
            recommendation_score=score,
            recommendation_reasons=reasons,
            weather_snapshot=weather_data,
        )

        outfit_repository.save_outfit(
            db=db,
            outfit=outfit,
            garment_roles=combination,
        )

        db.commit()

        saved_outfit = outfit_repository.get_by_id(
            db=db,
            outfit_id=outfit.id,
            profile_id=profile.id,
        )

        if saved_outfit is None:
            raise RecommendationError("A recomendação foi salva, mas não pôde ser recuperada.")

        return saved_outfit, weather

    except RecommendationError:
        raise

    except Exception:
        db.rollback()
        raise
