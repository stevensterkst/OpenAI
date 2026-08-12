from fastapi import APIRouter
from fastapi.responses import HTMLResponse, JSONResponse
from pathlib import Path
from datetime import datetime
import hashlib, json, mimetypes, re, subprocess, shutil, zipfile

router = APIRouter()
IMG_EXT={'.jpg','.jpeg','.png','.webp','.gif','.bmp','.tif','.tiff','.heic'}
TEXT_EXT={'.txt','.md','.csv','.json','.xml','.html','.htm','.log','.yaml','.yml','.rtf'}
DOC_EXT=TEXT_EXT|{'.docx','.xlsx','.xlsm','.pdf'}

def meta(p, hash_file=False):
    s=p.stat(); out={'path':str(p),'name':p.name,'extension':p.suffix.lower(),'size_bytes':s.st_size,'mime':mimetypes.guess_type(p.name)[0],'created_at':datetime.fromtimestamp(s.st_ctime).isoformat(),'modified_at':datetime.fromtimestamp(s.st_mtime).isoformat()}
    if hash_file:
        h=hashlib.sha256()
        with p.open('rb') as f:
            for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
        out['sha256']=h.hexdigest()
    return out

def files(root):
    return (p for p in Path(root).expanduser().rglob('*') if p.is_file())

