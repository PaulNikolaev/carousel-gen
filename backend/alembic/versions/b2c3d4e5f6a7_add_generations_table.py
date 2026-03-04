"""add generations table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2025-03-04

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    generation_status_enum = postgresql.ENUM(
        "queued", "running", "done", "failed",
        name="generation_status_enum", create_type=True
    )
    generation_status_enum.create(op.get_bind(), checkfirst=True)
    generation_status_enum_col = postgresql.ENUM(
        "queued", "running", "done", "failed",
        name="generation_status_enum", create_type=False
    )

    op.create_table(
        "generations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("carousel_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", generation_status_enum_col, nullable=False, server_default=sa.text("'queued'::generation_status_enum")),
        sa.Column("tokens_estimate", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("tokens_used", sa.Integer(), nullable=True),
        sa.Column("result", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("attempt", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["carousel_id"], ["carousels.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_generations_carousel_id"), "generations", ["carousel_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_generations_carousel_id"), table_name="generations")
    op.drop_table("generations")
    op.execute("DROP TYPE IF EXISTS generation_status_enum")
