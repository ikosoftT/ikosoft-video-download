FROM node:22-bookworm-slim AS runtime
FROM python:3.12-slim-bookworm
COPY --from=runtime /usr/local/bin/node /usr/local/bin/node
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt requirements-worker.txt ./
RUN pip install --no-cache-dir -r requirements-worker.txt
COPY app.py ./
COPY static ./static
RUN useradd --create-home worker && mkdir -p /app/work/downloads && chown -R worker:worker /app
USER worker
ENV PORT=8000 WORKER_MODE=1
EXPOSE 8000
CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:${PORT} --workers 1 --threads 8 --timeout 120 app:app"]
