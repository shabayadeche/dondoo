import { appConfig } from "@phd-ass/config";
import { type CaseSummary, type FollowUpTask, workflowStepsByProcedure } from "@phd-ass/domain";
import { startTransition, useDeferredValue, useEffect, useMemo, useRef, useState, type FormEvent, type ReactNode } from "react";
import {
  ApiRequestError,
  clearStoredSession,
  defaultLookups,
  deleteCaseImage,
  fetchCaseDetail,
  fetchCaseHistory,
  fetchCaseImageBinary,
  fetchCasePdfBinary,
  fetchPatientRelationship,
  searchPatients,
  fetchRevisionPdfBinary,
  fetchShellData,
  getStoredSession,
  loginClinician,
  logoutClinician,
  runCaseAction,
  saveCaseDraft,
  saveFollowUpTask,
  storeSession,
  submitStartCase,
  uploadCaseImage
} from "./api";
import type {
  ApiBundle,
  CaseHistoryPayload,
  AuthenticatedSessionPayload,
  CaseActionName,
  CaseImageAttachmentPayload,
  CaseLesionPayload,
  CaseSegmentPayload,
  CaseSpecimenPayload,
  ClinicalDraftCasePayload,
  ClinicalFollowUpTaskPayload,
  ClinicalLookupsPayload,
  PatientRelationshipSuggestion,
  PatientLookupOption,
  ClinicianLookupOption,
  FacilityUnitLookupOption,
  ProcedureType,
  LoginPayload,
  MetaPayload,
  StartCasePayload,
  TaskStatus,
  ValueLookupOption,
  WorkflowStep,
  WorkspaceRole
} from "./types";

type ScreenKey = "dashboard" | "cases" | "tasks" | "new-procedure" | "case-detail";
type StatusTone = "accent" | "success" | "warning" | "critical" | "neutral";
type BannerTone = "success" | "error";
type DashboardLaneKey = "drafts" | "ready" | "tasks";
type SimpleOption = { value: string; label: string };
type IconName =
  | "dashboard"
  | "cases"
  | "tasks"
  | "new-case"
  | "help"
  | "sign-out"
  | "back"
  | "draft"
  | "ready"
  | "finalized"
  | "workflow"
  | "team"
  | "location"
  | "preview"
  | "save"
  | "pdf"
  | "checklist"
  | "close"
  | "history"
  | "edit"
  | "image"
  | "upload"
  | "trash";
type HelpDockItem = { label: string; detail?: string };
type HelpDockSection = {
  eyebrow: string;
  title: string;
  icon: IconName;
  items: HelpDockItem[];
  numbered?: boolean;
};

const procedureOrder: ProcedureType[] = ["colonoscopy", "egd", "ercp", "eus"];
const sexOptions: SimpleOption[] = [
  { value: "female", label: "Female" },
  { value: "male", label: "Male" },
  { value: "intersex", label: "Intersex" },
  { value: "unknown", label: "Unknown" }
];
const priorityOptions: SimpleOption[] = [
  { value: "elective", label: "Elective" },
  { value: "urgent", label: "Urgent" },
  { value: "emergency", label: "Emergency" }
];
const asaOptions: SimpleOption[] = ["I", "II", "III", "IV", "V"].map((value) => ({ value, label: value }));
const antithromboticOptions: SimpleOption[] = [
  { value: "na", label: "Not applicable" },
  { value: "continue", label: "Continue" },
  { value: "hold", label: "Hold" },
  { value: "bridging_other", label: "Bridging or other" }
];
const prepQualityOptions: SimpleOption[] = [
  { value: "adequate", label: "Adequate" },
  { value: "inadequate", label: "Inadequate" }
];
const terminalIleumOptions: SimpleOption[] = [
  { value: "not_attempted", label: "Not attempted" },
  { value: "intubated", label: "Intubated" },
  { value: "abnormal", label: "Abnormal" }
];
const egdExtentOptions: SimpleOption[] = [
  { value: "esophagus", label: "Esophagus" },
  { value: "stomach", label: "Stomach" },
  { value: "duodenal_bulb", label: "Duodenal bulb" },
  { value: "second_duodenum", label: "Second part of duodenum" },
  { value: "jejunum_other", label: "Jejunum or other" }
];
const ercpPapillaOptions: SimpleOption[] = [
  { value: "native", label: "Native papilla" },
  { value: "prior_sphincterotomy", label: "Prior sphincterotomy" },
  { value: "altered_anatomy", label: "Altered anatomy" }
];
const successOptions: SimpleOption[] = [
  { value: "yes", label: "Yes" },
  { value: "partial", label: "Partial" },
  { value: "no", label: "No" }
];
const drainageOptions: SimpleOption[] = [
  { value: "complete", label: "Complete" },
  { value: "partial", label: "Partial" },
  { value: "not_achieved", label: "Not achieved" }
];
const eusRouteOptions: SimpleOption[] = [
  { value: "upper", label: "Upper EUS" },
  { value: "lower", label: "Lower EUS" }
];
const eusEchoendoscopeOptions: SimpleOption[] = [
  { value: "radial", label: "Radial" },
  { value: "linear", label: "Linear" },
  { value: "miniprobe", label: "Miniprobe" }
];
const eusIntentOptions: SimpleOption[] = [
  { value: "diagnostic", label: "Diagnostic" },
  { value: "tissue_acquisition", label: "Tissue acquisition" },
  { value: "therapeutic", label: "Therapeutic" }
];
const adequacyOptions: SimpleOption[] = [
  { value: "unknown", label: "Unknown" },
  { value: "adequate", label: "Adequate" },
  { value: "inadequate", label: "Inadequate" }
];
const pathologyStatusOptions: SimpleOption[] = [
  { value: "none", label: "No pathology pending" },
  { value: "pending_tracking_required", label: "Pending pathology tracking required" }
];
const adverseEventPlanOptions: SimpleOption[] = [
  { value: "routine_discharge", label: "Routine discharge" },
  { value: "observe_admit", label: "Observe or admit" },
  { value: "other", label: "Other" }
];
const technicalLimitationOptions: SimpleOption[] = [
  { value: "none", label: "None" },
  { value: "poor_prep", label: "Poor preparation" },
  { value: "stricture", label: "Stricture" },
  { value: "pain", label: "Pain or intolerance" },
  { value: "other", label: "Other" }
];
const polypTechniqueOptions: SimpleOption[] = [
  { value: "cold_snare", label: "Cold snare" },
  { value: "hot_snare", label: "Hot snare" },
  { value: "forceps", label: "Forceps" },
  { value: "other", label: "Other" }
];
const tattooOptions: SimpleOption[] = [
  { value: "na", label: "Not applicable" },
  { value: "placed", label: "Placed" }
];
const surveillanceReasonOptions: SimpleOption[] = [
  { value: "guideline_based", label: "Guideline based" },
  { value: "prep_quality", label: "Preparation quality" },
  { value: "piecemeal_resection", label: "Piecemeal resection" },
  { value: "other", label: "Other" }
];
const taskTypeOptions: SimpleOption[] = [
  { value: "pathology_review", label: "Pathology review" },
  { value: "result_communication", label: "Result communication" },
  { value: "specimen_resolution", label: "Specimen resolution" },
  { value: "surveillance_followup", label: "Surveillance follow-up" }
];
const taskStatusOptions: SimpleOption[] = [
  { value: "open", label: "Open" },
  { value: "in_progress", label: "In progress" },
  { value: "closed", label: "Closed" },
  { value: "cancelled", label: "Cancelled" }
];
const quickReportPhrases = [
  "Examination completed without immediate complication.",
  "Findings discussed with the patient and referring team.",
  "Await histology before confirming the surveillance interval."
];
const segmentNameOptions: SimpleOption[] = [
  { value: "terminal_ileum", label: "Terminal ileum" },
  { value: "cecum", label: "Cecum" },
  { value: "ascending_colon", label: "Ascending colon" },
  { value: "transverse_colon", label: "Transverse colon" },
  { value: "descending_colon", label: "Descending colon" },
  { value: "sigmoid_colon", label: "Sigmoid colon" },
  { value: "rectum_retroflexion", label: "Rectum retroflexion" }
];
const screenContent: Record<ScreenKey, { eyebrow: string; title: string; summary: string }> = {
  dashboard: {
    eyebrow: "Shift overview",
    title: "Clinical work queue",
    summary: "Focus on reports in progress, cases ready for sign-off, and follow-up that needs action today."
  },
  cases: {
    eyebrow: "Procedure reporting",
    title: "Case queue",
    summary: "Review draft, reopened, ready, and finalized procedures in one sorted clinical list."
  },
  tasks: {
    eyebrow: "Post-procedure follow-up",
    title: "Follow-up tasks",
    summary: "See pathology, communication, and surveillance work by due date and current status."
  },
  "new-procedure": {
    eyebrow: "Procedure start",
    title: "Start a new case",
    summary: "Capture the minimum patient, schedule, and care-team details needed to open a clean draft."
  },
  "case-detail": {
    eyebrow: "Clinical authoring",
    title: "Case detail",
    summary: "Complete the structured procedure record, maintain follow-up tasks, and move the case through sign-off."
  }
};
const startCaseChecks: HelpDockItem[] = [
  { label: "Use the patient identifier exactly as it should appear on the final report." },
  { label: "Confirm the room and time before the team starts capturing procedure findings." },
  { label: "Assign the performing endoscopist up front so sign-off and audit trails stay accurate." }
];
const caseAuthoringChecks: HelpDockItem[] = [
  { label: "Save the draft after material edits before changing workflow status." },
  { label: "Generate a preview before marking the case ready for sign-off." },
  { label: "Finalize only when structured findings, narrative preview, and follow-up tasks agree." }
];

type WorkspaceSnapshot = {
  drafts: number;
  ready: number;
  tasks: number;
  finalizedToday: number;
};

function formatCountPhrase(count: number, singular: string, plural = `${singular}s`): string {
  return `${count} ${count === 1 ? singular : plural}`;
}

function AppIcon({ name, size = 18 }: { name: IconName; size?: number }) {
  const commonProps = {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.9,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    "aria-hidden": true
  };

  switch (name) {
    case "dashboard":
      return (
        <svg {...commonProps}>
          <rect x="3.5" y="3.5" width="7" height="7" rx="1.5" />
          <rect x="13.5" y="3.5" width="7" height="7" rx="1.5" />
          <rect x="3.5" y="13.5" width="7" height="7" rx="1.5" />
          <rect x="13.5" y="13.5" width="7" height="7" rx="1.5" />
        </svg>
      );
    case "cases":
      return (
        <svg {...commonProps}>
          <path d="M8 3.5h7l4 4v13H5V3.5h3" />
          <path d="M15 3.5v4h4" />
          <path d="M8.5 12h7" />
          <path d="M8.5 16h7" />
        </svg>
      );
    case "tasks":
      return (
        <svg {...commonProps}>
          <circle cx="12" cy="12" r="8.5" />
          <path d="m8.8 12 2.2 2.2 4.4-4.6" />
        </svg>
      );
    case "new-case":
      return (
        <svg {...commonProps}>
          <rect x="4" y="4" width="16" height="16" rx="3.5" />
          <path d="M12 8v8" />
          <path d="M8 12h8" />
        </svg>
      );
    case "help":
      return (
        <svg {...commonProps}>
          <path d="M12 4a8.5 8.5 0 0 1 8.5 8.5A8.5 8.5 0 0 1 12 21a8.3 8.3 0 0 1-3.8-.9L4 21l1.1-3.6A8.4 8.4 0 0 1 3.5 12.5 8.5 8.5 0 0 1 12 4Z" />
          <path d="M9.7 9.5a2.6 2.6 0 1 1 4.5 1.8c-.8.8-1.6 1.2-1.6 2.2" />
          <path d="M12 17.2h.01" />
        </svg>
      );
    case "sign-out":
      return (
        <svg {...commonProps}>
          <path d="M9 4.5H5.5v15H9" />
          <path d="M13 8.5 18 12l-5 3.5" />
          <path d="M18 12H8" />
        </svg>
      );
    case "back":
      return (
        <svg {...commonProps}>
          <path d="m10 6.5-5 5.5 5 5.5" />
          <path d="M19 12H5.5" />
        </svg>
      );
    case "draft":
      return (
        <svg {...commonProps}>
          <path d="M7 4.5h8l3 3v12H7z" />
          <path d="M15 4.5v3h3" />
          <path d="m9.5 16.5 4.8-4.8 1.8 1.8-4.8 4.8-2.4.6Z" />
        </svg>
      );
    case "ready":
      return (
        <svg {...commonProps}>
          <path d="M12 3.5 19 7v5c0 4.2-2.7 6.8-7 8-4.3-1.2-7-3.8-7-8V7l7-3.5Z" />
          <path d="m9.2 11.9 1.9 1.9 3.8-4" />
        </svg>
      );
    case "finalized":
      return (
        <svg {...commonProps}>
          <path d="M7 3.5h8l3 3v14H7z" />
          <path d="M15 3.5v3h3" />
          <path d="m9.5 13 1.8 1.8 3.7-3.8" />
        </svg>
      );
    case "workflow":
      return (
        <svg {...commonProps}>
          <circle cx="6" cy="6.5" r="2.5" />
          <circle cx="18" cy="12" r="2.5" />
          <circle cx="8" cy="18" r="2.5" />
          <path d="M8.1 8.2 10.8 10a3.4 3.4 0 0 0 1.9.6h2.8" />
          <path d="m7.3 8.8.5 5.8" />
        </svg>
      );
    case "team":
      return (
        <svg {...commonProps}>
          <circle cx="9" cy="9" r="3" />
          <path d="M4.5 18a4.5 4.5 0 0 1 9 0" />
          <circle cx="17.5" cy="8" r="2.2" />
          <path d="M15.8 18a3.8 3.8 0 0 1 3.7-3" />
        </svg>
      );
    case "location":
      return (
        <svg {...commonProps}>
          <path d="M12 20.5c3.7-4.1 5.5-7.1 5.5-9.4A5.5 5.5 0 1 0 6.5 11c0 2.3 1.8 5.3 5.5 9.5Z" />
          <circle cx="12" cy="11" r="2.2" />
        </svg>
      );
    case "preview":
      return (
        <svg {...commonProps}>
          <path d="M2.5 12s3.2-5.5 9.5-5.5 9.5 5.5 9.5 5.5-3.2 5.5-9.5 5.5S2.5 12 2.5 12Z" />
          <circle cx="12" cy="12" r="2.5" />
        </svg>
      );
    case "save":
      return (
        <svg {...commonProps}>
          <path d="M5 4.5h11l3 3V19.5H5z" />
          <path d="M8 4.5v5h7v-5" />
          <path d="M8 19.5v-5h8v5" />
        </svg>
      );
    case "pdf":
      return (
        <svg {...commonProps}>
          <path d="M7 3.5h8l3 3v14H7z" />
          <path d="M15 3.5v3h3" />
          <path d="M9 15h6" />
          <path d="M9 11h4" />
        </svg>
      );
    case "image":
      return (
        <svg {...commonProps}>
          <rect x="4" y="5" width="16" height="14" rx="2.5" />
          <circle cx="9" cy="10" r="1.4" />
          <path d="m7 17 4-4 2.7 2.7 1.4-1.5L18 17" />
        </svg>
      );
    case "upload":
      return (
        <svg {...commonProps}>
          <path d="M12 16V5" />
          <path d="m7.5 9.5 4.5-4.5 4.5 4.5" />
          <path d="M5 19h14" />
        </svg>
      );
    case "trash":
      return (
        <svg {...commonProps}>
          <path d="M5 7h14" />
          <path d="M9 7V5h6v2" />
          <path d="M7 7l1 13h8l1-13" />
          <path d="M10.5 11v5" />
          <path d="M13.5 11v5" />
        </svg>
      );
    case "checklist":
      return (
        <svg {...commonProps}>
          <path d="M9.5 7h8" />
          <path d="M9.5 12h8" />
          <path d="M9.5 17h8" />
          <path d="m4.8 7 1.2 1.3 2-2.3" />
          <path d="m4.8 12 1.2 1.3 2-2.3" />
          <path d="m4.8 17 1.2 1.3 2-2.3" />
        </svg>
      );
    case "close":
      return (
        <svg {...commonProps}>
          <path d="m6 6 12 12" />
          <path d="m18 6-12 12" />
        </svg>
      );
    case "history":
      return (
        <svg {...commonProps}>
          <path d="M4 12a8 8 0 1 0 2.3-5.7" />
          <path d="M4 5v5h5" />
          <path d="M12 8v4l2.8 1.7" />
        </svg>
      );
    case "edit":
      return (
        <svg {...commonProps}>
          <path d="m4.5 19.5 3.3-.8L18 8.5l-2.5-2.5L5.3 16.2l-.8 3.3Z" />
          <path d="m13.8 5.7 2.5 2.5" />
        </svg>
      );
  }

  return null;
}

function ButtonLabel({ icon, children }: { icon: IconName; children: ReactNode }) {
  return (
    <span className="button-content">
      <span className="button-icon" aria-hidden="true">
        <AppIcon name={icon} size={16} />
      </span>
      <span>{children}</span>
    </span>
  );
}

function QuickPhraseButtons({ onInsert }: { onInsert: (phrase: string) => void }) {
  return (
    <div className="quick-phrase-row" aria-label="Quick report phrases">
      {quickReportPhrases.map((phrase) => <button key={phrase} className="text-button" type="button" onClick={() => onInsert(phrase)}>+ {phrase.slice(0, 28)}…</button>)}
    </div>
  );
}

function getRoleWorkspaceCopy(role: WorkspaceRole, snapshot: WorkspaceSnapshot): {
  headerSummary: string;
  headerNote: string;
  dashboardEyebrow: string;
  dashboardTitle: string;
  dashboardSummary: string;
  laneOrder: DashboardLaneKey[];
} {
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
    default:
      return {
        headerSummary: screenContent.dashboard.summary,
        headerNote: "Keep drafting, sign-off, and follow-up in one queue.",
        dashboardEyebrow: "Clinical queue",
        dashboardTitle: "Queue overview",
        dashboardSummary: "Start new work, clear active items, and keep the case trail intact.",
        laneOrder: ["drafts", "ready", "tasks"]
      };
  }
}
const defaultMeta: MetaPayload = {
  appName: appConfig.appName,
  odooRecommendedModule: appConfig.odooRecommendedModule,
  odooRecommendedModuleLabel: appConfig.odooRecommendedModuleLabel,
  workflowSteps: workflowStepsByProcedure.colonoscopy,
  workflowStepsByProcedure,
  dashboardSnapshot: {
    activeDrafts: 0,
    openTasks: 0,
    finalizedToday: 0
  }
};
type StartCaseForm = Omit<StartCasePayload, "procedureType" | "dobOrAge"> & {
  procedureType: ProcedureType | "";
  dobOrAge: string;
};

const initialCaseForm: StartCaseForm = {
  procedureType: "",
  patientIdentifier: "",
  procedureDatetime: "",
  dobOrAge: "",
  sex: "unknown",
  facilityCode: "",
  facilityUnit: "",
  endoscopistUserId: "",
  referrerService: "",
  assistantNurseUserId: ""
};

const dateLabelFormatter = new Intl.DateTimeFormat("en-US", {
  weekday: "long",
  month: "long",
  day: "numeric"
});
const dateTimeFormatter = new Intl.DateTimeFormat("en-US", {
  month: "short",
  day: "numeric",
  hour: "numeric",
  minute: "2-digit"
});
const shortDateFormatter = new Intl.DateTimeFormat("en-US", {
  month: "short",
  day: "numeric"
});
const timeFormatter = new Intl.DateTimeFormat("en-US", {
  hour: "numeric",
  minute: "2-digit"
});

