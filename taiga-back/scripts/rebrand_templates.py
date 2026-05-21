"""
Localise the two stock project templates (Scrum, Kanban) to the language
of university coursework.

The fixture role slugs are referenced as foreign-key-like identifiers when
projects are bootstrapped, so they MUST stay untouched. Only the display
name and description are rewritten.

Run once before the very first `manage.py loaddata` of the templates
fixture, or before the first container start. After projects have been
created the fixture is no longer consulted — existing projects keep
whatever role names they were created with.
"""

import json
from pathlib import Path

FIXTURE = Path(__file__).resolve().parent.parent / "taiga" / "projects" / "fixtures" / "initial_project_templates.json"

ROLE_RENAMES = {
    "ux":             "Instructor",
    "design":         "Teaching Assistant",
    "front":          "Team Lead",
    "back":           "Student",
    "product-owner":  "Course Coordinator",
    "stakeholder":    "Reviewer",
}

TEMPLATE_RENAMES = {
    "scrum": {
        "name": "Scrum (Course Project)",
        "description": (
            "Sprint-based template suited to semester-long course projects "
            "and graduation theses. Backlog holds the requirements list, "
            "sprints map to the academic calendar (typically 2-week "
            "iterations), and burndown / velocity surface how the team is "
            "tracking against the syllabus deadline."
        ),
    },
    "kanban": {
        "name": "Kanban (Lab & Workshop)",
        "description": (
            "Flow-based template suited to lab assignments and workshops "
            "where work arrives continuously. WIP limits help students "
            "avoid context switching; the board doubles as a status report "
            "the instructor can review at any time."
        ),
    },
}

# University-context custom attributes prepopulated on every new project
# created from these templates. They show up automatically on each user
# story / task / issue detail panel — no per-project setup needed.
ACADEMIC_FIELDS = [
    {
        "name": "Course",
        "description": "Subject code or course title (e.g. CS-301 Software Engineering).",
        "type": "text",
        "order": 1,
        "extra": None,
    },
    {
        "name": "Group",
        "description": "Student group, e.g. COM22-B.",
        "type": "text",
        "order": 2,
        "extra": None,
    },
    {
        "name": "Semester",
        "description": "Academic period (e.g. Spring 2026, Fall 2026).",
        "type": "text",
        "order": 3,
        "extra": None,
    },
]


def main() -> None:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))

    for entry in data:
        fields = entry["fields"]
        slug = fields["slug"]

        if slug in TEMPLATE_RENAMES:
            fields["name"] = TEMPLATE_RENAMES[slug]["name"]
            fields["description"] = TEMPLATE_RENAMES[slug]["description"]

        for role in fields.get("roles", []):
            new_name = ROLE_RENAMES.get(role["slug"])
            if new_name:
                role["name"] = new_name

        # Attach the academic custom fields to every relevant artefact
        # type. Re-run is safe: the loop replaces the list wholesale.
        for key in ("us_custom_attributes",
                    "task_custom_attributes",
                    "issue_custom_attributes"):
            fields[key] = [dict(f) for f in ACADEMIC_FIELDS]

    FIXTURE.write_text(
        json.dumps(data, ensure_ascii=False, indent=4) + "\n",
        encoding="utf-8",
    )
    print(f"updated {FIXTURE}")


if __name__ == "__main__":
    main()
