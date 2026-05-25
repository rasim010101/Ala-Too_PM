# Ala-Too PM — Technical Documentation

**Project:** Ala-Too PM — Project Management Workspace  
**Organization:** Ala-Too International University  
**Version:** 1.0  
**Date:** May 2026  
**Author:** Rasim (IT Internship, 2026)  
**Base platform:** Taiga (open-source, MPL-2.0 / AGPL-3.0)  
**Repository:** https://github.com/rasim010101/Ala-Too_PM

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [System Architecture](#2-system-architecture)
3. [Technology Stack](#3-technology-stack)
4. [Component Description](#4-component-description)
5. [Customizations and Modifications](#5-customizations-and-modifications)
6. [Database Schema Overview](#6-database-schema-overview)
7. [Configuration Reference](#7-configuration-reference)
8. [API Endpoints Overview](#8-api-endpoints-overview)
9. [Security Considerations](#9-security-considerations)
10. [Known Limitations](#10-known-limitations)
11. [File Structure](#11-file-structure)

---

## 1. Project Overview

**Ala-Too PM** is a university-adapted project management platform built on top of
the open-source [Taiga](https://taiga.io) project management suite. It provides
Ala-Too International University students and instructors with a self-hosted
collaborative workspace supporting:

- **Scrum** sprints with user stories, tasks, and a Taskboard
- **Kanban** boards with customizable swimlanes and WIP limits
- **Issue tracker** with custom fields, priorities, and assignments
- **Wiki** for project documentation and knowledge management
- **Role-based access control** with university-specific roles

The platform is entirely self-hosted inside a Docker Compose stack, requires no
cloud subscription, and runs on any machine with Docker installed.

---

## 2. System Architecture

### High-level diagram

```
  Browser (student / instructor)
        │  HTTP(S) + WebSocket
        ▼
  ┌─────────────────────┐
  │  taiga-gateway      │  nginx (port 9000 → internal routing)
  └─────────────────────┘
        │
  ┌─────┴──────────────────────────────────────┐
  │                Docker network              │
  │                                            │
  │  ┌──────────────┐   ┌────────────────────┐ │
  │  │ taiga-front  │   │   taiga-back       │ │
  │  │ (AngularJS   │   │ (Django + DRF API) │ │
  │  │  static SPA) │   └────────┬───────────┘ │
  │  └──────────────┘            │              │
  │                    ┌─────────┤              │
  │  ┌──────────────┐  │  ┌──────┴──────────┐  │
  │  │ taiga-events │  │  │   taiga-db      │  │
  │  │ (Node.js WS) │  │  │  (PostgreSQL)   │  │
  │  └──────┬───────┘  │  └─────────────────┘  │
  │         │          │                        │
  │  ┌──────┴──────────┴──────────────────────┐ │
  │  │   RabbitMQ (two virtual hosts)         │ │
  │  │   taiga-async-rabbitmq (Celery tasks)  │ │
  │  │   taiga-events-rabbitmq (WS fan-out)   │ │
  │  └────────────────────────────────────────┘ │
  │                                            │
  │  ┌──────────────┐  ┌─────────────────────┐  │
  │  │ taiga-async  │  │  taiga-protected    │  │
  │  │ (Celery      │  │  (nginx for         │  │
  │  │  worker)     │  │   protected media)  │  │
  │  └──────────────┘  └─────────────────────┘  │
  └────────────────────────────────────────────┘
```

### Request flow

1. The browser loads the **AngularJS SPA** from `taiga-front` (served by the gateway).
2. The SPA sends **REST API calls** to `taiga-back` (`/api/v1/...`).
3. `taiga-back` reads/writes **PostgreSQL** (`taiga-db`) and publishes events to **RabbitMQ**.
4. `taiga-events` (Node.js) subscribes to RabbitMQ and forwards events over **WebSocket** to open browser tabs, enabling real-time updates without polling.
5. Long-running jobs (email delivery, notifications) are offloaded to **Celery** workers (`taiga-async`) via a separate RabbitMQ vhost.
6. User-uploaded files (avatars, attachments) are stored in a Docker-managed volume and served through **taiga-protected** (nginx with `X-Accel-Redirect`).

---

## 3. Technology Stack

| Layer | Technology | Version |
|---|---|---|
| Container runtime | Docker + Docker Compose | Docker ≥ 24 |
| Reverse proxy / gateway | nginx | 1.25 (Alpine) |
| Backend framework | Django | 3.2 |
| REST API | Django REST Framework (DRF) | 3.12 |
| Async tasks | Celery | 5.x |
| Message broker | RabbitMQ | 3.11 |
| Database | PostgreSQL | 12.3 |
| Frontend framework | AngularJS | 1.x (compiled SPA) |
| Real-time events | Node.js + AMQP | 16.x |
| CSS / Styling | Custom CSS override (no SCSS recompile needed) | — |
| OS (dev/demo) | Windows 11 + Docker Desktop | — |
| Public tunnel (demo) | Cloudflare Quick Tunnel (`cloudflared`) | latest |

---

## 4. Component Description

### 4.1 taiga-gateway

- **Image:** `nginx:1.25-alpine` (custom config from `gateway/taiga.conf`)
- **Exposed port:** `9000` (configurable via `HTTP_PORT` in `.env`)
- **Responsibility:** Routes incoming requests to the correct backend:
  - `/api/` → `taiga-back:8000`
  - `/admin/` → `taiga-back:8000`
  - `/events` → `taiga-events:8888` (WebSocket upgrade)
  - `/media/` → `taiga-protected:8003`
  - Everything else → `taiga-front:6363` (static SPA files)

### 4.2 taiga-back

- **Image:** `ala-too-pm-back` (built from `taiga-back/Dockerfile`)
- **Framework:** Django 3.2 + Django REST Framework
- **Responsibilities:**
  - Full REST API for all entities (projects, user stories, tasks, issues, wiki, etc.)
  - User authentication (token-based)
  - PostgreSQL ORM via Django models
  - Publishes change events to RabbitMQ for real-time propagation
  - Runs database migrations on startup
  - Loads project template fixtures on first run
- **Modified files:**
  - `taiga-back/settings/common.py` — product name, telemetry disabled
  - `taiga-back/docker/config.py` — default FROM email
  - `taiga-back/taiga/projects/fixtures/initial_project_templates.json` — university roles
  - `taiga-back/taiga/base/templates/emails/` — email subject / footer text

### 4.3 taiga-front

- **Image:** `ala-too-pm-front` (built on top of `taigaio/taiga-front`)
- **Technology:** Pre-compiled AngularJS 1.x SPA (HTML, CSS, JS bundles)
- **Responsibilities:** Renders the entire UI, communicates exclusively via REST API calls to `taiga-back`
- **Branding overlay** (files in `taiga-front/branding/`):

  | File | Purpose |
  |---|---|
  | `theme-alatoo-overrides.css` | Re-paints navbar, sidebars, buttons, login page in AIU colours |
  | `locale-en.json` | Replaces all "Taiga" strings with "Ala-Too PM" |
  | `images/logo-alatoo.png` | University seal (used as background-image via CSS) |

- **CSS technique:** Since the Taiga SVG logo is compiled into `templates.js` (binary bundle), it cannot be replaced by swapping a file. The override CSS hides the inline SVG with `display:none` and paints the university seal via `background-image` on the parent element.

### 4.4 taiga-events

- **Image:** `taigaio/taiga-events`
- **Technology:** Node.js WebSocket server
- **Responsibility:** Receives events from `taiga-back` via RabbitMQ and pushes them to connected browser clients. Enables live updates (e.g., a Kanban card moved by one user is immediately visible to all other users on the same board).

### 4.5 taiga-async + taiga-async-rabbitmq

- **Image:** `ala-too-pm-back` (same image as taiga-back, different entrypoint)
- **Technology:** Celery worker
- **Responsibility:** Processes background jobs: email notifications, Webhooks, periodic cleanup tasks.
- **RabbitMQ vhost:** `taiga-async` (separate from the events vhost)

### 4.6 taiga-db

- **Image:** `postgres:12.3`
- **Responsibility:** Persistent relational data store
- **Persistence:** Docker named volume `taiga-db-data`

### 4.7 taiga-protected

- **Image:** `nginx:1.25-alpine`
- **Responsibility:** Serves uploaded files (attachments, avatars) using nginx's `X-Accel-Redirect` mechanism. Files are only delivered when `taiga-back` has validated that the requesting user has permission to view them.

---

## 5. Customizations and Modifications

All modifications are **additive overlays** — the upstream Taiga source code is not rewritten. This design allows future upstream updates to be merged with minimal conflicts.

### 5.1 Visual branding

File: `taiga-front/branding/theme-alatoo-overrides.css`

| Element | Original | Modified |
|---|---|---|
| Navigation bar background | Taiga green | AIU navy `#1d2b6e` |
| Primary buttons | Taiga green | AIU red `#c4202c` |
| Login / register page | Taiga green gradient | AIU navy solid |
| Logo (navbar) | Taiga snowflake SVG | AIU university seal PNG |
| Logo (login page) | Taiga snowflake SVG | AIU university seal PNG |
| All sidebars | Light grey | Transparent (navy shows through) |
| University banner | — (did not exist) | Fixed top bar with institution name |
| Newsletter prompts | Visible | Hidden (`display:none`) |

Colour palette:
```
--alatoo-primary:   #1d2b6e  (navy  — seal ring and lettering)
--alatoo-accent:    #c4202c  (red   — "ALA-TOO 1996" band)
--alatoo-text-on:   #ffffff  (white — text on coloured surfaces)
```

### 5.2 String / localisation rebrand

File: `taiga-front/branding/locale-en.json`

- Product name `"Taiga"` → `"Ala-Too PM"` (all occurrences in UI strings)
- Project template display names updated
- Newsletter opening strings replaced with empty strings

### 5.3 Project templates

File: `taiga-back/taiga/projects/fixtures/initial_project_templates.json`  
Script: `taiga-back/scripts/rebrand_templates.py`

The two default project templates are adapted for academic use:

| Upstream name | Ala-Too PM name |
|---|---|
| Scrum | Scrum (Course Project) |
| Kanban | Kanban (Lab & Workshop) |

Default roles per template (was: `Back`, `Front`, `UX`, `Design`, `Product Owner`, `Stakeholder`):

| New role | Description |
|---|---|
| Instructor | Project owner, full permissions |
| Teaching Assistant | Can manage tasks and members |
| Team Lead | Student with elevated privileges |
| Student | Regular contributor |
| Course Coordinator | Read + comment access across projects |
| Reviewer | Read-only evaluation access |

### 5.4 Backend settings

File: `taiga-back/settings/common.py`

```python
ENABLE_TELEMETRY = False        # no data sent to Taiga cloud
PRODUCT_NAME = "Ala-Too PM"
PRODUCT_URL  = "https://alatoo.edu.kg"
```

### 5.5 Operations tooling (new files)

| File | Purpose |
|---|---|
| `docker-compose.yml` | Ties all 9 services into a single stack |
| `.env.example` | Template for environment configuration |
| `gateway/taiga.conf` | nginx routing rules |
| `start.ps1` | Windows automation: Cloudflare tunnel + .env update + Docker start |
| `ONBOARDING.md` | Step-by-step local setup guide |
| `DEPLOY.md` | Production VPS deployment with HTTPS |
| `.gitignore` | Excludes `.env`, `node_modules/`, `media/`, `logs/`, `__pycache__/` |

---

## 6. Database Schema Overview

The database is managed entirely by Django migrations. Below are the core entity groups (not exhaustive):

| Entity group | Key tables |
|---|---|
| Users & auth | `users_user`, `users_authdata` |
| Projects | `projects_project`, `projects_projecttemplate`, `projects_membership` |
| Roles | `users_role`, `users_rolepermission` |
| Scrum | `userstories_userstory`, `tasks_task`, `milestones_milestone` (sprints) |
| Kanban | `userstories_userstory` with swimlane |
| Issues | `issues_issue`, `issues_issuetype`, `issues_priority`, `issues_severity` |
| Wiki | `wiki_wikipage`, `wiki_wikilink` |
| Attachments | `attachments_attachment` |
| Events | Published via RabbitMQ, not stored in PostgreSQL |

---

## 7. Configuration Reference

All runtime configuration lives in `.env` (generated from `.env.example`).

| Variable | Default | Description |
|---|---|---|
| `TAIGA_SCHEME` | `http` | `http` for local, `https` for production |
| `TAIGA_DOMAIN` | `localhost:9000` | Public hostname used in generated URLs |
| `TAIGA_WS_SCHEME` | `ws` | `ws` or `wss` for WebSocket |
| `TAIGA_SECRET_KEY` | (change this) | Django signing key — must be random and secret |
| `POSTGRES_DB` | `taiga` | Database name |
| `POSTGRES_USER` | `taiga` | Database user |
| `POSTGRES_PASSWORD` | (change this) | Database password |
| `RABBITMQ_USER` | `taiga` | RabbitMQ user |
| `RABBITMQ_PASS` | (change this) | RabbitMQ password |
| `RABBITMQ_ERLANG_COOKIE` | (change this) | RabbitMQ cluster cookie |
| `HTTP_PORT` | `9000` | Host port the gateway listens on |
| `PUBLIC_REGISTER_ENABLED` | `True` | Allow self-registration (set `False` in production) |
| `COOKIE_SECURE` | `False` | Set `True` when served over HTTPS |
| `EMAIL_BACKEND` | `console` | `smtp.EmailBackend` for real email delivery |
| `ENABLE_TELEMETRY` | `False` | Never sends data to Taiga cloud |

---

## 8. API Endpoints Overview

The REST API follows standard DRF conventions. All endpoints are prefixed with `/api/v1/`.

| Resource | Endpoint prefix | Methods |
|---|---|---|
| Authentication | `/api/v1/auth` | POST (login, register) |
| Users | `/api/v1/users` | GET, PATCH, DELETE |
| Projects | `/api/v1/projects` | GET, POST, PATCH, DELETE |
| Memberships | `/api/v1/memberships` | GET, POST, DELETE |
| Sprints (milestones) | `/api/v1/milestones` | GET, POST, PATCH, DELETE |
| User stories | `/api/v1/userstories` | GET, POST, PATCH, DELETE |
| Tasks | `/api/v1/tasks` | GET, POST, PATCH, DELETE |
| Issues | `/api/v1/issues` | GET, POST, PATCH, DELETE |
| Wiki pages | `/api/v1/wiki` | GET, POST, PATCH, DELETE |
| Attachments | `/api/v1/*/attachments` | GET, POST, DELETE |

Authentication uses a token passed in the `Authorization: Bearer <token>` header, obtained after a successful POST to `/api/v1/auth`.

---

## 9. Security Considerations

| Concern | Approach |
|---|---|
| Secret management | `.env` is in `.gitignore` and never committed to the repository |
| Media file access | Served only through `taiga-protected` which validates permissions server-side |
| HTTPS | Required in production via Let's Encrypt (see `DEPLOY.md`) |
| Cookies | `COOKIE_SECURE=True` must be set when serving over HTTPS |
| Telemetry | Disabled (`ENABLE_TELEMETRY=False`) — no external data transmission |
| Self-registration | Should be set to `False` (`PUBLIC_REGISTER_ENABLED=False`) in a production university deployment to require invitation-only signup |
| API tokens | Expire on logout; stored only in browser `localStorage` by the SPA |

---

## 10. Known Limitations

| Limitation | Notes |
|---|---|
| Demo URL changes on each restart | The Cloudflare Quick Tunnel (`trycloudflare.com`) assigns a new random subdomain every time `cloudflared` starts. `start.ps1` automates the reconfiguration. |
| No persistent public URL without a server | A permanent installation requires either a VPS with a real domain (see `DEPLOY.md`) or a paid tunnel plan. |
| GitHub Codespaces sleep | Codespaces instances pause after 30 minutes of inactivity; Docker containers must be restarted with `docker compose up -d` after resume. |
| Wiki optimistic locking | Taiga uses a version field to prevent concurrent edits. If you open a wiki page, someone else saves it, and then you try to save — you'll get a conflict error. Always do Ctrl+F5 before editing to load the latest version. |
| Email in demo mode | `EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend` by default — emails are printed to the Docker log, not delivered. Set a real SMTP server for production. |

---

## 11. File Structure

```
internship_taiga/               ← repository root
├── docker-compose.yml          ← 9-service stack definition
├── .env.example                ← configuration template
├── .gitignore                  ← excludes .env, node_modules, media, logs
├── .gitattributes              ← line-ending rules for shell scripts
├── start.ps1                   ← Windows one-click startup automation
│
├── gateway/
│   └── taiga.conf              ← nginx routing configuration
│
├── taiga-back/                 ← Django backend (upstream + overlay)
│   ├── Dockerfile
│   ├── docker/
│   │   └── config.py           ← DEFAULT_FROM_EMAIL override
│   ├── settings/
│   │   └── common.py           ← PRODUCT_NAME, ENABLE_TELEMETRY
│   ├── scripts/
│   │   └── rebrand_templates.py← one-shot role/template rename script
│   └── taiga/projects/fixtures/
│       └── initial_project_templates.json  ← university roles fixture
│
├── taiga-front/                ← AngularJS frontend (upstream + overlay)
│   ├── Dockerfile
│   └── branding/               ← ALL front-end customizations
│       ├── theme-alatoo-overrides.css  ← colour / layout overrides
│       ├── locale-en.json      ← string rebrand (Taiga → Ala-Too PM)
│       └── images/
│           └── logo-alatoo.png ← university seal used in CSS
│
├── taiga-events/               ← Node.js WebSocket service (upstream only)
│
├── README.md                   ← project overview and change summary
├── ONBOARDING.md               ← local development setup guide
├── DEPLOY.md                   ← production VPS deployment guide
└── TECHNICAL_DOCUMENTATION.md  ← this file
```

---

*End of Technical Documentation*
