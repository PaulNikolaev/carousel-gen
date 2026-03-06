"""add design typography columns

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2025-03-06

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "carousel_designs",
        sa.Column("font_size", sa.Integer(), nullable=False, server_default=sa.text("16")),
    )
    op.add_column(
        "carousel_designs",
        sa.Column(
            "font_family",
            sa.String(length=128),
            nullable=False,
            server_default=sa.text("'system-ui'"),
        ),
    )
    op.add_column(
        "carousel_designs",
        sa.Column(
            "font_weight",
            sa.String(length=16),
            nullable=False,
            server_default=sa.text("'normal'"),
        ),
    )
    op.add_column(
        "carousel_designs",
        sa.Column(
            "font_style",
            sa.String(length=16),
            nullable=False,
            server_default=sa.text("'normal'"),
        ),
    )


def downgrade() -> None:
    op.drop_column("carousel_designs", "font_style")
    op.drop_column("carousel_designs", "font_weight")
    op.drop_column("carousel_designs", "font_family")
    op.drop_column("carousel_designs", "font_size")
