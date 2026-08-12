"""SS Second Brain v0.8.5: minimal-dependency, local-first, permission-gated brain.
No file mutation. No chat deletion. Cloud spending requires explicit approval.
"""
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, mimetypes, os, re, subprocess, sys, time, urllib.request, urllib.error

VERSION="0.8.5"
ROOT=Path(__file__).parent
APP=FastAPI(title="SS Second Brain",version=VERSION)
DATA=Path(os.environ.get("LOCALAPPDATA",str(Path.home()))) / "SS" / "data"
for d in (DATA/"chats",DATA/"memory",DATA/"indexes",DATA/"backups"): d.mkdir(parents=True,exist_ok=True)

PROVIDERS={
 "ollama":{"name":"Ollama","kind":"local","base":"http://127.0.0.1:11434","key":False},
 "jan":{"name":"Jan","kind":"local","base":"http://127.0.0.1:1337/v1","key":False},
 "lmstudio":{"name":"LM Studio","kind":"local","base":"http://127.0.0.1:1234/v1","key":False},
 "openrouter":{"name":"OpenRouter","kind":"cloud","base":"https://openrouter.ai/api/v1","key":True},
 "huggingface":{"name":"Hugging Face","kind":"cloud","base":"https://router.huggingface.co/v1","key":True},
 "venice":{"name":"Venice AI","kind":"cloud","base":"https://api.venice.ai/api/v1","key":True},
 "openai":{"name":"OpenAI","kind":"cloud","base":"https://api.openai.com/v1","key":True},
 "google":{"name":"Google Gemini","kind":"cloud","base":"https://generativelanguage.googleapis.com/v1beta/openai","key":True},
 "xai":{"name":"xAI / Grok","kind":"cloud","base":"https://api.x.ai/v1","key":True},
 "deepseek":{"name":"DeepSeek","kind":"cloud","base":"https://api.deepseek.com/v1","key":True},
 "mistral":{"name":"Mistral","kind":"cloud","base":"https://api.mistral.ai/v1","key":True},
 "moonshot":{"name":"Kimi / Moonshot","kind":"cloud","base":"https://api.moonshot.ai/v1","key":True},
 "zai":{"name":"Z.ai / GLM","kind":"cloud","base":"https://api.z.ai/api/paas/v4","key":True},
 "qwen":{"name":"Qwen / Alibaba","kind":"cloud","base":"https://dashscope-us.aliyuncs.com/compatible-mode/v1","key":True},
 "perplexity":{"name":"Perplexity","kind":"cloud","base":"https://api.perplexity.ai/v1","key":True},
}
CONNECTORS={
 "brave":{"name":"Brave Search","kind":"search","url":"https://api.search.brave.com/res/v1/web/search","key":True},
 "duckduckgo":{"name":"DuckDuckGo","kind":"web","url":"https://duckduckgo.com","key":False},
 "tor":{"name":"Tor","kind":"privacy","url":"https://www.torproject.org/","key":False},
 "huggingchat":{"name":"HuggingChat","kind":"web","url":"https://huggingface.co/chat/","key":False},
 "metaai":{"name":"Meta AI","kind":"web","url":"https://www.meta.ai/","key":False},
 "higgsfield":{"name":"Higgsfield","kind":"web","url":"https://higgsfield.ai/","key":False},
}
FREE_HINTS={"gemma3:1b","llama3.2:1b","qwen3:1.7b","qwen3:4b","phi4-mini:3.8b"}

def now(): return datetime.now(timezone.utc).isoformat()
def safe(s): return re.sub(r"[^A-Za-z0-9._-]+","_",str(s or "chat"))[:120] or "chat"
def atomic(p,obj):
 p.parent.mkdir(parents=True,exist_ok=True); t=p.with_suffix(p.suffix+".tmp"); t.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding="utf-8"); os.replace(t,p)
def save_chat(c):
 c=dict(c); c.setdefault("created_at",now()); c["updated_at"]=now(); atomic(DATA/"chats"/(safe(c.get("id"))+".json"),c); return str(DATA/"chats"/(safe(c.get("id"))+".json"))
