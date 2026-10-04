# Live public app and temporary download backend

Public app: https://vercel-one-omega-81.vercel.app

The Vercel frontend connects directly to an HTTPS Cloudflare Quick Tunnel for the Gunicorn downloader running on the owner's computer. Arabic/English, saved preference, real progress, downloadable files and the pending PayPal section remain enabled. No paid service or additional hosting account was used.

## Verified on October 4, 2026

From the public Vercel app in a browser, a public YouTube video was prepared and the Save button downloaded an actual 533,915-byte MP4 file. FFprobe confirmed AV1 video, AAC audio and 19.063583 seconds duration. The test did not use localhost URLs in the browser. The short test validates the public workflow; a 30-minute video was not downloaded as part of verification.

Implemented limits: two concurrent jobs, maximum two hours duration, maximum 1 GB file size. A 30-minute public video is within the duration limit, provided its resulting file remains below 1 GB and YouTube allows access. Selected quality is a ceiling; lower quality can reduce size. Completed files expire after one hour. Restarting the worker clears job state.

## Important operating condition

This is a working **temporary** backend, not independent permanent hosting. The owner's computer, network connection, Gunicorn process and Cloudflare tunnel process must stay running. Quick Tunnels have no uptime guarantee and generate a new hostname on restart. Vercel remains publicly hosted even if the backend stops; video downloads then fail with a connection error.

Current worker origin:
https://aspect-objectives-explosion-related.trycloudflare.com

Anyone knowing the worker URL can access the downloader. Browser CORS is restricted to the production Vercel origin, but CORS is not authentication. The worker limits job concurrency and file size; for broad public use, add authentication/rate limits and move it to persistent hosting.

## Restart after computer/process shutdown

From the project directory, run in one terminal:

```bash
WORKER_MODE=1 DOWNLOAD_DIR=work/public-downloads \
ALLOWED_ORIGINS=https://vercel-one-omega-81.vercel.app \
.venv/bin/gunicorn --bind 127.0.0.1:8001 --workers 1 --threads 8 --timeout 120 app:app
```

Run in a second terminal:

```bash
work/cloudflared tunnel --url http://127.0.0.1:8001 --no-autoupdate --protocol http2
```

Copy the new HTTPS URL printed by cloudflared, then update Vercel's `DOWNLOAD_BACKEND_URL` (production) and redeploy. Do not use localhost in the Vercel environment.

```bash
work/vercel-cli/node_modules/.bin/vercel env update DOWNLOAD_BACKEND_URL production --cwd deployment/vercel
# Paste the new tunnel URL at the prompt.
python3 deployment/build.py
work/vercel-cli/node_modules/.bin/vercel deploy --prod --yes --cwd deployment/vercel
```

`work/cloudflared` is the official Cloudflare Linux binary and the CLI is installed in `work/vercel-cli`. On another machine install the official tools, Python dependencies and FFmpeg/Node first. If Vercel login expires, use `vercel login`; never paste passwords/tokens into chat.

## Vercel-native experiment

A real synchronous Python Function with bundled Node and FFmpeg was deployed with a 60-second/3 MB video cap. Runtime dependency resolution was repaired, but the independent production test failed because YouTube returned: `Sign in to confirm you're not a bot.` No cookies, CAPTCHA solving, proxies for YouTube, DRM bypass or access restriction bypass were used. This experimental Function was removed from the active deployment. The working public app uses the full worker limits above, not the experimental one-minute cap.

For permanent availability independent of the owner's computer, provision an always-on HTTPS worker/server and replace only `DOWNLOAD_BACKEND_URL`. The Vercel frontend remains unchanged.

Sources: [Vercel Function limits](https://vercel.com/docs/functions/limitations), [Cloudflare Quick Tunnels and lifecycle](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/).
