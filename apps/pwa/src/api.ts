import { appConfig } from "@phd-ass/config";
import type { CaseSummary, FollowUpTask } from "@phd-ass/domain";
import type {
  ApiBundle,
  AuthenticatedSessionPayload,
  CaseHistoryPayload,
  CaseActionName,
  CaseActionPayload,
  CaseDraftWriteResponse,
  ClinicalDraftCasePayload,
  ClinicalLookupsPayload,
  PatientRelationshipSuggestion,
  PatientLookupOption,
  FollowUpTaskUpdatePayload,
  FollowUpTaskWriteResponse,
  HealthPayload,
  LoginPayload,
  MetaPayload,
  RoleDashboardPayload,
  StartCasePayload,
  StartCaseResponse
} from "./types";

const envBaseUrl = import.meta.env.VITE_CLINICAL_API_BASE_URL?.trim();
export const clinicalApiBaseUrl = envBaseUrl || "";
export const sessionStorageKey = "phd-ass-session";

export class ApiRequestError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

function isExpiredSession(session: AuthenticatedSessionPayload): boolean {
  const expiresAt = new Date(session.expiresAt).getTime();
  return Number.isFinite(expiresAt) && expiresAt <= Date.now();
}

function readStoredSession(): AuthenticatedSessionPayload | null {
  if (typeof window === "undefined") {
    return null;
  }

  const stored = window.localStorage.getItem(sessionStorageKey);
  if (!stored) {
    return null;
  }

  try {
    const parsed = JSON.parse(stored) as AuthenticatedSessionPayload;
    if (isExpiredSession(parsed)) {
      window.localStorage.removeItem(sessionStorageKey);
      return null;
    }
    return parsed;
  } catch {
    window.localStorage.removeItem(sessionStorageKey);
    return null;
  }
}

export function storeSession(session: AuthenticatedSessionPayload): void {
  if (typeof window !== "undefined") {
    window.localStorage.setItem(sessionStorageKey, JSON.stringify(session));
  }
}

export function clearStoredSession(): void {
  if (typeof window !== "undefined") {
    window.localStorage.removeItem(sessionStorageKey);
  }
}

export function getStoredSession(): AuthenticatedSessionPayload | null {
  return readStoredSession();
}

async function readErrorMessage(response: Response): Promise<string> {
  const fallback = `${response.status} ${response.statusText}`;

  try {
    const payload = (await response.json()) as { detail?: string | { message?: string } };
    if (typeof payload.detail === "string" && payload.detail.trim()) {
      return payload.detail;
    }
    if (payload.detail && typeof payload.detail === "object" && typeof payload.detail.message === "string") {
      return payload.detail.message;
    }
  } catch {
    // Fall through to plain text.
  }

  try {
    const text = await response.text();
    return text.trim() || fallback;
  } catch {
    return fallback;
  }
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  if (init?.body !== undefined && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const session = readStoredSession();
  if (session?.token) {
    headers.set("Authorization", `Bearer ${session.token}`);
  }

  const response = await fetch(`${clinicalApiBaseUrl}${path}`, {
    ...init,
    headers
  });

  if (!response.ok) {
    throw new ApiRequestError(response.status, await readErrorMessage(response));
  }

  return (await response.json()) as T;
}

function parseFilename(contentDisposition: string | null): string | null {
  if (!contentDisposition) {
    return null;
  }

  const utf8Match = contentDisposition.match(/filename\*=UTF-8''([^;]+)/i);
  if (utf8Match?.[1]) {
    try {
      return decodeURIComponent(utf8Match[1]);
    } catch {
      return utf8Match[1];
    }
  }

  const plainMatch = contentDisposition.match(/filename="?([^";]+)"?/i);
  return plainMatch?.[1] || null;
}

async function requestBinary(path: string, init?: RequestInit): Promise<{ blob: Blob; filename: string | null }> {
  const headers = new Headers(init?.headers);

  const session = readStoredSession();
  if (session?.token) {
    headers.set("Authorization", `Bearer ${session.token}`);
  }

  const response = await fetch(`${clinicalApiBaseUrl}${path}`, {
    ...init,
    headers
  });

  if (!response.ok) {
    throw new ApiRequestError(response.status, await readErrorMessage(response));
  }

  return {
    blob: await response.blob(),
    filename: parseFilename(response.headers.get("Content-Disposition"))
  };
}

