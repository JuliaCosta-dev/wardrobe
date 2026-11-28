"""allow permanent outfit history

Revision ID: 11a3b7c9d201
Revises: d1b0fe54f910
"""

from collections.abc import Sequence

from alembic import op

revision: str = "11a3b7c9d201"
down_revision: str | Sequence[str] | None = "d1b0fe54f910"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """
    Remove a unicidade permanente da assinatura.

    A regra de não repetição continua sendo controlada por
    expires_at e pelo gerador de combinações.
    """

    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'uq_outfits_profile_signature'
                  AND conrelid = 'outfits'::regclass
            ) THEN
                ALTER TABLE outfits
                DROP CONSTRAINT uq_outfits_profile_signature;
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    """
    Restaura a restrição única.

    Atenção: o downgrade poderá falhar se existirem combinações
    repetidas no histórico após esta migração.
    """

    op.create_unique_constraint(
        "uq_outfits_profile_signature",
        "outfits",
        ["profile_id", "signature"],
    )
