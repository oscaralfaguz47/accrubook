#!/usr/bin/env bash
# Smoke test of the production backend image (ADR 0007: build once, promote the same image).
#
# Runs the image the way Railway does (gunicorn, production settings, HTTPS behind a
# proxy) against a throwaway PostgreSQL, and fails unless /api/health/ reports "ok".
# Usage: scripts/smoke-image.sh <image> <revision>   (or `make smoke-image`)
set -euo pipefail

image="${1:?usage: scripts/smoke-image.sh <image> <revision>}"
revision="${2:?usage: scripts/smoke-image.sh <image> <revision>}"
name="accrubook-smoke"
port="8001" # 8000 is the development backend from docker-compose.yml

# The image must say which commit it was built from (OCI label), so an image in the
# registry can always be traced back to its source. Checked before any container starts.
label="$(docker image inspect \
  --format '{{ index .Config.Labels "org.opencontainers.image.revision" }}' "$image")"
if [ "$label" != "$revision" ]; then
  echo "Revision label is '$label', expected '$revision'." >&2
  exit 1
fi

cleanup() {
  local status=$?
  if [ "$status" -ne 0 ]; then
    echo "Smoke test failed. Logs of the API container:"
    docker logs "$name-api" 2>&1 || true
  fi
  docker rm --force "$name-api" "$name-db" >/dev/null 2>&1 || true
  docker network rm "$name" >/dev/null 2>&1 || true
  exit "$status"
}
trap cleanup EXIT

docker network create "$name" >/dev/null

# Same image tag as the db service in docker-compose.yml.
docker run --detach --name "$name-db" --network "$name" \
  --env POSTGRES_PASSWORD=smoke-test-only \
  postgres:17-alpine >/dev/null

# Only the required variables are set, so every other setting keeps its production
# default (HTTPS only, JSON logs, API docs off). These values are throwaway.
docker run --detach --name "$name-api" --network "$name" \
  --publish "127.0.0.1:$port:8000" \
  --env DJANGO_SECRET_KEY=smoke-test-only-not-a-real-secret \
  --env DATABASE_URL="postgres://postgres:smoke-test-only@$name-db:5432/postgres" \
  --env GUNICORN_WORKERS=2 \
  "$image" >/dev/null

# Railway terminates TLS and sends X-Forwarded-Proto: https; without it the app
# redirects to HTTPS. Until gunicorn listens and PostgreSQL accepts connections,
# Docker's port forwarder resets the connection or the API answers 503, so each
# attempt is a fresh request and the API gets up to 30 seconds to become ready.
response=""
for attempt in $(seq 1 15); do
  if response="$(curl --fail --silent --show-error --max-time 5 \
    --header "X-Forwarded-Proto: https" \
    "http://localhost:$port/api/health/")"; then
    break
  fi
  echo "Attempt $attempt/15: API not ready yet, retrying in 2 seconds."
  sleep 2
done
echo "$response"

# A redirect (301) is not an error for curl, so the body is checked as well.
if [[ "$response" != *'"status": "ok"'* ]]; then
  echo "Unexpected health response." >&2
  exit 1
fi
echo "Smoke test passed: $image"
