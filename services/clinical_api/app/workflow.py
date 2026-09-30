"""Authoritative clinical workflow rules shared by API actions and tests."""

from __future__ import annotations

from typing import Literal


CaseStatusValue = Literal["draft", "draft_reopened", "ready_for_signoff", "finalized"]
CaseActionValue = Literal["preview", "mark_ready_for_signoff", "finalize", "return_to_draft", "reopen"]

ADMIN_ROLES = frozenset({"operations_admin", "workspace_admin"})


def ensure_case_action_allowed(
    *,
    action: CaseActionValue,
    status: CaseStatusValue,
    role: str | None,
    reopen_reason: str | None = None,
) -> None:
    """Raise a clear error when an action would violate clinical workflow rules.

    These checks deliberately run server-side. The PWA may hide unavailable
    controls, but it cannot grant permission or create a state transition.
    """
    if action == "preview":
        if status == "finalized":
            raise ValueError("Finalized cases must be reopened before a new preview can be generated.")
        return
    if action == "mark_ready_for_signoff":
        if status not in {"draft", "draft_reopened"}:
            raise ValueError("Only a draft or reopened case can be marked ready for sign-off.")
        return
    if action == "finalize":
        if role != "endoscopist":
            raise PermissionError("Only an endoscopist can finalize a report.")
        if status != "ready_for_signoff":
            raise ValueError("A case must be marked ready for sign-off before it can be finalized.")
        return
    if action == "return_to_draft":
        if role not in ADMIN_ROLES:
            raise PermissionError("Only a clinical operations admin can return a case to draft.")
        if status == "finalized":
            raise ValueError("Finalized cases must be reopened instead of returned to draft directly.")
        if status not in {"ready_for_signoff", "draft_reopened"}:
            raise ValueError("Only a ready or reopened case can be returned to draft.")
        return
    if action == "reopen":
        if role not in ADMIN_ROLES:
            raise PermissionError("Only a clinical operations admin can reopen a finalized report.")
        if status != "finalized":
            raise ValueError("Only finalized cases can be reopened.")
        if not (reopen_reason or "").strip():
            raise ValueError("Enter a reopen reason before reopening a finalized case.")
        return
    raise ValueError(f"Unsupported case action: {action}")
