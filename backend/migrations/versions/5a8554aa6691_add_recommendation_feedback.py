"""add recommendation feedback

Revision ID: 5a8554aa6691
Revises: 66c0a6ccba9e
Create Date: 2026-11-25 14:30:45.162002

"""

from collections.abc import Sequence
from textwrap import dedent

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5a8554aa6691"
down_revision: str | Sequence[str] | None = "66c0a6ccba9e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        "recommendation_feedback",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("profile_id", sa.Uuid(), nullable=False),
        sa.Column("outfit_id", sa.Uuid(), nullable=False),
        sa.Column("rating", sa.String(length=10), nullable=False),
        sa.Column("reason", sa.String(length=40), nullable=True),
        sa.Column("comment", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            dedent(
                """
                reason IS NULL OR reason IN (
                    'liked_style',
                    'comfortable',
                    'matched_weather',
                    'not_my_style',
                    'weather_mismatch',
                    'disliked_items',
                    'other'
                )
                """
            ).strip(),
            name="ck_recommendation_feedback_reason",
        ),
        sa.CheckConstraint(
            "rating IN ('positive', 'negative')",
            name="ck_recommendation_feedback_rating",
        ),
        sa.ForeignKeyConstraint(
            ["outfit_id"],
            ["outfits.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["profile_id"],
            ["profiles.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("outfit_id"),
    )

    op.create_index(
        "ix_recommendation_feedback_profile_created",
        "recommendation_feedback",
        ["profile_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index(
        "ix_recommendation_feedback_profile_created",
        table_name="recommendation_feedback",
    )
    op.drop_table("recommendation_feedback")
