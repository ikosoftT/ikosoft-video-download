import os, re, time, uuid, threading, shutil
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, jsonify, send_file
import yt_dlp

app = Flask(__name__, static_folder='static', static_url_path='')
app.config['MAX_CONTENT_LENGTH'] = 4096
ROOT = Path(os.getenv('DOWNLOAD_DIR', str(Path(__file__).parent / 'work' / 'downloads')))
ROOT.mkdir(parents=True, exist_ok=True)
jobs = {}
lock = threading.RLock()
pool = ThreadPoolExecutor(max_workers=2)
TTL = 3600
MAX_BYTES = 1024 * 1024 * 1024


ERRORS = {
    'invalid_url': ('دخل رابط HTTPS صحيح ديال فيديو YouTube.', 'Enter a valid HTTPS YouTube video URL.'),
    'quality': ('اختار جودة صحيحة.', 'Choose a valid video quality.'),
    'busy': ('كاينين جوج تحميلات خدامين. تسنى شوية وعاود جرّب.', 'Two downloads are running. Please wait and try again.'),
    'expired': ('التحميل تسالا الوقت ديالو. عاود حضّرو.', 'This download has expired. Prepare it again.'),
    'not_ready': ('الملف باقي ما واجدش أو تسالا الوقت ديالو.', 'The file is not ready or has expired.'),
    'restricted': ('YouTube طلب تسجيل الدخول أو قيّد الوصول لهاد الفيديو. جرّب فيديو عمومي آخر.', 'YouTube requires sign-in or restricts access to this video. Try another public video.'),
    'unavailable': ('هاد الفيديو ما متاحش، تحيد أو محظور فالمنطقة.', 'This video is unavailable, removed, or blocked in your region.'),
    'network': ('تعذر الاتصال بـ YouTube. تأكد من الإنترنت وعاود جرّب.', 'Could not connect to YouTube. Check your internet connection and try again.'),
    'size': ('الفيديو كبر من الحد المسموح: 1 GB.', 'The video exceeds the 1 GB limit.'),
    'duration': ('الفيديو فات ساعتين، الحد المسموح.', 'Videos longer than two hours are not supported.'),
    'live': ('البث المباشر ما مدعومش.', 'Live streams are not supported.'),
    'download': ('تعذر تحميل الفيديو. جرّب فيديو عمومي آخر أو حدّث yt-dlp.', 'Could not download this video. Try another public video or update yt-dlp.'),
    'request': ('الطلب ما صحيحش. عاود جرّب.', 'Invalid request. Please try again.'),
}

def error_text(code):
    return ERRORS.get(code, ERRORS['download'])[1 if request.args.get('lang') == 'en' else 0]

def error_response(code, status):
    return jsonify(error=error_text(code), error_code=code), status

@app.errorhandler(413)
def too_large(error):
    return error_response('request', 413)

def normalize_url(value):
    if not isinstance(value, str) or len(value) > 2048:
        raise ValueError('دخل رابط YouTube صحيح.')
    parsed = urlparse(value.strip())
    if parsed.scheme != 'https' or parsed.username or parsed.password or parsed.port:
        raise ValueError('خاص الرابط يبدا بـ https:// ويكون ديال YouTube.')
    host = (parsed.hostname or '').lower()
    parts = parsed.path.strip('/').split('/')
    if host == 'youtu.be':
        video = parts[0]
    elif host in ('youtube.com', 'www.youtube.com', 'm.youtube.com'):
        video = parse_qs(parsed.query).get('v', [''])[0] if parsed.path == '/watch' else (parts[1] if len(parts) == 2 and parts[0] in ('shorts', 'embed', 'live') else '')
    else:
        video = ''
    if not re.fullmatch(r'[A-Za-z0-9_-]{11}', video):
        raise ValueError('دخل رابط فيديو واحد من YouTube، ماشي playlist.')
    return 'https://www.youtube.com/watch?v=' + video

def update(key, **values):
    with lock:
        jobs[key].update(values)

def public(job):
    result = {k: v for k, v in job.items() if k not in ('path', 'created')}
    if result.get('error_code'):
        result['error'] = error_text(result['error_code'])
    return result

