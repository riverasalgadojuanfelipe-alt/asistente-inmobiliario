"""add latitud longitud to propiedades

Revision ID: 02bc2f6ffe27
Revises: b6bb0f966528
Create Date: 2026-09-27 15:40:20.294787

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '02bc2f6ffe27'
down_revision: Union[str, None] = 'b6bb0f966528'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "propiedades",
        sa.Column("latitud", sa.Numeric(precision=10, scale=7), nullable=True),
    )
    op.add_column(
        "propiedades",
        sa.Column("longitud", sa.Numeric(precision=10, scale=7), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("propiedades", "longitud")
    op.drop_column("propiedades", "latitud")
