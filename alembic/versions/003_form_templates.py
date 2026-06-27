"""form_templates — contract Layer 6 template registry table.

Revision ID: 003
Revises: 002
Create Date: 2026-06-26

Distinct from the legacy `template` table (int PK + uploaded PDF). This is the
standards registry keyed by `form_type`, holding incident-schema field definitions and
mappings. `fields` and `field_mappings_from_incident` use sa.JSON for
consistency with migrations 001/002 and SQLite test-harness compatibility.

`form_type` is a plain VARCHAR (not a Postgres ENUM): custom jurisdictions are
registered here and are not part of the built-in FormType enum.
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
import sqlmodel

revision: str = "003"
down_revision: str | None = "002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "form_templates",
        sa.Column("template_id", sa.Uuid(), primary_key=True),
        sa.Column("form_type", sqlmodel.sql.sqltypes.AutoString, nullable=False),
        sa.Column("display_name", sqlmodel.sql.sqltypes.AutoString, nullable=False),
        sa.Column("jurisdiction", sqlmodel.sql.sqltypes.AutoString, nullable=False),
        sa.Column("agency_type", sqlmodel.sql.sqltypes.AutoString, nullable=True),
        sa.Column("fields", sa.JSON, nullable=False),
        sa.Column("field_mappings_from_incident", sa.JSON, nullable=False),
        sa.Column("source_standard", sqlmodel.sql.sqltypes.AutoString, nullable=True),
        sa.Column("pdf_template_ref", sqlmodel.sql.sqltypes.AutoString, nullable=True),
        sa.Column("version", sqlmodel.sql.sqltypes.AutoString, nullable=False),
        sa.Column("status", sqlmodel.sql.sqltypes.AutoString, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_index(
        "ix_form_templates_form_type",
        "form_templates",
        ["form_type"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_form_templates_form_type", table_name="form_templates")
    op.drop_table("form_templates")
