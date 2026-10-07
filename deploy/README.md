# Deploying the public site on Ubuntu

`docker-compose.yml` at the repo root runs two containers:

- **caddy**: the only service with published ports (80/443). It gets and renews
  Let's Encrypt certificates and forwards requests to the other services.
- **static-site**: Apache serving `static/` and running the Contact Us form
  script (`static/cgi-bin/contact.py`).

## One-time setup

1. **DNS:** create an A record for your domain pointing at your home's public
   IP address.
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
   cp deploy/site.example.env deploy/site.env          # set SITE_DOMAIN
   cp deploy/contact.example.ini deploy/contact.ini    # Gmail SMTP + recipient
   chmod 600 deploy/site.env deploy/contact.ini
   ```
   Use the same Gmail SMTP details as the Supabase project
   (Supabase dashboard → Authentication → SMTP Settings).
5. **Start:**
   ```sh
   docker compose up -d --build
   ```
   Within a minute or so `https://<your domain>` should load with a valid
   certificate. `docker compose logs -f caddy` shows certificate progress.

Docker starts on boot and `restart: unless-stopped` brings both containers
back after a reboot.

## Updating

```sh
git pull && docker compose up -d --build
```

After editing only `deploy/contact.ini`, run `docker compose restart static-site`.
After editing `deploy/Caddyfile` or `deploy/site.env`, run `docker compose up -d caddy --force-recreate`.

## Checking it works

- Pages load over HTTPS, and `http://` redirects to `https://`.
- `/cgi-bin/contact.py` opened in a browser returns 405 (it only accepts POST).
- Sending the contact form lands on `contact.html#sent` and the email arrives
  with Reply-To set to the visitor. Failures are logged:
  `docker compose logs static-site | grep contact.py`.
- `docker compose logs static-site` shows visitors' public IP addresses, not
  `172.x` Docker addresses. The contact form's per-IP limit depends on this.

## Adding the React frontend and API later

Each new service joins the `web` network in `docker-compose.yml` without
publishing ports, and gets a block in `deploy/Caddyfile` (examples are
commented in both files), e.g. `app.<domain>` → `frontend` and
`api.<domain>` → `api:8000`. Add a DNS record for each subdomain. Also add the
new frontend origin to the CORS list in `app/main.py` and point
`VITE_API_URL` at the API's public URL.

Keep site-wide settings like `SITE_DOMAIN` out of the root `.env`: the
backend's settings class rejects unknown keys there.
