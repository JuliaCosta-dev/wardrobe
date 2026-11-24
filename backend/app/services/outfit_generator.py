from hashlib import sha256
from random import SystemRandom
from uuid import UUID

from app.models.garment import Garment

# Quantidade máxima de tentativas para encontrar uma combinação
# que ainda não esteja no histórico.
MAX_GENERATION_ATTEMPTS = 300

# Categorias que podem complementar o look.
# Cada uma pode contribuir com, no máximo, uma peça.
OPTIONAL_CATEGORIES = {
    "bags": "bag",
    "accessories": "accessory",
    "jewelry": "jewelry",
    "hair_accessories": "hair_accessory",
}


class OutfitCombinationError(Exception):
    """Não foi possível montar uma combinação válida."""


def create_signature(garment_ids: list[UUID]) -> str:
    """
    Cria uma assinatura estável para uma combinação.

    Ordenar os IDs antes de calcular o hash garante que
    a mesma combinação tenha a mesma assinatura,
    independentemente da ordem das peças.
    """

    normalized_ids = sorted(str(garment_id) for garment_id in garment_ids)

    content = "|".join(normalized_ids)

    return sha256(content.encode("utf-8")).hexdigest()


def matches_context(
    garment: Garment,
    occasion: str | None,
    season: str | None,
    formality: int | None,
) -> bool:
    """
    Verifica se uma peça atende aos filtros solicitados.

    Uma peça sem informação de ocasião ou estação continua
    elegível, porque não temos dados suficientes para descartá-la.

    A formalidade aceita uma diferença de até um nível.
    """

    if occasion:
        allowed_occasions = {value.casefold() for value in garment.occasion_tags}

        if allowed_occasions and occasion.casefold() not in allowed_occasions:
            return False

    if season:
        allowed_seasons = {value.casefold() for value in garment.season_tags}

        if allowed_seasons and season.casefold() not in allowed_seasons:
            return False

    if formality is not None and garment.formality is not None:
        if abs(garment.formality - formality) > 1:
            return False

    return True


def generate_candidate(
    garments: list[Garment],
    occasion: str | None,
    season: str | None,
    formality: int | None,
    rng: SystemRandom,
) -> list[tuple[Garment, str]]:
    """
    Monta uma combinação candidata.

    Estruturas permitidas:
    - top + bottom + shoes
    - one_piece + shoes

    Complementos são opcionais.
    """

    eligible = [
        garment
        for garment in garments
        if matches_context(
            garment=garment,
            occasion=occasion,
            season=season,
            formality=formality,
        )
    ]

    by_category: dict[str, list[Garment]] = {}

    for garment in eligible:
        by_category.setdefault(garment.category, []).append(garment)

    shoes = by_category.get("shoes", [])

    # Sem calçados não geramos uma combinação completa.
    if not shoes:
        raise OutfitCombinationError("Cadastre pelo menos um calçado disponível para gerar looks.")

    # Existem duas estruturas possíveis para o look.
    structures = []

    if by_category.get("tops") and by_category.get("bottoms"):
        structures.append("separates")

    if by_category.get("one_piece"):
        structures.append("one_piece")

    if not structures:
        raise OutfitCombinationError(
            "Seu closet precisa ter uma parte de cima e uma parte "
            "de baixo, ou uma peça única, além de um calçado."
        )

    selected_structure = rng.choice(structures)

    selected: list[tuple[Garment, str]] = []

    if selected_structure == "separates":
        selected.append((rng.choice(by_category["tops"]), "top"))
        selected.append((rng.choice(by_category["bottoms"]), "bottom"))
    else:
        selected.append((rng.choice(by_category["one_piece"]), "one_piece"))

    selected.append((rng.choice(shoes), "shoes"))

    # Complementos não são obrigatórios.
    # Se houver peças disponíveis, o algoritmo decide
    # aleatoriamente se cada categoria será utilizada.
    for category, role in OPTIONAL_CATEGORIES.items():
        options = by_category.get(category, [])

        if options and rng.choice((True, False)):
            selected.append((rng.choice(options), role))

    return selected


def generate_unique_combination(
    garments: list[Garment],
    used_signatures: set[str],
    occasion: str | None,
    season: str | None,
    formality: int | None,
) -> tuple[list[tuple[Garment, str]], str]:
    """
    Procura uma combinação que ainda não tenha sido utilizada.

    O algoritmo não recebe IDs de peças enviados pelo cliente.
    Todas as peças são selecionadas a partir do closet autenticado.
    """

    rng = SystemRandom()

    # Verifica previamente se existe alguma estrutura básica possível.
    eligible = [
        garment
        for garment in garments
        if matches_context(
            garment,
            occasion,
            season,
            formality,
        )
    ]

    categories = {garment.category for garment in eligible}

    has_separates = {"tops", "bottoms", "shoes"}.issubset(categories)
    has_one_piece = {"one_piece", "shoes"}.issubset(categories)

    if not has_separates and not has_one_piece:
        raise OutfitCombinationError(
            "Não existem peças suficientes e compatíveis para gerar um look."
        )

    for _ in range(MAX_GENERATION_ATTEMPTS):
        candidate = generate_candidate(
            garments=garments,
            occasion=occasion,
            season=season,
            formality=formality,
            rng=rng,
        )

        signature = create_signature([garment.id for garment, _ in candidate])

        if signature not in used_signatures:
            return candidate, signature

    raise OutfitCombinationError(
        "Não encontrei uma combinação inédita com as peças disponíveis. "
        "Adicione novas peças ao closet ou tente novamente após o período "
        "de validade dos looks anteriores."
    )
