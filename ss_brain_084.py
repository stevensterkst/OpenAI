"""SS Second Brain v0.8.4 stable runtime.
Local-first, RAM-aware, persistent chats, read-only file intelligence.
"""
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, mimetypes, os, re, sys, time, urllib.request

VERSION="0.8.4"; ROOT=Path(__file__).parent
APP=FastAPI(title="SS Second Brain",version=VERSION)
DATA=Path(os.environ.get("LOCALAPPDATA",str(Path.home()))) / "SS" / "data"
for n in ("chats","memory","indexes","backups"): (DATA/n).mkdir(parents=True,exist_ok=True)
PROVIDERS={
 "ollama":{"name":"Ollama","kind":"local","base":"http://127.0.0.1:11434"},
 "jan":{"name":"Jan","kind":"local","base":"http://127.0.0.1:1337/v1"},
 "lmstudio":{"name":"LM Studio","kind":"local","base":"http://127.0.0.1:1234/v1"},
 "openrouter":{"name":"OpenRouter","kind":"cloud","base":"https://openrouter.ai/api/v1"},
 "huggingface":{"name":"Hugging Face","kind":"cloud","base":"https://router.huggingface.co/v1"},
 "venice":{"name":"Venice AI","kind":"cloud","base":"https://api.venice.ai/api/v1"},
 "openai":{"name":"OpenAI","kind":"cloud","base":"https://api.openai.com/v1"},
 "google":{"name":"Google Gemini","kind":"cloud","base":"https://generativelanguage.googleapis.com/v1beta/openai"},
 "xai":{"name":"xAI / Grok","kind":"cloud","base":"https://api.x.ai/v1"},
 "deepseek":{"name":"DeepSeek","kind":"cloud","base":"https://api.deepseek.com/v1"},
 "mistral":{"name":"Mistral","kind":"cloud","base":"https://api.mistral.ai/v1"},
 "moonshot":{"name":"Kimi / Moonshot","kind":"cloud","base":"https://api.moonshot.ai/v1"},
 "zai":{"name":"Z.ai / GLM","kind":"cloud","base":"https://api.z.ai/api/paas/v4"},
 "qwen":{"name":"Qwen / Alibaba","kind":"cloud","base":"https://dashscope-us.aliyuncs.com/compatible-mode/v1"},
 "perplexity":{"name":"Perplexity","kind":"cloud","base":"https://api.perplexity.ai/v1"}}
CONNECTORS={"brave":{"name":"Brave Search","url":"https://api.search.brave.com/res/v1/web/search"},"duckduckgo":{"name":"DuckDuckGo","url":"https://duckduckgo.com"},"tor":{"name":"Tor","url":"https://www.torproject.org/"},"huggingchat":{"name":"HuggingChat","url":"https://huggingface.co/chat/"},"metaai":{"name":"Meta AI","url":"https://www.meta.ai/"},"higgsfield":{"name":"Higgsfield","url":"https://higgsfield.ai/"}}
FREE={"gemma3:1b","llama3.2:1b","qwen3:1.7b","qwen3:4b","phi4-mini:3.8b"}
def now(): return datetime.now(timezone.utc).isoformat()
def safe(s): return re.sub(r"[^A-Za-z0-9._-]+","_",str(s or "chat"))[:120] or "chat"
def save(p,obj):
 p.parent.mkdir(parents=True,exist_ok=True); t=p.with_suffix(p.suffix+".tmp"); t.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding="utf-8"); os.replace(t,p)
def req(url,method="GET",payload=None,key=None,timeout=120):
 data=json.dumps(payload).encode() if payload is not None else None; h={"Accept":"application/json"}
 if payload is not None:h["Content-Type"]="application/json"
 if key:h["Authorization"]="Bearer "+key
 with urllib.request.urlopen(urllib.request.Request(url,data=data,headers=h,method=method),timeout=timeout) as r:return json.loads(r.read().decode("utf-8",errors="replace"))
def ram():
 try:
  if sys.platform=="win32":
   import ctypes
   class S(ctypes.Structure): _fields_=[("length",ctypes.c_ulong),("load",ctypes.c_ulong),("total",ctypes.c_ulonglong),("avail",ctypes.c_ulonglong),("page",ctypes.c_ulonglong),("availpage",ctypes.c_ulonglong),("virt",ctypes.c_ulonglong),("availvirt",ctypes.c_ulonglong),("availx",ctypes.c_ulonglong)]
   s=S();s.length=ctypes.sizeof(S);ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(s));return s.avail/2**30
  return 0.0
 except:return 0.0
def priority():
 r=ram()
 return (["qwen3:4b","phi4-mini:3.8b","qwen3:1.7b","gemma3:1b","llama3.2:1b"] if r>=7 else ["phi4-mini:3.8b","qwen3:1.7b","gemma3:1b","llama3.2:1b"] if r>=4 else ["qwen3:1.7b","gemma3:1b","llama3.2:1b"] if r>=2 else ["gemma3:1b","llama3.2:1b"])
