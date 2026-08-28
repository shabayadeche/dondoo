import type { ProcedureType } from "./enums.js";

export type WorkflowStep = {
  id: string;
  label: string;
  description: string;
};

const sharedStartSteps: WorkflowStep[] = [
  {
    id: "start_case",
    label: "Start Case",
    description: "Create the case and assign the care team."
  },
  {
    id: "safety",
    label: "Safety",
    description: "Capture shared safety and consent data."
  }
];

export const colonoscopyWorkflowSteps: WorkflowStep[] = [
  ...sharedStartSteps,
  {
    id: "prep_completeness",
    label: "Prep And Completeness",
    description: "Record bowel prep, cecal completion, and core timing."
  },
  {
    id: "segment_exam",
    label: "Segment Exam",
    description: "Capture segment-level inspection and IBD activity if applicable."
  },
  {
    id: "lesion_log",
    label: "Lesion Log",
    description: "Record polyp and lesion details in structured rows."
  },
  {
    id: "specimens_plan",
    label: "Specimens And Plan",
    description: "Document specimens, impression, and follow-up instructions."
  },
  {
    id: "review_signoff",
    label: "Review And Sign-Off",
    description: "Preview the narrative note and finalize the case."
  }
];

export const egdWorkflowSteps: WorkflowStep[] = [
  ...sharedStartSteps,
  {
    id: "egd_exam",
    label: "EGD Exam",
    description: "Capture esophageal, gastric, and duodenal findings plus therapy details."
  },
  {
    id: "specimens_plan",
    label: "Specimens And Plan",
    description: "Document biopsies, impression, and follow-up instructions."
  },
  {
    id: "review_signoff",
    label: "Review And Sign-Off",
    description: "Preview the narrative note and finalize the case."
  }
];

export const ercpWorkflowSteps: WorkflowStep[] = [
  ...sharedStartSteps,
  {
    id: "ercp_intervention",
    label: "ERCP Intervention",
    description: "Capture cannulation, duct therapy, stents, and immediate complications."
  },
  {
    id: "specimens_plan",
    label: "Specimens And Plan",
    description: "Document impression, device details, and follow-up instructions."
  },
  {
    id: "review_signoff",
    label: "Review And Sign-Off",
    description: "Preview the narrative note and finalize the case."
  }
];

export const eusWorkflowSteps: WorkflowStep[] = [
  ...sharedStartSteps,
  {
    id: "eus_exam",
    label: "EUS Exam",
    description: "Capture regions examined, target lesion details, and sampling activity."
  },
  {
    id: "specimens_plan",
    label: "Specimens And Plan",
    description: "Document sampling adequacy, impression, and follow-up instructions."
  },
  {
    id: "review_signoff",
    label: "Review And Sign-Off",
    description: "Preview the narrative note and finalize the case."
  }
];

export const workflowStepsByProcedure: Record<ProcedureType, WorkflowStep[]> = {
  colonoscopy: colonoscopyWorkflowSteps,
  egd: egdWorkflowSteps,
  ercp: ercpWorkflowSteps,
  eus: eusWorkflowSteps
};
