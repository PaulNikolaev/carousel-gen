"""init carousel slide design

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2025-03-04

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    source_type_enum = postgresql.ENUM(
        "text", "video", "links", name="source_type_enum", create_type=True
    )
    source_type_enum.create(op.get_context().bind, checkfirst=True)
    source_type_enum_col = postgresql.ENUM(
        "text", "video", "links", name="source_type_enum", create_type=False
    )

    carousel_status_enum = postgresql.ENUM(
        "draft", "generating", "ready", "failed",
        name="carousel_status_enum", create_type=True
    )
    carousel_status_enum.create(op.get_context().bind, checkfirst=True)
    carousel_status_enum_col = postgresql.ENUM(
        "draft", "generating", "ready", "failed",
        name="carousel_status_enum", create_type=False
    )

    op.create_table(
        "carousels",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("source_type", source_type_enum_col, nullable=False),
        sa.Column("source_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("format", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("status", carousel_status_enum_col, nullable=False, server_default=sa.text("'draft'::carousel_status_enum")),
        sa.Column("language", sa.String(length=16), nullable=False, server_default="ru"),
        sa.Column("slides_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "slides",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("carousel_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=1024), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("footer", sa.String(length=512), nullable=False),
        sa.Column("design_overrides", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.ForeignKeyConstraint(["carousel_id"], ["carousels.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_slides_carousel_id"), "slides", ["carousel_id"], unique=False)
    op.create_unique_constraint("uq_slides_carousel_order", "slides", ["carousel_id", "order"])

    template_enum = postgresql.ENUM(
        "classic", "bold", "minimal", name="template_enum", create_type=True
    )
    template_enum.create(op.get_context().bind, checkfirst=True)
    template_enum_col = postgresql.ENUM(
        "classic", "bold", "minimal", name="template_enum", create_type=False
    )

    background_type_enum = postgresql.ENUM(
        "color", "image", name="background_type_enum", create_type=True
    )
    background_type_enum.create(op.get_context().bind, checkfirst=True)
    background_type_enum_col = postgresql.ENUM(
        "color", "image", name="background_type_enum", create_type=False
    )

    op.create_table(
        "carousel_designs",
        sa.Column("carousel_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("template", template_enum_col, nullable=False),
        sa.Column("background_type", background_type_enum_col, nullable=False),
        sa.Column("background_value", sa.String(length=512), nullable=False, server_default=""),
        sa.Column("overlay", sa.Float(), nullable=False, server_default=sa.text("0.0")),
        sa.Column("padding", sa.Integer(), nullable=False, server_default=sa.text("24")),
        sa.Column("alignment_h", sa.String(length=32), nullable=False, server_default="center"),
        sa.Column("alignment_v", sa.String(length=32), nullable=False, server_default="center"),
        sa.Column("header_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("header_text", sa.String(length=512), nullable=False, server_default=""),
        sa.Column("footer_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("footer_text", sa.String(length=512), nullable=False, server_default=""),
        sa.ForeignKeyConstraint(["carousel_id"], ["carousels.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("carousel_id"),
    )


def downgrade() -> None:
    op.drop_table("carousel_designs")
    op.drop_index(op.f("ix_slides_carousel_id"), table_name="slides")
    op.drop_constraint("uq_slides_carousel_order", "slides", type_="unique")
    op.drop_table("slides")
    op.drop_table("carousels")

    op.execute("DROP TYPE IF EXISTS background_type_enum")
    op.execute("DROP TYPE IF EXISTS template_enum")
    op.execute("DROP TYPE IF EXISTS carousel_status_enum")
    op.execute("DROP TYPE IF EXISTS source_type_enum")
