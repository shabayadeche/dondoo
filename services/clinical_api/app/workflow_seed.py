from app.schemas import DashboardSnapshot, WorkflowStep


SHARED_START_STEPS = [
    WorkflowStep(
        id="start_case",
        label="Start Case",
        description="Create the case and assign the care team.",
    ),
    WorkflowStep(
        id="safety",
        label="Safety",
        description="Capture shared safety and consent data.",
    ),
]

COLONOSCOPY_WORKFLOW_STEPS = [
    *SHARED_START_STEPS,
    WorkflowStep(
        id="prep_completeness",
        label="Prep And Completeness",
        description="Record bowel prep, cecal completion, and core timing.",
    ),
    WorkflowStep(
        id="segment_exam",
        label="Segment Exam",
        description="Capture segment-level inspection and IBD activity if applicable.",
    ),
    WorkflowStep(
        id="lesion_log",
        label="Lesion Log",
        description="Record polyp and lesion details in structured rows.",
    ),
    WorkflowStep(
        id="specimens_plan",
        label="Specimens And Plan",
        description="Document specimens, impression, and follow-up instructions.",
    ),
    WorkflowStep(
        id="review_signoff",
        label="Review And Sign-Off",
        description="Preview the narrative note and finalize the case.",
    ),
]

EGD_WORKFLOW_STEPS = [
    *SHARED_START_STEPS,
    WorkflowStep(
        id="egd_exam",
        label="EGD Exam",
        description="Capture esophageal, gastric, and duodenal findings plus therapy details.",
    ),
    WorkflowStep(
        id="specimens_plan",
        label="Specimens And Plan",
        description="Document biopsies, impression, and follow-up instructions.",
    ),
    WorkflowStep(
        id="review_signoff",
        label="Review And Sign-Off",
        description="Preview the narrative note and finalize the case.",
    ),
]

ERCP_WORKFLOW_STEPS = [
    *SHARED_START_STEPS,
    WorkflowStep(
        id="ercp_intervention",
        label="ERCP Intervention",
        description="Capture cannulation, duct therapy, stents, and immediate complications.",
    ),
    WorkflowStep(
        id="specimens_plan",
        label="Specimens And Plan",
        description="Document impression, device details, and follow-up instructions.",
    ),
    WorkflowStep(
        id="review_signoff",
        label="Review And Sign-Off",
        description="Preview the narrative note and finalize the case.",
    ),
]

EUS_WORKFLOW_STEPS = [
    *SHARED_START_STEPS,
    WorkflowStep(
        id="eus_exam",
        label="EUS Exam",
        description="Capture regions examined, target lesion details, and sampling activity.",
    ),
    WorkflowStep(
        id="specimens_plan",
        label="Specimens And Plan",
        description="Document sampling adequacy, impression, and follow-up instructions.",
    ),
    WorkflowStep(
        id="review_signoff",
        label="Review And Sign-Off",
        description="Preview the narrative note and finalize the case.",
    ),
]

WORKFLOW_STEPS_BY_PROCEDURE = {
    "colonoscopy": COLONOSCOPY_WORKFLOW_STEPS,
    "egd": EGD_WORKFLOW_STEPS,
    "ercp": ERCP_WORKFLOW_STEPS,
    "eus": EUS_WORKFLOW_STEPS,
}

DASHBOARD_SNAPSHOT = DashboardSnapshot(activeDrafts=6, openTasks=8, finalizedToday=11)