def boundary(name,e):
 s=str(e).lower(); return f"{name} is unreachable; SS stopped at that boundary." if "refused" in s or "urlopen error" in s else f"{name} rejected the credential/permission." if "401" in s or "403" in s else f"{name} rate-limited the request." if "429" in s else f"{name}: {e}"
def allfiles(root): return (p for p in Path(root).expanduser().rglob("*") if p.is_file())
def meta(p,h=False):
 s=p.stat();r={"path":str(p),"name":p.name,"size_bytes":s.st_size,"extension":p.suffix.lower(),"mime":mimetypes.guess_type(p.name)[0],"created_at":datetime.fromtimestamp(s.st_ctime).isoformat(),"modified_at":datetime.fromtimestamp(s.st_mtime).isoformat()}
 if h:
  z=hashlib.sha256()
  with open(p,"rb") as f:
   for b in iter(lambda:f.read(1024*1024),b""):z.update(b)
  r["sha256"]=z.hexdigest()
 return r
def text(p):
 e=p.suffix.lower()
 if e in {".txt",".md",".csv",".json",".xml",".html",".htm",".log",".yaml",".yml",".rtf"}:return p.read_text(encoding="utf-8",errors="replace")
 if e==".pdf":
  from pypdf import PdfReader;return "\n\n".join(x.extract_text() or "" for x in PdfReader(str(p)).pages)
 if e==".docx":
  from docx import Document;return "\n".join(x.text for x in Document(str(p)).paragraphs)
 raise ValueError("Extractor not installed for "+e)
def chat_path(cid):return DATA/"chats"/(safe(cid)+".json")
def chat_list():
 out=[]
 for p in sorted((DATA/"chats").glob("*.json"),key=lambda x:x.stat().st_mtime,reverse=True):
  try:
   c=json.loads(p.read_text(encoding="utf-8"));out.append({"id":c.get("id",p.stem),"title":c.get("title","Chat"),"updated_at":c.get("updated_at"),"messages":len(c.get("messages",[]))})
  except:pass
 return out
@APP.get("/",response_class=HTMLResponse)
async def home():return HTMLResponse((ROOT/"web"/"brain.html").read_text(encoding="utf-8"))
@APP.get("/console",response_class=HTMLResponse)
async def console():return await home()
@APP.get("/workspace",response_class=HTMLResponse)
async def workspace():return await home()
@APP.get("/system")
async def system():return {"service":"SS Second Brain","version":VERSION,"status":"online","port":8765,"ram_available_gb":round(ram(),2),"storage":str(DATA),"policy":{"auto_delete_chats":False,"file_mutation":False,"cloud_spend_without_approval":False}}
@APP.get("/api/providers")
async def providers():return {"version":VERSION,"providers":PROVIDERS,"connectors":CONNECTORS,"free_models":sorted(FREE,key=str.lower)}
@APP.get("/api/chats")
async def chats():return {"chats":chat_list(),"never_delete":True}
@APP.get("/api/chats/{cid}")
async def getchat(cid):
 p=chat_path(cid)
 if not p.exists():return JSONResponse({"ok":False,"error":"Chat not found"},404)
 return json.loads(p.read_text(encoding="utf-8"))
@APP.get("/api/models/{pid}")
async def models(pid):
 p=PROVIDERS.get(pid)
 if not p:return JSONResponse({"ok":False,"error":"Unknown provider"},400)
 try:
  if pid=="ollama":
   d=req(p["base"]+"/api/tags");m=sorted([{"id":x.get("name"),"free":True} for x in d.get("models",[])],key=lambda x:x["id"].lower());return {"ok":True,"models":m,"free":m}
  if p["kind"]=="local":return {"ok":False,"models":[],"message":p["name"]+" local API is not running."}
  return {"ok":True,"models":[],"message":"Credential required before querying models."}
 except Exception as e:return JSONResponse({"ok":False,"error":boundary(p["name"],e)},502)
@APP.post("/api/chat")
async def dochat(b:dict):
 pid=b.get("provider","ollama");p=PROVIDERS.get(pid);model=b.get("model");msgs=b.get("messages") or []
 if not p or not model:return JSONResponse({"ok":False,"error":"Provider and model required"},400)
 if p["kind"]=="cloud" and not b.get("cloud_approved"):return JSONResponse({"ok":False,"error":"Cloud use requires explicit approval for this turn."},403)
 try:
  st=time.perf_counter()
  if pid=="ollama":d=req(p["base"]+"/api/chat","POST",{"model":model,"messages":msgs,"stream":False,"options":{"temperature":b.get("temperature",.6)}});ans=(d.get("message") or {}).get("content","")
  else:
   if not b.get("apiKey"):return JSONResponse({"ok":False,"error":p["name"]+" API key not configured."},400)
   d=req(p["base"]+"/chat/completions","POST",{"model":model,"messages":msgs,"temperature":b.get("temperature",.5)},b["apiKey"]);ans=((d.get("choices") or [{}])[0].get("message") or {}).get("content","")
  if b.get("chat_id"):save(chat_path(b["chat_id"]),{"id":b["chat_id"],"title":b.get("title","SS chat"),"provider":pid,"model":model,"messages":msgs+[{"role":"assistant","content":ans}],"updated_at":now()})
  return {"ok":True,"text":ans,"provider":pid,"model":model,"latency_ms":round((time.perf_counter()-st)*1000)}
 except Exception as e:return JSONResponse({"ok":False,"error":boundary(p["name"],e)},502)