def extract(p):
    e=p.suffix.lower()
    if e in TEXT_EXT: return p.read_text(encoding='utf-8',errors='replace')
    if e=='.docx':
        with zipfile.ZipFile(p) as z:
            raw=z.read('word/document.xml').decode('utf-8','replace')
        return re.sub(r'<[^>]+>',' ',raw).replace('&amp;','&').replace('&lt;','<').replace('&gt;','>')
    if e in {'.xlsx','.xlsm'}:
        with zipfile.ZipFile(p) as z:
            names=z.namelist(); strings=[]
            if 'xl/sharedStrings.xml' in names:
                raw=z.read('xl/sharedStrings.xml').decode('utf-8','replace'); strings=re.findall(r'<t[^>]*>(.*?)</t>',raw)
            parts=[]
            for n in names:
                if n.startswith('xl/worksheets/sheet') and n.endswith('.xml'):
                    raw=z.read(n).decode('utf-8','replace'); vals=re.findall(r'<v>(.*?)</v>',raw); parts.extend(vals)
            return '\n'.join(strings+parts)
    if e=='.pdf':
        exe=shutil.which('pdftotext')
        if exe:
            r=subprocess.run([exe,'-','-'],input=p.read_bytes(),stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
            if r.returncode==0:return r.stdout.decode('utf-8','replace')
        raise RuntimeError('PDF extraction unavailable: install an approved PDF extractor later; no file was changed.')
    raise RuntimeError('No read-only extractor available for '+e)

@router.get('/workspace',response_class=HTMLResponse)
async def workspace():
    return HTMLResponse('''<!doctype html><html><head><meta charset="utf-8"><title>SS Workspace v0.8.4</title><style>body{font:14px Segoe UI;background:#071018;color:#eaf2f6;margin:0;padding:22px}main{max-width:1200px;margin:auto}.box{background:#0a1621;border:1px solid #294050;border-radius:10px;padding:14px;margin:10px 0}.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}input,button{background:#08131d;color:#fff;border:1px solid #34505f;border-radius:6px;padding:9px}input{width:100%;box-sizing:border-box}button{cursor:pointer}.row{padding:7px;border-bottom:1px solid #243844}.small{font-size:11px;color:#91a7b5}.ok{color:#55d8ca}.bad{color:#ff8b8b}pre{white-space:pre-wrap;max-height:420px;overflow:auto;background:#061019;padding:10px}@media(max-width:800px){.grid{display:block}}</style></head><body><main><div class=box><b>SS SECOND BRAIN · FILE / LEGAL WORKSPACE · v0.8.4</b><p class=small>READ-ONLY: scan, extract, compare and prepare source context. No delete, rename, move or overwrite operation exists here.</p><input id=f placeholder="C:\\Users\\...\\Documents\\Case"><p><button onclick=scan()>SCAN DOCUMENTS</button> <button onclick=dups()>ANALYSE EXACT PHOTO DUPLICATES</button></p><div id=s class=small></div></div><div class=grid><section class=box><b>DOCUMENTS</b><div id=files></div></section><section class=box><b>DUPLICATE PHOTOS</b><div id=d></div></section><section class="box" style="grid-column:1/-1"><b>SELECTED SOURCE / EXTRACTED TEXT</b><div id=x class=small>Select a document above.</div></section></div></main><script>let rows=[];const $=x=>document.getElementById(x),esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));async function scan(){let folder=$('f').value.trim();if(!folder)return;$('s').textContent='Scanning read-only…';let r=await fetch('/api/workspace/scan',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({folder,limit:20000})});let j=await r.json();if(!j.ok){$('s').innerHTML='<span class=bad>'+esc(j.error)+'</span>';return}rows=j.files.filter(x=>['.pdf','.docx','.xlsx','.xlsm','.txt','.md','.csv','.json','.rtf'].includes(x.extension));$('s').innerHTML='<span class=ok>'+j.count+' files scanned; '+j.total_bytes.toLocaleString()+' bytes. Nothing changed.</span>';$('files').innerHTML=rows.map((x,i)=>'<div class=row><button onclick="extract('+i+')">EXTRACT</button> <b>'+esc(x.name)+'</b><br><span class=small>'+esc(x.extension)+' · '+x.size_bytes.toLocaleString()+' bytes · created '+esc(x.created_at)+'</span></div>').join('')||'<span class=small>No supported documents.</span>'}async function extract(i){let r=await fetch('/api/workspace/extract',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({path:rows[i].path,max_chars:150000})});let j=await r.json();$('x').innerHTML=j.ok?'<pre>'+esc(j.text)+'</pre>':'<span class=bad>'+esc(j.error)+'</span>'}async function dups(){let folder=$('f').value.trim();if(!folder)return;$('d').textContent='Hashing photos read-only…';let r=await fetch('/api/workspace/duplicates',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({folder})});let j=await r.json();if(!j.ok){$('d').innerHTML='<span class=bad>'+esc(j.error)+'</span>';return}$('d').innerHTML='<span class=ok>'+j.images_scanned+' images · '+j.group_count+' exact duplicate groups · '+j.recoverable_bytes.toLocaleString()+' bytes potentially recoverable</span>'+j.groups.map(g=>'<div class=row><b>KEEP</b> '+esc(g.keep.path)+'<br><span class=small>'+g.duplicates.map(x=>esc(x.path)).join('<br>')+'</span></div>').join('')||'<p class=small>No exact duplicates found.</p>'}</script></body></html>''')

@router.post('/api/workspace/scan')
async def scan(body:dict):
    root=Path(body.get('folder','')).expanduser()
    if not root.is_dir(): return JSONResponse({'ok':False,'error':f'Folder does not exist: {root}'},400)
    limit=min(int(body.get('limit',20000)),50000); rows=[]; total=0
    for i,p in enumerate(files(root)):
        if i>=limit: break
        try:
            m=meta(p,bool(body.get('with_hash')));rows.append(m);total+=m['size_bytes']
        except OSError: pass
    return {'ok':True,'files':rows,'count':len(rows),'total_bytes':total,'read_only':True,'actions_performed':[]}

@router.post('/api/workspace/extract')
async def extract_route(body:dict):
    p=Path(body.get('path','')).expanduser()
    if not p.is_file(): return JSONResponse({'ok':False,'error':'File does not exist'},400)
    try:
        text=extract(p);lim=min(int(body.get('max_chars',150000)),500000)
        return {'ok':True,'metadata':meta(p),'text':text[:lim],'truncated':len(text)>lim,'read_only':True}
    except Exception as e: return JSONResponse({'ok':False,'error':str(e),'read_only':True},400)

@router.post('/api/workspace/duplicates')
async def duplicates(body:dict):
    root=Path(body.get('folder','')).expanduser()
    if not root.is_dir(): return JSONResponse({'ok':False,'error':'Folder does not exist'},400)
    groups={};scanned=0
    for p in files(root):
        if p.suffix.lower() not in IMG_EXT: continue
        try:
            m=meta(p,True);groups.setdefault(m['sha256'],[]).append(m);scanned+=1
        except OSError: pass
    out=[];recover=0
    for g in groups.values():
        if len(g)>1:
            g.sort(key=lambda x:(x['created_at'],x['path'].lower()));dups=g[1:];bytes_=sum(x['size_bytes'] for x in dups);recover+=bytes_;out.append({'keep':g[0],'duplicates':dups,'recoverable_bytes':bytes_,'reason':'Exact SHA-256 duplicate. Oldest creation timestamp proposed as canonical. No action performed.'})
    return {'ok':True,'images_scanned':scanned,'group_count':len(out),'recoverable_bytes':recover,'groups':out,'read_only':True,'actions_performed':[]}

@router.post('/api/workspace/context')
async def context(body:dict):
    paths=[Path(x).expanduser() for x in body.get('paths',[])]; parts=[];total=0;lim=min(int(body.get('max_chars',90000)),250000)
    for p in paths:
        if not p.is_file(): continue
        try:
            t=extract(p); piece=f'\n\n===== SOURCE: {p.name} | {p} =====\n{t}\n';parts.append(piece);total+=len(piece)
            if total>=lim:break
        except Exception as e: parts.append(f'\n===== SOURCE: {p.name} | EXTRACTION ERROR: {e} =====\n')
    return {'ok':True,'context':''.join(parts)[:lim],'sources':[str(p) for p in paths],'read_only':True}
