# Ikosoft Video Download

A local YouTube video downloader with a Darija interface, real server downloads using yt-dlp, progress polling, and attachment delivery to your device.

## Run

Requires Python 3.11+, FFmpeg and Node.js 22+ (or a supported yt-dlp JavaScript runtime). FFmpeg must be on PATH. On Ubuntu install system prerequisites with `sudo apt install python3-venv ffmpeg nodejs` (verify Node version; older Ubuntu packages may need updating).

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python app.py
```

Open http://127.0.0.1:8000. Paste a public YouTube video URL, choose a maximum quality, then click the file download button once ready. The selected resolution is a ceiling; actual formats depend on YouTube. Video and audio are merged with FFmpeg. MP4 is preferred; WebM is possible when MP4 isn't available.

```bash
.venv/bin/pip install pytest
.venv/bin/python -m pytest -q
```

## Limits

Two concurrent jobs, maximum two hours / 1 GB per video. Completed files expire after one hour, checked once per minute. Restart clears local files and job records. Progress can restart for separate audio/video streams; merging has an indeterminate duration. Browser saving is a separate transfer after server preparation. Do not restart while preparing or saving a file.

Only canonical public YouTube video URLs are accepted; playlists and arbitrary websites are rejected. Private, paid, age restricted, geo restricted, DRM protected and live content are not supported. No cookies, authentication or restriction bypass is implemented. YouTube can reject requests from an IP or require sign-in; the app reports that error. Keep yt-dlp updated with `.venv/bin/pip install -U 'yt-dlp[default]'` when YouTube changes. See [yt-dlp documentation](https://github.com/yt-dlp/yt-dlp) for runtime and extractor requirements.

Use only for videos you have permission to download. This is a single-user local application: binds to loopback, uses opaque download IDs, and does not include accounts or production hardening. Do not expose the Flask development server to the internet. UI fonts use Google Fonts with system font fallbacks; downloaded media never goes to a third-party app service.

## Languages and PayPal support

Use the header's **العربية / English** buttons. Arabic uses RTL and English uses LTR; the choice is remembered in local storage. Switching languages updates active progress and error messages without interrupting the download. API errors accept `?lang=ar` or `?lang=en` and return stable `error_code` values.

The support section initially opens only https://www.paypal.com/ and explicitly says donation setup is pending. No recipient is configured and this link does not donate to the owner. To set your actual PayPal support link later, provide an HTTPS PayPal or PayPal.me URL:

```bash
PAYPAL_SUPPORT_URL='https://www.paypal.com/donate/?hosted_button_id=YOUR_BUTTON_ID' .venv/bin/python app.py
```

Replace the example with your real link before enabling donations. Unsupported domains fall back to the pending placeholder. The app never collects payment details; configured support links open PayPal in a new tab.

## Public Vercel deployment

See `deployment/DEPLOYMENT.md`. The prepared public architecture hosts the bilingual UI on Vercel and the real download worker on a persistent HTTPS Docker host. Build the frontend with `python3 deployment/build.py`. Configure `DOWNLOAD_BACKEND_URL` on Vercel and `ALLOWED_ORIGINS` on the worker. Public frontend: https://vercel-one-omega-81.vercel.app. Public downloads now use a temporary HTTPS Cloudflare tunnel to the owner’s computer. Browser download of a real video/audio MP4 was verified. The owner’s computer and tunnel/worker processes must remain running; this is not permanent independent hosting. See deployment/DEPLOYMENT.md for restart instructions and limits.
