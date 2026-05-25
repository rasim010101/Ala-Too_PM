# How to Run Ala-Too PM Locally

> **Current deployment status:** The application runs on a local machine via Docker.
> A public server installation (with a permanent domain and HTTPS) requires a VPS —
> see `DEPLOY.md` for those instructions once a server is available.

---

## What you need before starting

| Requirement | Where to get it |
|---|---|
| **Docker Desktop** (Windows / macOS) | https://www.docker.com/products/docker-desktop/ |
| **~6 GB free RAM** | Close heavy applications before starting |
| **~5 GB free disk space** | For Docker images downloaded on first run |
| **Internet connection** | Only on first run, to download base images |

> **Windows users:** after installing Docker Desktop, make sure it is running
> (look for the Docker whale icon in the system tray — it should be white, not grey).
> Open **PowerShell**, not Command Prompt (cmd).

---

## Step 1 — Extract the archive

Unzip `ala-too-pm-v1.0.zip` into any folder, for example:

```
C:\Projects\ala-too-pm\
```

You should see these files inside:

```
docker-compose.yml
.env.example
HOW_TO_RUN.md   ← this file
README.md
ONBOARDING.md
DEPLOY.md
TECHNICAL_DOCUMENTATION.md
gateway/
taiga-back/
taiga-front/
taiga-events/
```

---

## Step 2 — Create the configuration file

Open PowerShell, navigate to the extracted folder, and create `.env`:

```powershell
cd C:\Projects\ala-too-pm
Copy-Item .env.example .env
```

The default `.env` values work for a local run — you do not need to change anything
for the first launch.

---

## Step 3 — Build and start

```powershell
docker compose up -d --build
```

**The first run takes 5–15 minutes** — Docker downloads base images (~2 GB)
and compiles Python dependencies. Subsequent starts take about 30 seconds.

Watch the progress:

```powershell
docker compose logs -f taiga-back
```

When you see the line `Starting Taiga API...` — the application is ready.
Press `Ctrl+C` to stop watching logs (the app keeps running in the background).

---

## Step 4 — Create the first admin account

```powershell
docker compose exec taiga-back python manage.py createsuperuser
```

You will be prompted for:
- **Username** — e.g. `admin`
- **Email** — any valid email address
- **Password** — choose a strong one

---

## Step 5 — Open in browser

Go to: **http://localhost:9000**

Log in with the username and password you just created.

### What you will see

- **Create project** → choose *Scrum (Course Project)* or *Kanban (Lab & Workshop)*
- **Settings → Members** → invite users; role dropdown includes *Instructor, Teaching Assistant, Team Lead, Student, Course Coordinator, Reviewer*
- **Wiki** tab inside any project for documentation
- **Issues** tab for bug/task tracking
- The top bar shows the Ala-Too International University identification band

---

## Stopping and restarting

```powershell
# Stop all containers (data is preserved)
docker compose down

# Start again (fast, no rebuild needed)
docker compose up -d

# Full wipe — deletes ALL data (irreversible)
docker compose down -v
```

---

## Troubleshooting

**"Cannot connect" / page does not open**  
→ Check that Docker Desktop is running. Run `docker compose ps` — all services should show `Up`.

**`taiga-back` keeps restarting**  
→ The database is still initialising. Wait 30 seconds and run `docker compose ps` again.
It recovers automatically.

**Port 9000 is already in use**  
→ Open `.env`, change `HTTP_PORT=9000` to any free port (e.g. `8080`), then run
`docker compose up -d` again. Open `http://localhost:8080` instead.

**Kanban / Scrum board is empty after browser refresh**  
→ The WebSocket connection may have dropped. Refresh the page (F5).

**Wiki page shows "infinite loading" when saving**  
→ Press `Ctrl+F5` to hard-reload the page before editing, then try again.
This is caused by a stale version cached in the browser.

---

## Accessing the Django admin panel

If needed, the Django administration interface is available at:

**http://localhost:9000/admin/**

Log in with the superuser account created in Step 4. Use this panel to manage
users, permissions, and site settings directly.

---

## Notes on production deployment

This archive is configured for **local use only** (`TAIGA_DOMAIN=localhost:9000`).

To deploy on a public server (with a real domain name and HTTPS certificate):
1. Obtain a Linux VPS and a domain name
2. Follow the instructions in `DEPLOY.md` — it covers nginx, Let's Encrypt, and all
   environment variable changes needed for production

---

*For a full technical description of the system, see `TECHNICAL_DOCUMENTATION.md`.*
