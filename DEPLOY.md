# Ala-Too PM — production deployment

> **Note:** This guide describes a *future* production deployment scenario.
> The current version of the project runs locally on a development machine.
> No public VPS or domain has been provisioned yet.
> For running the project right now, see **`HOW_TO_RUN.md`** instead.

---

This walks through putting Ala-Too PM on a single Ubuntu 22.04 VPS with
its own domain and a real HTTPS certificate. The compose file is the
same one used in `HOW_TO_RUN.md`; the only differences are the
environment values, the gateway sitting behind nginx + certbot on the
host, and a real SMTP backend instead of the console one.

Assumed in the rest of the document (replace with real values when a server is available):

- Domain:    `pm.alatoo.edu.kg` (placeholder — replace with actual domain)
- Server IP: `203.0.113.10`     (placeholder — replace with actual server IP)
- Operator:  has `sudo` and SSH access

## 1. Server prep

```bash
ssh root@203.0.113.10
adduser alatoo && usermod -aG sudo alatoo
rsync --archive --chown=alatoo:alatoo ~/.ssh /home/alatoo
exit
ssh alatoo@203.0.113.10
```

Install Docker (use the official convenience script — it sets up the
apt repo correctly) and certbot:

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
newgrp docker

sudo apt update
sudo apt install -y nginx certbot python3-certbot-nginx git ufw

sudo ufw allow OpenSSH
sudo ufw allow 80,443/tcp
sudo ufw enable
```

## 2. DNS

Point an A record `pm.alatoo.edu.kg` → `203.0.113.10` and wait until
`dig +short pm.alatoo.edu.kg` returns the right IP. Certbot will not
issue a certificate until DNS is correct.

## 3. Get the code on the server

```bash
mkdir -p /opt/ala-too-pm
cd /opt/ala-too-pm
# whichever way you ship the repo onto the box:
git clone <your-repo-url> .          # or scp from your laptop
cp .env.example .env
```

Generate the secrets:

```bash
sed -i "s|^TAIGA_SECRET_KEY=.*|TAIGA_SECRET_KEY=$(python3 -c 'import secrets;print(secrets.token_urlsafe(50))')|" .env
sed -i "s|^POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$(openssl rand -hex 24)|" .env
sed -i "s|^RABBITMQ_PASS=.*|RABBITMQ_PASS=$(openssl rand -hex 24)|" .env
sed -i "s|^RABBITMQ_ERLANG_COOKIE=.*|RABBITMQ_ERLANG_COOKIE=$(openssl rand -hex 24)|" .env
```

Open `.env` and update for production:

```bash
TAIGA_SCHEME=https
TAIGA_WS_SCHEME=wss
TAIGA_DOMAIN=pm.alatoo.edu.kg
COOKIE_SECURE=True
HTTP_PORT=9000             # only reachable through the host nginx
PUBLIC_REGISTER_ENABLED=False   # invitation-only for university staff

EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.alatoo.edu.kg
EMAIL_HOST_USER=no-reply@alatoo.edu.kg
EMAIL_HOST_PASSWORD=<smtp password>
EMAIL_USE_TLS=True
```

## 4. Bring the stack up

```bash
docker compose up -d --build
docker compose exec taiga-back python manage.py createsuperuser
```

The stack now serves plain HTTP on `127.0.0.1:9000` of the server. It
is not reachable from outside yet — the host firewall does not let
9000 through. nginx on the host will terminate TLS and proxy to it.

## 5. Host nginx + Let's Encrypt

```bash
sudo tee /etc/nginx/sites-available/pm.alatoo.edu.kg >/dev/null <<'NGINX'
server {
    listen 80;
    server_name pm.alatoo.edu.kg;

    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:9000;
        proxy_http_version 1.1;
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade           $http_upgrade;
        proxy_set_header Connection        "upgrade";
        proxy_read_timeout                 7d;
    }
}
NGINX

sudo ln -s /etc/nginx/sites-available/pm.alatoo.edu.kg /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

sudo certbot --nginx -d pm.alatoo.edu.kg --redirect --agree-tos -m it-support@alatoo.edu.kg --no-eff-email
```

Certbot rewrites the nginx config in place to terminate TLS on 443 and
30x-redirect 80→443. The auto-renew systemd timer is installed by the
apt package; no extra cron is needed.

## 6. Smoke test

- `curl -I https://pm.alatoo.edu.kg/` returns `200`.
- Browser visit shows the Ala-Too PM login screen and the certificate is
  valid.
- `Settings → Project templates` lists *Scrum (Course Project)* and
  *Kanban (Lab & Workshop)*; their role pickers list *Instructor*,
  *Student*, etc.
- `docker compose exec taiga-back python manage.py sendtestemail your@email`
  delivers a message through the configured SMTP server.

## 7. Day-2 operations

| Task                       | Command                                                      |
| -------------------------- | ------------------------------------------------------------ |
| Tail logs                  | `docker compose logs -f taiga-back`                          |
| Restart a single service   | `docker compose restart taiga-back`                          |
| Rebuild after a code edit  | `docker compose up -d --build taiga-back`                    |
| Backup the database        | `docker compose exec taiga-db pg_dump -U taiga taiga > backup-$(date +%F).sql` |
| Restore                    | `cat backup.sql \| docker compose exec -T taiga-db psql -U taiga taiga` |
| Backup uploaded files      | `docker run --rm -v ala-too-pm_taiga-media-data:/d -v $PWD:/b alpine tar czf /b/media-$(date +%F).tgz -C /d .` |

## 8. Updating

The overlay is small and isolated, so pulling upstream changes is
mostly mechanical:

```bash
cd /opt/ala-too-pm
git fetch upstream
git merge upstream/master         # resolve conflicts in branding/ if any
docker compose up -d --build
```

`taiga-back/scripts/rebrand_templates.py` only needs to be re-run if
the upstream `initial_project_templates.json` fixture changes, and
even then only if you want the renames to apply to brand-new installs.
Existing projects keep the role names they were created with.