async function requestFormJson<T>(path: string, body: FormData, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);

  const session = readStoredSession();
  if (session?.token) {
    headers.set("Authorization", `Bearer ${session.token}`);
  }

  const response = await fetch(`${clinicalApiBaseUrl}${path}`, {
    ...init,
    method: init?.method || "POST",
    body,
    headers
  });

  if (!response.ok) {
    throw new ApiRequestError(response.status, await readErrorMessage(response));
  }

  return (await response.json()) as T;
}

function addShellWarning(warnings: string[], message: string): void {
  if (!warnings.includes(message)) {
    warnings.push(message);
  }
}

export function loginClinician(payload: LoginPayload): Promise<AuthenticatedSessionPayload> {
  return requestJson<AuthenticatedSessionPayload>("/api/session/login", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function fetchCurrentSession(): Promise<AuthenticatedSessionPayload> {
  return requestJson<AuthenticatedSessionPayload>("/api/session/me");
}

export function logoutClinician(): Promise<{ status: string }> {
  return requestJson<{ status: string }>("/api/session/logout", {
    method: "POST"
  });
}

export async function fetchShellData(): Promise<ApiBundle> {
  const [healthResult, metaResult, casesResult, tasksResult, lookupsResult, dashboardResult] = await Promise.allSettled([
    requestJson<HealthPayload>("/health"),
    requestJson<MetaPayload>("/api/meta"),
    requestJson<CaseSummary[]>("/api/cases"),
    requestJson<FollowUpTask[]>("/api/tasks"),
    requestJson<ClinicalLookupsPayload>("/api/lookups"),
    requestJson<RoleDashboardPayload>("/api/dashboard")
  ]);

  const authFailure = [healthResult, metaResult, casesResult, tasksResult, lookupsResult, dashboardResult].find(
    (result): result is PromiseRejectedResult =>
      result.status === "rejected" && result.reason instanceof ApiRequestError && result.reason.status === 401
  );
  if (authFailure) {
    throw authFailure.reason;
  }

  const warnings: string[] = [];
  const health = healthResult.status === "fulfilled"
    ? healthResult.value
    : { status: "offline", service: "clinical-api" };
  const meta = metaResult.status === "fulfilled"
    ? metaResult.value
    : defaultMeta;
  const cases = casesResult.status === "fulfilled"
    ? casesResult.value
    : [];
  const tasks = tasksResult.status === "fulfilled"
    ? tasksResult.value
    : [];
  const lookups = lookupsResult.status === "fulfilled"
    ? lookupsResult.value
    : defaultLookups;
  const dashboard = dashboardResult.status === "fulfilled" ? dashboardResult.value : undefined;

  if (metaResult.status === "rejected") {
    addShellWarning(warnings, "Workflow defaults are in use while the live configuration reloads.");
  }
  if (casesResult.status === "rejected" || tasksResult.status === "rejected") {
    addShellWarning(warnings, "Live queue data is unavailable. Refresh the workspace after the API connection recovers.");
  }
  if (lookupsResult.status === "rejected") {
    addShellWarning(warnings, "Reference lists are unavailable. Starting a new case may be limited until the service recovers.");
  }
  if (dashboardResult.status === "rejected") {
    addShellWarning(warnings, "Role priorities are temporarily using the local workspace fallback.");
  }

  return { health, meta, cases, tasks, lookups, dashboard, warnings };
}

export function submitStartCase(payload: StartCasePayload): Promise<StartCaseResponse> {
  return requestJson<StartCaseResponse>("/api/cases", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function fetchCaseDetail(externalCaseId: string): Promise<ClinicalDraftCasePayload> {
  return requestJson<ClinicalDraftCasePayload>(`/api/cases/${encodeURIComponent(externalCaseId)}`);
}

export function fetchCaseHistory(externalCaseId: string): Promise<CaseHistoryPayload> {
  return requestJson<CaseHistoryPayload>(`/api/cases/${encodeURIComponent(externalCaseId)}/history`);
}

export function uploadCaseImage(externalCaseId: string, file: File, caption: string): Promise<CaseDraftWriteResponse> {
  const body = new FormData();
  body.append("file", file);
  if (caption.trim()) {
    body.append("caption", caption.trim());
  }
  return requestFormJson<CaseDraftWriteResponse>(`/api/cases/${encodeURIComponent(externalCaseId)}/images`, body);
}

export function deleteCaseImage(externalCaseId: string, externalImageId: string): Promise<CaseDraftWriteResponse> {
  return requestJson<CaseDraftWriteResponse>(
    `/api/cases/${encodeURIComponent(externalCaseId)}/images/${encodeURIComponent(externalImageId)}`,
    { method: "DELETE" }
  );
}

export function fetchCaseImageBinary(externalCaseId: string, externalImageId: string): Promise<{ blob: Blob; filename: string | null }> {
  return requestBinary(`/api/cases/${encodeURIComponent(externalCaseId)}/images/${encodeURIComponent(externalImageId)}`);
}

export function saveCaseDraft(externalCaseId: string, payload: ClinicalDraftCasePayload): Promise<CaseDraftWriteResponse> {
  return requestJson<CaseDraftWriteResponse>(`/api/cases/${encodeURIComponent(externalCaseId)}`, {
    method: "PUT",
    body: JSON.stringify(payload)
  });
}

export function fetchPatientRelationship(patientIdentifier: string): Promise<PatientRelationshipSuggestion | null> {
  return requestJson<PatientRelationshipSuggestion | null>(
    `/api/patient-relationship?patient_identifier=${encodeURIComponent(patientIdentifier.trim())}`
  );
}

export function searchPatients(query: string): Promise<PatientLookupOption[]> {
  return requestJson<PatientLookupOption[]>(`/api/patients/search?query=${encodeURIComponent(query.trim())}`);
}

export function runCaseAction(
  externalCaseId: string,
  action: CaseActionName,
  payload?: CaseActionPayload
): Promise<CaseDraftWriteResponse> {
  return requestJson<CaseDraftWriteResponse>(`/api/cases/${encodeURIComponent(externalCaseId)}/actions/${action}`, {
    method: "POST",
    body: JSON.stringify(payload ?? {})
  });
}

export function saveFollowUpTask(taskId: string, payload: FollowUpTaskUpdatePayload): Promise<FollowUpTaskWriteResponse> {
  return requestJson<FollowUpTaskWriteResponse>(`/api/tasks/${encodeURIComponent(taskId)}`, {
    method: "PUT",
    body: JSON.stringify(payload)
  });
}

export function getCasePdfUrl(externalCaseId: string): string {
  return `${clinicalApiBaseUrl}/api/cases/${encodeURIComponent(externalCaseId)}/pdf`;
}

export function getRevisionPdfUrl(externalCaseId: string, revisionNumber: number): string {
  return `${clinicalApiBaseUrl}/api/cases/${encodeURIComponent(externalCaseId)}/revisions/${revisionNumber}/pdf`;
}

export function fetchCasePdfBinary(externalCaseId: string): Promise<{ blob: Blob; filename: string | null }> {
  return requestBinary(`/api/cases/${encodeURIComponent(externalCaseId)}/pdf`);
}

export function fetchRevisionPdfBinary(
  externalCaseId: string,
  revisionNumber: number
): Promise<{ blob: Blob; filename: string | null }> {
  return requestBinary(`/api/cases/${encodeURIComponent(externalCaseId)}/revisions/${revisionNumber}/pdf`);
}

export const defaultLookups: ClinicalLookupsPayload = {
  facilities: [],
  facilityUnits: [],
  endoscopists: [],
  nurses: [],
  referrerServices: []
};

export const defaultMeta: MetaPayload = {
  appName: appConfig.appName,
  odooRecommendedModule: appConfig.odooRecommendedModule,
  odooRecommendedModuleLabel: appConfig.odooRecommendedModuleLabel,
  workflowSteps: [],
  workflowStepsByProcedure: {},
  dashboardSnapshot: {
    activeDrafts: 0,
    openTasks: 0,
    finalizedToday: 0
  }
};
