# Deploying the public site on Ubuntu

`docker-compose.yml` at the repo root runs three containers:

- **caddy**: the only service with published ports (80/443). It gets and renews
  Let's Encrypt certificates, forwards requests to the other services, and
  redirects `www.<domain>` and the old static pages (`/about.html`, ...) to
  their new addresses.
- **frontend**: the built React app, at `https://<domain>`.
- **api**: the FastAPI backend, at `https://<domain>/api/...`. Being on the
  same origin as the React app, it needs no CORS entry. Its SQLite database
  lives in the `api_data` volume. It also handles the Contact Us form.

The Apache static site in `static/` is no longer deployed; the React app
replaced it.

For running the API and React app on a development machine, see
"Local development" at the end.

## One-time setup

1. **DNS:** create A records for your domain and for `www.<domain>`, both
   pointing at your home's public IP address.
2. **Router:** forward TCP 80 and 443 (and UDP 443 for HTTP/3) to the Ubuntu machine.
   Caddy needs port 80 reachable to obtain certificates.
3. **Docker:**
   ```sh
   sudo apt update && sudo apt install -y docker.io docker-compose-v2 git
   sudo usermod -aG docker $USER   # then log out and back in
   ```
4. **Code and settings:**
   ```sh
   git clone <repo-url> church-alliance && cd church-alliance
   cp deploy/site.example.env deploy/site.env          # set SITE_DOMAIN (no www)
   cp example.env .env                                 # api: Supabase, Cloudinary, SMTP
   cp frontend/example.env frontend/.env               # Supabase URL + publishable key
   chmod 600 deploy/site.env .env
   ```
   `VITE_API_URL` in `frontend/.env` is ignored by the production build (the
   app calls `/api/...` on its own origin). `DATABASE_URL` in `.env` is
   overridden by `docker-compose.yml` to point at the volume.
   For `CONTACT_SMTP_*`, use the same Gmail SMTP details as the Supabase
   project (Supabase dashboard → Authentication → SMTP Settings). Contact
   messages go to every user with the administrator role.
   In Supabase (Authentication → URL Configuration), set the Site URL to
   `https://<domain>` so login and confirmation emails link to it.
5. **Start:**
   ```sh
   docker compose up -d --build
   ```
   Within a minute or so `https://<your domain>` should load with a valid
   certificate. `docker compose logs -f caddy` shows certificate progress.

Docker starts on boot and `restart: unless-stopped` brings the containers
back after a reboot.

**Moving from the old static-site setup:** `docker compose up -d --build
--remove-orphans` stops the old `static-site` container. `deploy/contact.ini`
is no longer used and can be deleted.

## Updating

```sh
git pull && docker compose up -d --build
```

After editing `deploy/Caddyfile` or `deploy/site.env`, run `docker compose up -d caddy --force-recreate`.
After editing `.env`, run `docker compose up -d api --force-recreate`.
After editing `frontend/.env`, rebuild: `docker compose up -d --build frontend`
(Vite bakes these values into the bundle).

Run the API's maintenance commands inside its container, e.g. the abandoned
upload cleanup (schedule this with cron) and the course seed:

```sh
docker compose exec api python -m app.storage.cleanup
docker compose exec api python -m app.db.certification.seed
```

Back up the database by copying it out of the volume:
`docker compose cp api:/data/church-alliance.db ./church-alliance-backup.db`.

## Checking it works

- `https://<domain>` loads the React app, and `http://` redirects to `https://`.
- `https://www.<domain>/about` redirects to `https://<domain>/about`, and
  `/about.html` redirects to `/about`.
- Reloading a deep link such as `/news/1` still works (the frontend container
  falls back to `index.html`).
- `https://<domain>/api/v1/certifications` returns JSON.
- Sending the Contact Us form shows a confirmation and the email reaches each
  administrator. Failures are logged: `docker compose logs api | grep -i contact`.
- `docker compose logs api` shows visitors' public IP addresses, not `172.x`
  Docker addresses. The contact form's per-IP limit depends on this.
- `docker compose ps` shows `api` as healthy.

## Adding more services

Each new service joins the `web` network in `docker-compose.yml` without
publishing ports, and gets a block in `deploy/Caddyfile`. Add a DNS record
for any new subdomain.

Keep site-wide settings like `SITE_DOMAIN` out of the root `.env`: the
backend's settings class rejects unknown keys there.

## Local development

`docker-compose.dev.yml` runs just the API and the Vite dev server, with
hot reload, on any machine with Docker (no Python, uv or Node needed):

```sh
cp example.env .env                     # fill in Supabase, Cloudinary, ...
cp frontend/example.env frontend/.env   # Supabase URL + publishable key
docker compose -f docker-compose.dev.yml up --build
```

- React app: http://localhost:5173. API: http://localhost:8000/docs.
- Edits under `app/` and `frontend/` reload automatically (file polling, so
  it also works from Windows and macOS).
- The database is in the `dev_api_data` volume, separate from any
  `./church-alliance.db` on the host. Reset it with
  `docker compose -f docker-compose.dev.yml down -v`.
- After changing `pyproject.toml`/`uv.lock`, add `--build` again. After
  changing `frontend/package.json`, restart the frontend service, which runs
  `npm install` on start.
