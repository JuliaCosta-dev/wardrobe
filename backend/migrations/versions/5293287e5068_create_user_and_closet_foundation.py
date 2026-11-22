"""create user and closet foundation

Revision ID: 5293287e5068
Revises: 44dbbd0ac597
Create Date: 2026-11-21 16:35:49.474588

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5293287e5068"
down_revision: str | Sequence[str] | None = "44dbbd0ac597"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_index("ix_users_email", table_name="users")
    op.create_unique_constraint(
        "users_email_key",
        "users",
        ["email"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "users_email_key",
        "users",
        type_="unique",
    )
    op.create_index(
        "ix_users_email",
        "users",
        ["email"],
        unique=True,
    )
