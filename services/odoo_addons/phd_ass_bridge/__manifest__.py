{
    "name": "Endoscopy Clinical Workspace",
    "version": "19.0.1.0.0",
    "summary": "Clinical workspace and integration layer for structured endoscopy reporting.",
    "category": "Tools",
    "author": "PhD-Ass",
    "license": "LGPL-3",
    "depends": ["base", "web"],
    "images": ["static/description/icon.png"],
    "data": [
        "security/phd_ass_security.xml",
        "security/ir.model.access.csv",
        "views/res_config_settings_views.xml",
        "views/phd_ass_case_views.xml",
    ],
    "installable": True,
    "application": False,
}
