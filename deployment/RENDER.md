# Render Free migration preparation

Status: configuration prepared; Render account authorization pending. Existing public Vercel app continues using the working temporary Cloudflare worker. Do not remove that fallback until a Render public video download has been verified.

`render.yaml` creates exactly one Docker web service on **plan: free**, no databases, disks, paid workers, previews or autoscaling. Docker includes Python, Node and FFmpeg, runs as a non-root user, binds to Render's PORT, uses a single Gunicorn process to preserve job state and serves the existing API.

Before creation, verify the Render workspace cannot incur charges: no payment method, or enforced applicable spend limit of zero. Free compute alone does not prevent usage overage billing when payment details exist. Do not upgrade or add a payment card. If Render requires billing details, stop and report the requirement instead of proceeding.

## Authorization and source

Authorize the Render plugin or the waiting CLI device authorization. No password or API key needs to be shared in chat. GitHub account access is confirmed, but no dedicated Ikosoft Video Download repository exists among the accessible repositories. A dedicated repository/source must be created for the Docker service; do not overwrite an unrelated existing repository. Code is ready in the project ZIP.

## Deploy and verify

Use a dedicated GitHub repository and create the service from the root Dockerfile with Free selected, or use the root Render Blueprint. Set ALLOWED_ORIGINS to the Vercel public origin. Keep one replica/process. Poll deploy/logs until ready; then create a real public YouTube job directly on Render, poll it, download the attachment and check both video/audio streams with ffprobe. Datacenter IP restrictions from YouTube are a real possible failure; do not bypass them or declare success based on health checks.

Only after file verification: update Vercel DOWNLOAD_BACKEND_URL to the exact Render HTTPS origin, redeploy, and repeat browser preparation/save from the public frontend. Keep the Cloudflare fallback running until this final test passes.

## Free limits

Render sleeps a Free service after 15 minutes without inbound requests. Waking can take around a minute. Sleep/restart removes ephemeral files and job records, so prepared downloads might expire earlier than the app's nominal one-hour cleanup. Active polling during a job provides inbound requests; do not add keep-alive automation to prevent idle sleep. A newly woken client should wait for health before job creation.

App limits remain two concurrent jobs, two hours per video, 1 GB per resulting file. A 30-minute video is within the duration limit, but size, memory/resources and YouTube access still determine success. Free cloud resources have not yet been verified for larger files. No new one-minute/3 MB application cap is imposed.

Sources: https://render.com/docs/free and https://render.com/docs/blueprint-spec.
