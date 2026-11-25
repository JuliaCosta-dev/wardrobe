from itertools import islice, product
from typing import Any

from app.models.garment import Garment
from app.services.outfit_generator import create_signature

# Limite para evitar explosão combinatória quando o closet for grande.
MAX_BASE_COMBINATIONS = 5000

OPTIONAL_CATEGORIES = {
    "bags": "bag",
    "accessories": "accessory",
    "jewelry": "jewelry",
    "hair_accessories": "hair_accessory",
}

FORMALITY_LEVELS = {
    "very_casual": 1,
    "casual": 2,
    "smart_casual": 3,
    "formal": 4,
}


class ContextualOutfitError(Exception):
    """Não foi possível montar uma recomendação válida."""


def _matches_context(
    garment: Garment,
    occasion: str | None,
    season: str | None,
    formality: int | None,
) -> bool:
    """Aplica os filtros solicitados sem excluir peças sem metadados."""

    if occasion and garment.occasion_tags:
        tags = {tag.casefold() for tag in garment.occasion_tags}

        if occasion.casefold() not in tags:
            return False

    if season and garment.season_tags:
        tags = {tag.casefold() for tag in garment.season_tags}

        if season.casefold() not in tags:
            return False

    if formality is not None and garment.formality is not None:
        if abs(garment.formality - formality) > 1:
            return False

    return True


def _warmth_target(temperature: float) -> int:
    """
    Converte a temperatura em um nível de aquecimento desejado.

    Esta é uma heurística inicial, não uma medição científica
    de conforto térmico.
    """

    if temperature < 12:
        return 5

    if temperature < 18:
        return 4

    if temperature < 24:
        return 3

    if temperature < 29:
        return 2

    return 1


def _normalized_colors(garment: Garment) -> set[str]:
    """Retorna as cores conhecidas da peça em formato normalizado."""

    colors = set()

    if garment.primary_color:
        colors.add(garment.primary_color.strip().casefold())

    for color in garment.colors or []:
        if isinstance(color, str) and color.strip():
            colors.add(color.strip().casefold())

    return colors


def _score_garment(
    garment: Garment,
    preferences: dict[str, Any],
    weather: dict[str, Any],
) -> tuple[float, list[str]]:
    """Calcula a contribuição de uma peça para a pontuação do look."""

    score = 0.0
    reasons = []

    colors = _normalized_colors(garment)

    preferred_colors = {
        value.casefold()
        for value in preferences.get("preferred_colors", [])
        if isinstance(value, str)
    }

    avoided_colors = {
        value.casefold()
        for value in preferences.get("avoided_colors", [])
        if isinstance(value, str)
    }

    if colors & preferred_colors:
        score += 4
        reasons.append("Inclui uma das suas cores preferidas.")

    if colors & avoided_colors:
        score -= 8
        reasons.append("Inclui uma cor que você marcou como evitada.")

    # Preferências de ocasiões.
    preferred_occasions = set(preferences.get("occasions", []))
    garment_occasions = set(garment.occasion_tags or [])

    if preferred_occasions & garment_occasions:
        score += 2
        reasons.append("Considera suas ocasiões preferidas.")

    # Preferências de estações.
    preferred_seasons = set(preferences.get("seasons", []))
    garment_seasons = set(garment.season_tags or [])

    if preferred_seasons & garment_seasons:
        score += 2
        reasons.append("Considera suas estações preferidas.")

    preferred_fits = set(preferences.get("fit_preferences", []))

    if garment.fit_preference and garment.fit_preference in preferred_fits:
        score += 2
        reasons.append("Considera sua preferência de caimento.")

    preferred_formality = {
        FORMALITY_LEVELS[value]
        for value in preferences.get("formality_levels", [])
        if value in FORMALITY_LEVELS
    }

    if garment.formality is not None and garment.formality in preferred_formality:
        score += 3
        reasons.append("Está alinhada à formalidade que você prefere.")

    temperature = weather.get("temperature")

    if isinstance(temperature, (int, float)) and garment.warmth_level is not None:
        target = _warmth_target(float(temperature))
        difference = abs(garment.warmth_level - target)

        warmth_score = max(-8, 8 - (difference * 4))
        score += warmth_score

    if garment.is_favorite:
        score += 2
        reasons.append("Inclui uma peça marcada como favorita.")

    return score, reasons


