"""SS 0.9 workspace extension loaded before Uvicorn starts.

The base app remains the chat/provider engine. This module adds the read-only
file intelligence layer without replacing the user's existing chat archive.
"""
from fastapi import HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pathlib import Path
from datetime import datetime
import hashlib, mimetypes, os, re
import app as base

APP = base.APP
ROOT = base.ROOT
DATA = base.data_root()
TEXT_EXT={'.txt','.md','.csv','.json','.xml','.html','.htm','.rtf','.log','.yaml','.yml'}
IMAGE_EXT={'.jpg','.jpeg','.png','.webp','.gif','.bmp','.tif','.tiff','.heic'}

def files(root):
    p=Path(root).expanduser()
    if not p.is_dir(): raise ValueError(f'Folder does not exist: {p}')
    return (x for x in p.rglob('*') if x.is_file())

def sha256(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def meta(p, digest=False):
    s=p.stat(); ext=p.suffix.lower()
    r={'path':str(p),'name':p.name,'extension':ext,'mime':mimetypes.guess_type(p.name)[0],
       'size_bytes':s.st_size,'created_at':datetime.fromtimestamp(s.st_ctime).isoformat(),
       'modified_at':datetime.fromtimestamp(s.st_mtime).isoformat(),'is_image':ext in IMAGE_EXT}
    if digest:r['sha256']=sha256(p)
    return r

def extract(p):
    ext=p.suffix.lower()
    if ext in TEXT_EXT:return p.read_text(encoding='utf-8',errors='replace')
    if ext=='.pdf':
        if not base.PdfReader: raise ValueError('PDF extractor unavailable; install pypdf.')
        return '\n\n'.join((x.extract_text() or '') for x in base.PdfReader(str(p)).pages)
    if ext=='.docx':
        if not base.Document: raise ValueError('DOCX extractor unavailable; install python-docx.')
        d=base.Document(str(p)); out=[x.text for x in d.paragraphs]
        out += [' | '.join(c.text for c in row.cells) for t in d.tables for row in t.rows]
        return '\n'.join(out)
    if ext in ('.xlsx','.xlsm'):
        if not base.load_workbook: raise ValueError('Excel extractor unavailable; install openpyxl.')
        wb=base.load_workbook(str(p),read_only=True,data_only=True);out=[]
        for ws in wb.worksheets:
            out.append(f'## SHEET: {ws.title}')
            out += [' | '.join('' if v is None else str(v) for v in row) for row in ws.iter_rows(values_only=True)]
        return '\n'.join(out)
    raise ValueError(f'No safe text extractor for {ext}; nothing was changed.')

@APP.get('/workspace',response_class=HTMLResponse)
async def workspace_page(): return HTMLResponse((ROOT/'web'/'workspace.html').read_text(encoding='utf-8'))

@APP.post('/api/workspace/scan')
async def scan(body:dict):
    try:
        root=Path(body.get('folder','')).expanduser(); limit=min(int(body.get('limit',5000)),20000)
        rows=[]; total=0
        for i,p in enumerate(files(root)):
            if i>=limit:break
            try:
                r=meta(p,bool(body.get('with_hash'))); rows.append(r); total+=r['size_bytes']
            except (OSError,PermissionError): pass
        return {'ok':True,'folder':str(root),'files':rows,'count':len(rows),'total_bytes':total,'truncated':len(rows)>=limit,'read_only':True}
    except Exception as e:return JSONResponse({'ok':False,'error':str(e)},400)

@APP.post('/api/workspace/extract')
async def extract_file(body:dict):
    try:
        p=Path(body.get('path','')).expanduser(); text=extract(p); limit=min(int(body.get('max_chars',200000)),500000)
        return {'ok':True,'metadata':meta(p),'text':text[:limit],'characters':len(text),'truncated':len(text)>limit,'read_only':True}
    except Exception as e:return JSONResponse({'ok':False,'error':str(e)},400)

@APP.post('/api/workspace/context')
async def context(body:dict):
    budget=min(int(body.get('max_chars',120000)),500000); used=0; parts=[]; errors=[]
    for raw in body.get('paths',[]):
        if used>=budget:break
        try:
            p=Path(raw).expanduser(); text=extract(p); take=min(len(text),budget-used)
            parts.append(f'===== SOURCE: {p} =====\n{text[:take]}'); used+=take
        except Exception as e: errors.append({'path':raw,'error':str(e)})
    return {'ok':True,'sources':len(parts),'characters':used,'context':'\n\n'.join(parts),'errors':errors,'read_only':True}

@APP.post('/api/workspace/duplicates')
async def duplicates(body:dict):
    try:
        root=Path(body.get('folder','')).expanduser(); groups={}; count=0
        for p in files(root):
            if p.suffix.lower() not in IMAGE_EXT:continue
            try:
                r=meta(p,True);groups.setdefault(r['sha256'],[]).append(r);count+=1
            except (OSError,PermissionError):pass
        proposals=[]
        for g in groups.values():
            if len(g)<2:continue
            keep=min(g,key=lambda x:(x['created_at'],x['path'].lower()))
            dup=[x for x in g if x['path']!=keep['path']]
            proposals.append({'keep':keep,'duplicates':dup,'recoverable_bytes':sum(x['size_bytes'] for x in dup),
                              'reason':'Exact SHA-256 duplicate. Oldest creation timestamp proposed as canonical. No deletion performed.'})
        return {'ok':True,'folder':str(root),'images_scanned':count,'duplicate_groups':proposals,
                'group_count':len(proposals),'recoverable_bytes':sum(x['recoverable_bytes'] for x in proposals),
                'actions_performed':[],'read_only':True}
    except Exception as e:return JSONResponse({'ok':False,'error':str(e)},400)

@APP.get('/api/workspace/policy')
async def workspace_policy():
    return {'read_only_default':True,'delete_enabled':False,'move_enabled':False,'rename_enabled':False,
            'preserve_original_metadata':True,'preserve_originals':True,
            'description':'SS analyses files and proposes actions. It does not delete, rename, move or overwrite files.'}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(APP,host='127.0.0.1',port=8765)
