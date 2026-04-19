"""initial schema — all 22 canonical objects

Revision ID: 0001_initial
Revises:
Create Date: 2026-04-19

Bootstrap migration: creates every table defined in app.models via
Base.metadata.create_all. Subsequent revisions will use autogenerate.

Rationale: running autogenerate on a fresh repo requires a live DB,
which the plan cannot assume during v0 scaffold. This single-pass
bootstrap is functionally equivalent and trivially replaceable once a
dev DB exists.
"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op

from app.models import Base

revision: str = "0001_initial"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
