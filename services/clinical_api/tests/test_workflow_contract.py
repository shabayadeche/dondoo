from __future__ import annotations

import unittest

from app.workflow import ensure_case_action_allowed


class ClinicalWorkflowContractTests(unittest.TestCase):
    def test_only_draft_states_can_be_marked_ready(self) -> None:
        ensure_case_action_allowed(action="mark_ready_for_signoff", status="draft", role="nurse")
        ensure_case_action_allowed(action="mark_ready_for_signoff", status="draft_reopened", role="operations_admin")
        with self.assertRaisesRegex(ValueError, "Only a draft or reopened"):
            ensure_case_action_allowed(action="mark_ready_for_signoff", status="finalized", role="endoscopist")

    def test_finalize_requires_endoscopist_and_ready_status(self) -> None:
        ensure_case_action_allowed(action="finalize", status="ready_for_signoff", role="endoscopist")
        with self.assertRaisesRegex(PermissionError, "Only an endoscopist"):
            ensure_case_action_allowed(action="finalize", status="ready_for_signoff", role="nurse")
        with self.assertRaisesRegex(ValueError, "marked ready"):
            ensure_case_action_allowed(action="finalize", status="draft", role="endoscopist")

    def test_reopen_is_admin_only_and_requires_reason(self) -> None:
        ensure_case_action_allowed(action="reopen", status="finalized", role="operations_admin", reopen_reason="Correction required.")
        with self.assertRaisesRegex(PermissionError, "clinical operations admin"):
            ensure_case_action_allowed(action="reopen", status="finalized", role="endoscopist", reopen_reason="Correction")
        with self.assertRaisesRegex(ValueError, "reopen reason"):
            ensure_case_action_allowed(action="reopen", status="finalized", role="operations_admin", reopen_reason="")

    def test_return_to_draft_cannot_change_a_finalized_report(self) -> None:
        ensure_case_action_allowed(action="return_to_draft", status="ready_for_signoff", role="workspace_admin")
        with self.assertRaisesRegex(ValueError, "must be reopened"):
            ensure_case_action_allowed(action="return_to_draft", status="finalized", role="workspace_admin")
