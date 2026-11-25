from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services.contextual_outfit_generator import (
    ContextualOutfitError,
    generate_recommendation,
)


def make_garment(
    category: str,
    *,
    color: str = "black",
    warmth: int = 2,
    favorite: bool = False,
    occasions: list[str] | None = None,
    seasons: list[str] | None = None,
):
    """Cria uma peça simples para testar o algoritmo sem banco de dados."""

    return SimpleNamespace(
        id=uuid4(),
        category=category,
        status="available",
        occasion_tags=occasions or [],
        season_tags=seasons or [],
        formality=2,
        primary_color=color,
        colors=[],
        fit_preference="regular",
        warmth_level=warmth,
        is_favorite=favorite,
    )


def test_generates_a_complete_outfit():
    garments = [
        make_garment("tops"),
        make_garment("bottoms"),
        make_garment("shoes"),
    ]

    combination, signature, score, reasons = generate_recommendation(
        garments=garments,
        used_signatures=set(),
        preferences={},
        weather={"temperature": 25},
    )

    assert len(combination) == 3
    assert signature
    assert 0 <= score <= 100
    assert {role for _, role in combination} == {
        "top",
        "bottom",
        "shoes",
    }
    assert isinstance(reasons, list)


def test_respects_preferred_colors():
    preferred_outfit = [
        make_garment("tops", color="blue"),
        make_garment("bottoms", color="black"),
        make_garment("shoes", color="black"),
    ]

    ordinary_outfit = [
        make_garment("tops", color="green"),
        make_garment("bottoms", color="black"),
        make_garment("shoes", color="black"),
    ]

    preferred_result = generate_recommendation(
        garments=preferred_outfit,
        used_signatures=set(),
        preferences={"preferred_colors": ["blue"]},
        weather={"temperature": 25},
    )

    ordinary_result = generate_recommendation(
        garments=ordinary_outfit,
        used_signatures=set(),
        preferences={"preferred_colors": ["blue"]},
        weather={"temperature": 25},
    )

    assert preferred_result[2] > ordinary_result[2]


def test_respects_preferred_occasions():
    preferred_outfit = [
        make_garment("tops", occasions=["work"]),
        make_garment("bottoms"),
        make_garment("shoes"),
    ]

    ordinary_outfit = [
        make_garment("tops", occasions=["party"]),
        make_garment("bottoms"),
        make_garment("shoes"),
    ]

    preferred_result = generate_recommendation(
        garments=preferred_outfit,
        used_signatures=set(),
        preferences={"occasions": ["work"]},
        weather={"temperature": 25},
    )

    ordinary_result = generate_recommendation(
        garments=ordinary_outfit,
        used_signatures=set(),
        preferences={"occasions": ["work"]},
        weather={"temperature": 25},
    )

    assert preferred_result[2] > ordinary_result[2]
    assert "Considera suas ocasiões preferidas." in preferred_result[3]


def test_respects_preferred_seasons():
    preferred_outfit = [
        make_garment("tops", seasons=["summer"]),
        make_garment("bottoms"),
        make_garment("shoes"),
    ]

    ordinary_outfit = [
        make_garment("tops", seasons=["winter"]),
        make_garment("bottoms"),
        make_garment("shoes"),
    ]

    preferred_result = generate_recommendation(
        garments=preferred_outfit,
        used_signatures=set(),
        preferences={"seasons": ["summer"]},
        weather={"temperature": 25},
    )

    ordinary_result = generate_recommendation(
        garments=ordinary_outfit,
        used_signatures=set(),
        preferences={"seasons": ["summer"]},
        weather={"temperature": 25},
    )

    assert preferred_result[2] > ordinary_result[2]
    assert "Considera suas estações preferidas." in preferred_result[3]


def test_does_not_repeat_used_combination():
    garments = [
        make_garment("tops"),
        make_garment("bottoms"),
        make_garment("shoes"),
    ]

    first_result = generate_recommendation(
        garments=garments,
        used_signatures=set(),
        preferences={},
        weather={"temperature": 25},
    )

    with pytest.raises(ContextualOutfitError):
        generate_recommendation(
            garments=garments,
            used_signatures={first_result[1]},
            preferences={},
            weather={"temperature": 25},
        )


def test_requires_shoes():
    garments = [
        make_garment("tops"),
        make_garment("bottoms"),
    ]

    with pytest.raises(ContextualOutfitError):
        generate_recommendation(
            garments=garments,
            used_signatures=set(),
            preferences={},
            weather={"temperature": 25},
        )


def test_filters_by_occasion():
    top = make_garment("tops", occasions=["work"])
    bottom = make_garment("bottoms")
    shoe = make_garment("shoes")

    with pytest.raises(ContextualOutfitError):
        generate_recommendation(
            garments=[top, bottom, shoe],
            used_signatures=set(),
            preferences={},
            weather={"temperature": 25},
            occasion="party",
        )


def test_avoided_colors_reduce_score():
    garments = [
        make_garment("tops", color="red"),
        make_garment("bottoms", color="black"),
        make_garment("shoes", color="black"),
    ]

    ordinary = generate_recommendation(
        garments=garments,
        used_signatures=set(),
        preferences={},
        weather={"temperature": 25},
    )

    avoided = generate_recommendation(
        garments=garments,
        used_signatures=set(),
        preferences={"avoided_colors": ["red"]},
        weather={"temperature": 25},
    )

    assert avoided[2] < ordinary[2]
