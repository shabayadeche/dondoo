import assert from "node:assert/strict";
import test from "node:test";

import { getCaseActionAvailability, getDashboardLaneOrder, getStartCaseReadiness } from "./workflow";

test("an endoscopist can finalize only a ready report", () => {
  const ready = getCaseActionAvailability("endoscopist", "ready_for_signoff");
  const draft = getCaseActionAvailability("endoscopist", "draft");

  assert.equal(ready.canFinalize, true);
  assert.equal(draft.canFinalize, false);
  assert.equal(draft.canMarkReady, true);
});

test("administrators can correct workflow state without finalizing", () => {
  const ready = getCaseActionAvailability("operations_admin", "ready_for_signoff");
  const finalized = getCaseActionAvailability("workspace_admin", "finalized");

  assert.equal(ready.canReturnToDraft, true);
  assert.equal(ready.canFinalize, false);
  assert.equal(finalized.canReopen, true);
  assert.equal(finalized.canMarkReady, false);
});

test("nurses cannot access finalization or administrative recovery actions", () => {
  const availability = getCaseActionAvailability("nurse", "draft_reopened");

  assert.equal(availability.canMarkReady, true);
  assert.equal(availability.canFinalize, false);
  assert.equal(availability.canReturnToDraft, false);
  assert.equal(availability.canReopen, false);
});

test("case start requires only draft-critical data, not unit or nurse assignment", () => {
  const draftInput = {
    patientIdentifier: "PT-2026-001",
    procedureType: "colonoscopy",
    procedureDatetime: "2026-09-30T10:00",
    facilityCode: "MAIN",
    endoscopistUserId: "dr.njoroge",
  };
  const ready = getStartCaseReadiness(draftInput);
  const missingEndoscopist = getStartCaseReadiness({ ...draftInput, endoscopistUserId: "" });

  assert.equal(ready.canCreateDraft, true);
  assert.equal(missingEndoscopist.canCreateDraft, false);
});

test("dashboard uses a complete server priority order and otherwise falls back", () => {
  const fallback = ["drafts", "ready", "tasks"] as const;
  const serverOrder = getDashboardLaneOrder({
    role: "endoscopist",
    headline: "Review ready reports first.",
    primaryLane: "ready",
    lanes: [
      { key: "ready", label: "Ready for sign-off", count: 2 },
      { key: "drafts", label: "Active drafts", count: 1 },
      { key: "tasks", label: "Open follow-up", count: 0 },
    ],
    finalizedToday: 1,
  }, [...fallback]);
  const invalidOrder = getDashboardLaneOrder({
    role: "nurse",
    headline: "Keep active documentation moving.",
    primaryLane: "drafts",
    lanes: [
      { key: "drafts", label: "Active drafts", count: 1 },
      { key: "drafts", label: "Active drafts", count: 1 },
    ],
    finalizedToday: 0,
  }, [...fallback]);

  assert.deepEqual(serverOrder, ["ready", "drafts", "tasks"]);
  assert.deepEqual(invalidOrder, fallback);
});