def list_chats():
 out=[]
 for p in sorted((DATA/"chats").glob("*.json"),key=lambda x:x.stat().st_mtime,reverse=True):
  try:
   c=json.loads(p.read_text(encoding="utf-8")); out.append({"id":c.get("id",p.stem),"title":c.get("title","Chat"),"updated_at":c.get("updated_at"),"provider":c.get("provider"),"model":c.get("model"),"messages":len(c.get("messages",[]))})
  except Exception: pass
 return out

def http_json(url,method="GET",payload=None,headers=None,timeout=120):
 data=None
 if payload is not None: data=json.dumps(payload).encode()
 h={"Accept":"application/json"}; h.update(headers or {})
 if payload is not None:h["Content-Type"]="application/json"
 req=urllib.request.Request(url,data=data,headers=h,method=method)
 with urllib.request.urlopen(req,timeout=timeout) as r:return json.loads(r.read().decode("utf-8",errors="replace"))

def mem_gb():
 try:
  import psutil; return psutil.virtual_memory().available/2**30
 except Exception:
  return 0.0

def local_candidates():
 f=mem_gb()
 if f>=7:return ["qwen3:4b","phi4-mini:3.8b","qwen3:1.7b","gemma3:1b","llama3.2:1b"]
 if f>=4:return ["phi4-mini:3.8b","qwen3:1.7b","gemma3:1b","llama3.2:1b"]
 if f>=2:return ["qwen3:1.7b","gemma3:1b","llama3.2:1b"]
 return ["gemma3:1b","llama3.2:1b"]

def boundary(name,e):
 s=str(e); low=s.lower()
 if "urlopen error" in low or "connection refused" in low:return f"{name} is unreachable; SS stopped at that boundary."
 if "401" in s or "403" in s:return f"{name} rejected the credential or permission."
 if "429" in s:return f"{name} rate-limited the request."
 return f"{name}: {s}"

def extract_text(p):
 ext=p.suffix.lower()
 if ext in {".txt",".md",".csv",".json",".xml",".html",".htm",".log",".yaml",".yml",".rtf"}:return p.read_text(encoding="utf-8",errors="replace")
 if ext==".pdf":
  try:
   from pypdf import PdfReader
   return "\n\n".join(x.extract_text() or "" for x in PdfReader(str(p)).pages)
  except Exception as e: raise RuntimeError("PDF extraction is an optional module; SS core remains operational. "+str(e))
 if ext==".docx":
  try:
   from docx import Document
   d=Document(str(p)); return "\n".join(x.text for x in d.paragraphs)
  except Exception as e: raise RuntimeError("DOCX extraction is an optional module; install it only when needed. "+str(e))
 raise ValueError(f"No extractor installed for {ext}")

def file_meta(p,hash_it=False):
 s=p.stat(); r={"path":str(p),"name":p.name,"size_bytes":s.st_size,"extension":p.suffix.lower(),"mime":mimetypes.guess_type(p.name)[0],"created_at":datetime.fromtimestamp(s.st_ctime).isoformat(),"modified_at":datetime.fromtimestamp(s.st_mtime).isoformat()}
 if hash_it:
  h=hashlib.sha256()
  with open(p,"rb") as f:
   for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
  r["sha256"]=h.hexdigest()
 return r

def iter_files(root): return (p for p in Path(root).expanduser().rglob("*") if p.is_file())

def relevance(query,text):
 words=[w.lower() for w in re.findall(r"[\w]{4,}",query)]; low=text.lower(); score=sum(low.count(w) for w in words); return score

def task_profile(task):
 t=task.lower(); legal=any(x in t for x in ("legal","law","contract","court","procedure","evidence","claim","case","agreement","judge","deadline")); deep=legal or any(x in t for x in ("analyse","analyze","compare","contradiction","strategy","research","draft")); return {"domain":"legal" if legal else "general","depth":"deep" if deep else "normal","needs_sources":legal or "source" in t}

