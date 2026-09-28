import json,time
from pathlib import Path
P=Path(__file__).resolve().parent.parent/"memory"/"store.json"
DEFAULT=[{"id":"architecture","text":"Provider-independent SmartOrchestrator; deterministic code first; smallest capable model; escalate only when needed.","source":"SS architecture"},
{"id":"safety","text":"Read-only by default. Destructive/external side effects require explicit approval and a rollback path.","source":"SS architecture"},
{"id":"boundary","text":"Every boundary explains attempted action, obstacle, evidence, significance, ways forward and safe alternative.","source":"SS architecture"},
{"id":"hardware","text":"HP 15s eq2xxx Ryzen 5000 context with integrated AMD Radeon. GPU shared memory is not assumed to be extra RAM.","source":"hardware context"}]
def load():
    if not P.exists(): P.write_text(json.dumps(DEFAULT,indent=2),encoding="utf8")
    return json.loads(P.read_text(encoding="utf8"))
def search(q):
    a=[];terms=q.lower().split()
    for x in load():
        score=sum(t in x["text"].lower() for t in terms)
        if score:a.append((score,x))
    return [x for _,x in sorted(a,key=lambda z:z[0],reverse=True)[:8]]
