from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pathlib import Path
import urllib.request, json
APP=FastAPI(title='SS Provider Console',version='0.8.5')
ROOT=Path(__file__).parent
@APP.get('/',response_class=HTMLResponse)
def home(): return HTMLResponse((ROOT/'index.html').read_text(encoding='utf-8'))
@APP.get('/health')
def health():
 try:
  with urllib.request.urlopen('http://127.0.0.1:8765/system',timeout=3) as r:return {'ok':True,'brain':json.loads(r.read())}
 except Exception as e:return {'ok':False,'brain':'offline','error':str(e)}
