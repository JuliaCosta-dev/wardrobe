"""restore outfit usages migration

Revision ID: d1b0fe54f910
Revises: 91d91d251a14
"""

from collections.abc import Sequence

from alembic import op

revision: str = "d1b0fe54f910"
down_revision: str | Sequence[str] | None = "91d91d251a14"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """
    Restaura a migração que criou outfit_usages.

    A tabela já existe no banco atual. O IF NOT EXISTS também
    permite executar esta revisão em uma instalação nova.
    """

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS outfit_usages (
            id UUID NOT NULL PRIMARY KEY,
            outfit_id UUID NOT NULL,
            used_at TIMESTAMP WITH TIME ZONE NOT NULL,
            notes VARCHAR(500),
            created_at TIMESTAMP WITH TIME ZONE
                NOT NULL DEFAULT now(),
            CONSTRAINT fk_outfit_usages_outfit_id
                FOREIGN KEY (outfit_id)
                REFERENCES outfits (id)
                ON DELETE CASCADE
        )
        """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_outfit_usages_outfit_used_at
        ON outfit_usages (outfit_id, used_at)
        """
    )


def downgrade() -> None:
    """
    Não remove a tabela.

    Esta revisão é uma restauração de histórico de migrações.
    Remover a tabela poderia destruir dados reais já existentes.
    """
    pass
