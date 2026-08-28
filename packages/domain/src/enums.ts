export const procedureTypes = ["colonoscopy", "egd", "ercp", "eus"] as const;

export type ProcedureType = (typeof procedureTypes)[number];

export const sexOptions = ["female", "male", "intersex", "unknown"] as const;

export type SexOption = (typeof sexOptions)[number];

export const caseStatuses = [
  "draft",
  "ready_for_signoff",
  "finalized",
  "draft_reopened"
] as const;

export type CaseStatus = (typeof caseStatuses)[number];

export const roles = [
  "endoscopist",
  "nurse",
  "unit_admin",
  "quality_reviewer"
] as const;

export type Role = (typeof roles)[number];

export const taskStatuses = ["open", "in_progress", "closed", "cancelled"] as const;

export type TaskStatus = (typeof taskStatuses)[number];

export const taskTypes = [
  "pathology_review",
  "result_communication",
  "specimen_resolution",
  "surveillance_followup"
] as const;

export type TaskType = (typeof taskTypes)[number];
