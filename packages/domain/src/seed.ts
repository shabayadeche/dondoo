import type { CaseSummary, DashboardSnapshot, FollowUpTask } from "./types.js";

export const dashboardSnapshot: DashboardSnapshot = {
  activeDrafts: 6,
  openTasks: 11,
  finalizedToday: 14
};

export const sampleCases: CaseSummary[] = [
  {
    id: "case-1001",
    patientIdentifier: "PT-2026-001",
    procedureType: "colonoscopy",
    status: "draft",
    procedureDatetime: "2026-08-18T08:30:00Z",
    endoscopistName: "Dr. A. Njoroge"
  },
  {
    id: "case-1002",
    patientIdentifier: "PT-2026-002",
    procedureType: "egd",
    status: "finalized",
    procedureDatetime: "2026-08-18T09:10:00Z",
    endoscopistName: "Dr. B. Kamau"
  }
];

export const sampleTasks: FollowUpTask[] = [
  {
    id: "task-2001",
    caseId: "case-1002",
    type: "pathology_review",
    status: "open",
    ownerName: "Dr. B. Kamau",
    dueDate: "2026-08-20"
  },
  {
    id: "task-2002",
    caseId: "case-1001",
    type: "result_communication",
    status: "in_progress",
    ownerName: "Nurse W. Akinyi"
  }
];
