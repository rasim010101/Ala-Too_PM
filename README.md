# Ala-Too PM

A project-management workspace for Ala-Too International University, built on top of the
open-source Taiga platform (MPL-2.0). Provides Kanban boards, Scrum
sprints, an issue tracker, a wiki and per-project role permissions
suitable for course projects, theses and lab work.

The stack is split across three Git-tracked components inherited from
upstream Taiga and tied together by a single Docker Compose file at the
repository root:

| Component       | Role                                          |
| --------------- | --------------------------------------------- |
| `taiga-back/`   | Django + DRF API, Postgres, Celery workers    |
| `taiga-front/`  | AngularJS single-page client                  |
| `taiga-events/` | Node.js WebSocket fan-out for live updates    |

## What was changed relative to upstream Taiga

The upstream project remains intact and unmodified everywhere it is not
necessary to touch it. Our overlay is concentrated in a handful of
places so it is easy to audit and to merge upstream updates later.

- **Branding**: product name, page titles, meta description, login /
  register / error wordmark, email subjects, footer support links.
  The brand colour palette is layered on top of the original theme via
  a small CSS override rather than rewriting the SCSS source.
- **Defaults for university use**: the two stock project templates
  (Scrum and Kanban) are renamed to *Scrum (Course Project)* and
  *Kanban (Lab & Workshop)*, and the six default roles per template
  become *Instructor*, *Teaching Assistant*, *Team Lead*, *Student*,
  *Course Coordinator*, *Reviewer*. Role slugs (which are used as
  identifiers) are preserved so the change is backward-compatible.
- **Operations**: a root `docker-compose.yml`, an `nginx` gateway in
  `gateway/`, and an `.env.example` to make a fresh `docker compose up`
  produce a working install.
- **No telemetry**: the back image runs with `ENABLE_TELEMETRY=False`.

Files that hold the overlay:

```
docker-compose.yml
.env.example
gateway/taiga.conf
taiga-front/branding/                       # the front overlay
taiga-back/scripts/rebrand_templates.py     # one-shot fixture rebrand
taiga-back/settings/common.py               # SR dict (product_name, etc.)
taiga-back/docker/config.py                 # DEFAULT_FROM_EMAIL default
taiga-back/taiga/base/templates/emails/...  # email title/footer
```

## Getting started

See [`ONBOARDING.md`](ONBOARDING.md) for a step-by-step local install on
Windows, macOS or Linux.

See [`DEPLOY.md`](DEPLOY.md) for a production install on an Ubuntu VPS
with a real domain and HTTPS.

## Upstream

- Upstream project: https://github.com/taigaio
- Licence: MPL-2.0 (back, events), AGPL-3.0 (front). Both licences
  travel with the source.
