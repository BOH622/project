"""Provider-scope enforcement — every read path for provider-owned data goes through here.

The canonical contract: any function producing provider-visible data MUST take a
`provider_org_id` argument and filter by it. This module gives us a chokepoint that
refuses to build a query without one, so drift is caught at type-check and test time.
"""
from __future__ import annotations

import uuid
from typing import TypeVar

from sqlalchemy import ColumnElement, Select, select
from sqlalchemy.orm import DeclarativeBase

T = TypeVar("T", bound=DeclarativeBase)


class ScopeError(Exception):
    """Raised when provider-scope enforcement is violated."""


def provider_scoped(
    model: type[T],
    provider_org_id: uuid.UUID,
    scope_column: str = "provider_org_id",
) -> Select[tuple[T]]:
    """Build a SELECT that is already filtered by provider_org_id.

    Every provider-facing query should originate here rather than a naked `select()`.
    """
    if provider_org_id is None:
        raise ScopeError("provider_org_id is required for provider-scoped queries")
    if not hasattr(model, scope_column):
        raise ScopeError(
            f"{model.__name__} has no {scope_column} column — cannot apply provider scope. "
            "Join through an Assignment or explicitly widen the scope at the caller."
        )
    col: ColumnElement = getattr(model, scope_column)
    return select(model).where(col == provider_org_id)
