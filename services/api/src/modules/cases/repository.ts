import { sampleCases, sampleTasks, type CaseSummary, type FollowUpTask } from "@phd-ass/domain";
import type { OdooDraftCasePayload } from "./odoo-draft-schema.js";

const odooDraftCases = new Map<string, OdooDraftCasePayload>();

export function listCases() {
  const storedCases = Array.from(odooDraftCases.values()).map(mapDraftCaseToSummary);
  return mergeById(storedCases, sampleCases);
}

export function listTasks() {
  const storedTasks = Array.from(odooDraftCases.values()).flatMap(mapDraftCaseToTasks);
  return mergeById(storedTasks, sampleTasks);
}

export function upsertOdooDraftCase(payload: OdooDraftCasePayload) {
  odooDraftCases.set(payload.external_case_id, payload);
  return payload;
}

function mapDraftCaseToSummary(payload: OdooDraftCasePayload): CaseSummary {
  return {
    id: payload.external_case_id,
    patientIdentifier: payload.patient_identifier,
    procedureType: payload.procedure_type,
    status: payload.case_status,
    procedureDatetime: payload.procedure_datetime,
    endoscopistName: payload.endoscopist_user_ref || payload.endoscopist_user_id || "Odoo Draft User"
  };
}

function mapDraftCaseToTasks(payload: OdooDraftCasePayload): FollowUpTask[] {
  return payload.followup_tasks.map((task) => {
    const mappedTask: FollowUpTask = {
      id: task.followup_task_id,
      caseId: payload.external_case_id,
      type: task.task_type || "pathology_review",
      status: task.task_status || "open",
      ownerName: task.task_owner_user_ref || task.task_owner_user_id || "Unassigned"
    };

    if (task.due_date) {
      mappedTask.dueDate = task.due_date;
    }

    return mappedTask;
  });
}

function mergeById<T extends { id: string }>(preferred: T[], fallback: T[]) {
  const seen = new Set(preferred.map((item) => item.id));
  return [...preferred, ...fallback.filter((item) => !seen.has(item.id))];
}