function asDateValue(value: string | undefined | null): Date | null {
  if (!value) {
    return null;
  }

  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

function toIsoDatetime(value: string): string {
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? value : parsed.toISOString();
}

function toLocalDateTimeValue(value: string | undefined | null): string {
  const parsed = asDateValue(value);
  if (!parsed) {
    return value || "";
  }

  const localValue = new Date(parsed.getTime() - parsed.getTimezoneOffset() * 60000);
  return localValue.toISOString().slice(0, 16);
}

function toDateInputValue(value: string | undefined | null): string {
  if (!value) {
    return "";
  }
  return value.includes("T") ? value.slice(0, 10) : value;
}

function formatLabel(value: string): string {
  return value
    .split("_")
    .map((part) => (part ? `${part.slice(0, 1).toUpperCase()}${part.slice(1)}` : part))
    .join(" ");
}

function formatProcedureLabel(procedure: StartCasePayload["procedureType"]): string {
  if (procedure === "egd" || procedure === "ercp" || procedure === "eus") {
    return procedure.toUpperCase();
  }
  return "Colonoscopy";
}

function formatTaskTypeLabel(taskType: FollowUpTask["type"]): string {
  return formatLabel(taskType);
}

function formatStatusLabel(status: string): string {
  return formatLabel(status);
}

function formatDateTime(value: string): string {
  const parsed = asDateValue(value);
  return parsed ? dateTimeFormatter.format(parsed) : value;
}

function clinicianMatchesFacility(option: ClinicianLookupOption, facilityCode: string | null | undefined): boolean {
  if (!facilityCode || option.facilityCodes === undefined) {
    return true;
  }
  return option.facilityCodes.includes(facilityCode);
}

function nurseMatchesEndoscopist(option: ClinicianLookupOption, endoscopistUserId: string | null | undefined): boolean {
  if (!endoscopistUserId) {
    return false;
  }
  if (option.endoscopistUserIds === undefined) {
    return true;
  }
  return option.endoscopistUserIds.includes(endoscopistUserId);
}

function filterNursesForCase(
  options: ClinicianLookupOption[],
  endoscopistUserId: string | null | undefined,
  facilityCode: string | null | undefined,
): ClinicianLookupOption[] {
  return options.filter((option) => nurseMatchesEndoscopist(option, endoscopistUserId) && clinicianMatchesFacility(option, facilityCode));
}

function singleFacilityCode(option: ClinicianLookupOption | null | undefined): string | null {
  const codes = [...new Set((option?.facilityCodes || []).map((code) => code.trim()).filter(Boolean))];
  return codes.length === 1 ? codes[0] ?? null : null;
}

function formatFileSize(sizeBytes?: number | null): string {
  if (!sizeBytes || sizeBytes < 1) {
    return "Size not recorded";
  }
  if (sizeBytes < 1024) {
    return `${sizeBytes} B`;
  }
  if (sizeBytes < 1024 * 1024) {
    return `${(sizeBytes / 1024).toFixed(1)} KB`;
  }
  return `${(sizeBytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatShortDate(value: string): string {
  const parsed = asDateValue(value);
  return parsed ? shortDateFormatter.format(parsed) : value;
}

function formatSessionExpiry(value: string): string {
  const parsed = asDateValue(value);
  if (!parsed) {
    return value;
  }

  const now = new Date();
  const sameDay =
    parsed.getFullYear() === now.getFullYear() &&
    parsed.getMonth() === now.getMonth() &&
    parsed.getDate() === now.getDate();
  return sameDay ? timeFormatter.format(parsed) : `${shortDateFormatter.format(parsed)} ${timeFormatter.format(parsed)}`;
}

function parseNullableNumber(value: string): number | null {
  if (!value.trim()) {
    return null;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function getCaseStatusTone(status: CaseSummary["status"]): StatusTone {
  switch (status) {
    case "ready_for_signoff":
      return "warning";
    case "finalized":
      return "success";
    case "draft_reopened":
      return "critical";
    case "draft":
    default:
      return "accent";
  }
}

function getTaskStatusTone(status: FollowUpTask["status"]): StatusTone {
  switch (status) {
    case "closed":
      return "success";
    case "cancelled":
      return "neutral";
    case "in_progress":
      return "accent";
    case "open":
    default:
      return "warning";
  }
}

function getErrorPresentation(
  message: string,
  screen: ScreenKey
): { title: string; body: string; actionLabel: string; actionKind: "reload" | "cases" } {
  const normalized = message.trim().toLowerCase();

  if (screen === "case-detail" && normalized === "not found") {
    return {
      title: "Selected case unavailable",
      body: "This case is no longer available in the queue. Return to cases and open another record.",
      actionLabel: "Back to cases",
      actionKind: "cases"
    };
  }

  if (normalized === "not found") {
    return {
      title: "Queue data unavailable",
      body: "The workspace could not load the live queue. Reload the queue or confirm the clinical API is still serving the expected endpoints.",
      actionLabel: "Reload queue",
      actionKind: "reload"
    };
  }

  if (screen === "case-detail") {
    return {
      title: "Case data unavailable",
      body: message,
      actionLabel: "Back to cases",
      actionKind: "cases"
    };
  }

  return {
    title: "Workspace data unavailable",
    body: message,
    actionLabel: "Reload queue",
    actionKind: "reload"
  };
}

function isActionableTask(task: FollowUpTask): boolean {
  return task.status === "open" || task.status === "in_progress";
}

function isDraftLikeCase(caseItem: CaseSummary): boolean {
  return caseItem.status === "draft" || caseItem.status === "draft_reopened";
}

function compareCaseByRecent(left: CaseSummary, right: CaseSummary): number {
  return (asDateValue(right.procedureDatetime)?.getTime() ?? 0) - (asDateValue(left.procedureDatetime)?.getTime() ?? 0);
}

function taskStatusRank(status: FollowUpTask["status"]): number {
  switch (status) {
    case "open":
      return 0;
    case "in_progress":
      return 1;
    case "closed":
      return 2;
    case "cancelled":
    default:
      return 3;
  }
}

function compareTaskByPriority(left: FollowUpTask, right: FollowUpTask): number {
  const statusDiff = taskStatusRank(left.status) - taskStatusRank(right.status);
  if (statusDiff !== 0) {
    return statusDiff;
  }

  const leftDue = asDateValue(left.dueDate);
  const rightDue = asDateValue(right.dueDate);
  if (leftDue && rightDue) {
    return leftDue.getTime() - rightDue.getTime();
  }
  if (leftDue) {
    return -1;
  }
  if (rightDue) {
    return 1;
  }
  return left.type.localeCompare(right.type);
}

function getDueMeta(dueDate?: string): { label: string; tone: StatusTone } {
  if (!dueDate) {
    return { label: "No due date", tone: "neutral" };
  }

  const parsed = asDateValue(dueDate);
  if (!parsed) {
    return { label: dueDate, tone: "neutral" };
  }

  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const target = new Date(parsed);
  target.setHours(0, 0, 0, 0);
  const diffDays = Math.round((target.getTime() - today.getTime()) / 86400000);

  if (diffDays < 0) {
    return { label: `Overdue - ${formatShortDate(dueDate)}`, tone: "critical" };
  }
  if (diffDays === 0) {
    return { label: `Due today - ${formatShortDate(dueDate)}`, tone: "warning" };
  }
  if (diffDays <= 2) {
    return { label: `Due soon - ${formatShortDate(dueDate)}`, tone: "accent" };
  }
  return { label: `Due ${formatShortDate(dueDate)}`, tone: "neutral" };
}

function countFinalizedToday(cases: CaseSummary[]): number {
  const now = new Date();
  return cases.filter((entry) => {
    const parsed = asDateValue(entry.procedureDatetime);
    if (!parsed || entry.status !== "finalized") {
      return false;
    }
    return (
      parsed.getFullYear() === now.getFullYear() &&
      parsed.getMonth() === now.getMonth() &&
      parsed.getDate() === now.getDate()
    );
  }).length;
}

function countCaseOpenTasks(caseDraft: ClinicalDraftCasePayload): number {
  return caseDraft.followup_tasks.filter((task) => task.task_status === "open" || task.task_status === "in_progress").length;
}

function normalizeCaseForSave(caseDraft: ClinicalDraftCasePayload, lookups: ClinicalLookupsPayload): ClinicalDraftCasePayload {
  const facilityUnit = lookups.facilityUnits.find((option) => option.code === caseDraft.facility_unit_code);
  const facility = lookups.facilities.find((option) => option.code === caseDraft.facility_code);
  return {
    ...caseDraft,
    procedure_datetime: toIsoDatetime(caseDraft.procedure_datetime),
    facility_code: facilityUnit?.facilityCode || facility?.code || caseDraft.facility_code || null,
    facility_unit_code: facilityUnit?.code || caseDraft.facility_unit_code || null,
    facility_unit: facilityUnit?.label || facility?.label || caseDraft.facility_unit,
    image_attachments: caseDraft.image_attachments || []
  };
}

function buildSelectedCaseScreenCopy(caseDraft: ClinicalDraftCasePayload | null): { eyebrow: string; title: string; summary: string } {
  if (!caseDraft) {
    return screenContent["case-detail"];
  }

  return {
    eyebrow: `${formatProcedureLabel(caseDraft.procedure_type)} - ${formatStatusLabel(caseDraft.case_status)}`,
    title: caseDraft.patient_identifier,
    summary: `Case ${caseDraft.external_case_id} - ${formatDateTime(caseDraft.procedure_datetime)}`
  };
}

function createEmptySegment(): CaseSegmentPayload {
  return {
    segment_name: segmentNameOptions[0]?.value || "cecum",
    normal: false,
    finding_note: "",
    photo_taken: false
  };
}

function createEmptyLesion(existingCount: number): CaseLesionPayload {
  return {
    lesion_index: existingCount + 1,
    lesion_location: "",
    lesion_size_mm: null,
    lesion_morphology: "",
    resection_method: "",
    complete_resection: false,
    retrieved: false,
    specimen_container_ref: ""
  };
}

function createEmptySpecimen(): CaseSpecimenPayload {
  return {
    container_label: "",
    specimen_site: "",
    specimen_count: null,
    test_question: "",
    label_verified: false
  };
}

function createEmptyTask(): ClinicalFollowUpTaskPayload {
  return {
    task_type: "pathology_review",
    task_status: "open",
    task_owner_user_id: "",
    task_owner_user_ref: "",
    due_date: "",
    resolution_note: ""
  };
}

export default function App() {
  const [session, setSession] = useState<AuthenticatedSessionPayload | null>(() => getStoredSession());
  const [activeScreen, setActiveScreen] = useState<ScreenKey>("dashboard");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [authError, setAuthError] = useState<string | null>(null);
  const [banner, setBanner] = useState<{ tone: BannerTone; text: string } | null>(null);
  const [bundle, setBundle] = useState<ApiBundle | null>(null);
  const [caseQuery, setCaseQuery] = useState("");
  const [taskQuery, setTaskQuery] = useState("");
  const [caseSubmitting, setCaseSubmitting] = useState(false);
  const [signingIn, setSigningIn] = useState(false);
  const [caseForm, setCaseForm] = useState<StartCaseForm>(initialCaseForm);
  const caseFormTouchedFields = useRef<Set<string>>(new Set());
  const notifiedWorkIds = useRef<Set<string>>(new Set());
  const [patientRelationshipSuggestion, setPatientRelationshipSuggestion] = useState<PatientRelationshipSuggestion | null>(null);
  const [patientRelationshipLoading, setPatientRelationshipLoading] = useState(false);
  const [patientSearchResults, setPatientSearchResults] = useState<PatientLookupOption[]>([]);
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null);
  const [caseDetail, setCaseDetail] = useState<ClinicalDraftCasePayload | null>(null);
  const [caseHistory, setCaseHistory] = useState<CaseHistoryPayload | null>(null);
  const [caseDetailLoading, setCaseDetailLoading] = useState(false);
  const [caseHistoryLoading, setCaseHistoryLoading] = useState(false);
  const [caseSaving, setCaseSaving] = useState(false);
  const [caseLastSavedAt, setCaseLastSavedAt] = useState<string | null>(null);
  const autosaveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [caseActionLoading, setCaseActionLoading] = useState<CaseActionName | null>(null);
  const [taskSavingId, setTaskSavingId] = useState<string | null>(null);
  const [imageUploading, setImageUploading] = useState(false);
  const [imageDeletingId, setImageDeletingId] = useState<string | null>(null);
  const [reopenReason, setReopenReason] = useState("");

  const deferredCaseQuery = useDeferredValue(caseQuery);
  const deferredTaskQuery = useDeferredValue(taskQuery);
  const todayLabel = useMemo(() => dateLabelFormatter.format(new Date()), []);

  const meta = bundle?.meta ?? defaultMeta;
  const lookups = bundle?.lookups ?? defaultLookups;
  const cases = bundle?.cases ?? [];
  const tasks = bundle?.tasks ?? [];
  const caseScreenCopy = buildSelectedCaseScreenCopy(caseDetail);
  const activeRole: WorkspaceRole = session?.primaryRole ?? "endoscopist";

  const sortedCases = useMemo(() => [...cases].sort(compareCaseByRecent), [cases]);
  const sortedTasks = useMemo(() => [...tasks].sort(compareTaskByPriority), [tasks]);
  const draftOrReopenedCases = useMemo(() => sortedCases.filter(isDraftLikeCase), [sortedCases]);
  const readyForSignoffCases = useMemo(() => sortedCases.filter((entry) => entry.status === "ready_for_signoff"), [sortedCases]);
  const openTasks = useMemo(() => sortedTasks.filter(isActionableTask), [sortedTasks]);
  const finalizedTodayCount = useMemo(() => countFinalizedToday(sortedCases), [sortedCases]);
  const workspaceSnapshot = useMemo<WorkspaceSnapshot>(() => ({
    drafts: draftOrReopenedCases.length,
    ready: readyForSignoffCases.length,
    tasks: openTasks.length,
    finalizedToday: finalizedTodayCount
  }), [draftOrReopenedCases.length, readyForSignoffCases.length, openTasks.length, finalizedTodayCount]);

  useEffect(() => {
    if (!session || typeof window === "undefined" || !("Notification" in window) || window.Notification.permission !== "granted") {
      return;
    }
    const overdue = sortedTasks.filter((task) => isActionableTask(task) && getDueMeta(task.dueDate).tone === "critical");
    const ready = readyForSignoffCases;
    for (const task of overdue) {
      const key = `task:${task.id}`;
      if (!notifiedWorkIds.current.has(key)) {
        new window.Notification("Overdue follow-up task", { body: `${task.type.replaceAll("_", " ")} for case ${task.caseId}` });
        notifiedWorkIds.current.add(key);
      }
    }
    for (const report of ready) {
      const key = `case:${report.id}`;
      if (!notifiedWorkIds.current.has(key)) {
        new window.Notification("Report ready for sign-off", { body: `${report.patientIdentifier} - ${report.procedureType.toUpperCase()}` });
        notifiedWorkIds.current.add(key);
      }
    }
  }, [readyForSignoffCases, session, sortedTasks]);
  const roleWorkspaceCopy = useMemo(() => getRoleWorkspaceCopy(activeRole, workspaceSnapshot), [activeRole, workspaceSnapshot]);
  const screenCopy = activeScreen === "case-detail"
    ? caseScreenCopy
    : activeScreen === "dashboard"
      ? { ...screenContent.dashboard, summary: roleWorkspaceCopy.headerSummary }
      : screenContent[activeScreen];
  const shellWarningMessage = (bundle?.warnings ?? []).join(" ");
  const errorPresentation = error ? getErrorPresentation(error, activeScreen) : null;
  const caseWorkflowSteps = caseDetail ? meta.workflowStepsByProcedure[caseDetail.procedure_type] ?? meta.workflowSteps : meta.workflowSteps;

  const filteredCases = useMemo(() => {
    const query = deferredCaseQuery.trim().toLowerCase();
    if (!query) {
      return sortedCases;
    }

    return sortedCases.filter((entry) => {
      const haystack = `${entry.patientIdentifier} ${entry.endoscopistName} ${entry.procedureType} ${entry.status}`.toLowerCase();
      return haystack.includes(query);
    });
  }, [deferredCaseQuery, sortedCases]);

  const filteredTasks = useMemo(() => {
    const query = deferredTaskQuery.trim().toLowerCase();
    if (!query) {
      return sortedTasks;
    }

    return sortedTasks.filter((entry) => {
      const haystack = `${entry.ownerName} ${entry.type} ${entry.status} ${entry.caseId}`.toLowerCase();
      return haystack.includes(query);
    });
  }, [deferredTaskQuery, sortedTasks]);

  const selectedCaseFormUnit = lookups.facilityUnits.find((option) => option.code === caseForm.facilityUnit);
  const caseFormEndoscopist = lookups.endoscopists.find((option) => option.userId === caseForm.endoscopistUserId)
    || (session?.primaryRole === "endoscopist" && session.login === caseForm.endoscopistUserId
      ? { userId: session.login, label: session.displayName, role: "endoscopist" as const, facilityCodes: session.facilityCodes }
      : null);
  const inferredFacilityCode = singleFacilityCode(caseFormEndoscopist);
  const selectedCaseFormFacilityCode = caseForm.facilityCode || selectedCaseFormUnit?.facilityCode || inferredFacilityCode || null;

  const endoscopistOptions = useMemo(() => {
    const byId = new Map<string, ClinicianLookupOption>();
    for (const option of lookups.endoscopists) {
      if (!clinicianMatchesFacility(option, selectedCaseFormFacilityCode)) {
        continue;
      }
      byId.set(option.userId, option);
    }
    if (session?.primaryRole === "endoscopist" && !byId.has(session.login)) {
      byId.set(session.login, { userId: session.login, label: session.displayName, role: "endoscopist", facilityCodes: session.facilityCodes });
    }
    return Array.from(byId.values()).sort((left, right) => left.label.localeCompare(right.label));
  }, [lookups.endoscopists, selectedCaseFormFacilityCode, session]);

  const allNurseOptions = useMemo(() => {
    const byId = new Map<string, ClinicianLookupOption>();
    for (const option of lookups.nurses) {
      if (!clinicianMatchesFacility(option, selectedCaseFormFacilityCode)) {
        continue;
      }
      byId.set(option.userId, option);
    }
    if (session?.primaryRole === "nurse" && !byId.has(session.login)) {
      byId.set(session.login, { userId: session.login, label: session.displayName, role: "nurse", endoscopistUserIds: [], facilityCodes: session.facilityCodes });
    }
    return Array.from(byId.values()).sort((left, right) => left.label.localeCompare(right.label));
  }, [lookups.nurses, selectedCaseFormFacilityCode, session]);
  const nurseOptions = useMemo(
    () => filterNursesForCase(allNurseOptions, caseForm.endoscopistUserId, selectedCaseFormFacilityCode),
    [allNurseOptions, caseForm.endoscopistUserId, selectedCaseFormFacilityCode],
  );

  const facilityUnitOptions = lookups.facilityUnits.filter((option) => !selectedCaseFormFacilityCode || option.facilityCode === selectedCaseFormFacilityCode);
  const referrerServiceOptions = lookups.referrerServices;
  const activeFacilityUnits = useMemo(() => {
    if (!caseDetail?.facility_code) {
      return facilityUnitOptions;
    }
    const matchingUnits = facilityUnitOptions.filter((option) => option.facilityCode === caseDetail.facility_code);
    return matchingUnits.length ? matchingUnits : facilityUnitOptions;
  }, [caseDetail?.facility_code, facilityUnitOptions]);

  useEffect(() => {
    if (!session) {
      return;
    }

    setCaseForm((current) => {
      const nextForm = { ...current };
      let changed = false;

      if (!current.endoscopistUserId && session.primaryRole === "endoscopist") {
        nextForm.endoscopistUserId = session.login;
        changed = true;
      }
      return changed ? nextForm : current;
    });
  }, [session]);

  useEffect(() => {
    if (!inferredFacilityCode) {
      return;
    }
    setCaseForm((current) => current.facilityCode ? current : { ...current, facilityCode: inferredFacilityCode });
  }, [inferredFacilityCode]);

  useEffect(() => {
    setCaseForm((current) => {
      const selectedNurse = current.assistantNurseUserId
        ? allNurseOptions.find((option) => option.userId === current.assistantNurseUserId)
        : null;
      const selectedEndoscopist = current.endoscopistUserId
        ? endoscopistOptions.find((option) => option.userId === current.endoscopistUserId)
        : null;
      if (current.endoscopistUserId && !selectedEndoscopist) {
        return { ...current, endoscopistUserId: "", assistantNurseUserId: "" };
      }
      if (selectedNurse && !filterNursesForCase([selectedNurse], current.endoscopistUserId, selectedCaseFormFacilityCode).length) {
        return { ...current, assistantNurseUserId: "" };
      }
      if (
        !current.assistantNurseUserId &&
        session?.primaryRole === "nurse" &&
        allNurseOptions.some((option) => option.userId === session.login && filterNursesForCase([option], current.endoscopistUserId, selectedCaseFormFacilityCode).length)
      ) {
        return { ...current, assistantNurseUserId: session.login };
      }
      return current;
    });
  }, [allNurseOptions, endoscopistOptions, caseForm.endoscopistUserId, selectedCaseFormFacilityCode, session]);

  useEffect(() => {
    setCaseForm((current) => {
      const nextForm = { ...current };
      let changed = false;

      if (current.facilityUnit && !facilityUnitOptions.some((option) => option.code === current.facilityUnit)) {
        nextForm.facilityUnit = "";
        changed = true;
      }

      if (!current.referrerService && referrerServiceOptions[0]) {
        nextForm.referrerService = referrerServiceOptions[0].value;
        changed = true;
      } else if (
        current.referrerService &&
        !referrerServiceOptions.some((option) => option.value === current.referrerService)
      ) {
        nextForm.referrerService = referrerServiceOptions[0]?.value || "";
        changed = true;
      }

      return changed ? nextForm : current;
    });
  }, [facilityUnitOptions, referrerServiceOptions]);

  useEffect(() => {
    const query = caseForm.patientIdentifier.trim();
    if (query.length < 2) {
      setPatientSearchResults([]);
      return;
    }
    let cancelled = false;
    const timer = window.setTimeout(() => {
      searchPatients(query).then((results) => {
        if (!cancelled) setPatientSearchResults(results);
      }).catch(() => {
        if (!cancelled) setPatientSearchResults([]);
      });
    }, 250);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [caseForm.patientIdentifier]);

  useEffect(() => {
    if (!session) {
      setLoading(false);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);
    setAuthError(null);

    fetchShellData()
      .then((result) => {
        if (!cancelled) {
          setBundle(result);
        }
      })
      .catch((loadError: unknown) => {
        if (!cancelled) {
          if (loadError instanceof ApiRequestError && loadError.status === 401) {
            clearStoredSession();
            setSession(null);
            setBundle(null);
            setCaseDetail(null);
            setCaseHistory(null);
            setSelectedCaseId(null);
            setAuthError("Your session expired or is no longer valid. Sign in again.");
            return;
          }
          setError(loadError instanceof Error ? loadError.message : "Failed to load the clinical workspace.");
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [session]);

  useEffect(() => {
    if (!session || !selectedCaseId) {
      setCaseDetail(null);
      setCaseHistory(null);
      return;
    }
    if (activeScreen !== "case-detail") {
      return;
    }

    let cancelled = false;
    setCaseDetailLoading(true);
    setCaseHistoryLoading(true);

    Promise.all([fetchCaseDetail(selectedCaseId), fetchCaseHistory(selectedCaseId)])
      .then(([detailResult, historyResult]) => {
        if (!cancelled) {
          setCaseDetail(detailResult);
          setCaseHistory(historyResult);
          if (detailResult.case_status !== "finalized") {
            setReopenReason("");
          }
        }
      })
      .catch((loadError: unknown) => {
        if (cancelled) {
          return;
        }
        if (loadError instanceof ApiRequestError && loadError.status === 401) {
          clearStoredSession();
          setSession(null);
          setBundle(null);
          setCaseDetail(null);
          setCaseHistory(null);
          setSelectedCaseId(null);
          setAuthError("Your session expired or is no longer valid. Sign in again.");
          return;
        }
        setError(loadError instanceof Error ? loadError.message : "Failed to load the selected case.");
      })
      .finally(() => {
        if (!cancelled) {
          setCaseDetailLoading(false);
          setCaseHistoryLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [activeScreen, selectedCaseId, session]);

  async function refreshWorkspace(): Promise<void> {
    const nextBundle = await fetchShellData();
    setBundle(nextBundle);
  }

  async function handleReloadWorkspace() {
    setBanner(null);
    setError(null);
    setLoading(true);

    try {
      await refreshWorkspace();
    } catch (refreshError: unknown) {
      setError(refreshError instanceof Error ? refreshError.message : "Queue data could not be refreshed.");
    } finally {
      setLoading(false);
    }
  }

  function handleNav(screen: ScreenKey) {
    if (activeScreen === "case-detail" && screen !== "case-detail") {
      setError(null);
    }
    startTransition(() => setActiveScreen(screen));
  }

  function updateCaseForm<K extends keyof StartCaseForm>(field: K, value: StartCaseForm[K]) {
    caseFormTouchedFields.current.add(String(field));
    setCaseForm((current) => {
      const nextForm = {
        ...current,
        [field]: value
      };
      if (field === "endoscopistUserId") {
        const selectedEndoscopist = lookups.endoscopists.find((option) => option.userId === value)
          || (session?.primaryRole === "endoscopist" && session.login === value
            ? { userId: session.login, label: session.displayName, role: "endoscopist" as const, facilityCodes: session.facilityCodes }
            : null);
        const endoscopistFacilityCode = singleFacilityCode(selectedEndoscopist);
        const selectedFacilityIsValid = !nextForm.facilityCode || Boolean(selectedEndoscopist?.facilityCodes?.includes(nextForm.facilityCode));
        if (!selectedFacilityIsValid) {
          nextForm.facilityCode = endoscopistFacilityCode || "";
          nextForm.facilityUnit = "";
          nextForm.assistantNurseUserId = "";
        }
        const selectedNurse = nextForm.assistantNurseUserId
          ? allNurseOptions.find((option) => option.userId === nextForm.assistantNurseUserId)
          : null;
        if (selectedNurse && !filterNursesForCase([selectedNurse], String(value || ""), selectedCaseFormFacilityCode).length) {
          nextForm.assistantNurseUserId = "";
        }
      }
      if (field === "facilityCode" && value !== current.facilityCode) {
        nextForm.facilityUnit = "";
        nextForm.endoscopistUserId = "";
        nextForm.assistantNurseUserId = "";
      }
      return nextForm;
    });
  }

  function openCase(externalCaseId: string) {
    setSelectedCaseId(externalCaseId);
    handleNav("case-detail");
    setBanner(null);
    setError(null);
  }

  function handleApiFailure(requestError: unknown, fallbackMessage: string): boolean {
    if (requestError instanceof ApiRequestError && requestError.status === 401) {
      clearStoredSession();
      setSession(null);
      setBundle(null);
      setCaseDetail(null);
      setCaseHistory(null);
      setSelectedCaseId(null);
      setAuthError("Your session expired or is no longer valid. Sign in again.");
      setBanner(null);
      return true;
    }

    const message = requestError instanceof Error ? requestError.message : fallbackMessage;
    setBanner({ tone: "error", text: message });
    return false;
  }

  async function handleSignIn(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSigningIn(true);
    setAuthError(null);

    const formData = new FormData(event.currentTarget);
    const payload: LoginPayload = {
      login: String(formData.get("login") || "").trim(),
      password: String(formData.get("password") || "")
    };

    if (!payload.login || !payload.password) {
      setAuthError("Enter your workspace login and password.");
      setSigningIn(false);
      return;
    }

    try {
      const nextSession = await loginClinician(payload);
      storeSession(nextSession);
      setSession(nextSession);
      setError(null);
      setBanner(null);
      setActiveScreen("dashboard");
      setSelectedCaseId(null);
      setCaseDetail(null);
      setCaseHistory(null);
      setCaseForm({
        ...initialCaseForm,
        endoscopistUserId: nextSession.primaryRole === "endoscopist" ? nextSession.login : "",
        assistantNurseUserId: nextSession.primaryRole === "nurse" ? nextSession.login : ""
      });
      event.currentTarget.reset();
    } catch (signInError: unknown) {
      setAuthError(signInError instanceof Error ? signInError.message : "Sign-in failed.");
    } finally {
      setSigningIn(false);
    }
  }

  async function handleSignOut() {
    try {
      await logoutClinician();
    } catch {
      // Clear the client session even if the API session has already expired.
    }

    clearStoredSession();
    setSession(null);
    setBundle(null);
    setCaseDetail(null);
    setCaseHistory(null);
    setSelectedCaseId(null);
    setError(null);
    setAuthError(null);
    setBanner(null);
    caseFormTouchedFields.current.clear();
    setCaseForm(initialCaseForm);
    setActiveScreen("dashboard");
  }

  async function handleCreateCase(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!caseForm.procedureType) {
      setBanner({ tone: "error", text: "Select a case type before creating a draft." });
      return;
    }
    setCaseSubmitting(true);
    setBanner(null);

    try {
      const response = await submitStartCase({
        ...caseForm,
        ...(selectedCaseFormFacilityCode ? { facilityCode: selectedCaseFormFacilityCode } : {}),
        procedureType: caseForm.procedureType,
        procedureDatetime: toIsoDatetime(caseForm.procedureDatetime)
      });
      await refreshWorkspace();
      if (response.externalCaseId) {
        openCase(response.externalCaseId);
      } else {
        handleNav("cases");
      }
      setBanner({ tone: "success", text: response.externalCaseId ? `${response.message} (${response.externalCaseId})` : response.message });
      caseFormTouchedFields.current.clear();
      setCaseForm({
        ...initialCaseForm,
        endoscopistUserId: session?.primaryRole === "endoscopist" ? session.login : "",
        assistantNurseUserId: session?.primaryRole === "nurse" ? session.login : ""
      });
    } catch (submitError: unknown) {
      if (!handleApiFailure(submitError, "Case creation failed.")) {
        setCaseSubmitting(false);
      }
      return;
    }

    setCaseSubmitting(false);
  }

  async function handlePatientIdentifierBlur(identifierOverride?: string) {
    const identifier = (identifierOverride ?? caseForm.patientIdentifier).trim();
    if (!identifier) {
      setPatientRelationshipSuggestion(null);
      return;
    }
    setPatientRelationshipLoading(true);
    try {
      const suggestion = await fetchPatientRelationship(identifier);
      setPatientRelationshipSuggestion(suggestion);
      if (suggestion) {
        setCaseForm((current) => ({
          ...current,
          facilityCode: caseFormTouchedFields.current.has("facilityCode")
            ? current.facilityCode || ""
            : suggestion.facilityCode,
          facilityUnit: caseFormTouchedFields.current.has("facilityUnit")
            ? current.facilityUnit
            : suggestion.facilityUnitCode || current.facilityUnit,
          endoscopistUserId: caseFormTouchedFields.current.has("endoscopistUserId")
            ? current.endoscopistUserId
            : suggestion.endoscopistUserId,
        }));
      }
    } catch {
      setPatientRelationshipSuggestion(null);
    } finally {
      setPatientRelationshipLoading(false);
    }
  }

  function handleSelectPatient(patient: PatientLookupOption) {
    caseFormTouchedFields.current.delete("facilityCode");
    caseFormTouchedFields.current.delete("facilityUnit");
    caseFormTouchedFields.current.delete("endoscopistUserId");
    setPatientSearchResults([]);
    setCaseForm((current) => ({
      ...current,
      patientIdentifier: patient.patientIdentifier,
      dobOrAge: patient.dobOrAge || current.dobOrAge,
      sex: patient.sex || current.sex,
    }));
    void handlePatientIdentifierBlur(patient.patientIdentifier);
  }

  function updateCaseDetailField<K extends keyof ClinicalDraftCasePayload>(field: K, value: ClinicalDraftCasePayload[K]) {
    setCaseDetail((current) => {
      if (!current) {
        return current;
      }

      const nextCase = { ...current, [field]: value };
      if (field === "bbps_right" || field === "bbps_transverse" || field === "bbps_left") {
        const scores = [nextCase.bbps_right, nextCase.bbps_transverse, nextCase.bbps_left];
        nextCase.bbps_total = scores.every((score) => typeof score === "number")
          ? scores.reduce((total, score) => total + Number(score), 0)
          : null;
      }
      if (field === "endoscopist_user_id") {
        const endoscopist = lookups.endoscopists.find((option) => option.userId === value && clinicianMatchesFacility(option, nextCase.facility_code));
        nextCase.endoscopist_user_ref = endoscopist?.label || null;
        const selectedNurse = nextCase.assistant_nurse_user_id
          ? lookups.nurses.find((option) => option.userId === nextCase.assistant_nurse_user_id)
          : null;
        if (selectedNurse && !filterNursesForCase([selectedNurse], String(value || ""), nextCase.facility_code).length) {
          nextCase.assistant_nurse_user_id = null;
          nextCase.assistant_nurse_user_ref = null;
        }
      }
      if (field === "assistant_nurse_user_id") {
        const nurse = lookups.nurses.find((option) => option.userId === value && clinicianMatchesFacility(option, nextCase.facility_code));
        nextCase.assistant_nurse_user_ref = nurse?.label || null;
      }
      return nextCase;
    });
    queueCaseAutosave();
  }

  function queueCaseAutosave() {
    if (autosaveTimerRef.current) clearTimeout(autosaveTimerRef.current);
    autosaveTimerRef.current = setTimeout(() => {
      autosaveTimerRef.current = null;
      void handleSaveCaseDraft();
    }, 1500);
  }

  function updateCaseFacility(facilityCode: string) {
    setCaseDetail((current) => {
      if (!current) {
        return current;
      }

      const matchingFacility = lookups.facilities.find((option) => option.code === facilityCode);
      const matchingUnit = lookups.facilityUnits.find(
        (option) => option.code === current.facility_unit_code && option.facilityCode === facilityCode
      );
      const endoscopistAllowed = lookups.endoscopists.some(
        (option) => option.userId === current.endoscopist_user_id && clinicianMatchesFacility(option, facilityCode)
      );
      const nextEndoscopistUserId = endoscopistAllowed ? current.endoscopist_user_id ?? null : null;
      const nextAssistantNurseUserId = nextEndoscopistUserId ? current.assistant_nurse_user_id ?? null : null;

      return {
        ...current,
        facility_code: facilityCode || null,
        facility_unit_code: matchingUnit?.code || null,
        facility_unit: matchingUnit?.label || matchingFacility?.label || current.facility_unit,
        endoscopist_user_id: nextEndoscopistUserId,
        assistant_nurse_user_id: nextAssistantNurseUserId,
      };
    });
    queueCaseAutosave();
  }

  function updateCaseFacilityUnit(unitCode: string) {
    setCaseDetail((current) => {
      if (!current) {
        return current;
      }

      const matchingUnit = lookups.facilityUnits.find((option) => option.code === unitCode);
      const nextFacilityCode = matchingUnit?.facilityCode || current.facility_code || null;
      const endoscopistAllowed = lookups.endoscopists.some(
        (option) => option.userId === current.endoscopist_user_id && clinicianMatchesFacility(option, nextFacilityCode)
      );
      const nextEndoscopistUserId = endoscopistAllowed ? current.endoscopist_user_id ?? null : null;
      const nextAssistantNurseUserId = nextEndoscopistUserId ? current.assistant_nurse_user_id ?? null : null;
      return {
        ...current,
        facility_code: nextFacilityCode,
        facility_unit_code: matchingUnit?.code || null,
        facility_unit: matchingUnit?.label || current.facility_unit,
        endoscopist_user_id: nextEndoscopistUserId,
        assistant_nurse_user_id: nextAssistantNurseUserId,
      };
    });
    queueCaseAutosave();
  }

  function updateSegment(index: number, field: keyof CaseSegmentPayload, value: string | boolean) {
    setCaseDetail((current) => {
      if (!current) {
        return current;
      }
      const nextRows = [...current.segment_exam];
      const existing = nextRows[index];
      if (!existing) {
        return current;
      }
      nextRows[index] = { ...existing, [field]: value };
      return { ...current, segment_exam: nextRows };
    });
    queueCaseAutosave();
  }

  function updateLesion(index: number, field: keyof CaseLesionPayload, value: string | boolean | number | null) {
    setCaseDetail((current) => {
      if (!current) {
        return current;
      }
      const nextRows = [...current.lesions];
      const existing = nextRows[index];
      if (!existing) {
        return current;
      }
      nextRows[index] = { ...existing, [field]: value };
      return { ...current, lesions: nextRows };
    });
    queueCaseAutosave();
  }

  function updateSpecimen(index: number, field: keyof CaseSpecimenPayload, value: string | boolean | number | null) {
    setCaseDetail((current) => {
      if (!current) {
        return current;
      }
      const nextRows = [...current.specimens];
      const existing = nextRows[index];
      if (!existing) {
        return current;
      }
      nextRows[index] = { ...existing, [field]: value };
      return { ...current, specimens: nextRows };
    });
    queueCaseAutosave();
  }

  function updateFollowUpTask(index: number, field: keyof ClinicalFollowUpTaskPayload, value: string | null) {
    setCaseDetail((current) => {
      if (!current) {
        return current;
      }
      const nextRows = [...current.followup_tasks];
      const existing = nextRows[index];
      if (!existing) {
        return current;
      }
      nextRows[index] = { ...existing, [field]: value };
      return { ...current, followup_tasks: nextRows };
    });
    queueCaseAutosave();
  }

  function addSegment() {
    setCaseDetail((current) => (current ? { ...current, segment_exam: [...current.segment_exam, createEmptySegment()] } : current));
    queueCaseAutosave();
  }

  function removeSegment(index: number) {
    setCaseDetail((current) => (current ? { ...current, segment_exam: current.segment_exam.filter((_, itemIndex) => itemIndex !== index) } : current));
    queueCaseAutosave();
  }

  function addLesion() {
    setCaseDetail((current) => (current ? { ...current, lesions: [...current.lesions, createEmptyLesion(current.lesions.length)] } : current));
    queueCaseAutosave();
  }

  function removeLesion(index: number) {
    setCaseDetail((current) => (current ? { ...current, lesions: current.lesions.filter((_, itemIndex) => itemIndex !== index) } : current));
    queueCaseAutosave();
  }

  function addSpecimen() {
    setCaseDetail((current) => (current ? { ...current, specimens: [...current.specimens, createEmptySpecimen()] } : current));
    queueCaseAutosave();
  }

  function removeSpecimen(index: number) {
    setCaseDetail((current) => (current ? { ...current, specimens: current.specimens.filter((_, itemIndex) => itemIndex !== index) } : current));
    queueCaseAutosave();
  }

  function addFollowUpTask() {
    setCaseDetail((current) => (current ? { ...current, followup_tasks: [...current.followup_tasks, createEmptyTask()] } : current));
    queueCaseAutosave();
  }

  function removeFollowUpTask(index: number) {
    setCaseDetail((current) => (current ? { ...current, followup_tasks: current.followup_tasks.filter((_, itemIndex) => itemIndex !== index) } : current));
    queueCaseAutosave();
  }

  async function handleSaveCaseDraft() {
    if (!caseDetail) {
      return;
    }

    if (autosaveTimerRef.current) {
      clearTimeout(autosaveTimerRef.current);
      autosaveTimerRef.current = null;
    }

    setCaseSaving(true);
    setBanner(null);

    try {
      const response = await saveCaseDraft(caseDetail.external_case_id, normalizeCaseForSave(caseDetail, lookups));
      setCaseDetail(response.payload);
      setCaseHistory(await fetchCaseHistory(response.externalCaseId));
      await refreshWorkspace();
      setCaseLastSavedAt(new Date().toISOString());
      setBanner({ tone: "success", text: response.message });
    } catch (saveError: unknown) {
      if (!handleApiFailure(saveError, "Failed to save the draft case.")) {
        setCaseSaving(false);
      }
      return;
    }

    setCaseSaving(false);
  }

  async function handleCaseAction(action: CaseActionName) {
    if (!caseDetail) {
      return;
    }

    setCaseActionLoading(action);
    setBanner(null);

    try {
      const response = await runCaseAction(caseDetail.external_case_id, action, action === "reopen" ? { reason: reopenReason } : undefined);
      setCaseDetail(response.payload);
      setCaseHistory(await fetchCaseHistory(response.externalCaseId));
      if (action === "reopen") {
        setReopenReason("");
      }
      await refreshWorkspace();
      setBanner({ tone: "success", text: response.message });
    } catch (actionError: unknown) {
      if (!handleApiFailure(actionError, "Failed to run the case action.")) {
        setCaseActionLoading(null);
      }
      return;
    }

    setCaseActionLoading(null);
  }

  async function handleSaveTask(index: number) {
    if (!caseDetail) {
      return;
    }

    const task = caseDetail.followup_tasks[index];
    if (!task) {
      return;
    }
    const taskId = task.followup_task_id || task.external_task_id;
    if (!taskId) {
      setBanner({ tone: "error", text: "Save the draft first to create a new follow-up task before updating it individually." });
      return;
    }

    setTaskSavingId(taskId);
    setBanner(null);

    try {
      const taskPayload: {
        task_owner_user_id?: string;
        task_owner_user_ref?: string;
        due_date?: string;
        task_status: TaskStatus;
        resolution_note?: string;
      } = {
        task_status: task.task_status
      };
      if (task.task_owner_user_id) {
        taskPayload.task_owner_user_id = task.task_owner_user_id;
      }
      if (task.task_owner_user_ref) {
        taskPayload.task_owner_user_ref = task.task_owner_user_ref;
      }
      if (task.due_date) {
        taskPayload.due_date = task.due_date;
      }
      if (task.resolution_note) {
        taskPayload.resolution_note = task.resolution_note;
      }

      const response = await saveFollowUpTask(taskId, taskPayload);
      await Promise.all([
        refreshWorkspace(),
        fetchCaseDetail(response.caseId).then((result) => setCaseDetail(result)),
        fetchCaseHistory(response.caseId).then((result) => setCaseHistory(result)),
      ]);
      setBanner({ tone: "success", text: response.message });
    } catch (taskError: unknown) {
      if (!handleApiFailure(taskError, "Failed to update the follow-up task.")) {
        setTaskSavingId(null);
      }
      return;
    }

    setTaskSavingId(null);
  }

  async function handleUploadCaseImage(file: File, caption: string): Promise<void> {
    if (!caseDetail) {
      return;
    }

    setImageUploading(true);
    setBanner(null);

    try {
      const response = await uploadCaseImage(caseDetail.external_case_id, file, caption);
      setCaseDetail((current) =>
        current
          ? {
              ...current,
              image_attachments: response.payload.image_attachments || [],
            }
          : response.payload,
      );
      setCaseHistory(await fetchCaseHistory(response.externalCaseId));
      await refreshWorkspace();
      setBanner({ tone: "success", text: response.message });
    } catch (uploadError: unknown) {
      handleApiFailure(uploadError, "Failed to attach the image.");
    } finally {
      setImageUploading(false);
    }
  }

  async function handleDeleteCaseImage(externalImageId: string): Promise<void> {
    if (!caseDetail) {
      return;
    }

    setImageDeletingId(externalImageId);
    setBanner(null);

    try {
      const response = await deleteCaseImage(caseDetail.external_case_id, externalImageId);
      setCaseDetail((current) =>
        current
          ? {
              ...current,
              image_attachments: response.payload.image_attachments || [],
            }
          : response.payload,
      );
      setCaseHistory(await fetchCaseHistory(response.externalCaseId));
      await refreshWorkspace();
      setBanner({ tone: "success", text: response.message });
    } catch (deleteError: unknown) {
      handleApiFailure(deleteError, "Failed to remove the image.");
    } finally {
      setImageDeletingId(null);
    }
  }

  async function openBinaryInNewTab(loadFile: () => Promise<{ blob: Blob; filename: string | null }>) {
    const popup = typeof window !== "undefined" ? window.open("", "_blank", "noopener,noreferrer") : null;

    try {
      const { blob } = await loadFile();
      if (typeof window === "undefined") {
        return;
      }

      const objectUrl = window.URL.createObjectURL(blob);
      if (popup) {
        popup.location.href = objectUrl;
      } else {
        const link = window.document.createElement("a");
        link.href = objectUrl;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        link.click();
      }
      window.setTimeout(() => window.URL.revokeObjectURL(objectUrl), 60_000);
    } catch (pdfError) {
      popup?.close();
      throw pdfError;
    }
  }

  async function handleOpenCaseImage(image: CaseImageAttachmentPayload): Promise<void> {
    if (!caseDetail || !image.external_image_id) {
      return;
    }

    setBanner(null);
    try {
      await openBinaryInNewTab(() => fetchCaseImageBinary(caseDetail.external_case_id, image.external_image_id || ""));
    } catch (imageError: unknown) {
      handleApiFailure(imageError, "Failed to open the case image.");
    }
  }

  async function handleOpenCasePdf() {
    if (!caseDetail) {
      return;
    }

    setBanner(null);
    try {
      await openBinaryInNewTab(() => fetchCasePdfBinary(caseDetail.external_case_id));
    } catch (pdfError: unknown) {
      handleApiFailure(pdfError, "Failed to open the finalized PDF.");
    }
  }

  async function handleOpenRevisionPdf(revisionNumber: number) {
    if (!caseDetail) {
      return;
    }

    setBanner(null);
    try {
      await openBinaryInNewTab(() => fetchRevisionPdfBinary(caseDetail.external_case_id, revisionNumber));
    } catch (pdfError: unknown) {
      handleApiFailure(pdfError, "Failed to open the revision PDF.");
    }
  }

  if (!session) {
    return (
      <main className="login-shell">
        <section className="login-panel login-panel-simple">
          <img className="login-brand-logo" src="/brand/dondoo-logo.svg" alt="Dondoo" />
          <div className="form-heading">
            <p className="eyebrow">Clinical workspace</p>
            <h1>Sign in</h1>
            <p>Use your workspace account to continue.</p>
          </div>
          {authError ? <section className="banner error-banner">{authError}</section> : null}
          <form className="login-form" onSubmit={handleSignIn}>
            <label>
              Username
              <input name="login" placeholder="dr.njoroge" autoComplete="username" required />
            </label>
            <label>
              Password
              <input name="password" type="password" autoComplete="current-password" required />
            </label>
            <button className="primary-button" type="submit" disabled={signingIn}>
              {signingIn ? "Signing in..." : "Sign in"}
            </button>
          </form>
          <p className="login-footnote">Dondoo clinical workspace · {todayLabel}</p>
        </section>
      </main>
    );
  }

  return (
    <main className="workspace-shell">
      <header className="workspace-header">
        <div className="app-bar-brand">
          <img className="app-bar-logo" src="/brand/dondoo-logo.svg" alt="Dondoo" />
          <span className="app-bar-divider" aria-hidden="true" />
          <span className="app-bar-context">{screenCopy.eyebrow}</span>
        </div>

        <div className="header-actions">
          <div className="chip-row stacked-actions">
            {activeScreen === "case-detail" ? (
              <button className="secondary-button" type="button" onClick={() => handleNav("cases")}>
                <ButtonLabel icon="back">Back to cases</ButtonLabel>
              </button>
            ) : null}
            <button className="primary-button" type="button" onClick={() => handleNav("new-procedure")}>
              <ButtonLabel icon="new-case">Start case</ButtonLabel>
            </button>
          </div>
        </div>
      </header>

      <div className="workspace-frame">
        <aside className="rail-shell">
          <section className="rail-card rail-nav-card">
            <div className="rail-identity">
              <p className="eyebrow">Signed in</p>
              <strong>{session.displayName}</strong>
              <span>{formatLabel(session.primaryRole)}</span>
            </div>

            <nav className="nav-links">
              <NavigationButton active={activeScreen === "dashboard"} icon="dashboard" label="Dashboard" caption="Shift view" onClick={() => handleNav("dashboard")} />
              <NavigationButton
                active={activeScreen === "cases" || activeScreen === "case-detail"}
                icon="cases"
                label="Cases"
                caption="Draft and sign-off"
                count={draftOrReopenedCases.length + readyForSignoffCases.length}
                onClick={() => handleNav("cases")}
              />
              <NavigationButton
                active={activeScreen === "tasks"}
                icon="tasks"
                label="Tasks"
                caption="Follow-up actions"
                count={openTasks.length}
                onClick={() => handleNav("tasks")}
              />
              <NavigationButton active={activeScreen === "new-procedure"} icon="new-case" label="New case" caption="Open draft" onClick={() => handleNav("new-procedure")} />
            </nav>

            <div className="rail-footer">
              <p className="muted-text">Session until {formatSessionExpiry(session.expiresAt)}</p>
              <button className="secondary-button" type="button" onClick={() => void handleSignOut()}>
                <ButtonLabel icon="sign-out">Sign out</ButtonLabel>
              </button>
            </div>
          </section>
        </aside>

        <section className="content-shell">
          {errorPresentation ? (
            <section className="banner error-banner workspace-banner">
              <div className="banner-copy">
                <strong>{errorPresentation.title}</strong>
                <p>{errorPresentation.body}</p>
              </div>
              {errorPresentation.actionKind === "reload" ? (
                <button className="secondary-button" type="button" onClick={() => void handleReloadWorkspace()}>
                  <ButtonLabel icon="dashboard">{errorPresentation.actionLabel}</ButtonLabel>
                </button>
              ) : (
                <button
                  className="secondary-button"
                  type="button"
                  onClick={() => {
                    setSelectedCaseId(null);
                    setCaseDetail(null);
                    setCaseHistory(null);
                    setError(null);
                    handleNav("cases");
                  }}
                >
                  <ButtonLabel icon="back">{errorPresentation.actionLabel}</ButtonLabel>
                </button>
              )}
            </section>
          ) : null}
          {shellWarningMessage ? (
            <section className="banner warning-banner workspace-banner">
              <div className="banner-copy">
                <strong>Workspace running in fallback mode</strong>
                <p>{shellWarningMessage}</p>
              </div>
              <button className="secondary-button" type="button" onClick={() => void handleReloadWorkspace()}>
                <ButtonLabel icon="dashboard">Reload queue</ButtonLabel>
              </button>
            </section>
          ) : null}
          {banner ? <section className={`banner ${banner.tone === "success" ? "success-banner" : "error-banner"}`}>{banner.text}</section> : null}

          {activeScreen === "dashboard" ? (
            <DashboardView
              role={session.primaryRole}
              cases={sortedCases}
              tasks={sortedTasks}
              onOpenCases={() => handleNav("cases")}
              onOpenTasks={() => handleNav("tasks")}
            />
          ) : null}

          {activeScreen === "cases" ? (
            <CasesView
              cases={filteredCases}
              query={caseQuery}
              setQuery={setCaseQuery}
              onStartCase={() => handleNav("new-procedure")}
              onSelectCase={openCase}
            />
          ) : null}

          {activeScreen === "tasks" ? (
            <TasksView tasks={filteredTasks} query={taskQuery} setQuery={setTaskQuery} onSelectCase={openCase} />
          ) : null}

          {activeScreen === "new-procedure" ? (
            <NewProcedureView
              caseForm={caseForm}
              caseSubmitting={caseSubmitting}
              facilityUnitOptions={facilityUnitOptions}
              facilityOptions={lookups.facilities}
              resolvedFacilityCode={selectedCaseFormFacilityCode}
              facilityIsInferred={Boolean(inferredFacilityCode && !caseForm.facilityCode)}
              referrerServiceOptions={referrerServiceOptions}
              endoscopistOptions={endoscopistOptions}
              nurseOptions={nurseOptions}
              onSubmit={handleCreateCase}
              onPatientIdentifierBlur={handlePatientIdentifierBlur}
              patientRelationshipSuggestion={patientRelationshipSuggestion}
              patientRelationshipLoading={patientRelationshipLoading}
              patientSearchResults={patientSearchResults}
              onSelectPatient={handleSelectPatient}
              setCaseForm={updateCaseForm}
            />
          ) : null}

          {activeScreen === "case-detail" ? (
            <CaseDetailView
              session={session}
              caseDraft={caseDetail}
              caseHistory={caseHistory}
              caseDetailLoading={caseDetailLoading}
              caseHistoryLoading={caseHistoryLoading}
              caseSaving={caseSaving}
              caseLastSavedAt={caseLastSavedAt}
              caseActionLoading={caseActionLoading}
              taskSavingId={taskSavingId}
              imageUploading={imageUploading}
              imageDeletingId={imageDeletingId}
              lookups={lookups}
              activeFacilityUnits={activeFacilityUnits}
              workflowSteps={caseWorkflowSteps}
              reopenReason={reopenReason}
              setReopenReason={setReopenReason}
              onBackToCases={() => handleNav("cases")}
              onSaveDraft={() => void handleSaveCaseDraft()}
              onRunAction={(action) => void handleCaseAction(action)}
              onOpenCasePdf={() => void handleOpenCasePdf()}
              onOpenRevisionPdf={(revisionNumber) => void handleOpenRevisionPdf(revisionNumber)}
              onUploadImage={handleUploadCaseImage}
              onOpenImage={(image) => void handleOpenCaseImage(image)}
              onRemoveImage={(externalImageId) => void handleDeleteCaseImage(externalImageId)}
              onUpdateField={updateCaseDetailField}
              onUpdateFacility={updateCaseFacility}
              onUpdateFacilityUnit={updateCaseFacilityUnit}
              onUpdateSegment={updateSegment}
              onAddSegment={addSegment}
              onRemoveSegment={removeSegment}
              onUpdateLesion={updateLesion}
              onAddLesion={addLesion}
              onRemoveLesion={removeLesion}
              onUpdateSpecimen={updateSpecimen}
              onAddSpecimen={addSpecimen}
              onRemoveSpecimen={removeSpecimen}
              onUpdateTask={updateFollowUpTask}
              onAddTask={addFollowUpTask}
              onRemoveTask={removeFollowUpTask}
              onSaveTask={(index) => void handleSaveTask(index)}
            />
          ) : null}
        </section>
      </div>

      {activeScreen === "dashboard" ? (
        <FloatingHelpDock
          label="Dashboard help"
          title="Dashboard quick guide"
          summary="Use the dashboard to see what needs attention now, then open Cases or Tasks for the full work queue."
          sections={[
            {
              eyebrow: "Getting started",
              title: "Start a clean case",
              icon: "checklist",
              items: startCaseChecks
            },
            {
              eyebrow: "At a glance",
              title: "What the dashboard shows",
              icon: "dashboard",
              items: [
                { label: "Ready reports", detail: "Cases waiting for endoscopist review and sign-off." },
                { label: "Open follow-up", detail: "Tasks that still need an owner or completion." },
                { label: "Recently finalized", detail: "Completed reports available for past-record review." }
              ]
            },
            {
              eyebrow: "Next step",
              title: "Keep work moving",
              icon: "checklist",
              items: [{ label: "Open a card to continue, or use Start case for a new draft." }]
            }
          ]}
        />
      ) : null}

      <nav className="mobile-nav">
        <MobileNavigationButton active={activeScreen === "dashboard"} icon="dashboard" label="Home" onClick={() => handleNav("dashboard")} />
        <MobileNavigationButton
          active={activeScreen === "cases" || activeScreen === "case-detail"}
          icon="cases"
          label="Cases"
          count={draftOrReopenedCases.length + readyForSignoffCases.length}
          onClick={() => handleNav("cases")}
        />
        <MobileNavigationButton active={activeScreen === "tasks"} icon="tasks" label="Tasks" count={openTasks.length} onClick={() => handleNav("tasks")} />
        <MobileNavigationButton active={activeScreen === "new-procedure"} icon="new-case" label="Start" onClick={() => handleNav("new-procedure")} />
      </nav>
    </main>
  );
}

function DashboardView({
  role,
  cases,
  tasks,
  onOpenCases,
  onOpenTasks
}: {
  role: WorkspaceRole;
  cases: CaseSummary[];
  tasks: FollowUpTask[];
  onOpenCases: () => void;
  onOpenTasks: () => void;
}) {
  const draftCases = cases.filter(isDraftLikeCase);
  const readyCases = cases.filter((entry) => entry.status === "ready_for_signoff");
  const finalizedToday = countFinalizedToday(cases);
  const actionableTaskCount = tasks.filter(isActionableTask).length;
  const highlightedDrafts = draftCases.slice(0, 3);
  const highlightedTasks = tasks.filter(isActionableTask).slice(0, 3);
  const recentFinalized = cases.filter((entry) => entry.status === "finalized").slice(0, 4);
  const roleCopy = getRoleWorkspaceCopy(role, {
    drafts: draftCases.length,
    ready: readyCases.length,
    tasks: actionableTaskCount,
    finalizedToday
  });
  const queueConfigs: Record<DashboardLaneKey, {
    eyebrow: string;
    title: string;
    summary: string;
    icon: IconName;
    count: number;
    tone: StatusTone;
    emptyTitle: string;
    emptyMessage: string;
    actionLabel: string;
    actionIcon: IconName;
    onAction: () => void;
    items: ReactNode[];
  }> = {
    drafts: {
      eyebrow: "Drafts",
      title: "Still in progress",
      summary: "Cases that still need authoring, corrections, or another review pass.",
      icon: "draft",
      count: draftCases.length,
      tone: draftCases.length ? "accent" : "neutral",
      emptyTitle: "Draft queue is clear",
      emptyMessage: "New or reopened cases will appear here when active reporting resumes.",
      actionLabel: "Open cases",
      actionIcon: "cases",
      onAction: onOpenCases,
      items: highlightedDrafts.map((entry) => (
        <DashboardQueueItem
          key={entry.id}
          icon="draft"
          title={entry.patientIdentifier}
          subtitle={`${formatProcedureLabel(entry.procedureType)} - ${formatDateTime(entry.procedureDatetime)}`}
          detail={entry.endoscopistName}
          tone={getCaseStatusTone(entry.status)}
          badge={formatStatusLabel(entry.status)}
        />
      ))
    },
    ready: {
      eyebrow: "Ready",
      title: "Waiting for sign-off",
      summary: "Completed reports that can move straight into clinical sign-off.",
      icon: "ready",
      count: readyCases.length,
      tone: readyCases.length ? "warning" : "neutral",
      emptyTitle: "Sign-off queue is clear",
      emptyMessage: "Cases ready for sign-off will appear here as soon as drafting is complete.",
      actionLabel: "Open cases",
      actionIcon: "cases",
      onAction: onOpenCases,
      items: readyCases.slice(0, 3).map((entry) => (
        <DashboardQueueItem
          key={entry.id}
          icon="ready"
          title={entry.patientIdentifier}
          subtitle={`${formatProcedureLabel(entry.procedureType)} - ${formatDateTime(entry.procedureDatetime)}`}
          detail={entry.endoscopistName}
          tone="warning"
          badge="Ready"
        />
      ))
    },
    tasks: {
      eyebrow: "Tasks",
      title: "Still open",
      summary: "Follow-up actions that still need a callback, pathology review, or closure.",
      icon: "tasks",
      count: actionableTaskCount,
      tone: actionableTaskCount ? "critical" : "success",
      emptyTitle: "Follow-up queue is clear",
      emptyMessage: "Outstanding callbacks and surveillance tasks will appear here when they need action.",
      actionLabel: "Open tasks",
      actionIcon: "tasks",
      onAction: onOpenTasks,
      items: highlightedTasks.map((entry) => {
        const due = getDueMeta(entry.dueDate);
        return (
          <DashboardQueueItem
            key={entry.id}
            icon="tasks"
            title={formatTaskTypeLabel(entry.type)}
            subtitle={`Case ${entry.caseId}`}
            detail={`${entry.ownerName} - ${due.label}`}
            tone={getTaskStatusTone(entry.status)}
            badge={formatStatusLabel(entry.status)}
          />
        );
      })
    }
  };
  return (
    <section className="dashboard-stack">
      <section className="panel dashboard-summary-panel">
        <div className="dashboard-queue-strip">
          {roleCopy.laneOrder.map((lane) => {
            const config = queueConfigs[lane];
            return (
              <DashboardQueueStripItem
                key={lane}
                icon={config.icon}
                label={config.eyebrow}
                value={config.count}
                tone={config.tone}
                caption={config.title}
              />
            );
          })}
          <DashboardQueueStripItem
            icon="finalized"
            label="Finalized"
            value={finalizedToday}
            tone={finalizedToday ? "success" : "neutral"}
            caption="today"
          />
        </div>
      </section>

      <section className="dashboard-lane-grid">
        {roleCopy.laneOrder.map((lane) => {
          const config = queueConfigs[lane];
          return (
            <QueuePanel
              key={lane}
              eyebrow={config.eyebrow}
              title={config.title}
              summary={config.summary}
              icon={config.icon}
              count={config.count}
              tone={config.tone}
              emptyTitle={config.emptyTitle}
              emptyMessage={config.emptyMessage}
              actionLabel={config.actionLabel}
              actionIcon={config.actionIcon}
              onAction={config.onAction}
              items={config.items}
            />
          );
        })}
      </section>

      <section className="panel dashboard-history-panel">
        <div className="panel-header">
          <div>
            <p className="eyebrow">Completed work</p>
            <h2>Recently finalized</h2>
          </div>
          <button className="secondary-button" type="button" onClick={onOpenCases}>
            <ButtonLabel icon="cases">All cases</ButtonLabel>
          </button>
        </div>
        <div className="list-stack">
          {recentFinalized.length ? (
            recentFinalized.map((entry) => <CaseCard key={entry.id} entry={entry} compact />)
          ) : (
            <EmptyStateCard title="No finalized cases yet" body="Completed reports will appear here after sign-off." compact />
          )}
        </div>
      </section>
    </section>
  );
}

function CasesView({
  cases,
  query,
  setQuery,
  onStartCase,
  onSelectCase
}: {
  cases: CaseSummary[];
  query: string;
  setQuery: (next: string) => void;
  onStartCase: () => void;
  onSelectCase: (externalCaseId: string) => void;
}) {
  const [statusFilter, setStatusFilter] = useState<"all" | CaseSummary["status"]>("all");
  const [procedureFilter, setProcedureFilter] = useState<"all" | ProcedureType>("all");
  const visibleCases = cases.filter((entry) => (statusFilter === "all" || entry.status === statusFilter) && (procedureFilter === "all" || entry.procedureType === procedureFilter));
  const workingCases = visibleCases.filter(isDraftLikeCase);
  const readyCases = visibleCases.filter((entry) => entry.status === "ready_for_signoff");
  const finalizedCases = visibleCases.filter((entry) => entry.status === "finalized");
  const patientGroups = Array.from(
    visibleCases.reduce((groups, entry) => {
      const current = groups.get(entry.patientIdentifier) || [];
      current.push(entry);
      groups.set(entry.patientIdentifier, current);
      return groups;
    }, new Map<string, CaseSummary[]>()).entries()
  ).sort((left, right) => left[0].localeCompare(right[0]));

  return (
    <section className="view-stack">
      <div className="panel queue-toolbar">
        <div className="panel-header">
          <div>
            <p className="eyebrow">Cases</p>
            <h2>Open reports</h2>
          </div>
          <button className="primary-button" type="button" onClick={onStartCase}>
            <ButtonLabel icon="new-case">Start case</ButtonLabel>
          </button>
        </div>
        <div className="queue-toolbar-controls">
          <input
            className="search-input"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search patient identifier, clinician, or procedure"
          />
          <span className="queue-result-count" role="status">{visibleCases.length} shown</span>
        </div>
        <div className="filter-row queue-filter-row" aria-label="Case filters">
          <label className="compact-field">Status
            <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value as typeof statusFilter)}>
              <option value="all">All statuses</option><option value="draft">Draft</option><option value="draft_reopened">Reopened</option><option value="ready_for_signoff">Ready for sign-off</option><option value="finalized">Finalized</option>
            </select>
          </label>
          <label className="compact-field">Procedure
            <select value={procedureFilter} onChange={(event) => setProcedureFilter(event.target.value as typeof procedureFilter)}>
              <option value="all">All procedures</option><option value="colonoscopy">Colonoscopy</option><option value="egd">EGD</option><option value="ercp">ERCP</option><option value="eus">EUS</option>
            </select>
          </label>
        </div>
      </div>

      {visibleCases.length ? (
        <div className="case-list-shell">
          <SurfaceSection
            eyebrow="Ready"
            title="Waiting for sign-off"
            summary="Reports that can now move to the endoscopist for review and final sign-off."
            icon="ready"
            count={readyCases.length}
            tone={readyCases.length ? "warning" : "neutral"}
          >
            {readyCases.length ? readyCases.map((entry) => <CaseCard key={entry.id} entry={entry} interactive onOpen={() => onSelectCase(entry.id)} />) : <p className="empty-copy">No cases are waiting for sign-off.</p>}
          </SurfaceSection>

          <SurfaceSection
            eyebrow="In progress"
            title="Drafts and reopened cases"
            summary="Cases that still need procedure details, corrections, or another review pass."
            icon="draft"
            count={workingCases.length}
            tone={workingCases.length ? "accent" : "neutral"}
          >
            {workingCases.length ? workingCases.map((entry) => <CaseCard key={entry.id} entry={entry} interactive onOpen={() => onSelectCase(entry.id)} />) : <p className="empty-copy">No draft or reopened cases match the current search.</p>}
          </SurfaceSection>

          <SurfaceSection
            eyebrow="Completed"
            title="Finalized reports"
            summary="Closed reports stay here for review without getting mixed into current work."
            icon="finalized"
            count={finalizedCases.length}
            tone={finalizedCases.length ? "success" : "neutral"}
          >
            {finalizedCases.length ? finalizedCases.map((entry) => <CaseCard key={entry.id} entry={entry} interactive onOpen={() => onSelectCase(entry.id)} />) : <p className="empty-copy">No finalized cases match the current search.</p>}
          </SurfaceSection>

          <SurfaceSection
            eyebrow="Patients"
            title="My patients"
            summary="Patients represented in your accessible cases. Open the most recent case to continue review."
            icon="cases"
            count={patientGroups.length}
            tone={patientGroups.length ? "accent" : "neutral"}
          >
            {patientGroups.length ? patientGroups.map(([patientIdentifier, patientCases]) => {
              const latest = [...patientCases].sort(compareCaseByRecent)[0];
              if (!latest) {
                return null;
              }
              return (
                <button className="clinical-row clinical-row-button" type="button" key={patientIdentifier} onClick={() => onSelectCase(latest.id)}>
                  <span className="clinical-row-icon">{patientCases.length}</span>
                  <span className="clinical-row-content">
                    <strong>{patientIdentifier}</strong>
                    <span>{patientCases.length} procedure{patientCases.length === 1 ? "" : "s"} - latest {formatDateTime(latest.procedureDatetime)}</span>
                  </span>
                  <span className="clinical-row-meta">{latest.endoscopistName}</span>
                </button>
              );
            }) : <p className="empty-copy">No patients match the current search.</p>}
          </SurfaceSection>
        </div>
      ) : (
        <EmptyStateCard title="No matching cases" body="Try a broader search or start a new procedure to open the next draft." />
      )}
    </section>
  );
}

function TasksView({
  tasks,
  query,
  setQuery,
  onSelectCase
}: {
  tasks: FollowUpTask[];
  query: string;
  setQuery: (next: string) => void;
  onSelectCase: (externalCaseId: string) => void;
}) {
  const overdueTasks = tasks.filter((entry) => isActionableTask(entry) && getDueMeta(entry.dueDate).tone === "critical");
  const activeTasks = tasks.filter((entry) => isActionableTask(entry) && getDueMeta(entry.dueDate).tone !== "critical");
  const closedTasks = tasks.filter((entry) => entry.status === "closed" || entry.status === "cancelled");

  return (
    <section className="view-stack">
      <div className="panel queue-toolbar">
        <div className="panel-header">
          <div>
            <p className="eyebrow">Tasks</p>
            <h2>Follow-up work</h2>
          </div>
        </div>
        <div className="queue-toolbar-controls">
          <input
            className="search-input"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search owner, task type, case ID, or status"
          />
          <span className="queue-result-count" role="status">{tasks.length} shown</span>
        </div>
      </div>

      {tasks.length ? (
        <div className="task-list-shell">
          <SurfaceSection
            eyebrow="Overdue"
            title="Needs attention"
            summary="These tasks need action soon so they do not drift further behind."
            icon="tasks"
            count={overdueTasks.length}
            tone={overdueTasks.length ? "critical" : "neutral"}
          >
            {overdueTasks.length ? overdueTasks.map((entry) => <TaskCard key={entry.id} entry={entry} interactive onOpen={() => onSelectCase(entry.caseId)} />) : <p className="empty-copy">No overdue tasks match the current search.</p>}
          </SurfaceSection>

          <SurfaceSection
            eyebrow="Open"
            title="Still in progress"
            summary="Follow-up that is active, assigned, and not currently overdue."
            icon="checklist"
            count={activeTasks.length}
            tone={activeTasks.length ? "accent" : "neutral"}
          >
            {activeTasks.length ? activeTasks.map((entry) => <TaskCard key={entry.id} entry={entry} interactive onOpen={() => onSelectCase(entry.caseId)} />) : <p className="empty-copy">No active tasks match the current search.</p>}
          </SurfaceSection>

          <SurfaceSection
            eyebrow="Closed"
            title="Finished work"
            summary="Resolved tasks remain visible here without crowding the active list."
            icon="finalized"
            count={closedTasks.length}
            tone={closedTasks.length ? "success" : "neutral"}
          >
            {closedTasks.length ? closedTasks.map((entry) => <TaskCard key={entry.id} entry={entry} interactive onOpen={() => onSelectCase(entry.caseId)} />) : <p className="empty-copy">No resolved tasks match the current search.</p>}
          </SurfaceSection>
        </div>
      ) : (
        <EmptyStateCard
          title="No matching tasks"
          body="Follow-up tasks will appear here once pathology, communication, or surveillance work is created."
        />
      )}
    </section>
  );
}

function NewProcedureView({
  caseForm,
  caseSubmitting,
  facilityUnitOptions,
  facilityOptions,
  resolvedFacilityCode,
  facilityIsInferred,
  referrerServiceOptions,
  endoscopistOptions,
  nurseOptions,
  onSubmit,
  onPatientIdentifierBlur,
  patientRelationshipSuggestion,
  patientRelationshipLoading,
  patientSearchResults,
  onSelectPatient,
  setCaseForm
}: {
  caseForm: StartCaseForm;
  caseSubmitting: boolean;
  facilityUnitOptions: FacilityUnitLookupOption[];
  facilityOptions: { code: string; label: string }[];
  resolvedFacilityCode: string | null;
  facilityIsInferred: boolean;
  referrerServiceOptions: ValueLookupOption[];
  endoscopistOptions: ClinicianLookupOption[];
  nurseOptions: ClinicianLookupOption[];
  onSubmit: (event: FormEvent<HTMLFormElement>) => Promise<void>;
  onPatientIdentifierBlur: () => Promise<void>;
  patientRelationshipSuggestion: PatientRelationshipSuggestion | null;
  patientRelationshipLoading: boolean;
  patientSearchResults: PatientLookupOption[];
  onSelectPatient: (patient: PatientLookupOption) => void;
  setCaseForm: <K extends keyof StartCaseForm>(field: K, value: StartCaseForm[K]) => void;
}) {
  const assignmentOverride = patientRelationshipSuggestion && (
    (caseForm.facilityCode && caseForm.facilityCode !== patientRelationshipSuggestion.facilityCode) ||
    (caseForm.endoscopistUserId && caseForm.endoscopistUserId !== patientRelationshipSuggestion.endoscopistUserId)
  );
  const caseTypeLabel = caseForm.procedureType ? formatProcedureLabel(caseForm.procedureType) : "Case type required";
  const canCreateDraft = Boolean(
    caseForm.procedureType &&
    caseForm.patientIdentifier.trim() &&
    caseForm.procedureDatetime &&
    resolvedFacilityCode &&
    caseForm.endoscopistUserId
  );
  const startSteps = [
    { label: "Patient", complete: Boolean(caseForm.patientIdentifier.trim()) },
    { label: "Case type", complete: Boolean(caseForm.procedureType) },
    { label: "Schedule", complete: Boolean(caseForm.procedureDatetime && resolvedFacilityCode) },
    { label: "Team", complete: Boolean(caseForm.endoscopistUserId) }
  ];
  return (
    <section className="view-stack">
        <article className="panel case-start-panel">
        <div className="panel-header">
          <div>
            <p className="eyebrow">Draft starter</p>
            <h2>Patient, timing, and team</h2>
          </div>
          <span className={`status-chip tone-${caseForm.procedureType ? "accent" : "warning"}`}>{caseTypeLabel}</span>
        </div>

        <ol className="case-start-progress" aria-label="Case setup progress">
          {startSteps.map((step, index) => (
            <li key={step.label} className={step.complete ? "is-complete" : ""}>
              <span>{step.complete ? "✓" : index + 1}</span>
              <strong>{step.label}</strong>
            </li>
          ))}
        </ol>

        <form className="case-form case-start-form" onSubmit={(event) => void onSubmit(event)}>
          <section className="form-section">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Patient context</p>
                <h3>Who is being scoped</h3>
              </div>
            </div>
            <div className="field-grid">
              <label>
                Patient identifier
                <input
                  value={caseForm.patientIdentifier}
                  onChange={(event) => setCaseForm("patientIdentifier", event.target.value)}
                  onBlur={() => void onPatientIdentifierBlur()}
                  placeholder="PT-2026-001 or patient name"
                  required
                />
              </label>
              {patientSearchResults.length ? (
                <div className="patient-search-results" role="listbox" aria-label="Matching patients">
                  {patientSearchResults.map((patient) => (
                    <button className="patient-search-option" type="button" key={patient.patientIdentifier} onMouseDown={(event) => event.preventDefault()} onClick={() => onSelectPatient(patient)}>
                      <strong>{patient.displayName}</strong>
                      <span>{patient.patientIdentifier}{patient.medicalRecordNumber ? ` - MRN ${patient.medicalRecordNumber}` : ""}</span>
                    </button>
                  ))}
                </div>
              ) : null}
              {patientRelationshipLoading ? <p className="field-help">Checking active endoscopist assignment...</p> : null}
              {patientRelationshipSuggestion ? (
                <p className="field-help">
                  Suggested assignment: {patientRelationshipSuggestion.endoscopistLabel} at {patientRelationshipSuggestion.facilityLabel}.
                </p>
              ) : null}
              {assignmentOverride ? (
                <p className="assignment-confirmation" role="status">
                  One-time referral / different treatment site: this case will use the selected facility and endoscopist.
                </p>
              ) : null}
              <label>
                DOB or age (optional)
                <input value={caseForm.dobOrAge || ""} onChange={(event) => setCaseForm("dobOrAge", event.target.value)} />
              </label>
              <label>
                Sex
                <select value={caseForm.sex} onChange={(event) => setCaseForm("sex", event.target.value as StartCasePayload["sex"])}>
                  {sexOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Referrer service
                <select value={caseForm.referrerService || ""} onChange={(event) => setCaseForm("referrerService", event.target.value)}>
                  <option value="">Not recorded yet</option>
                  {referrerServiceOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
            </div>
          </section>

          <section className="form-section">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Case type</p>
                <h3>Select the procedure</h3>
              </div>
            </div>
            <div className="field-grid">
              <label>
                Case type
                <select
                  value={caseForm.procedureType}
                  onChange={(event) => setCaseForm("procedureType", event.target.value as ProcedureType | "")}
                  required
                >
                  <option value="">Select case type</option>
                  {procedureOrder.map((procedure) => (
                    <option key={procedure} value={procedure}>
                      {formatProcedureLabel(procedure)}
                    </option>
                  ))}
                </select>
              </label>
              <p className="field-help">Choose a case type to set up the correct clinical record. Procedure guidance is available while documenting the case.</p>
            </div>
          </section>

          <section className="form-section">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Schedule and room</p>
                <h3>Where and when the case starts</h3>
              </div>
            </div>
            <div className="field-grid">
              <label>
                {facilityIsInferred ? "Facility (selected automatically)" : "Facility"}
                <select value={caseForm.facilityCode || resolvedFacilityCode || ""} onChange={(event) => setCaseForm("facilityCode", event.target.value)} required={!facilityIsInferred}>
                  <option value="">Select facility</option>
                  {facilityOptions.map((option) => <option key={option.code} value={option.code}>{option.label}</option>)}
                </select>
              </label>
              <label>
                Procedure date and time
                <input
                  type="datetime-local"
                  value={caseForm.procedureDatetime}
                  onChange={(event) => setCaseForm("procedureDatetime", event.target.value)}
                  required
                />
              </label>
              <label>
                Facility unit (optional)
                <select value={caseForm.facilityUnit} onChange={(event) => setCaseForm("facilityUnit", event.target.value)}>
                  <option value="">Select unit</option>
                  {facilityUnitOptions.map((option) => (
                    <option key={option.code} value={option.code}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
            </div>
          </section>

          <section className="form-section">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Care team</p>
                <h3>Assign the procedure owners</h3>
              </div>
            </div>
            <div className="field-grid">
              <label>
                Endoscopist
                <select value={caseForm.endoscopistUserId} onChange={(event) => setCaseForm("endoscopistUserId", event.target.value)} required>
                  <option value="">Select endoscopist</option>
                  {endoscopistOptions.map((option) => (
                    <option key={option.userId} value={option.userId}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Assistant or nurse (optional)
                <select value={caseForm.assistantNurseUserId || ""} onChange={(event) => setCaseForm("assistantNurseUserId", event.target.value)}>
                  <option value="">Assign later if needed</option>
                  {nurseOptions.map((option) => (
                    <option key={option.userId} value={option.userId}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
            </div>
          </section>

          <div className="case-start-actions">
            <p className="field-help" aria-live="polite">
              {canCreateDraft ? "Everything needed is in place. Create the draft to begin structured reporting." : "Complete the highlighted setup steps to create a draft."}
            </p>
            <button className="primary-button" type="submit" disabled={caseSubmitting || !canCreateDraft}>
              <ButtonLabel icon="new-case">{caseSubmitting ? "Creating draft..." : "Create draft case"}</ButtonLabel>
            </button>
          </div>
        </form>
        </article>
    </section>
  );
}

function CaseDetailView({
  session,
  caseDraft,
  caseHistory,
  caseDetailLoading,
  caseHistoryLoading,
  caseSaving,
  caseLastSavedAt,
  caseActionLoading,
  taskSavingId,
  imageUploading,
  imageDeletingId,
  lookups,
  activeFacilityUnits,
  workflowSteps,
  reopenReason,
  setReopenReason,
  onBackToCases,
  onSaveDraft,
  onRunAction,
  onOpenCasePdf,
  onOpenRevisionPdf,
  onUploadImage,
  onOpenImage,
  onRemoveImage,
  onUpdateField,
  onUpdateFacility,
  onUpdateFacilityUnit,
  onUpdateSegment,
  onAddSegment,
  onRemoveSegment,
  onUpdateLesion,
  onAddLesion,
  onRemoveLesion,
  onUpdateSpecimen,
  onAddSpecimen,
  onRemoveSpecimen,
  onUpdateTask,
  onAddTask,
  onRemoveTask,
  onSaveTask
}: {
  session: AuthenticatedSessionPayload;
  caseDraft: ClinicalDraftCasePayload | null;
  caseHistory: CaseHistoryPayload | null;
  caseDetailLoading: boolean;
  caseHistoryLoading: boolean;
  caseSaving: boolean;
  caseLastSavedAt: string | null;
  caseActionLoading: CaseActionName | null;
  taskSavingId: string | null;
  imageUploading: boolean;
  imageDeletingId: string | null;
  lookups: ClinicalLookupsPayload;
  activeFacilityUnits: FacilityUnitLookupOption[];
  workflowSteps: WorkflowStep[];
  reopenReason: string;
  setReopenReason: (value: string) => void;
  onBackToCases: () => void;
  onSaveDraft: () => void;
  onRunAction: (action: CaseActionName) => void;
  onOpenCasePdf: () => void;
  onOpenRevisionPdf: (revisionNumber: number) => void;
  onUploadImage: (file: File, caption: string) => Promise<void>;
  onOpenImage: (image: CaseImageAttachmentPayload) => void;
  onRemoveImage: (externalImageId: string) => void;
  onUpdateField: <K extends keyof ClinicalDraftCasePayload>(field: K, value: ClinicalDraftCasePayload[K]) => void;
  onUpdateFacility: (facilityCode: string) => void;
  onUpdateFacilityUnit: (facilityUnitCode: string) => void;
  onUpdateSegment: (index: number, field: keyof CaseSegmentPayload, value: string | boolean) => void;
  onAddSegment: () => void;
  onRemoveSegment: (index: number) => void;
  onUpdateLesion: (index: number, field: keyof CaseLesionPayload, value: string | boolean | number | null) => void;
  onAddLesion: () => void;
  onRemoveLesion: (index: number) => void;
  onUpdateSpecimen: (index: number, field: keyof CaseSpecimenPayload, value: string | boolean | number | null) => void;
  onAddSpecimen: () => void;
  onRemoveSpecimen: (index: number) => void;
  onUpdateTask: (index: number, field: keyof ClinicalFollowUpTaskPayload, value: string | null) => void;
  onAddTask: () => void;
  onRemoveTask: (index: number) => void;
  onSaveTask: (index: number) => void;
}) {
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imageCaption, setImageCaption] = useState("");

  if (caseDetailLoading && !caseDraft) {
    return (
      <section className="view-stack">
        <article className="panel empty-panel">
          <h3>Loading case detail</h3>
          <p>The clinical draft is being retrieved from the backend.</p>
        </article>
      </section>
    );
  }

  if (!caseDraft) {
    return (
      <section className="view-stack">
        <EmptyStateCard title="No case selected" body="Select a procedure case from the queue to review and continue the structured report." />
      </section>
    );
  }

  const editable = caseDraft.case_status !== "finalized";
  const [timerRunning, setTimerRunning] = useState(true);
  const [timerSeconds, setTimerSeconds] = useState(0);
  useEffect(() => {
    if (!timerRunning || caseDraft.case_status === "finalized") return undefined;
    const timer = window.setInterval(() => setTimerSeconds((seconds) => seconds + 1), 1000);
    return () => window.clearInterval(timer);
  }, [timerRunning, caseDraft.case_status]);
  const timerLabel = `${String(Math.floor(timerSeconds / 60)).padStart(2, "0")}:${String(timerSeconds % 60).padStart(2, "0")}`;
  const canFinalize = session.primaryRole === "endoscopist" && caseDraft.case_status === "ready_for_signoff";
  const canReturnToDraft = (session.primaryRole === "operations_admin" || session.primaryRole === "workspace_admin") &&
    (caseDraft.case_status === "ready_for_signoff" || caseDraft.case_status === "draft_reopened");
  const canReopen = (session.primaryRole === "operations_admin" || session.primaryRole === "workspace_admin") && caseDraft.case_status === "finalized";
  const hasFinalizedPdf = caseDraft.case_status === "finalized";
  const openTaskCount = countCaseOpenTasks(caseDraft);
  const imageAttachments = caseDraft.image_attachments || [];
  const imageCount = imageAttachments.length;
  const caseEndoscopistOptions = lookups.endoscopists.filter((option) => clinicianMatchesFacility(option, caseDraft.facility_code));
  const caseNurseOptions = filterNursesForCase(lookups.nurses, caseDraft.endoscopist_user_id, caseDraft.facility_code);
  async function handleImageUploadSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!imageFile || imageUploading) {
      return;
    }
    await onUploadImage(imageFile, imageCaption);
    setImageFile(null);
    setImageCaption("");
    event.currentTarget.reset();
  }
  const helpSections: HelpDockSection[] = [
    {
      eyebrow: "Workflow guide",
      title: `${formatProcedureLabel(caseDraft.procedure_type)} pathway`,
      icon: "workflow",
      items: workflowSteps.map((step) => ({ label: step.label, detail: step.description })),
      numbered: true
    },
    {
      eyebrow: "Authoring checks",
      title: "Before moving the case forward",
      icon: "checklist",
      items: caseAuthoringChecks
    }
  ];
  const phaseAnchors = [
    ["pre-check", "Pre-check"],
    ["procedure", "Procedure"],
    ["findings", "Findings"],
    ["specimens", "Specimens & images"],
    ["sign-off", "Plan & sign-off"]
  ] as const;
  const signoffChecklist = [
    ["Patient and procedure identified", Boolean(caseDraft.patient_identifier && caseDraft.procedure_datetime)],
    ["Consent and team pause documented", Boolean(caseDraft.consent_documented && caseDraft.team_pause_completed)],
    ["Impression and communication plan", Boolean(caseDraft.impression || caseDraft.egd_impression || caseDraft.ercp_impression || caseDraft.eus_impression)],
    ["Procedure-specific quality fields", caseDraft.procedure_type !== "colonoscopy" || Boolean(caseDraft.prep_quality && caseDraft.segment_exam.length)],
    ["Follow-up ownership reviewed", caseDraft.followup_tasks.every((task) => Boolean(task.task_owner_user_id || task.task_owner_user_ref))]
  ] as const;

  return (
    <>
      <section className="case-detail-layout">
        <div className="panel-stack">
        <article className="hero-panel">
          <div className="panel-header">
            <div>
              <p className="eyebrow">{formatProcedureLabel(caseDraft.procedure_type)}</p>
              <h2>{caseDraft.patient_identifier}</h2>
            </div>
            <span className={`status-chip tone-${getCaseStatusTone(caseDraft.case_status)}`}>{formatStatusLabel(caseDraft.case_status)}</span>
            <span className="save-state" role="status">{caseSaving ? "Saving changes…" : caseLastSavedAt ? `Saved ${formatDateTime(caseLastSavedAt)}` : "Draft not yet saved"}</span>
          </div>
          <div className="metadata-grid">
            <div>
              <span>Case ID</span>
              <strong>{caseDraft.external_case_id}</strong>
            </div>
            <div>
              <span>Procedure time</span>
              <strong>{formatDateTime(caseDraft.procedure_datetime)}</strong>
            </div>
            <div>
              <span>Lead clinician</span>
              <strong>{caseDraft.endoscopist_user_ref || caseDraft.endoscopist_user_id || "Unassigned"}</strong>
            </div>
          </div>
          <div className="detail-signal-grid">
            <SignalCard icon="history" label="Procedure timer" value={timerLabel} tone="accent" note={timerRunning ? "Session elapsed" : "Paused"} compact />
            <SignalCard
              icon="tasks"
              label="Open follow-up"
              value={openTaskCount}
              tone={openTaskCount ? "critical" : "success"}
              note="Tasks still need closure"
              compact
            />
            <SignalCard
              icon="edit"
              label="Authoring mode"
              value={editable ? "Editable" : "Locked"}
              tone={editable ? "accent" : "neutral"}
              note={editable ? "Draft changes allowed" : "Reopen to amend"}
              compact
            />
          </div>
          </article>

          <nav className="case-phase-nav" aria-label="Case sections">
            {phaseAnchors.map(([id, label]) => (
              <button key={id} className="secondary-button" type="button" onClick={() => document.getElementById(`case-section-${id}`)?.scrollIntoView({ behavior: "smooth", block: "start" })}>
                {label}
              </button>
            ))}
          </nav>

        <article id="case-section-pre-check" className="panel case-section-anchor">
          <div className="panel-header">
            <div>
              <p className="eyebrow">Core record</p>
              <h2>Patient, team, and sign-off prerequisites</h2>
            </div>
            {!editable ? <span className="status-chip tone-neutral">Locked until reopened</span> : null}
          </div>

          <div className="field-grid field-grid-three">
            <label>
              Patient identifier
              <input
                value={caseDraft.patient_identifier}
                disabled={!editable}
                onChange={(event) => onUpdateField("patient_identifier", event.target.value)}
              />
            </label>
            <label>
              DOB or age
              <input value={caseDraft.dob_or_age || ""} disabled={!editable} onChange={(event) => onUpdateField("dob_or_age", event.target.value)} />
            </label>
            <label>
              Sex
              <select value={caseDraft.sex} disabled={!editable} onChange={(event) => onUpdateField("sex", event.target.value as ClinicalDraftCasePayload["sex"])}>
                {sexOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Procedure date and time
              <input
                type="datetime-local"
                value={toLocalDateTimeValue(caseDraft.procedure_datetime)}
                disabled={!editable}
                onChange={(event) => onUpdateField("procedure_datetime", toIsoDatetime(event.target.value))}
              />
            </label>
            <label>
              Facility
              <select value={caseDraft.facility_code || ""} disabled={!editable} onChange={(event) => onUpdateFacility(event.target.value)}>
                <option value="">Select facility</option>
                {lookups.facilities.map((option) => (
                  <option key={option.code} value={option.code}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Unit
              <select value={caseDraft.facility_unit_code || ""} disabled={!editable} onChange={(event) => onUpdateFacilityUnit(event.target.value)}>
                <option value="">Select unit</option>
                {activeFacilityUnits.map((option) => (
                  <option key={option.code} value={option.code}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Endoscopist
              <select value={caseDraft.endoscopist_user_id || ""} disabled={!editable} onChange={(event) => onUpdateField("endoscopist_user_id", event.target.value)}>
                <option value="">Select endoscopist</option>
                {caseEndoscopistOptions.map((option) => (
                  <option key={option.userId} value={option.userId}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Assistant or nurse
              <select
                value={caseDraft.assistant_nurse_user_id || ""}
                disabled={!editable}
                onChange={(event) => onUpdateField("assistant_nurse_user_id", event.target.value)}
              >
                <option value="">Not assigned</option>
                {caseNurseOptions.map((option) => (
                  <option key={option.userId} value={option.userId}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Referrer service
              <select value={caseDraft.referrer_service || ""} disabled={!editable} onChange={(event) => onUpdateField("referrer_service", event.target.value)}>
                <option value="">Not recorded</option>
                {lookups.referrerServices.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Indication
              <textarea value={caseDraft.indication || ""} disabled={!editable} onChange={(event) => onUpdateField("indication", event.target.value)} />
            </label>
            <label>
              Priority
              <select
                value={caseDraft.priority || ""}
                disabled={!editable}
                onChange={(event) => onUpdateField("priority", (event.target.value || null) as ClinicalDraftCasePayload["priority"])}
              >
                <option value="">Not set</option>
                {priorityOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              ASA class
              <select value={caseDraft.asa_class || ""} disabled={!editable} onChange={(event) => onUpdateField("asa_class", event.target.value || null)}>
                <option value="">Not set</option>
                {asaOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Sedation or anesthesia
              <input
                value={caseDraft.sedation_anesthesia || ""}
                disabled={!editable}
                onChange={(event) => onUpdateField("sedation_anesthesia", event.target.value)}
              />
            </label>
            <label>
              Allergies
              <textarea value={caseDraft.allergies || ""} disabled={!editable} onChange={(event) => onUpdateField("allergies", event.target.value)} />
            </label>
            <label>
              Adverse event note
              <textarea value={String(caseDraft.adverse_event_note || "")} disabled={!editable} onChange={(event) => onUpdateField("adverse_event_note", event.target.value)} placeholder="Document event, response, and escalation." />
            </label>
            <label>
              Antithrombotic plan
              <select
                value={caseDraft.antithrombotic_plan || ""}
                disabled={!editable}
                onChange={(event) => onUpdateField("antithrombotic_plan", event.target.value || null)}
              >
                <option value="">Not set</option>
                {antithromboticOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <div className="checkbox-grid">
            <ToggleField label="Two patient identifiers verified" checked={Boolean(caseDraft.patient_identity_verified)} disabled={!editable} onChange={(checked) => onUpdateField("patient_identity_verified", checked)} />
            <ToggleField label="Consent documented" checked={Boolean(caseDraft.consent_documented)} disabled={!editable} onChange={(checked) => onUpdateField("consent_documented", checked)} />
            <ToggleField label="Team pause completed" checked={Boolean(caseDraft.team_pause_completed)} disabled={!editable} onChange={(checked) => onUpdateField("team_pause_completed", checked)} />
            <ToggleField label="SpO2 monitoring" checked={Boolean(caseDraft.monitor_spo2)} disabled={!editable} onChange={(checked) => onUpdateField("monitor_spo2", checked)} />
            <ToggleField label="Heart rate monitoring" checked={Boolean(caseDraft.monitor_hr)} disabled={!editable} onChange={(checked) => onUpdateField("monitor_hr", checked)} />
            <ToggleField label="Blood pressure monitoring" checked={Boolean(caseDraft.monitor_bp)} disabled={!editable} onChange={(checked) => onUpdateField("monitor_bp", checked)} />
            <ToggleField label="ECG monitoring" checked={Boolean(caseDraft.monitor_ecg)} disabled={!editable} onChange={(checked) => onUpdateField("monitor_ecg", checked)} />
            <ToggleField label="Capnography monitoring" checked={Boolean(caseDraft.monitor_capnography)} disabled={!editable} onChange={(checked) => onUpdateField("monitor_capnography", checked)} />
            <ToggleField label="Adverse event occurred" checked={Boolean(caseDraft.adverse_event_during_procedure)} disabled={!editable} onChange={(checked) => onUpdateField("adverse_event_during_procedure", checked)} />
          </div>
        </article>

        <article id="case-section-procedure" className="panel case-section-anchor">
          <div className="panel-header">
            <div>
              <p className="eyebrow">Procedure fields</p>
              <h2>{formatProcedureLabel(caseDraft.procedure_type)} details</h2>
            </div>
          </div>

          {caseDraft.procedure_type === "colonoscopy" ? (
            <div className="form-section">
              <div className="field-grid field-grid-three">
                <label>
                  Bowel prep agent
                  <input value={String(caseDraft.bowel_prep_agent || "")} disabled={!editable} onChange={(event) => onUpdateField("bowel_prep_agent", event.target.value)} />
                </label>
                <label>
                  Insertion time
                  <input value={String(caseDraft.insertion_time || "")} disabled={!editable} onChange={(event) => onUpdateField("insertion_time", event.target.value)} placeholder="HH:MM" />
                </label>
                <label>
                  Prep quality
                  <select value={String(caseDraft.prep_quality || "")} disabled={!editable} onChange={(event) => onUpdateField("prep_quality", event.target.value || null)}>
                    <option value="">Not set</option>
                    {prepQualityOptions.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Terminal ileum status
                  <select value={String(caseDraft.terminal_ileum_status || "")} disabled={!editable} onChange={(event) => onUpdateField("terminal_ileum_status", event.target.value || null)}>
                    <option value="">Not set</option>
                    {terminalIleumOptions.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  BBPS right
                  <input type="number" value={caseDraft.bbps_right ?? ""} disabled={!editable} onChange={(event) => onUpdateField("bbps_right", parseNullableNumber(event.target.value))} />
                </label>
                <label>
                  BBPS transverse
                  <input type="number" value={caseDraft.bbps_transverse ?? ""} disabled={!editable} onChange={(event) => onUpdateField("bbps_transverse", parseNullableNumber(event.target.value))} />
                </label>
                <label>
                  BBPS left
                  <input type="number" value={caseDraft.bbps_left ?? ""} disabled={!editable} onChange={(event) => onUpdateField("bbps_left", parseNullableNumber(event.target.value))} />
                </label>
                <label>
                  BBPS total
                  <input type="number" value={caseDraft.bbps_total ?? ""} readOnly aria-readonly="true" placeholder="Auto-calculated" />
                </label>
                <label>
                  Withdrawal time (minutes)
                  <input
                    type="number"
                    value={caseDraft.withdrawal_time_minutes ?? ""}
                    disabled={!editable}
                    onChange={(event) => onUpdateField("withdrawal_time_minutes", parseNullableNumber(event.target.value))}
                  />
                </label>
                <label>
                  Pathology status
                  <select value={String(caseDraft.pathology_status || "")} disabled={!editable} onChange={(event) => onUpdateField("pathology_status", event.target.value || null)}>
                    <option value="">Not set</option>
                    {pathologyStatusOptions.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Surveillance interval
                  <input
                    value={String(caseDraft.surveillance_interval_value || "")}
                    disabled={!editable}
                    onChange={(event) => onUpdateField("surveillance_interval_value", event.target.value)}
                  />
                </label>
                <label>
                  Interval rationale
                  <select value={String(caseDraft.surveillance_interval_reason || "")} disabled={!editable} onChange={(event) => onUpdateField("surveillance_interval_reason", event.target.value || null)}>
                    <option value="">Not set</option>
                    {surveillanceReasonOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
                  </select>
                </label>
                <label>
                  Interval rationale note
                  <textarea value={String(caseDraft.surveillance_interval_reason_note || "")} disabled={!editable} onChange={(event) => onUpdateField("surveillance_interval_reason_note", event.target.value)} />
                </label>
                <label>
                  Small polyp technique
                  <select value={String(caseDraft.small_polyp_technique || "")} disabled={!editable} onChange={(event) => onUpdateField("small_polyp_technique", event.target.value || null)}>
                    <option value="">Not recorded</option>
                    {polypTechniqueOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
                  </select>
                </label>
                <label>
                  Resection or tattoo note
                  <textarea value={String(caseDraft.small_polyp_technique_note || caseDraft.tattoo_location_note || "")} disabled={!editable} onChange={(event) => onUpdateField("small_polyp_technique_note", event.target.value)} />
                </label>
                <label>
                  Tattoo status
                  <select value={String(caseDraft.tattoo_status || "")} disabled={!editable} onChange={(event) => onUpdateField("tattoo_status", event.target.value || null)}>
                    <option value="">Not recorded</option>
                    {tattooOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
                  </select>
                </label>
                <label>
                  Hemostasis or closure
                  <textarea value={String(caseDraft.hemostasis_or_closure || "")} disabled={!editable} onChange={(event) => onUpdateField("hemostasis_or_closure", event.target.value)} />
                </label>
                <label>
                  Technical limitation
                  <select value={String(caseDraft.technical_limitation || "")} disabled={!editable} onChange={(event) => onUpdateField("technical_limitation", event.target.value || null)}>
                    <option value="">Not recorded</option>
                    {technicalLimitationOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
                  </select>
                </label>
                <label>
                  Technical limitation note
                  <textarea
                    value={String(caseDraft.technical_limitation_note || "")}
                    disabled={!editable}
                    onChange={(event) => onUpdateField("technical_limitation_note", event.target.value)}
                  />
                </label>
                <label>
                  Impression
                  <QuickPhraseButtons onInsert={(phrase) => onUpdateField("impression", `${caseDraft.impression ? `${caseDraft.impression.trim()} ` : ""}${phrase}`)} />
                  <textarea value={String(caseDraft.impression || "")} disabled={!editable} onChange={(event) => onUpdateField("impression", event.target.value)} />
                </label>
                <label>
                  Adverse event plan
                  <select value={String(caseDraft.adverse_event_plan || "")} disabled={!editable} onChange={(event) => onUpdateField("adverse_event_plan", event.target.value || null)}>
                    <option value="">Not set</option>
                    {adverseEventPlanOptions.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </label>
              </div>

              <div className="checkbox-grid">
                <ToggleField label="Cecum reached" checked={Boolean(caseDraft.cecum_reached)} disabled={!editable} onChange={(checked) => onUpdateField("cecum_reached", checked)} />
                <ToggleField label="Appendiceal orifice landmark" checked={Boolean(caseDraft.cecal_landmark_appendiceal_orifice)} disabled={!editable} onChange={(checked) => onUpdateField("cecal_landmark_appendiceal_orifice", checked)} />
                <ToggleField label="Ileocecal valve landmark" checked={Boolean(caseDraft.cecal_landmark_ileocecal_valve)} disabled={!editable} onChange={(checked) => onUpdateField("cecal_landmark_ileocecal_valve", checked)} />
                <ToggleField label="Cecum photo captured" checked={Boolean(caseDraft.photo_cecum)} disabled={!editable} onChange={(checked) => onUpdateField("photo_cecum", checked)} />
                <ToggleField label="Pathology photo captured" checked={Boolean(caseDraft.photo_pathology)} disabled={!editable} onChange={(checked) => onUpdateField("photo_pathology", checked)} />
                <ToggleField label="Pending interval until pathology" checked={Boolean(caseDraft.surveillance_interval_pending_pathology)} disabled={!editable} onChange={(checked) => onUpdateField("surveillance_interval_pending_pathology", checked)} />
                <ToggleField label="Patient informed" checked={Boolean(caseDraft.informed_patient)} disabled={!editable} onChange={(checked) => onUpdateField("informed_patient", checked)} />
                <ToggleField label="Referrer informed" checked={Boolean(caseDraft.informed_referrer)} disabled={!editable} onChange={(checked) => onUpdateField("informed_referrer", checked)} />
                <ToggleField label="Written instructions given" checked={Boolean(caseDraft.written_instructions_given)} disabled={!editable} onChange={(checked) => onUpdateField("written_instructions_given", checked)} />
              </div>
            </div>
          ) : null}

          {caseDraft.procedure_type === "egd" ? (
            <div className="field-grid field-grid-three">
              <label>
                Extent reached
                <select value={String(caseDraft.egd_extent_reached || "")} disabled={!editable} onChange={(event) => onUpdateField("egd_extent_reached", event.target.value || null)}>
                  <option value="">Not set</option>
                  {egdExtentOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Esophagus findings
                <textarea value={String(caseDraft.egd_exam_esophagus_note || "")} disabled={!editable} onChange={(event) => onUpdateField("egd_exam_esophagus_note", event.target.value)} />
              </label>
              <label>
                Stomach findings
                <textarea value={String(caseDraft.egd_stomach_finding || "")} disabled={!editable} onChange={(event) => onUpdateField("egd_stomach_finding", event.target.value)} />
              </label>
              <label>
                Duodenum findings
                <textarea value={String(caseDraft.egd_duodenum_finding || "")} disabled={!editable} onChange={(event) => onUpdateField("egd_duodenum_finding", event.target.value)} />
              </label>
              <label>
                Impression
                <textarea value={String(caseDraft.egd_impression || "")} disabled={!editable} onChange={(event) => onUpdateField("egd_impression", event.target.value)} />
              </label>
              <label>
                Follow-up or surveillance
                <textarea value={String(caseDraft.egd_followup_surveillance || "")} disabled={!editable} onChange={(event) => onUpdateField("egd_followup_surveillance", event.target.value)} />
              </label>
              <label>
                H. pylori plan
                <textarea value={String(caseDraft.egd_h_pylori_plan || "")} disabled={!editable} onChange={(event) => onUpdateField("egd_h_pylori_plan", event.target.value)} />
              </label>
              <label>
                Medication or therapy
                <textarea value={String(caseDraft.egd_medication_therapy || "")} disabled={!editable} onChange={(event) => onUpdateField("egd_medication_therapy", event.target.value)} />
              </label>
              <div className="checkbox-grid checkbox-grid-inline">
                <ToggleField label="Specimens obtained" checked={Boolean(caseDraft.egd_specimens_obtained)} disabled={!editable} onChange={(checked) => onUpdateField("egd_specimens_obtained", checked)} />
                <ToggleField label="Result communication planned" checked={Boolean(caseDraft.egd_result_communication_planned)} disabled={!editable} onChange={(checked) => onUpdateField("egd_result_communication_planned", checked)} />
                <ToggleField label="Referrer communication planned" checked={Boolean(caseDraft.egd_referrer_communication_planned)} disabled={!editable} onChange={(checked) => onUpdateField("egd_referrer_communication_planned", checked)} />
              </div>
            </div>
          ) : null}

          {caseDraft.procedure_type === "ercp" ? (
            <div className="field-grid field-grid-three">
              <label>
                Papilla status
                <select value={String(caseDraft.ercp_papilla_status || "")} disabled={!editable} onChange={(event) => onUpdateField("ercp_papilla_status", event.target.value || null)}>
                  <option value="">Not set</option>
                  {ercpPapillaOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Therapeutic intent
                <textarea value={String(caseDraft.ercp_therapeutic_intent || "")} disabled={!editable} onChange={(event) => onUpdateField("ercp_therapeutic_intent", event.target.value)} />
              </label>
              <label>
                Technical success
                <select value={String(caseDraft.ercp_technical_success || "")} disabled={!editable} onChange={(event) => onUpdateField("ercp_technical_success", event.target.value || null)}>
                  <option value="">Not set</option>
                  {successOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Drainage achieved
                <select value={String(caseDraft.ercp_drainage_achieved || "")} disabled={!editable} onChange={(event) => onUpdateField("ercp_drainage_achieved", event.target.value || null)}>
                  <option value="">Not set</option>
                  {drainageOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Repeat intervention plan
                <textarea value={String(caseDraft.ercp_repeat_intervention || "")} disabled={!editable} onChange={(event) => onUpdateField("ercp_repeat_intervention", event.target.value)} />
              </label>
              <label>
                Repeat intervention timing
                <textarea value={String(caseDraft.ercp_repeat_intervention_timing || "")} disabled={!editable} onChange={(event) => onUpdateField("ercp_repeat_intervention_timing", event.target.value)} />
              </label>
              <label>
                Patient contact note
                <textarea value={String(caseDraft.ercp_patient_contact_note || "")} disabled={!editable} onChange={(event) => onUpdateField("ercp_patient_contact_note", event.target.value)} />
              </label>
              <label>
                Impression
                <textarea value={String(caseDraft.ercp_impression || "")} disabled={!editable} onChange={(event) => onUpdateField("ercp_impression", event.target.value)} />
              </label>
              <div className="checkbox-grid checkbox-grid-inline">
                <ToggleField label="Radiation protection verified" checked={Boolean(caseDraft.ercp_radiation_protection_verified)} disabled={!editable} onChange={(checked) => onUpdateField("ercp_radiation_protection_verified", checked)} />
                <ToggleField label="Tracking register entered" checked={Boolean(caseDraft.ercp_tracking_register_entered)} disabled={!editable} onChange={(checked) => onUpdateField("ercp_tracking_register_entered", checked)} />
                <ToggleField label="Temporary stent in situ" checked={Boolean(caseDraft.ercp_temporary_stent)} disabled={!editable} onChange={(checked) => onUpdateField("ercp_temporary_stent", checked)} />
              </div>
            </div>
          ) : null}

          {caseDraft.procedure_type === "eus" ? (
            <div className="field-grid field-grid-three">
              <label>
                Route
                <select value={String(caseDraft.eus_route || "")} disabled={!editable} onChange={(event) => onUpdateField("eus_route", event.target.value || null)}>
                  <option value="">Not set</option>
                  {eusRouteOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Echoendoscope
                <select value={String(caseDraft.eus_echoendoscope || "")} disabled={!editable} onChange={(event) => onUpdateField("eus_echoendoscope", event.target.value || null)}>
                  <option value="">Not set</option>
                  {eusEchoendoscopeOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Intent
                <select value={String(caseDraft.eus_intent || "")} disabled={!editable} onChange={(event) => onUpdateField("eus_intent", event.target.value || null)}>
                  <option value="">Not set</option>
                  {eusIntentOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Relevant anatomy documented
                <textarea
                  value={String(caseDraft.eus_relevant_anatomy_documented || "")}
                  disabled={!editable}
                  onChange={(event) => onUpdateField("eus_relevant_anatomy_documented", event.target.value)}
                />
              </label>
              <label>
                Pass count
                <input type="number" value={caseDraft.eus_passes_count ?? ""} disabled={!editable} onChange={(event) => onUpdateField("eus_passes_count", parseNullableNumber(event.target.value))} />
              </label>
              <label>
                Adequacy status
                <select value={String(caseDraft.eus_adequacy_status || "")} disabled={!editable} onChange={(event) => onUpdateField("eus_adequacy_status", event.target.value || null)}>
                  <option value="">Not set</option>
                  {adequacyOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Clinical plan
                <textarea value={String(caseDraft.eus_clinical_plan || "")} disabled={!editable} onChange={(event) => onUpdateField("eus_clinical_plan", event.target.value)} />
              </label>
              <label>
                Follow-up imaging or procedure
                <textarea
                  value={String(caseDraft.eus_followup_imaging_or_procedure || "")}
                  disabled={!editable}
                  onChange={(event) => onUpdateField("eus_followup_imaging_or_procedure", event.target.value)}
                />
              </label>
              <label>
                Multidisciplinary referral
                <textarea
                  value={String(caseDraft.eus_multidisciplinary_referral || "")}
                  disabled={!editable}
                  onChange={(event) => onUpdateField("eus_multidisciplinary_referral", event.target.value)}
                />
              </label>
              <label>
                Impression
                <textarea value={String(caseDraft.eus_impression || "")} disabled={!editable} onChange={(event) => onUpdateField("eus_impression", event.target.value)} />
              </label>
              <div className="checkbox-grid checkbox-grid-inline">
                <ToggleField label="FNA performed" checked={Boolean(caseDraft.eus_fna_performed)} disabled={!editable} onChange={(checked) => onUpdateField("eus_fna_performed", checked)} />
                <ToggleField label="FNB performed" checked={Boolean(caseDraft.eus_fnb_performed)} disabled={!editable} onChange={(checked) => onUpdateField("eus_fnb_performed", checked)} />
                <ToggleField label="Patient informed" checked={Boolean(caseDraft.informed_patient)} disabled={!editable} onChange={(checked) => onUpdateField("informed_patient", checked)} />
                <ToggleField label="Referrer informed" checked={Boolean(caseDraft.informed_referrer)} disabled={!editable} onChange={(checked) => onUpdateField("informed_referrer", checked)} />
              </div>
            </div>
          ) : null}
        </article>

        {caseDraft.procedure_type === "colonoscopy" ? (
          <article id="case-section-findings" className="panel case-section-anchor">
            <div className="panel-header">
              <div>
                <p className="eyebrow">Structured findings</p>
                <h2>Segments and lesions</h2>
              </div>
              {editable ? (
                <div className="chip-row">
                  <button className="secondary-button" type="button" onClick={onAddSegment}>
                    <ButtonLabel icon="new-case">Add segment</ButtonLabel>
                  </button>
                  <button className="secondary-button" type="button" onClick={onAddLesion}>
                    <ButtonLabel icon="new-case">Add lesion</ButtonLabel>
                  </button>
                </div>
              ) : null}
            </div>

            <div className="list-stack">
              {caseDraft.segment_exam.map((segment, index) => (
                <article key={`segment-${index}`} className="subcard">
                  <div className="panel-header">
                    <strong>Segment {index + 1}</strong>
                    {editable ? (
                      <button className="text-button" type="button" onClick={() => onRemoveSegment(index)}>
                        Remove
                      </button>
                    ) : null}
                  </div>
                  <div className="field-grid field-grid-three">
                    <label>
                      Segment name
                      <select value={segment.segment_name} disabled={!editable} onChange={(event) => onUpdateSegment(index, "segment_name", event.target.value)}>
                        {segmentNameOptions.map((option) => (
                          <option key={option.value} value={option.value}>
                            {option.label}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label>
                      Finding note
                      <textarea value={segment.finding_note || ""} disabled={!editable} onChange={(event) => onUpdateSegment(index, "finding_note", event.target.value)} />
                    </label>
                    <div className="checkbox-grid checkbox-grid-inline">
                      <ToggleField label="Normal" checked={segment.normal} disabled={!editable} onChange={(checked) => onUpdateSegment(index, "normal", checked)} />
                      <ToggleField label="Photo taken" checked={segment.photo_taken} disabled={!editable} onChange={(checked) => onUpdateSegment(index, "photo_taken", checked)} />
                    </div>
                  </div>
                </article>
              ))}
              {!caseDraft.segment_exam.length ? <p className="empty-copy">No segment rows recorded yet.</p> : null}

              {caseDraft.lesions.map((lesion, index) => (
                <article key={`lesion-${index}`} className="subcard">
                  <div className="panel-header">
                    <strong>Lesion {index + 1}</strong>
                    {editable ? (
                      <button className="text-button" type="button" onClick={() => onRemoveLesion(index)}>
                        Remove
                      </button>
                    ) : null}
                  </div>
                  <div className="field-grid field-grid-three">
                    <label>
                      Location
                      <input value={lesion.lesion_location || ""} disabled={!editable} onChange={(event) => onUpdateLesion(index, "lesion_location", event.target.value)} />
                    </label>
                    <label>
                      Size (mm)
                      <input type="number" value={lesion.lesion_size_mm ?? ""} disabled={!editable} onChange={(event) => onUpdateLesion(index, "lesion_size_mm", parseNullableNumber(event.target.value))} />
                    </label>
                    <label>
                      Morphology
                      <input value={lesion.lesion_morphology || ""} disabled={!editable} onChange={(event) => onUpdateLesion(index, "lesion_morphology", event.target.value)} />
                    </label>
                    <label>
                      Resection method
                      <input value={lesion.resection_method || ""} disabled={!editable} onChange={(event) => onUpdateLesion(index, "resection_method", event.target.value)} />
                    </label>
                    <label>
                      Specimen container
                      <input value={lesion.specimen_container_ref || ""} disabled={!editable} onChange={(event) => onUpdateLesion(index, "specimen_container_ref", event.target.value)} />
                    </label>
                    <div className="checkbox-grid checkbox-grid-inline">
                      <ToggleField label="Complete resection" checked={lesion.complete_resection} disabled={!editable} onChange={(checked) => onUpdateLesion(index, "complete_resection", checked)} />
                      <ToggleField label="Retrieved" checked={lesion.retrieved} disabled={!editable} onChange={(checked) => onUpdateLesion(index, "retrieved", checked)} />
                    </div>
                  </div>
                </article>
              ))}
              {!caseDraft.lesions.length ? <p className="empty-copy">No lesion rows recorded yet.</p> : null}
            </div>
          </article>
        ) : null}

        <article id="case-section-specimens" className="panel case-section-anchor">
          <div className="panel-header">
            <div>
              <p className="eyebrow">Specimens</p>
              <h2>Containers and site tracking</h2>
            </div>
            {editable ? (
              <button className="secondary-button" type="button" onClick={onAddSpecimen}>
                <ButtonLabel icon="new-case">Add specimen</ButtonLabel>
              </button>
            ) : null}
          </div>
          <div className="list-stack">
            {caseDraft.specimens.map((specimen, index) => (
              <article key={`specimen-${index}`} className="subcard">
                <div className="panel-header">
                  <strong>Specimen {index + 1}</strong>
                  {editable ? (
                    <button className="text-button" type="button" onClick={() => onRemoveSpecimen(index)}>
                      Remove
                    </button>
                  ) : null}
                </div>
                <div className="field-grid field-grid-three">
                  <label>
                    Container label
                    <input value={specimen.container_label || ""} disabled={!editable} onChange={(event) => onUpdateSpecimen(index, "container_label", event.target.value)} />
                  </label>
                  <label>
                    Specimen site
                    <input value={specimen.specimen_site || ""} disabled={!editable} onChange={(event) => onUpdateSpecimen(index, "specimen_site", event.target.value)} />
                  </label>
                  <label>
                    Count
                    <input type="number" value={specimen.specimen_count ?? ""} disabled={!editable} onChange={(event) => onUpdateSpecimen(index, "specimen_count", parseNullableNumber(event.target.value))} />
                  </label>
                  <label>
                    Test question
                    <textarea value={specimen.test_question || ""} disabled={!editable} onChange={(event) => onUpdateSpecimen(index, "test_question", event.target.value)} />
                  </label>
                  <div className="checkbox-grid checkbox-grid-inline">
                    <ToggleField label="Label verified" checked={specimen.label_verified} disabled={!editable} onChange={(checked) => onUpdateSpecimen(index, "label_verified", checked)} />
                  </div>
                </div>
              </article>
            ))}
            {!caseDraft.specimens.length ? <p className="empty-copy">No specimen rows recorded yet.</p> : null}
          </div>
        </article>

        <article className="panel image-record-panel">
          <div className="panel-header">
            <div className="title-with-icon">
              <span className="panel-icon" aria-hidden="true">
                <AppIcon name="image" size={18} />
              </span>
              <div>
                <p className="eyebrow">Images</p>
                <h2>Attached clinical images</h2>
              </div>
            </div>
            <span className="status-chip tone-neutral">{imageCount}</span>
          </div>

          {editable ? (
            <form className="image-upload-form" onSubmit={(event) => void handleImageUploadSubmit(event)}>
              <label className="image-file-picker">
                Image file
                <input
                  type="file"
                  accept="image/png,image/jpeg,image/webp,image/gif,image/bmp,image/tiff"
                  disabled={imageUploading}
                  onChange={(event) => setImageFile(event.target.files?.[0] || null)}
                />
              </label>
              <label>
                Caption
                <input
                  value={imageCaption}
                  disabled={imageUploading}
                  placeholder="Location, finding, or device context"
                  onChange={(event) => setImageCaption(event.target.value)}
                />
              </label>
              <button className="primary-button" type="submit" disabled={!imageFile || imageUploading}>
                <ButtonLabel icon="upload">{imageUploading ? "Attaching..." : "Attach image"}</ButtonLabel>
              </button>
            </form>
          ) : null}

          {imageAttachments.length ? (
            <div className="case-image-grid">
              {imageAttachments.map((image) => (
                <CaseImageCard
                  key={image.external_image_id || image.asset_ref || image.file_name}
                  caseId={caseDraft.external_case_id}
                  image={image}
                  editable={editable}
                  deleting={Boolean(image.external_image_id && imageDeletingId === image.external_image_id)}
                  onOpen={() => onOpenImage(image)}
                  onRemove={() => {
                    if (image.external_image_id) {
                      onRemoveImage(image.external_image_id);
                    }
                  }}
                />
              ))}
            </div>
          ) : (
            <div className="image-empty-state">
              <span className="panel-icon" aria-hidden="true">
                <AppIcon name="image" size={18} />
              </span>
              <div>
                <strong>No images attached</strong>
                <p className="muted-text">Case images will appear here with captions and upload details.</p>
              </div>
            </div>
          )}
        </article>

        <article id="case-section-sign-off" className="panel case-section-anchor">
          <div className="panel-header">
            <div>
              <p className="eyebrow">Follow-up tasks</p>
              <h2>Owner, due date, and closure state</h2>
            </div>
            {editable ? (
              <button className="secondary-button" type="button" onClick={onAddTask}>
                <ButtonLabel icon="new-case">Add follow-up task</ButtonLabel>
              </button>
            ) : null}
          </div>
          <div className="signoff-checklist" aria-label="Sign-off checklist">
            {signoffChecklist.map(([label, complete]) => (
              <div className={`signoff-check${complete ? " is-complete" : ""}`} key={label}>
                <span aria-hidden="true">{complete ? "✓" : "!"}</span>
                <strong>{label}</strong>
              </div>
            ))}
          </div>
          <div className="list-stack">
            {caseDraft.followup_tasks.map((task, index) => {
              const taskId = task.followup_task_id || task.external_task_id || `new-task-${index}`;
              const due = getDueMeta(task.due_date || undefined);
              return (
                <article key={taskId} className="subcard">
                  <div className="panel-header">
                    <div>
                      <strong>{formatTaskTypeLabel(task.task_type)}</strong>
                      <p className="muted-text">{task.followup_task_id || task.external_task_id || "Unsaved task"}</p>
                    </div>
                    <div className="chip-row">
                      <span className={`status-chip tone-${getTaskStatusTone(task.task_status)}`}>{formatStatusLabel(task.task_status)}</span>
                      {editable ? (
                        <button className="text-button" type="button" onClick={() => onRemoveTask(index)}>
                          Remove
                        </button>
                      ) : null}
                    </div>
                  </div>
                  <div className="field-grid field-grid-three">
                    <label>
                      Task type
                      <select value={task.task_type} disabled={!editable} onChange={(event) => onUpdateTask(index, "task_type", event.target.value)}>
                        {taskTypeOptions.map((option) => (
                          <option key={option.value} value={option.value}>
                            {option.label}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label>
                      Owner
                      <select value={task.task_owner_user_id || ""} disabled={!editable} onChange={(event) => onUpdateTask(index, "task_owner_user_id", event.target.value)}>
                        <option value="">Unassigned</option>
                        {[...lookups.endoscopists, ...caseNurseOptions].map((option) => (
                          <option key={`${option.role}-${option.userId}`} value={option.userId}>
                            {option.label}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label>
                      Due date
                      <input type="date" value={toDateInputValue(task.due_date)} disabled={!editable} onChange={(event) => onUpdateTask(index, "due_date", event.target.value)} />
                    </label>
                    <label>
                      Status
                      <select value={task.task_status} disabled={!editable} onChange={(event) => onUpdateTask(index, "task_status", event.target.value)}>
                        {taskStatusOptions.map((option) => (
                          <option key={option.value} value={option.value}>
                            {option.label}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label>
                      Resolution note
                      <textarea value={task.resolution_note || ""} disabled={!editable} onChange={(event) => onUpdateTask(index, "resolution_note", event.target.value)} />
                    </label>
                    <div className="task-actions">
                      <span className={`status-chip tone-${due.tone}`}>{due.label}</span>
                      <button
                        className="secondary-button"
                        type="button"
                        disabled={!editable || !task.followup_task_id && !task.external_task_id || taskSavingId === taskId}
                        onClick={() => onSaveTask(index)}
                      >
                        <ButtonLabel icon="save">{taskSavingId === taskId ? "Saving..." : "Save task status"}</ButtonLabel>
                      </button>
                    </div>
                  </div>
                </article>
              );
            })}
            {!caseDraft.followup_tasks.length ? <p className="empty-copy">No follow-up tasks recorded yet.</p> : null}
          </div>
        </article>
      </div>

      <aside className="detail-column sticky-column">
        <article className="panel">
          <div className="panel-header">
            <div>
              <p className="eyebrow">Control deck</p>
              <h2>Case controls</h2>
            </div>
          </div>
          <p className="muted-text control-deck-note">
            Save when needed, preview before sign-off, and only finalize once the record is complete enough to stand on its own.
          </p>
          <div className="detail-actions">
            <button className="primary-button" type="button" onClick={onSaveDraft} disabled={!editable || caseSaving}>
              <ButtonLabel icon="save">{caseSaving ? "Saving draft..." : "Save draft"}</ButtonLabel>
            </button>
            <button className="secondary-button" type="button" onClick={() => onRunAction("preview")} disabled={!editable || caseActionLoading === "preview"}>
              <ButtonLabel icon="preview">{caseActionLoading === "preview" ? "Generating preview..." : "Generate preview"}</ButtonLabel>
            </button>
            <button
              className="secondary-button"
              type="button"
              onClick={() => onRunAction("mark_ready_for_signoff")}
              disabled={!editable || caseActionLoading === "mark_ready_for_signoff" || caseDraft.case_status === "ready_for_signoff"}
            >
              <ButtonLabel icon="ready">{caseActionLoading === "mark_ready_for_signoff" ? "Updating..." : "Mark ready for sign-off"}</ButtonLabel>
            </button>
            {canFinalize ? (
              <button className="primary-button" type="button" onClick={() => onRunAction("finalize")} disabled={caseActionLoading === "finalize"}>
                <ButtonLabel icon="finalized">{caseActionLoading === "finalize" ? "Finalizing..." : "Finalize report"}</ButtonLabel>
              </button>
            ) : null}
            {canReturnToDraft ? (
              <button className="secondary-button" type="button" onClick={() => onRunAction("return_to_draft")} disabled={caseActionLoading === "return_to_draft"}>
                <ButtonLabel icon="draft">{caseActionLoading === "return_to_draft" ? "Returning..." : "Return to draft"}</ButtonLabel>
              </button>
            ) : null}
            {canReopen ? (
              <>
                <label>
                  Reopen reason
                  <textarea value={reopenReason} onChange={(event) => setReopenReason(event.target.value)} placeholder="Explain why the finalized case needs amendment." />
                </label>
                <button className="secondary-button" type="button" onClick={() => onRunAction("reopen")} disabled={caseActionLoading === "reopen"}>
                  <ButtonLabel icon="edit">{caseActionLoading === "reopen" ? "Reopening..." : "Reopen finalized case"}</ButtonLabel>
                </button>
              </>
            ) : null}
            {hasFinalizedPdf ? (
              <button className="secondary-button" type="button" onClick={onOpenCasePdf}>
                <ButtonLabel icon="pdf">Open finalized PDF</ButtonLabel>
              </button>
            ) : null}
            <button className="secondary-button" type="button" onClick={onBackToCases}>
              <ButtonLabel icon="back">Back to list</ButtonLabel>
            </button>
          </div>
        </article>

        <article className="panel">
          <div className="panel-header">
            <div>
              <p className="eyebrow">Validation</p>
              <h2>Clinical status</h2>
            </div>
          </div>
          <div className="list-stack">
            <div className="subcard">
              <span className={`status-chip tone-${getCaseStatusTone(caseDraft.case_status)}`}>{formatStatusLabel(caseDraft.case_status)}</span>
              <p className="muted-text">{caseDraft.validation_summary || "No validation summary generated yet."}</p>
            </div>
            <div className="subcard">
              <strong>Narrative preview</strong>
              <p className="muted-text">{caseDraft.report_narrative_snapshot || "Generate a preview to capture the narrative snapshot."}</p>
            </div>
            {caseDraft.finalized_at ? (
              <div className="subcard">
                <strong>Finalized record</strong>
                <p className="muted-text">
                  {formatDateTime(caseDraft.finalized_at)} by {caseDraft.finalized_by_user_ref || caseDraft.finalized_by_user_id || "Unknown user"}
                </p>
              </div>
            ) : null}
          </div>
        </article>

        <article className="panel">
          <div className="panel-header">
            <div>
              <p className="eyebrow">Revision history</p>
              <h2>Finalized snapshots</h2>
            </div>
          </div>
          <div className="list-stack">
            {caseHistoryLoading ? <p className="empty-copy">Loading finalized revisions...</p> : null}
            {!caseHistoryLoading && !caseHistory?.revisions.length ? <p className="empty-copy">No finalized revisions yet.</p> : null}
            {caseHistory?.revisions.map((revision) => (
              <article key={`revision-${revision.revisionNumber}`} className="subcard">
                <div className="panel-header">
                  <div>
                    <strong>Revision {revision.revisionNumber}</strong>
                    <p className="muted-text">
                      {revision.finalizedAt ? formatDateTime(revision.finalizedAt) : "Finalize date unavailable"}
                      {revision.finalizedBy ? ` by ${revision.finalizedBy}` : ""}
                    </p>
                  </div>
                  {revision.pdfAssetRef ? (
                    <button
                      className="secondary-button"
                      type="button"
                      onClick={() => onOpenRevisionPdf(revision.revisionNumber)}
                    >
                      <ButtonLabel icon="pdf">Open PDF</ButtonLabel>
                    </button>
                  ) : null}
                </div>
                <p className="muted-text">{revision.templateVersion || "Template version pending"}</p>
                <p>{revision.reportNarrativeSnapshot || "No narrative snapshot stored for this revision."}</p>
              </article>
            ))}
          </div>
        </article>

        <article className="panel">
          <div className="panel-header">
            <div>
              <p className="eyebrow">Audit trail</p>
              <h2>Workflow events</h2>
            </div>
          </div>
          <div className="list-stack">
            {caseHistoryLoading ? <p className="empty-copy">Loading audit events...</p> : null}
            {!caseHistoryLoading && !caseHistory?.auditEvents.length ? <p className="empty-copy">No audit events recorded yet.</p> : null}
            {caseHistory?.auditEvents.map((event) => (
              <article key={event.id} className="subcard">
                <div className="panel-header">
                  <div>
                    <strong>{formatLabel(event.eventType)}</strong>
                    <p className="muted-text">
                      {formatDateTime(event.createdAt)}
                      {event.actorDisplayName ? ` by ${event.actorDisplayName}` : ""}
                      {event.actorRole ? ` (${formatLabel(event.actorRole)})` : ""}
                    </p>
                  </div>
                  <span className="status-chip tone-neutral">{formatLabel(event.entityType)}</span>
                </div>
                {event.reason ? <p>{event.reason}</p> : null}
                {event.entityRef ? <p className="muted-text">Ref: {event.entityRef}</p> : null}
              </article>
            ))}
          </div>
        </article>
        </aside>
      </section>
      <FloatingHelpDock
        label="Procedure guide"
        title={`${formatProcedureLabel(caseDraft.procedure_type)} workflow`}
        summary="Keep the pathway and key authoring checks nearby without filling the right rail with reference content."
        sections={helpSections}
      />
    </>
  );
}

function ToggleField({
  label,
  checked,
  disabled,
  onChange
}: {
  label: string;
  checked: boolean;
  disabled?: boolean;
  onChange: (checked: boolean) => void;
}) {
  return (
    <label className={`toggle-field${disabled ? " is-disabled" : ""}`}>
      <input type="checkbox" checked={checked} disabled={disabled} onChange={(event) => onChange(event.target.checked)} />
      <span>{label}</span>
    </label>
  );
}

function CaseImageCard({
  caseId,
  image,
  editable,
  deleting,
  onOpen,
  onRemove
}: {
  caseId: string;
  image: CaseImageAttachmentPayload;
  editable: boolean;
  deleting: boolean;
  onOpen: () => void;
  onRemove: () => void;
}) {
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [previewFailed, setPreviewFailed] = useState(false);
  const canOpen = Boolean(image.external_image_id);

  useEffect(() => {
    let cancelled = false;
    let objectUrl: string | null = null;

    setPreviewUrl(null);
    setPreviewFailed(false);

    if (!image.external_image_id) {
      setPreviewFailed(true);
      return () => undefined;
    }

    fetchCaseImageBinary(caseId, image.external_image_id)
      .then(({ blob }) => {
        objectUrl = window.URL.createObjectURL(blob);
        if (cancelled) {
          window.URL.revokeObjectURL(objectUrl);
          return;
        }
        setPreviewUrl(objectUrl);
      })
      .catch(() => {
        if (!cancelled) {
          setPreviewFailed(true);
        }
      });

    return () => {
      cancelled = true;
      if (objectUrl) {
        window.URL.revokeObjectURL(objectUrl);
      }
    };
  }, [caseId, image.external_image_id]);

  return (
    <figure className="case-image-card">
      <button className="case-image-preview" type="button" onClick={onOpen} disabled={!canOpen} aria-label={`Open ${image.caption || image.file_name}`}>
        {previewUrl ? (
          <img src={previewUrl} alt={image.caption || image.file_name} />
        ) : (
          <span className="case-image-preview-fallback" aria-hidden="true">
            <AppIcon name={previewFailed ? "image" : "upload"} size={22} />
          </span>
        )}
      </button>
      <figcaption className="case-image-body">
        <div>
          <strong>{image.caption || image.file_name}</strong>
          {image.caption ? <p className="muted-text">{image.file_name}</p> : null}
        </div>
        <div className="case-image-meta">
          <span>{formatFileSize(image.size_bytes)}</span>
          <span>{image.content_type || "Image"}</span>
          <span>{image.uploaded_at ? formatDateTime(image.uploaded_at) : "Upload time not recorded"}</span>
        </div>
        <div className="case-image-actions">
          <button className="secondary-button" type="button" onClick={onOpen} disabled={!canOpen}>
            <ButtonLabel icon="preview">Open</ButtonLabel>
          </button>
          {editable ? (
            <button className="secondary-button danger-button" type="button" onClick={onRemove} disabled={!image.external_image_id || deleting}>
              <ButtonLabel icon="trash">{deleting ? "Removing..." : "Remove"}</ButtonLabel>
            </button>
          ) : null}
        </div>
      </figcaption>
    </figure>
  );
}

function NavigationButton({
  active,
  icon,
  label,
  caption,
  count,
  onClick
}: {
  active: boolean;
  icon: IconName;
  label: string;
  caption: string;
  count?: number;
  onClick: () => void;
}) {
  return (
    <button className={`nav-button${active ? " is-active" : ""}`} type="button" onClick={onClick}>
      <span className="nav-main">
        <span className="nav-icon" aria-hidden="true">
          <AppIcon name={icon} size={18} />
        </span>
        <span className="nav-text">
          <strong>{label}</strong>
          <small>{caption}</small>
        </span>
      </span>
      {typeof count === "number" ? <span className="nav-count">{count}</span> : null}
    </button>
  );
}

function MobileNavigationButton({
  active,
  icon,
  label,
  count,
  onClick
}: {
  active: boolean;
  icon: IconName;
  label: string;
  count?: number;
  onClick: () => void;
}) {
  return (
    <button className={`mobile-nav-button${active ? " is-active" : ""}`} type="button" onClick={onClick}>
      <span className="mobile-nav-icon" aria-hidden="true">
        <AppIcon name={icon} size={18} />
      </span>
      <strong>{label}</strong>
      {typeof count === "number" ? <span>{count}</span> : <span>&nbsp;</span>}
    </button>
  );
}

function SignalCard({
  icon,
  label,
  value,
  tone,
  note,
  compact = false
}: {
  icon: IconName;
  label: string;
  value: ReactNode;
  tone: StatusTone;
  note?: string;
  compact?: boolean;
}) {
  return (
    <article className={`signal-card tone-${tone}${compact ? " is-compact" : ""}`}>
      <div className="signal-topline">
        <span className="signal-icon" aria-hidden="true">
          <AppIcon name={icon} size={16} />
        </span>
        <span>{label}</span>
      </div>
      <strong>{value}</strong>
      {note ? <small>{note}</small> : null}
    </article>
  );
}

function DashboardQueueStripItem({
  icon,
  label,
  value,
  tone,
  caption
}: {
  icon: IconName;
  label: string;
  value: number;
  tone: StatusTone;
  caption: string;
}) {
  return (
    <article className={`queue-strip-item tone-${tone}`}>
      <div className="queue-strip-topline">
        <span className="micro-icon" aria-hidden="true">
          <AppIcon name={icon} size={15} />
        </span>
        <span>{label}</span>
      </div>
      <strong className="queue-strip-value">{value}</strong>
      <small>{caption}</small>
    </article>
  );
}

function SurfaceSection({
  eyebrow,
  title,
  summary,
  icon,
  count,
  tone,
  children
}: {
  eyebrow: string;
  title: string;
  summary: string;
  icon: IconName;
  count: number;
  tone: StatusTone;
  children: ReactNode;
}) {
  return (
    <section className={`panel surface-section tone-${tone}`}>
      <div className="surface-section-header">
        <div className="title-with-icon">
          <span className="panel-icon" aria-hidden="true">
            <AppIcon name={icon} size={18} />
          </span>
          <div>
            <p className="eyebrow">{eyebrow}</p>
            <h2>{title}</h2>
            <p className="surface-section-summary">{summary}</p>
          </div>
        </div>
        <span className={`status-chip tone-${tone}`}>{count}</span>
      </div>
      <div className="list-stack">{children}</div>
    </section>
  );
}

function QueuePanel({
  eyebrow,
  title,
  summary,
  icon,
  count,
  tone,
  emptyTitle,
  emptyMessage,
  actionLabel,
  actionIcon,
  onAction,
  items,
  compact = false
}: {
  eyebrow: string;
  title: string;
  summary: string;
  icon: IconName;
  count: number;
  tone: StatusTone;
  emptyTitle: string;
  emptyMessage: string;
  actionLabel: string;
  actionIcon: IconName;
  onAction: () => void;
  items: ReactNode[];
  compact?: boolean;
}) {
  return (
    <article className={`panel queue-panel tone-${tone}${compact ? " is-compact" : ""}`}>
      <div className="panel-header">
        <div className="title-with-icon">
          <span className="panel-icon" aria-hidden="true">
            <AppIcon name={icon} size={18} />
          </span>
          <div>
            <p className="eyebrow">{eyebrow}</p>
            <h2>{title}</h2>
            <p className="queue-panel-summary">{summary}</p>
          </div>
        </div>
        <span className={`status-chip tone-${tone}`}>{count}</span>
      </div>
      <div className="queue-list">{items.length ? items : <QueueEmptyState title={emptyTitle} body={emptyMessage} />}</div>
      <button className="secondary-button" type="button" onClick={onAction}>
        <ButtonLabel icon={actionIcon}>{actionLabel}</ButtonLabel>
      </button>
    </article>
  );
}

function QueueEmptyState({ title, body }: { title: string; body: string }) {
  return (
    <div className="queue-empty-state">
      <strong>{title}</strong>
      <p>{body}</p>
    </div>
  );
}

function DashboardQueueItem({
  icon,
  title,
  subtitle,
  detail,
  tone,
  badge
}: {
  icon: IconName;
  title: string;
  subtitle: string;
  detail: string;
  tone: StatusTone;
  badge: string;
}) {
  return (
    <article className="queue-item clinical-list-row">
      <div className="queue-item-topline">
        <div className="queue-title-row">
          <span className="micro-icon" aria-hidden="true">
            <AppIcon name={icon} size={15} />
          </span>
          <div className="clinical-row-title">
            <strong>{title}</strong>
            <small className="clinical-row-subtitle">{subtitle}</small>
          </div>
        </div>
        <span className={`status-chip tone-${tone}`}>{badge}</span>
      </div>
      <div className="clinical-row-meta">
        <span>{detail}</span>
      </div>
    </article>
  );
}

function FloatingHelpDock({
  label,
  title,
  summary,
  sections
}: {
  label: string;
  title: string;
  summary: string;
  sections: HelpDockSection[];
}) {
  const [open, setOpen] = useState(false);

  return (
    <div className={`floating-help-dock${open ? " is-open" : ""}`}>
      {open ? (
        <section className="floating-help-panel" role="dialog" aria-label={title}>
          <div className="help-panel-header">
            <div className="title-with-icon">
              <span className="panel-icon" aria-hidden="true">
                <AppIcon name="help" size={18} />
              </span>
              <div>
                <p className="eyebrow">Workflow help</p>
                <h2>{title}</h2>
              </div>
            </div>
            <button className="help-close-button" type="button" onClick={() => setOpen(false)} aria-label="Close workflow help">
              <AppIcon name="close" size={16} />
            </button>
          </div>
          <p className="muted-text">{summary}</p>
          <div className="help-section-stack">
            {sections.map((section) => (
              <article key={section.title} className="help-section">
                <div className="help-section-header">
                  <span className="panel-icon" aria-hidden="true">
                    <AppIcon name={section.icon} size={18} />
                  </span>
                  <div>
                    <p className="eyebrow">{section.eyebrow}</p>
                    <h3>{section.title}</h3>
                  </div>
                </div>
                <div className="help-section-items">
                  {section.items.map((item, index) => (
                    <div key={`${section.title}-${index}`} className="help-item">
                      <span className={`help-item-marker${section.numbered ? " is-numbered" : ""}`} aria-hidden="true">
                        {section.numbered ? index + 1 : <AppIcon name="checklist" size={14} />}
                      </span>
                      <div className="help-item-body">
                        <strong>{item.label}</strong>
                        {item.detail ? <p>{item.detail}</p> : null}
                      </div>
                    </div>
                  ))}
                </div>
              </article>
            ))}
          </div>
        </section>
      ) : null}
      <button className="floating-help-button" type="button" aria-expanded={open} onClick={() => setOpen((current) => !current)}>
        <span className="floating-help-button-icon" aria-hidden="true">
          <AppIcon name="help" size={18} />
        </span>
        <span className="floating-help-button-copy">
          <strong>{label}</strong>
          <small>Workflow and checks</small>
        </span>
      </button>
    </div>
  );
}

function CaseCard({
  entry,
  compact = false,
  interactive = false,
  onOpen
}: {
  entry: CaseSummary;
  compact?: boolean;
  interactive?: boolean;
  onOpen?: () => void;
}) {
  const content = (
    <>
      <div className="card-topline clinical-row-head">
        <div className="clinical-row-title">
          <h3>{entry.patientIdentifier}</h3>
          <p className="clinical-row-subtitle">
            {formatProcedureLabel(entry.procedureType)} / {formatDateTime(entry.procedureDatetime)}
          </p>
        </div>
        <span className={`status-chip tone-${getCaseStatusTone(entry.status)}`}>{formatStatusLabel(entry.status)}</span>
      </div>
      <div className="clinical-row-meta">
        <span><strong>{entry.endoscopistName}</strong></span>
        <span>{entry.id}</span>
      </div>
    </>
  );

  if (!interactive || !onOpen) {
    return <article className={`result-card clinical-row-card${compact ? " is-compact" : ""}`}>{content}</article>;
  }

  return (
    <button className={`result-card result-card-button clinical-row-card${compact ? " is-compact" : ""}`} type="button" onClick={onOpen}>
      {content}
    </button>
  );
}

function TaskCard({
  entry,
  interactive = false,
  onOpen
}: {
  entry: FollowUpTask;
  interactive?: boolean;
  onOpen?: () => void;
}) {
  const due = getDueMeta(entry.dueDate);
  const content = (
    <>
      <div className="card-topline clinical-row-head">
        <div className="clinical-row-title">
          <h3>{formatTaskTypeLabel(entry.type)}</h3>
          <p className="clinical-row-subtitle">Case {entry.caseId}</p>
        </div>
        <span className={`status-chip tone-${getTaskStatusTone(entry.status)}`}>{formatStatusLabel(entry.status)}</span>
      </div>
      <div className="clinical-row-meta">
        <span><strong>{entry.ownerName}</strong></span>
        <span className={`status-chip tone-${due.tone}`}>{due.label}</span>
        <span>{entry.id}</span>
      </div>
    </>
  );

  if (!interactive || !onOpen) {
    return <article className="result-card clinical-row-card">{content}</article>;
  }

  return (
    <button className="result-card result-card-button clinical-row-card" type="button" onClick={onOpen}>
      {content}
    </button>
  );
}

function EmptyStateCard({ title, body, compact = false }: { title: string; body: string; compact?: boolean }) {
  return (
    <article className={`panel empty-panel${compact ? " is-compact" : ""}`}>
      <h3>{title}</h3>
      <p>{body}</p>
    </article>
  );
}