@APP.get("/",response_class=HTMLResponse)
async def home(): return HTMLResponse((ROOT/"web"/"brain.html").read_text(encoding="utf-8"))
@APP.get("/console",response_class=HTMLResponse)
async def console(): return HTMLResponse((ROOT/"web"/"brain.html").read_text(encoding="utf-8"))
@APP.get("/workspace",response_class=HTMLResponse)
async def workspace(): return HTMLResponse((ROOT/"web"/"brain.html").read_text(encoding="utf-8"))
@APP.get("/system")
async def system(): return {"service":"SS Second Brain","version":VERSION,"status":"online","port":8765,"storage":str(DATA),"policy":{"auto_delete_chats":False,"file_mutation":False,"cloud_spend_without_approval":False},"ram_available_gb":round(mem_gb(),2)}
@APP.get("/api/providers")
async def providers(): return {"providers":PROVIDERS,"connectors":CONNECTORS,"free_models":sorted(FREE_HINTS,key=str.lower),"version":VERSION}
@APP.get("/api/resources")
async def resources(): return {"ram_available_gb":round(mem_gb(),2),"python":sys.version.split()[0]}
@APP.get("/api/chats")
async def chat_list(): return {"chats":list_chats(),"never_delete":True}
@APP.get("/api/chats/{cid}")
async def chat_get(cid):
 p=DATA/"chats"/(safe(cid)+".json")
 if not p.exists():return JSONResponse({"ok":False,"error":"Chat not found"},404)
 return json.loads(p.read_text(encoding="utf-8"))
@APP.post("/api/chats")
async def chat_save(body:dict):
 if not body.get("id") or not isinstance(body.get("messages"),list):return JSONResponse({"ok":False,"error":"id and messages required"},400)
 return {"ok":True,"path":save_chat(body),"never_delete":True}
@APP.get("/api/models/{pid}")
async def model_get(pid):
 p=PROVIDERS.get(pid)
 if not p:return JSONResponse({"ok":False,"error":"Unknown provider"},400)
 try:
  if pid=="ollama":
   d=http_json(p["base"]+"/api/tags"); ms=[{"id":m.get("name"),"free":True} for m in d.get("models",[])]
  else:return {"ok":True,"models":[],"message":"Enter credentials to query this provider."}
  ms=sorted(ms,key=lambda x:x["id"].lower()); return {"ok":True,"models":ms,"free":ms}
 except Exception as e:return JSONResponse({"ok":False,"error":boundary(p["name"],e)},502)
@APP.post("/api/chat")
async def chat(body:dict):
 pid=body.get("provider","ollama"); p=PROVIDERS.get(pid)
 if not p:return JSONResponse({"ok":False,"error":"Unknown provider"},400)
 if p["kind"]=="cloud" and not body.get("cloud_approved"):return JSONResponse({"ok":False,"error":"Cloud use requires explicit approval for this turn."},403)
 model=body.get("model"); messages=body.get("messages") or []
 if not model:return JSONResponse({"ok":False,"error":"Model required"},400)
 try:
  start=time.perf_counter()
  if pid=="ollama":
   d=http_json(p["base"]+"/api/chat","POST",{"model":model,"messages":messages,"stream":False,"options":{"temperature":body.get("temperature",0.6)}}); text=(d.get("message") or {}).get("content","")
  else:
   key=body.get("apiKey")
   if not key:return JSONResponse({"ok":False,"error":f"{p['name']} API key not configured yet."},400)
   h={"Authorization":"Bearer "+key}; d=http_json(p["base"]+"/chat/completions","POST",{"model":model,"messages":messages,"temperature":body.get("temperature",0.5)},h); text=((d.get("choices") or [{}])[0].get("message") or {}).get("content","")
  result={"ok":True,"text":text,"provider":pid,"model":model,"latency_ms":round((time.perf_counter()-start)*1000)}
  cid=body.get("chat_id")
  if cid:save_chat({"id":cid,"title":body.get("title") or "SS chat","provider":pid,"model":model,"messages":messages+[{"role":"assistant","content":text}]})
  return result
 except Exception as e:return JSONResponse({"ok":False,"error":boundary(p["name"],e)},502)
