# Ala-Too PM — local install

> **Current deployment status:** the application runs locally on your machine.
> There is no public server or domain yet. For future production deployment
> (VPS + real domain + HTTPS), see `DEPLOY.md`.

Boots the whole stack on your laptop in ~10 minutes (the first build is
slow because Docker has to compile Python dependencies; subsequent runs
are nearly instant). Tested on Windows 11 with Docker Desktop 4.x,
macOS 14 and Ubuntu 22.04.

## 1. Prerequisites

| Requirement | Notes |
|---|---|
| **Docker Desktop ≥ 4.20** (Windows / macOS) | https://www.docker.com/products/docker-desktop/ |
| **~6 GB free RAM** | Close heavy apps before starting |
| **~5 GB free disk space** | For Docker images on first run |
| **Internet connection** | Only needed on the first build |

On Windows, open **PowerShell** (not cmd) and make sure Docker Desktop
shows a white whale icon in the system tray before you run anything below.

## 2. Extract and configure

Unzip the archive into any folder, for example `C:\Projects\ala-too-pm`, then:

```powershell
cd C:\Projects\ala-too-pm
Copy-Item .env.example .env
```

For a local run the default values in `.env` are fine — no changes needed.

If you plan to expose the app to other devices on your network, change at
least these three values in `.env`:

| Key | What for |
|---|---|
| `TAIGA_SECRET_KEY` | Django session signing — any long random string |
| `POSTGRES_PASSWORD` | Database password |
| `RABBITMQ_PASS` | Broker password |

## 3. Build and start

```powershell
docker compose up -d --build
```

**First run takes 5–15 minutes** while Docker downloads base images (~2 GB)
and compiles Python dependencies. Subsequent starts take ~30 seconds.

Watch the backend finish starting:

```powershell
docker compose logs -f taiga-back
```

When you see `Starting Taiga API...` — the app is ready. Press `Ctrl+C` to
stop watching logs (containers keep running).

## 4. Create the first admin account

```powershell
docker compose exec taiga-back python manage.py createsuperuser
```

Enter a username (e.g. `admin`), email, and password when prompted.

## 5. Open the app

Visit **http://localhost:9000** and sign in with the account you just created.

The Django admin panel (for user management) is at **http://localhost:9000/admin/**.

To create your first course project:

1. Click **Create project**
2. Pick *Scrum (Course Project)* or *Kanban (Lab & Workshop)*
3. Invite members under **Settings → Members** — the role dropdown lists
   *Instructor, Teaching Assistant, Team Lead, Student, Course Coordinator, Reviewer*

## 6. Stop / restart / wipe

```powershell
# stop all containers (all data is preserved)
docker compose down

# start again (fast, no rebuild)
docker compose up -d

# wipe database and uploaded files completely (irreversible)
docker compose down -v
```

## Troubleshooting

**Page does not open / "Cannot connect"**  
→ Make sure Docker Desktop is running. Check `docker compose ps` — all services should show `Up`.

**`taiga-back` keeps restarting**  
→ The database is still initialising. Wait 30 seconds; the container retries automatically and will recover on its own.

**Port 9000 is already in use**  
→ Open `.env`, change `HTTP_PORT=9000` to any free port (e.g. `8080`), run `docker compose up -d`, then open `http://localhost:8080`.

**Kanban / Scrum board is empty after browser refresh**  
→ The WebSocket connection dropped. Press F5 to reload the page.

**Wiki shows infinite loading when saving**  
→ Press `Ctrl+F5` (hard reload) before editing the page to fetch the latest version from the server, then try saving again.

**Front loads but live updates don't work**  
→ Check `docker compose logs taiga-events`. If you are behind a corporate proxy that strips `Upgrade` headers, WebSocket connections will fail — switch to a hotspot or home network.

**Email links say `http://localhost:9000`**  
→ Expected for local runs. Set `TAIGA_DOMAIN` and `TAIGA_SCHEME` in `.env` when deploying publicly.