@APP.post("/api/auto-chat")
async def auto(b:dict):
 task=(b.get("task") or "").strip()
 if not task:return JSONResponse({"ok":False,"error":"Task required"},400)
 d=await models("ollama")
 if not d.get("ok") or not d.get("models"):return JSONResponse({"ok":False,"error":"Ollama is not reachable. Cloud providers are optional."},502)
 avail={x["id"] for x in d["models"]};m=next((x for x in priority() if x in avail),d["models"][0]["id"]);legal=any(x in task.lower() for x in ("legal","court","contract","evidence","case","procedure","claim","agreement"));sp="You are SS, a rigorous second brain. Never invent facts. Separate source facts, inference and uncertainty. "+("For legal work preserve exact dates, names, quotations and provenance; identify contradictions and missing evidence. Do not silently alter source material. " if legal else "")+"Never modify files without explicit permission."
 return await dochat({"provider":"ollama","model":m,"messages":[{"role":"system","content":sp},{"role":"user","content":task}],"chat_id":b.get("chat_id"),"title":task[:80]})
@APP.post("/api/files/scan")
async def scan(b:dict):
 root=Path(b.get("folder","")).expanduser()
 if not root.is_dir():return JSONResponse({"ok":False,"error":f"Folder does not exist: {root}"},400)
 lim=min(int(b.get("limit",10000)),50000);rows=[]
 for i,p in enumerate(allfiles(root)):
  if i>=lim:break
  try:rows.append(meta(p,bool(b.get("hash"))))
  except OSError:pass
 return {"ok":True,"files":rows,"count":len(rows),"truncated":len(rows)>=lim,"read_only":True}
@APP.post("/api/files/extract")
async def extract(b:dict):
 p=Path(b.get("path","")).expanduser()
 try:
  s=text(p);lim=min(int(b.get("max_chars",250000)),1000000);return {"ok":True,"metadata":meta(p),"text":s[:lim],"truncated":len(s)>lim,"read_only":True}
 except Exception as e:return JSONResponse({"ok":False,"error":str(e),"read_only":True},400)
@APP.post("/api/files/search")
async def search(b:dict):
 root=Path(b.get("folder","")).expanduser();q=(b.get("query") or "").lower();lim=min(int(b.get("limit",30)),200)
 if not root.is_dir() or not q:return JSONResponse({"ok":False,"error":"Folder and query required"},400)
 hits=[]
 for p in allfiles(root):
  try:
   s=text(p);score=sum(s.lower().count(w) for w in re.findall(r"[\w]{4,}",q))
   if score:hits.append({"path":str(p),"name":p.name,"score":score,"preview":re.sub(r"\s+"," ",s)[:900]})
  except:pass
 hits.sort(key=lambda x:(-x["score"],x["path"].lower()));return {"ok":True,"hits":hits[:lim],"read_only":True}
@APP.post("/api/files/duplicates")
async def duplicates(b:dict):
 root=Path(b.get("folder","")).expanduser()
 if not root.is_dir():return JSONResponse({"ok":False,"error":"Folder does not exist"},400)
 groups={};scanned=0
 for p in allfiles(root):
  if p.suffix.lower() not in {".jpg",".jpeg",".png",".webp",".gif",".bmp",".tif",".tiff",".heic"}:continue
  try:m=meta(p,True);groups.setdefault(m["sha256"],[]).append(m);scanned+=1
  except:pass
 out=[]
 for g in groups.values():
  if len(g)>1:
   g.sort(key=lambda x:(x["created_at"],x["path"].lower()));out.append({"keep":g[0],"duplicates":g[1:],"recoverable_bytes":sum(x["size_bytes"] for x in g[1:]),"reason":"Exact SHA-256 duplicate; oldest creation timestamp proposed as canonical. No action performed."})
 return {"ok":True,"images_scanned":scanned,"duplicate_groups":out,"recoverable_bytes":sum(x["recoverable_bytes"] for x in out),"read_only":True,"actions_performed":[]}
@APP.get("/api/files/policy")
async def policy():return {"read_only":True,"delete":False,"rename":False,"move":False,"overwrite":False,"preserve_metadata":True,"mutation_requires_explicit_permission":True}
