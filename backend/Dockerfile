# FitGH backend — minimal Dockerfile.
# Phase 1 Walking Skeleton — WS-B.6 ships the smoke-build target; WS-G.1
# replaces this with the production-grade multi-stage build (curl + ca-certs).
#
# This minimal image is enough for the CI 'docker-build-smoke' job to verify
# the requirements.txt installs cleanly and the entrypoint runs.

FROM python:3.12-slim

WORKDIR /app

# Layer caching: install deps first so source edits don't re-download wheels.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

EXPOSE 8000

# Default to gunicorn for local container smoke; fly.toml + WS-G.1 customise
# this in production (workers, threads, timeout, gunicorn.conf.py).
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--threads", "4", "--timeout", "60", "app:create_app()"]
