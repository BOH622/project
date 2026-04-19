"""Provider-scope enforcement tests — the most important canonical guardrail."""
from __future__ import annotations

import uuid

import pytest

from app.models import Invitation, Project
from app.queries.scope import ScopeError, provider_scoped


def test_provider_scoped_rejects_missing_org_id() -> None:
    with pytest.raises(ScopeError):
        provider_scoped(Invitation, None)  # type: ignore[arg-type]


def test_provider_scoped_rejects_model_without_scope_column() -> None:
    # Project has no provider_org_id — it's a shared record. Caller must scope via Assignment.
    with pytest.raises(ScopeError, match="provider_org_id"):
        provider_scoped(Project, uuid.uuid4())


def test_provider_scoped_builds_filtered_query() -> None:
    org_id = uuid.uuid4()
    stmt = provider_scoped(Invitation, org_id)
    compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
    assert "provider_org_id" in compiled
    assert str(org_id) in compiled
