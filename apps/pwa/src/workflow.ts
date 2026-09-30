import type { ClinicalDraftCasePayload, RoleDashboardPayload, WorkspaceRole } from "./types";

export type DashboardLaneKey = "drafts" | "ready" | "tasks";

export type CaseActionAvailability = {
  canPreview: boolean;
  canMarkReady: boolean;
  canFinalize: boolean;
  canReturnToDraft: boolean;
  canReopen: boolean;
};

export type StartCaseReadiness = {
  canCreateDraft: boolean;
  steps: Array<{ label: string; complete: boolean }>;
};

/**
 * Mirrors the API workflow contract for presentation only. The API remains
 * authoritative for permission and state-transition enforcement.
 */
export function getCaseActionAvailability(
  role: WorkspaceRole,
  status: ClinicalDraftCasePayload["case_status"],
): CaseActionAvailability {
  const isAdmin = role === "operations_admin" || role === "workspace_admin";
  return {
    canPreview: status !== "finalized",
    canMarkReady: status === "draft" || status === "draft_reopened",
    canFinalize: role === "endoscopist" && status === "ready_for_signoff",
    canReturnToDraft: isAdmin && (status === "ready_for_signoff" || status === "draft_reopened"),
    canReopen: isAdmin && status === "finalized",
  };
}

/** Required fields for creating a safe draft; optional team/unit data is staged later. */
export function getStartCaseReadiness(input: {
  patientIdentifier: string;
  procedureType: string;
  procedureDatetime: string;
  facilityCode: string | null | undefined;
  endoscopistUserId: string;
}): StartCaseReadiness {
  const steps = [
    { label: "Patient", complete: Boolean(input.patientIdentifier.trim()) },
    { label: "Case type", complete: Boolean(input.procedureType) },
    { label: "Schedule", complete: Boolean(input.procedureDatetime && input.facilityCode) },
    { label: "Team", complete: Boolean(input.endoscopistUserId) },
  ];
  return { canCreateDraft: steps.every((step) => step.complete), steps };
}

/** Use only a complete, non-duplicated server priority order. */
export function getDashboardLaneOrder(
  dashboard: RoleDashboardPayload | undefined,
  fallback: DashboardLaneKey[],
): DashboardLaneKey[] {
  const laneOrder = dashboard?.lanes.map((lane) => lane.key);
  if (!laneOrder || laneOrder.length !== 3 || new Set(laneOrder).size !== 3) {
    return fallback;
  }
  return laneOrder;
}
