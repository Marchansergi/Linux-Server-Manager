#!/usr/bin/env bash
# Starts the real backend serving the built frontend, with a throwaway database
# and a test user. Used by playwright.config.ts; run `npm run build` first.
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/../.." && pwd)"
dist="$repo_root/frontend/dist"
if [[ ! -f "$dist/index.html" ]]; then
  echo "Frontend build not found at $dist. Run 'npm run build' first." >&2
  exit 1
fi

data_dir="$(mktemp -d)"
trap 'rm -rf "$data_dir"' EXIT

export LSM_DATABASE_URL="sqlite:///$data_dir/e2e.db"
export LSM_COOKIE_SECURE=false
export LSM_LOGIN_MAX_ATTEMPTS=50
export LSM_FRONTEND_DIST="$dist"

cd "$repo_root/backend"
uv run python -c '
import os
from sqlalchemy.orm import Session
from app.config import load_settings
from app.db import create_db_engine, init_db
from app.services.auth import create_user

engine = create_db_engine(load_settings().database_url)
init_db(engine)
with Session(engine) as db:
    create_user(db, os.environ["E2E_USERNAME"], os.environ["E2E_PASSWORD"])
'
uv run uvicorn --factory app.main:build_app --host 127.0.0.1 --port "$E2E_PORT"
