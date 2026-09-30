import type { WorkspaceRole } from "./types";
import type { DashboardLaneKey } from "./workflow";

export type WorkspaceSnapshot = {
  drafts: number;
  ready: number;
  tasks: number;
  finalizedToday: number;
};

export type RoleWorkspaceCopy = {
  headerSummary: string;
  headerNote: string;
  dashboardEyebrow: string;
  dashboardTitle: string;
  dashboardSummary: string;
  laneOrder: DashboardLaneKey[];
};

function formatCountPhrase(count: number, singular: string, plural = `${singular}s`): string {
  return `${count} ${count === 1 ? singular : plural}`;
}

/**
 * Role-specific presentation copy. Queue enforcement and permissions remain
 * server-side; this simply makes each clinician's next action obvious.
 */
export function getRoleWorkspaceCopy(role: WorkspaceRole, snapshot: WorkspaceSnapshot): RoleWorkspaceCopy {
  switch (role) {
    case "endoscopist":
      return {
        headerSummary: snapshot.ready
          ? `${formatCountPhrase(snapshot.ready, "report")} ready, ${formatCountPhrase(snapshot.drafts, "draft")} active, ${formatCountPhrase(snapshot.tasks, "follow-up task")} open.`
          : `No reports are waiting for sign-off. ${formatCountPhrase(snapshot.drafts, "draft")} active, ${formatCountPhrase(snapshot.tasks, "follow-up task")} open.`,
        headerNote: snapshot.ready
          ? `Sign-off queue first. ${formatCountPhrase(snapshot.finalizedToday, "report")} finalized today.`
          : "No reports are waiting for sign-off. Active drafting is next.",
        dashboardEyebrow: "Endoscopist queue",
        dashboardTitle: "Ready reports come first",
        dashboardSummary: "Open the sign-off queue first, then return to active drafting and follow-up.",
        laneOrder: ["ready", "drafts", "tasks"]
      };
    case "nurse":
      return {
        headerSummary: `${formatCountPhrase(snapshot.drafts, "draft")} active, ${formatCountPhrase(snapshot.tasks, "follow-up task")} open, ${formatCountPhrase(snapshot.ready, "report")} ready.`,
        headerNote: "Documentation stays first. Follow-up and sign-off remain visible behind it.",
        dashboardEyebrow: "Nursing queue",
        dashboardTitle: "Keep drafts moving",
        dashboardSummary: "Open active drafts first, then clear follow-up and ready reports from the same queue.",
        laneOrder: ["drafts", "tasks", "ready"]
      };
    case "operations_admin":
    case "workspace_admin":
      return {
        headerSummary: `${formatCountPhrase(snapshot.tasks, "follow-up task")} open, ${formatCountPhrase(snapshot.ready, "report")} ready, ${formatCountPhrase(snapshot.drafts, "draft")} active.`,
        headerNote: "Queue health is the first check for this shift.",
        dashboardEyebrow: "Operations queue",
        dashboardTitle: "Clear delays first",
        dashboardSummary: "Follow-up items lead the queue. Ready reports and active drafts stay behind them.",
        laneOrder: ["tasks", "ready", "drafts"]
      };
  }
}
