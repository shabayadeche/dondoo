import assert from "node:assert/strict";
import test from "node:test";

import { getRoleWorkspaceCopy } from "./workspace";

const snapshot = { drafts: 3, ready: 2, tasks: 1, finalizedToday: 4 };

test("workspace copy puts each role's highest-value clinical queue first", () => {
  assert.deepEqual(getRoleWorkspaceCopy("endoscopist", snapshot).laneOrder, ["ready", "drafts", "tasks"]);
  assert.deepEqual(getRoleWorkspaceCopy("nurse", snapshot).laneOrder, ["drafts", "tasks", "ready"]);
  assert.deepEqual(getRoleWorkspaceCopy("operations_admin", snapshot).laneOrder, ["tasks", "ready", "drafts"]);
});

test("workspace copy uses singular count grammar for an endoscopist", () => {
  const copy = getRoleWorkspaceCopy("endoscopist", { drafts: 1, ready: 1, tasks: 1, finalizedToday: 1 });

  assert.match(copy.headerSummary, /1 report ready, 1 draft active, 1 follow-up task open/);
  assert.match(copy.headerNote, /1 report finalized today/);
});
