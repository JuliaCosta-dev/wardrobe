"""add outfit favorites

Revision ID: 91d91d251a14
Revises: 5a8554aa6691
Create Date: 2026-11-25 16:36:34.531465
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "91d91d251a14"
down_revision: str | Sequence[str] | None = "5a8554aa6691"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "outfits",
        sa.Column(
            "is_favorite",
            sa.Boolean(),
            server_default="false",
            nullable=False,
        ),
    )

    op.create_index(
        "ix_outfits_profile_favorite_generated",
        "outfits",
        ["profile_id", "is_favorite", "generated_at"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index(
        "ix_outfits_profile_favorite_generated",
        table_name="outfits",
    )

    op.drop_column("outfits", "is_favorite")