@APP.post("/api/auto-chat")
async def auto_chat(body:dict):
 task=(body.get("task") or "").strip()
 if not task:return JSONResponse({"ok":False,"error":"Task required"},400)
 profile=task_profile(task); d=await model_get("ollama")
 if not d.get("ok") or not d.get("models"):return JSONResponse({"ok":False,"error":"No local Ollama model is reachable. Start Ollama; cloud providers remain optional."},502)
 available={x["id"] for x in d["models"]}; chosen=next((m for m in local_candidates() if m in available),d["models"][0]["id"])
 system_prompt=("You are SS, a rigorous second-brain assistant. "
  "Never invent facts. Distinguish source facts, inference and uncertainty. "
  "For legal work, preserve exact dates, names, quotations and provenance; identify contradictions and missing evidence; never silently alter source material. "
  "For file operations, propose actions first and wait for explicit permission. "
  f"Task profile: {profile}.")
 msgs=[{"role":"system","content":system_prompt},{"role":"user","content":task}]
 return await chat({"provider":"ollama","model":chosen,"messages":msgs,"chat_id":body.get("chat_id"),"title":task[:80]})
@APP.post("/api/files/scan")
async def file_scan(body:dict):
 root=Path(body.get("folder","")).expanduser()
 if not root.is_dir():return JSONResponse({"ok":False,"error":f"Folder does not exist: {root}"},400)
 limit=min(int(body.get("limit",10000)),50000); rows=[]
 for i,p in enumerate(iter_files(root)):
  if i>=limit:break
  try:rows.append(file_meta(p,bool(body.get("hash"))))
  except OSError:pass
 return {"ok":True,"files":rows,"count":len(rows),"truncated":len(rows)>=limit,"read_only":True}
@APP.post("/api/files/extract")
async def file_extract(body:dict):
 p=Path(body.get("path","")).expanduser()
 try:
  text=extract_text(p); lim=min(int(body.get("max_chars",250000)),1000000); return {"ok":True,"metadata":file_meta(p),"text":text[:lim],"truncated":len(text)>lim,"read_only":True}
 except Exception as e:return JSONResponse({"ok":False,"error":str(e)},400)
@APP.post("/api/files/search")
async def file_search(body:dict):
 root=Path(body.get("folder","")).expanduser(); q=(body.get("query") or "").strip(); limit=min(int(body.get("limit",30)),100)
 if not root.is_dir() or not q:return JSONResponse({"ok":False,"error":"folder and query required"},400)
 hits=[]
 for p in iter_files(root):
  if p.suffix.lower() not in {".txt",".md",".csv",".json",".xml",".html",".htm",".log",".yaml",".yml",".rtf",".pdf",".docx"}:continue
  try:
   text=extract_text(p); score=relevance(q,text)
   if score:hits.append({"path":str(p),"score":score,"preview":text[:1200]})
  except Exception:pass
 hits.sort(key=lambda x:(-x["score"],x["path"].lower())); return {"ok":True,"query":q,"hits":hits[:limit],"read_only":True}
@APP.post("/api/files/duplicates")
async def duplicates(body:dict):
 root=Path(body.get("folder","")).expanduser()
 if not root.is_dir():return JSONResponse({"ok":False,"error":f"Folder does not exist: {root}"},400)
 groups={}; scanned=0
 for p in iter_files(root):
  if p.suffix.lower() not in {".jpg",".jpeg",".png",".webp",".gif",".bmp",".tif",".tiff",".heic"}:continue
  try:
   m=file_meta(p,True); groups.setdefault(m["sha256"],[]).append(m); scanned+=1
  except OSError:pass
 proposals=[]
 for g in groups.values():
  if len(g)<2:continue
  keep=min(g,key=lambda x:(x["created_at"],x["path"].lower())); dup=[x for x in g if x["path"]!=keep["path"]]
  proposals.append({"keep":keep,"duplicates":dup,"recoverable_bytes":sum(x["size_bytes"] for x in dup),"reason":"Exact SHA-256 duplicate. Oldest creation timestamp proposed as canonical. No action performed."})
 return {"ok":True,"images_scanned":scanned,"duplicate_groups":proposals,"recoverable_bytes":sum(x["recoverable_bytes"] for x in proposals),"read_only":True,"actions_performed":[]}
@APP.get("/api/files/policy")
async def file_policy():return {"read_only":True,"delete":False,"rename":False,"move":False,"overwrite":False,"preserve_metadata":True,"mutation_requires_explicit_permission":True}
