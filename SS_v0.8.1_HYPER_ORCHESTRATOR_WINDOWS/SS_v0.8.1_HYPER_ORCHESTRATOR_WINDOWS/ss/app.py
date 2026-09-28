from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from .orchestrator import SmartOrchestrator
from .agents import data
from .resources import snapshot,models,loaded,roots,inventory
from .providers import providers
from .memory import search
app=FastAPI(title="SS Second Brain",version="0.8.1");O=SmartOrchestrator()
class T(BaseModel):task:str;approval:bool=False;context:dict={}
class R(BaseModel):root:str
HTML="""<!doctype html><html><head><meta charset=utf-8><title>SS Second Brain v0.8.1</title><style>
body{font-family:Segoe UI,Arial;margin:0;background:#eef1f5;color:#17202a}header{background:#18202a;color:white;padding:20px 28px}main{max-width:1400px;margin:20px auto;padding:0 18px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(420px,1fr));gap:16px}.card{background:white;border:1px solid #ccd3da;border-radius:10px;padding:18px}.full{grid-column:1/-1}textarea,input{width:100%;box-sizing:border-box;padding:10px;margin:5px 0 10px}button{padding:9px 13px;margin:3px;border-radius:6px;border:1px solid #999;background:white}.primary{background:#18202a;color:white}pre{white-space:pre-wrap;background:#101418;color:#e8edf2;padding:13px;border-radius:7px;max-height:520px;overflow:auto}.agent{border:1px solid #d7dde3;border-radius:8px;padding:12px;margin:8px 0}.small{font-size:12px;color:#58636f}</style></head><body>
<header><h1>SS Second Brain <small>v0.8.1</small></h1><div>SmartOrchestrator · 8 agents · provider-independent · resource-aware · read-only</div></header><main><div class=grid>
<section class="card full"><h2>🧠 Intelligent Orchestrator</h2><p>Classify → retrieve context → plan multi-agent execution → choose deterministic code or smallest fitting model → execute → verify → explain boundaries.</p><textarea id=t rows=4>Analyze the SS architecture and propose the next highest-value improvements.</textarea><button class=primary onclick=run()>EXECUTE THROUGH SS</button><pre id=o>Ready.</pre></section>
<section class=card><h2>8 Live Agents</h2><div id=a>Loading...</div></section><section class=card><h2>Providers / Models</h2><pre id=p>Loading...</pre></section>
<section class=card><h2>Live Resources</h2><pre id=r>Loading...</pre><button onclick=load()>Refresh</button></section>
<section class=card><h2>Memory / Context</h2><input id=q value="SS architecture"><button onclick=mem()>Search</button><pre id=m></pre></section>
<section class=card><h2>Drive Discovery — READ ONLY</h2><button onclick=roots()>Discover drives</button><pre id=d></pre><input id=x placeholder="C:\\Users\\..."><button onclick=inv()>Inventory explicit root</button><pre id=i></pre></section>
<section class="card full"><h2>Safety Boundary</h2><p>No move, rename, delete, quarantine or destructive filesystem operation is exposed. Every blocked boundary explains the obstacle, evidence, significance, ways forward and safe alternative.</p></section>
</div></main><script>
async function j(u,o){let r=await fetch(u,o);return r.json()}
async function load(){let a=await j('/api/agents');document.getElementById('a').innerHTML=a.map(x=>`<div class=agent><b>${x.name}</b> <span class=small>[${x.id}]</span><br>${x.purpose}<br><span class=small>${x.capabilities.join(' · ')} · ${x.deterministic?'deterministic':'model-capable'}</span></div>`).join('');document.getElementById('p').textContent=JSON.stringify({providers:await j('/api/providers'),models:await j('/api/models')},null,2);document.getElementById('r').textContent=JSON.stringify(await j('/api/resources'),null,2)}
async function run(){document.getElementById('o').textContent='Planning/executing...';document.getElementById('o').textContent=JSON.stringify(await j('/api/execute',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({task:document.getElementById('t').value})}),null,2)}
async function mem(){document.getElementById('m').textContent=JSON.stringify(await j('/api/memory/search?q='+encodeURIComponent(document.getElementById('q').value)),null,2)}
async function roots(){document.getElementById('d').textContent=JSON.stringify(await j('/api/roots'),null,2)}
async function inv(){document.getElementById('i').textContent=JSON.stringify(await j('/api/inventory',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({root:document.getElementById('x').value})}),null,2)}
load();mem();
</script></body></html>"""
@app.get("/",response_class=HTMLResponse)
def home():return HTML
@app.get("/api/version")
def version():return {"name":"SS Second Brain","version":"0.8.1","orchestrator":"SmartOrchestrator"}
@app.get("/api/status")
def status():return {"status":"READY","version":"0.8.1","orchestrator":"SmartOrchestrator","resources":snapshot()}
@app.get("/api/resources")
def res():return snapshot()
@app.get("/api/agents")
def agents():return data()
@app.get("/api/providers")
def prov():return providers()
@app.get("/api/models")
def mod():return {"installed":models(),"loaded":loaded()}
@app.get("/api/memory/search")
def ms(q="SS architecture"):return search(q)
@app.get("/api/roots")
def dr():return roots()
@app.post("/api/inventory")
def inv(r:R):return inventory(r.root)
@app.post("/api/execute")
def execute(t:T):return O.run(t.task,t.context,t.approval)
