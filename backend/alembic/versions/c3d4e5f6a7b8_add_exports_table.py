"""add exports table

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2025-03-05

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    export_status_enum = postgresql.ENUM(
        "pending", "running", "done", "failed",
        name="export_status_enum", create_type=True,
    )
    export_status_enum.create(op.get_bind(), checkfirst=True)
    export_status_enum_col = postgresql.ENUM(
        "pending", "running", "done", "failed",
        name="export_status_enum", create_type=False,
    )

    op.create_table(
        "exports",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("carousel_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", export_status_enum_col, nullable=False, server_default=sa.text("'pending'::export_status_enum")),
        sa.Column("s3_key", sa.String(length=512), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["carousel_id"], ["carousels.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_exports_carousel_id"), "exports", ["carousel_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_exports_carousel_id"), table_name="exports")
    op.drop_table("exports")
    op.execute("DROP TYPE IF EXISTS export_status_enum")
