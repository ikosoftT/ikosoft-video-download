from pathlib import Path
import pytest
import app as module

@pytest.mark.parametrize('url', ['https://youtu.be/BaW_jenozKc', 'https://www.youtube.com/watch?v=BaW_jenozKc&list=foo', 'https://youtube.com/shorts/BaW_jenozKc'])
def test_urls(url):
    assert module.normalize_url(url) == 'https://www.youtube.com/watch?v=BaW_jenozKc'

@pytest.mark.parametrize('url', ['http://youtube.com/watch?v=BaW_jenozKc','https://youtube.com.evil.org/watch?v=BaW_jenozKc','https://localhost/test','https://youtube.com/playlist?list=x','https://user@youtube.com/watch?v=BaW_jenozKc',None])
def test_invalid(url):
    with pytest.raises(ValueError): module.normalize_url(url)

def test_api():
    client=module.app.test_client()
    assert client.get('/').status_code == 200
    assert client.post('/api/downloads',json={'url':'https://evil.org'}).status_code == 400
    assert client.get('/api/downloads/missing/file').status_code == 404

def test_real_job_flow_with_mock_extractor(monkeypatch,tmp_path):
    monkeypatch.setattr(module,'ROOT',tmp_path)
    class FakeYDL:
        def __init__(self, opts): self.opts=opts
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def extract_info(self,url,download):
            self.opts['progress_hooks'][0]({'status':'downloading','downloaded_bytes':5,'total_bytes':10})
            Path(self.opts['outtmpl'].replace('%(ext)s','mp4')).write_bytes(b'video-fixture')
            return {'title':'Test video'}
    monkeypatch.setattr(module.yt_dlp,'YoutubeDL',FakeYDL)
    module.jobs['test']=dict(id='test',status='queued',created=0)
    module.download('test','https://www.youtube.com/watch?v=BaW_jenozKc','720')
    client=module.app.test_client()
    status=client.get('/api/downloads/test').json
    assert status['status']=='ready' and 'path' not in status
    response=client.get('/api/downloads/test/file')
    assert response.data == b'video-fixture'
    assert 'attachment' in response.headers['Content-Disposition']
    module.jobs.pop('test')

def test_translated_errors():
    client=module.app.test_client()
    en=client.post('/api/downloads?lang=en',json={'url':'bad'}).json
    ar=client.post('/api/downloads?lang=ar',json={'url':'bad'}).json
    assert en['error']=='Enter a valid HTTPS YouTube video URL.'
    assert ar['error']!=en['error'] and ar['error_code']==en['error_code']
    assert client.get('/api/downloads/missing?lang=en').json['error'].startswith('This download')
    assert client.post('/api/downloads?lang=en',json=['bad']).status_code==400
    module.jobs['error-test']=dict(id='error-test',status='error',error_code='restricted',created=0)
    assert 'requires sign-in' in client.get('/api/downloads/error-test?lang=en').json['error']
    assert 'YouTube طلب' in client.get('/api/downloads/error-test?lang=ar').json['error']
    module.jobs.pop('error-test')

def test_paypal_config(monkeypatch):
    client=module.app.test_client()
    monkeypatch.delenv('PAYPAL_SUPPORT_URL',raising=False)
    assert client.get('/api/config').json == {'paypal_url':'https://www.paypal.com/','paypal_configured':False}
    monkeypatch.setenv('PAYPAL_SUPPORT_URL','https://paypal.me/example')
    assert client.get('/api/config').json['paypal_configured'] is True
    monkeypatch.setenv('PAYPAL_SUPPORT_URL','https://evil.org/paypal')
    assert client.get('/api/config').json['paypal_configured'] is False

def test_worker_cors(monkeypatch):
    monkeypatch.setenv('WORKER_MODE','1')
    monkeypatch.setenv('ALLOWED_ORIGINS','https://ikosoft.example.org')
    client=module.app.test_client()
    response=client.options('/api/downloads',headers={'Origin':'https://ikosoft.example.org','Access-Control-Request-Method':'POST'})
    assert response.status_code==204
    assert response.headers['Access-Control-Allow-Origin']=='https://ikosoft.example.org'
    assert client.post('/api/downloads',headers={'Origin':'https://evil.example.org'},json={'url':'bad'}).status_code==403