def download(key, url, quality):
    directory = ROOT / key
    directory.mkdir(exist_ok=True)
    def progress(data):
        if data['status'] == 'downloading':
            total = data.get('total_bytes') or data.get('total_bytes_estimate')
            done = data.get('downloaded_bytes', 0)
            if done > MAX_BYTES or sum(p.stat().st_size for p in directory.iterdir() if p.is_file()) > MAX_BYTES:
                raise ValueError('الفيديو كبر من الحد المسموح: 1 GB.')
            update(key, status='downloading', progress=round(min(99, done / total * 100), 1) if total else None, speed=data.get('speed'), eta=data.get('eta'))
        elif data['status'] == 'finished':
            update(key, status='processing', progress=99)
    def check(info, *, incomplete):
        if info.get('is_live') or info.get('live_status') == 'is_live':
            raise ValueError('Live streams are not supported.')
        if info.get('duration', 0) > 7200:
            raise ValueError('Videos longer than two hours are not supported.')
        if info.get('filesize', 0) > MAX_BYTES:
            raise ValueError('Video exceeds the 1 GB limit.')
    try:
        update(key, status='fetching')
        options = {'format': f'bv*[height<={quality}][ext=mp4]+ba[ext=m4a]/b[height<={quality}][ext=mp4]/b[height<={quality}]', 'outtmpl': str(directory / 'video.%(ext)s'), 'merge_output_format': 'mp4', 'noplaylist': True, 'quiet': True, 'no_warnings': True, 'progress_hooks': [progress], 'socket_timeout': 20, 'retries': 2, 'fragment_retries': 2, 'max_filesize': MAX_BYTES, 'match_filter': check, 'js_runtimes': {'node': {}}, 'cachedir': False}
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)
        files = [p for p in directory.iterdir() if p.suffix in ('.mp4', '.webm', '.mkv') and '.f' not in p.stem]
        if not files:
            raise ValueError('الفيديو ما توفرش للتحميل، أو فات الحد المسموح.')
        file = max(files, key=lambda p: p.stat().st_size)
        if file.stat().st_size > MAX_BYTES:
            raise ValueError('الفيديو كبر من الحد المسموح: 1 GB.')
        title = info.get('title', 'YouTube video')
        filename = re.sub(r'[^\w .-]', '', title, flags=re.UNICODE).strip()[:120] or 'video'
        update(key, status='ready', progress=100, title=title, filename=filename + file.suffix, size=file.stat().st_size, path=str(file), created=time.time())
    except Exception as error:
        message = re.sub(r'\x1b\[[0-9;]*m', '', str(error))
        lowered = message.lower()
        if any(s in lowered for s in ('sign in', 'private', 'members', 'age-restricted', 'bot')):
            code = 'restricted'
        elif 'unavailable' in lowered:
            code = 'unavailable'
        elif 'timed out' in lowered or 'network' in lowered or 'connection' in lowered:
            code = 'network'
        elif '1 gb' in lowered:
            code = 'size'
        elif 'two hours' in lowered:
            code = 'duration'
        elif 'live streams' in lowered:
            code = 'live'
        else:
            code = 'download'
        app.logger.warning('Download failed: %s', message[:500])
        update(key, status='error', error_code=code, created=time.time())
        shutil.rmtree(directory, ignore_errors=True)

def cleanup():
    while True:
        time.sleep(60)
        with lock:
            expired = [k for k, v in jobs.items() if time.time() - v['created'] > TTL and v['status'] in ('ready', 'error')]
            for k in expired:
                jobs.pop(k)
                shutil.rmtree(ROOT / k, ignore_errors=True)


@app.before_request
def allow_worker_origin():
    if not os.getenv('WORKER_MODE') or not request.path.startswith('/api/'):
        return None
    allowed = {origin.strip() for origin in os.getenv('ALLOWED_ORIGINS', '').split(',') if origin.strip()}
    origin = request.headers.get('Origin')
    if origin and origin not in allowed:
        return error_response('request', 403)
    if request.method == 'OPTIONS':
        return '', 204

@app.after_request
def worker_headers(response):
    allowed = {origin.strip() for origin in os.getenv('ALLOWED_ORIGINS', '').split(',') if origin.strip()}
    origin = request.headers.get('Origin')
    if os.getenv('WORKER_MODE') and origin in allowed:
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        response.vary.add('Origin')
    if request.path.startswith('/api/'):
        response.headers['Cache-Control'] = 'no-store'
    return response

@app.get('/')
def index():
    return app.send_static_file('index.html')

@app.post('/api/downloads')
def create():
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return error_response('request', 400)
    try:
        url = normalize_url(data.get('url'))
    except (ValueError, TypeError):
        return error_response('invalid_url', 400)
    quality = str(data.get('quality', '720'))
    if quality not in ('360', '720', '1080'):
        return error_response('quality', 400)
    with lock:
        if sum(j['status'] not in ('ready', 'error') for j in jobs.values()) >= 2:
            return error_response('busy', 429)
        key = uuid.uuid4().hex
        jobs[key] = dict(id=key, status='queued', progress=0, created=time.time())
    pool.submit(download, key, url, quality)
    return jsonify(id=key), 202

@app.get('/api/downloads/<key>')
def status(key):
    with lock:
        job = jobs.get(key)
        return (jsonify(public(job)), 200) if job else error_response('expired', 404)

@app.get('/api/downloads/<key>/file')
def file(key):
    with lock:
        job = jobs.get(key)
        if not job or job['status'] != 'ready':
            return error_response('not_ready', 404)
        return send_file(job['path'], as_attachment=True, download_name=job['filename'], conditional=True)

@app.get('/api/config')
def config():
    configured = os.getenv('PAYPAL_SUPPORT_URL', '').strip()
    parsed = urlparse(configured)
    valid = parsed.scheme == 'https' and parsed.hostname in ('paypal.com', 'www.paypal.com', 'paypal.me', 'www.paypal.me') and not parsed.username and not parsed.password and not parsed.port
    return jsonify(paypal_url=configured if valid else 'https://www.paypal.com/', paypal_configured=bool(valid and configured.rstrip('/') != 'https://www.paypal.com'))

@app.get('/api/health')
def health():
    return jsonify(ok=True, ffmpeg=bool(shutil.which('ffmpeg')), javascript=bool(shutil.which('node')))

def start_worker():
    for old in ROOT.iterdir():
        if old.is_dir(): shutil.rmtree(old, ignore_errors=True)
    threading.Thread(target=cleanup, daemon=True).start()

if os.getenv('WORKER_MODE'):
    start_worker()

if __name__ == '__main__':
    if not os.getenv('WORKER_MODE'): start_worker()
    app.run(host='127.0.0.1', port=int(os.getenv('PORT', '8000')), threaded=True)
