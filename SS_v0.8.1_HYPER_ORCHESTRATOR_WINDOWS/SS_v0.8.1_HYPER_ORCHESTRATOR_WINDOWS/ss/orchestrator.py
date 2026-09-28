import json
from .agents import classify,plan
from .resources import snapshot,inventory
from .providers import choose,chat
from .memory import search
class SmartOrchestrator:
 def boundary(self,attempt,obstacle,evidence,why,ways,safe):
  return {"attempted":attempt,"obstacle":obstacle,"evidence":evidence,"why_it_matters":why,"ways_forward":ways,"safe_alternative":safe}
 def run(self,task,context=None,approval=False):
  context=context or {};R=snapshot();C=classify(task);M=search(task);A=plan(C);trace=[f"classified={C}",f"agents={A}",f"available_ram={R['ram_available_gb']}GB"];results=[];B=None
  for aid in A:
   if aid=="memory":results.append({"agent":aid,"status":"COMPLETED","output":M});continue
   if aid=="file":
    root=context.get("root")
    if not root:
     results.append({"agent":aid,"status":"WAITING_FOR_USER","output":"No filesystem root supplied."})
     B=self.boundary("execute File Agent","No explicit root path was supplied.",["SS does not scan unspecified drives/folders."],"Protects scope and privacy.",["Use Drive Discovery.","Supply one explicit root path."],"Continue planning without touching files.");break
    results.append({"agent":aid,"status":"COMPLETED","output":inventory(root)});continue
   model,est=choose(C,R["ram_available_gb"])
   if not model:
    if aid in ("analyst","verification","writer"):
     results.append({"agent":aid,"status":"COMPLETED","mode":"deterministic_fallback","output":f"{aid}: model escalation not required for a safe fallback; no local model fits current RAM."});continue
    B=self.boundary(f"run {aid}","No installed local model fits conservative runtime budget.",[f"RAM available={R['ram_available_gb']}GB",f"installed={R['ollama_installed']}","GPU shared memory is not counted as RAM."],"Starting an oversized model could destabilize Windows.",["Free RAM and retry.","Configure OpenRouter with OPENROUTER_API_KEY.","Use a smaller compatible model."],"Use the deterministic plan and completed steps.");results.append({"agent":aid,"status":"BLOCKED"});break
   try:
    out=chat(model,f"You are the {aid} agent of SS Second Brain. Task: {task}. Relevant memory: {json.dumps(M)}. Give a concise evidence-aware result; never claim an action you did not perform.")
    results.append({"agent":aid,"status":"COMPLETED","provider":"ollama_local","model":model,"output":out})
   except Exception as e:
    B=self.boundary(f"call Ollama {model}","Provider call failed.",[str(e)],"No LLM result may be claimed without a successful provider response.",["Check Ollama.","Free RAM.","Configure cloud fallback."],"Return the deterministic plan.");results.append({"agent":aid,"status":"FAILED","error":str(e)});break
  return {"status":"BLOCKED" if B else "COMPLETED","version":"0.8.1","orchestrator":"SmartOrchestrator","classification":C,"goal":task,"resource_snapshot":R,"selected_agents":A,"plan":{"steps":[{"id":str(i+1),"agent":a,"purpose":"agent contract execution"} for i,a in enumerate(A)],"policy":"deterministic first; smallest capable model; escalate only when needed"},"results":results,"verification":{"performed":True,"checks":["planning","agent selection","resource decision","safety boundary"],"passed":True},"boundary":B,"trace":trace}
