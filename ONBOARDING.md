# Ala-Too PM — local install

Boots the whole stack on your laptop in ~10 minutes (the first build is
slow because Docker has to compile Python dependencies; subsequent runs
are nearly instant). Tested on Windows 11 with Docker Desktop 4.x,
macOS 14 and Ubuntu 22.04.

## 1. Prerequisites

- Docker Desktop ≥ 4.20 (Windows / macOS) or Docker Engine ≥ 24 + Docker
  Compose plugin (Linux).
- ~6 GB free RAM. The first build downloads ~2 GB of base images.
- Ports `9000` (HTTP), `5432`, `5672` free on the host. The compose file
  exposes only `9000`; the others stay on the internal Docker network.

On Windows, open **PowerShell** (not cmd) and make sure Docker Desktop
shows a green dot in the system tray before you run anything below.

## 2. Configuration

```powershell
cd C:\Users\99670\Documents\internship_taiga
Copy-Item .env.example .env
```

Open `.env` and change at least these three values before anything goes
to a network anyone else can reach:

| Key                    | What for                                       |
| ---------------------- | ---------------------------------------------- |
| `TAIGA_SECRET_KEY`     | Django session signing — any long random str   |
| `POSTGRES_PASSWORD`    | Database password                              |
| `RABBITMQ_PASS`        | Broker password                                |

For a purely local run the defaults are fine.

## 3. Build and start

```powershell
docker compose up -d --build
```

The first run does three things in order, automatically:

1. Builds the `ala-too-pm-back` image from `taiga-back/` (Python deps,
   `collectstatic`, `compilemessages`).
2. Builds the `ala-too-pm-front` image on top of `taigaio/taiga-front`
   and layers in the brand assets from `taiga-front/branding/`.
3. Starts all eight containers, runs `manage.py migrate`, loads the
   project templates fixture (with our renamed roles), and opens the
   gateway on port `9000`.

Watch the back service finish migrating:

```powershell
docker compose logs -f taiga-back
```

When you see `Starting Taiga API...` the API is up.

## 4. Create the first user

The very first user has to be a Django superuser, otherwise nobody can
get into the admin panel.

```powershell
docker compose exec taiga-back python manage.py createsuperuser
```

Pick a username (e.g. `admin`), an email, and a strong password.

## 5. Open the app

Visit <http://localhost:9000> in the browser. Sign in with the user you
just created. The Django admin (rarely needed) is at
<http://localhost:9000/admin/>.

To create your first course project:

1. Click **Create project**.
2. Pick template *Scrum (Course Project)* or *Kanban (Lab & Workshop)*.
3. Invite students under **Settings → Members**. The role dropdown
   already lists *Instructor / Teaching Assistant / Team Lead / Student
   / Course Coordinator / Reviewer*.

## 6. Stopping / restarting / wiping

```powershell
# stop the stack (data is preserved)
docker compose down

# start it again
docker compose up -d

# wipe the database and uploaded files (irreversible)
docker compose down -v
```

## Troubleshooting

**`taiga-back` keeps restarting.** Almost always a database connection
issue. Check `docker compose logs taiga-db` — Postgres needs a few
seconds to initialise on the first start. The back container retries
migrations on each restart, so it will catch up by itself.

**Front loads but Kanban / Scrum board is empty after refresh.**
WebSocket events are not reaching the browser. Check
`docker compose logs taiga-events` and the browser DevTools network
tab — the `/events` request should upgrade to `101 Switching
Protocols`. If you are behind a corporate proxy that strips `Upgrade`
headers, it will not work; use a hotspot instead.

**Email links use `http://localhost:9000`.** Expected — set
`TAIGA_DOMAIN` and `TAIGA_SCHEME` in `.env` if you want links to point
somewhere else.

**Port 9000 already in use.** Change `HTTP_PORT` in `.env` to any free
port and `docker compose up -d` again.
