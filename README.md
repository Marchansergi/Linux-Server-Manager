# Linux Server Manager

A self-hosted, lightweight web dashboard for monitoring Linux servers in
homelabs, development environments and small infrastructures.

**Status: Phase 1.** The dashboard is read-only and shows:

- System information: hostname, OS, kernel, architecture, uptime
- CPU usage (total and per core), load average, frequency
- RAM and swap usage
- Storage usage of block-device filesystems

It does not run commands or change anything on the server.

## Security model

- Every metrics endpoint requires a logged-in session. Only `/api/health` is public.
- Passwords are hashed with scrypt. Session tokens are random, stored only as
  SHA-256 hashes, and revocable (logout or password change).
- The session cookie is `HttpOnly`, `SameSite=Strict` and `Secure` by default.
- Failed logins are rate-limited per client IP (5 per 5 minutes by default).
- There is no sign-up. Users are created from the command line on the server.
- The Docker container runs as a non-root user with a read-only filesystem,
  no Linux capabilities, and the host filesystem mounted **read-only**.

> **Do not expose it directly to the internet.** Put it behind a reverse proxy
> with HTTPS (Caddy, Traefik, nginx) or reach it through a VPN.

## Quick start (Docker)

```bash
git clone https://github.com/Marchansergi/Linux-Server-Manager.git
cd Linux-Server-Manager
docker compose up -d --build

# Create the first user (prompts for a password, minimum 12 characters)
docker compose exec lsm python -m app.cli create-user admin
```

Open <http://localhost:8000>. By default the port is bound to `127.0.0.1` only.

To reset a password (this also signs the user out everywhere):

```bash
docker compose exec lsm python -m app.cli set-password admin
```

### How the container sees the host

A container normally sees its own filesystem and hostname, not the server's.
`docker-compose.yml` therefore:

- mounts the host root read-only at `/host` and sets `LSM_HOST_ROOT=/host`.
  The OS name is read from `/host/etc/os-release` and the mount table from
  `/host/proc/1/mounts`;
- uses `uts: host`, so the hostname is the server's.

CPU and memory come from `/proc`, which already reflects the whole host.

The read-only host mount is a trade-off: if the application were compromised,
an attacker could read host files that are readable by UID 10001 (not
`/etc/shadow` or other root-only files). If you don't accept that, run it
directly on the host instead (see below).

### Accessing it from other machines

Browsers only send `Secure` cookies over HTTPS or to `localhost`. To reach the
dashboard from your network:

1. **Recommended:** put an HTTPS reverse proxy in front of it. Set
   `FORWARDED_ALLOW_IPS` to the address the proxy connects from, so the backend
   trusts its `X-Forwarded-For` header. Otherwise every client appears with the
   proxy's IP, and login rate limiting treats all of them as one client.
2. **Trusted LAN only:** change the port to `"8000:8000"` and set
   `LSM_COOKIE_SECURE: "false"`. The password and session cookie then travel
   unencrypted.

## Running directly on the host

Requires Python 3.11+, [uv](https://docs.astral.sh/uv/) and Node.js 22.

```bash
cd frontend && npm ci && npm run build && cd ..
cd backend && uv sync --no-dev
uv run python -m app.cli create-user admin
LSM_FRONTEND_DIST=../frontend/dist uv run uvicorn --factory app.main:build_app --port 8000
```

Run it as an unprivileged user. Phase 1 needs no root privileges.

## Configuration

Environment variables, all optional (see [`.env.example`](.env.example)):

| Variable | Default | Description |
| --- | --- | --- |
| `LSM_DATABASE_URL` | `sqlite:///./data/lsm.db` | Users and sessions database |
| `LSM_HOST_ROOT` | `/` | Where the host filesystem is mounted (`/host` in Docker) |
| `LSM_SESSION_TTL_MINUTES` | `720` | Session lifetime |
| `LSM_COOKIE_SECURE` | `true` | Send the session cookie only over HTTPS/localhost |
| `LSM_LOGIN_MAX_ATTEMPTS` | `5` | Failed logins allowed per IP within the window |
| `LSM_LOGIN_WINDOW_SECONDS` | `300` | Rate-limit window |
| `LSM_FRONTEND_DIST` | unset | Built frontend to serve; unset means API only |
| `LSM_LOG_LEVEL` | `INFO` | Log level |

## API

All endpoints are under `/api` and return JSON. The OpenAPI schema is at
`/api/openapi.json`.

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| GET | `/health` | no | Liveness check |
| POST | `/auth/login` | no | `{username, password}`; sets the session cookie |
| POST | `/auth/logout` | no | Revokes the current session |
| GET | `/auth/me` | yes | Current user |
| GET | `/system/info` | yes | Hostname, OS, kernel, uptime |
| GET | `/system/cpu` | yes | CPU usage, cores, load, frequency |
| GET | `/system/memory` | yes | RAM and swap |
| GET | `/system/storage` | yes | Filesystem usage |

CPU usage is measured between consecutive requests (psutil's non-blocking
mode). With several dashboards open, each reading covers a shorter interval.

## Development

```
backend/    FastAPI app (routes → services → psutil / /proc), SQLite via SQLAlchemy
frontend/   React + TypeScript + Tailwind (Vite), Playwright end-to-end tests
```

Backend:

```bash
cd backend
uv sync
uv run uvicorn --factory app.main:build_app --reload   # http://127.0.0.1:8000
uv run pytest                                          # tests + coverage (min 85%)
uv run ruff check . && uv run ruff format --check . && uv run mypy app tests
```

For local development over plain HTTP, set `LSM_COOKIE_SECURE=false`.

Frontend (proxies `/api` to the backend on port 8000):

```bash
cd frontend
npm ci
npm run dev          # http://localhost:5173
npm run typecheck
npm run build && npm run test:e2e   # E2E runs against the real backend
```

## License

[MIT](LICENSE)
