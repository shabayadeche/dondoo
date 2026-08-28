import type { CaseStatus, ProcedureType, Role, TaskStatus, TaskType } from "./enums.js";

export type UserSummary = {
  id: string;
  fullName: string;
  role: Role;
};

export type CaseSummary = {
  id: string;
  patientIdentifier: string;
  procedureType: ProcedureType;
  status: CaseStatus;
  procedureDatetime: string;
  endoscopistName: string;
};

export type FollowUpTask = {
  id: string;
  caseId: string;
  type: TaskType;
  status: TaskStatus;
  ownerName: string;
  dueDate?: string;
};

export type DashboardSnapshot = {
  activeDrafts: number;
  openTasks: number;
  finalizedToday: number;
};