def _build_base_combinations(
    garments: list[Garment],
) -> list[list[tuple[Garment, str]]]:
    """Monta as estruturas obrigatórias de um look."""

    by_category: dict[str, list[Garment]] = {}

    for garment in garments:
        by_category.setdefault(garment.category, []).append(garment)

    shoes = by_category.get("shoes", [])

    if not shoes:
        raise ContextualOutfitError(
            "Cadastre pelo menos um calçado disponível para receber recomendações."
        )

    combinations = []

    tops = by_category.get("tops", [])
    bottoms = by_category.get("bottoms", [])
    one_pieces = by_category.get("one_piece", [])

    if tops and bottoms:
        for top, bottom, shoe in islice(
            product(tops, bottoms, shoes),
            MAX_BASE_COMBINATIONS,
        ):
            combinations.append(
                [
                    (top, "top"),
                    (bottom, "bottom"),
                    (shoe, "shoes"),
                ]
            )

    if one_pieces:
        remaining = max(
            0,
            MAX_BASE_COMBINATIONS - len(combinations),
        )

        for one_piece, shoe in islice(
            product(one_pieces, shoes),
            remaining,
        ):
            combinations.append(
                [
                    (one_piece, "one_piece"),
                    (shoe, "shoes"),
                ]
            )

    if not combinations:
        raise ContextualOutfitError("Seu closet não possui peças suficientes para montar um look.")

    return combinations


def _add_optional_items(
    combination: list[tuple[Garment, str]],
    garments: list[Garment],
    preferences: dict[str, Any],
    weather: dict[str, Any],
) -> list[tuple[Garment, str]]:
    """
    Adiciona no máximo uma peça de cada categoria complementar.

    A escolha é feita por pontuação, em vez de uma decisão aleatória.
    """

    result = list(combination)
    selected_ids = {garment.id for garment, _ in result}

    for category, role in OPTIONAL_CATEGORIES.items():
        options = [
            garment
            for garment in garments
            if garment.category == category and garment.id not in selected_ids
        ]

        if not options:
            continue

        best_option = max(
            options,
            key=lambda garment: _score_garment(
                garment,
                preferences,
                weather,
            )[0],
        )

        result.append((best_option, role))
        selected_ids.add(best_option.id)

    return result


def generate_recommendation(
    garments: list[Garment],
    used_signatures: set[str],
    preferences: dict[str, Any],
    weather: dict[str, Any],
    occasion: str | None = None,
    season: str | None = None,
    formality: int | None = None,
) -> tuple[list[tuple[Garment, str]], str, float, list[str]]:
    """
    Seleciona a combinação inédita de maior pontuação.

    O cliente não escolhe IDs de peças.
    O algoritmo trabalha exclusivamente com peças do perfil autenticado.
    """

    eligible = [
        garment
        for garment in garments
        if garment.status == "available"
        and _matches_context(
            garment,
            occasion,
            season,
            formality,
        )
    ]

    base_combinations = _build_base_combinations(eligible)

    ranked = []

    for base in base_combinations:
        combination = _add_optional_items(
            combination=base,
            garments=eligible,
            preferences=preferences,
            weather=weather,
        )

        signature = create_signature([garment.id for garment, _ in combination])

        if signature in used_signatures:
            continue

        total_score = 50.0
        reasons = []

        for garment, _role in combination:
            score, garment_reasons = _score_garment(
                garment,
                preferences,
                weather,
            )

            total_score += score
            reasons.extend(garment_reasons)

        temperature = weather.get("temperature")

        if isinstance(temperature, (int, float)):
            if temperature >= 29:
                reasons.append("Considera a temperatura elevada.")
            elif temperature < 18:
                reasons.append("Considera a temperatura mais baixa.")

        precipitation = weather.get("precipitation_probability")

        if isinstance(precipitation, (int, float)) and precipitation >= 40:
            reasons.append("Há possibilidade de chuva. Considere levar um guarda-chuva.")

        if not reasons:
            reasons.append("Combinação compatível com as peças disponíveis.")

        # Remove justificativas repetidas sem alterar a ordem.
        unique_reasons = list(dict.fromkeys(reasons))

        ranked.append(
            (
                combination,
                signature,
                round(max(0.0, min(100.0, total_score)), 2),
                unique_reasons,
            )
        )

    if not ranked:
        raise ContextualOutfitError(
            "Não encontrei uma combinação inédita. "
            "Adicione peças ao closet ou aguarde o vencimento "
            "dos looks anteriores."
        )

    ranked.sort(
        key=lambda item: (
            item[2],
            item[1],
        ),
        reverse=True,
    )

    return ranked[0]
