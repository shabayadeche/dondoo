{
    "name": "Endoscopy Patient Administration",
    "version": "19.0.1.0.0",
    "summary": "Patient registry and case linkage for the endoscopy workspace.",
    "category": "Tools",
    "author": "PhD-Ass",
    "license": "LGPL-3",
    "depends": ["phd_ass_bridge"],
    "data": [
        "security/phd_ass_patient_security.xml",
        "security/ir.model.access.csv",
        "views/phd_ass_patient_views.xml",
    ],
    "installable": True,
    "application": False,
}
