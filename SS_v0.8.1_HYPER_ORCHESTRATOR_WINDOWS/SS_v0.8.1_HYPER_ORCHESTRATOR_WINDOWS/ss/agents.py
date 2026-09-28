from dataclasses import dataclass
@dataclass
class A:
 id:str;name:str;purpose:str;caps:list[str];det:bool
AGENTS=[
 A("memory","Memory / Context","Retrieve relevant project knowledge with provenance.",["retrieval","provenance"],False),
 A("research","Research / Web","Gather external evidence when a web-capable provider/tool is available.",["research","sources"],False),
 A("analyst","Analyst / Reasoning","Decompose tasks, reason, compare evidence and plan.",["reasoning","planning"],False),
 A("writer","Writer","Produce structured output from verified inputs.",["writing"],False),
 A("coder","Coder / Developer","Design, inspect and generate software changes.",["coding","debugging"],False),
 A("file","File & Document","Read-only discovery, inventory and deterministic file analysis.",["files","metadata","hashing"],True),
 A("verification","Verification","Check evidence, consistency and execution results.",["verification"],True),
 A("automation","Automation","Prepare safe, reversible workflows; side effects require approval.",["workflow","automation"],False)]
def data():return [{"id":a.id,"name":a.name,"purpose":a.purpose,"capabilities":a.caps,"deterministic":a.det,"status":"READY"} for a in AGENTS]
def classify(t):
 t=t.lower()
 if any(x in t for x in ["code","python","program","bug","api","implement"]):return "coding"
 if any(x in t for x in ["research","latest","compare","source","web"]):return "research"
 if any(x in t for x in ["write","draft","email","summarize"]):return "writing"
 if any(x in t for x in ["file","folder","drive","duplicate"]):return "file"
 if any(x in t for x in ["automate","automation","schedule"]):return "automation"
 if any(x in t for x in ["analy","reason","plan","architecture","decide"]):return "reasoning"
 return "general"
def plan(c):
 return {"coding":["memory","analyst","coder","verification"],"research":["memory","research","analyst","verification","writer"],"writing":["memory","analyst","writer","verification"],"file":["memory","file","verification"],"automation":["analyst","automation","verification"],"reasoning":["memory","analyst","verification","writer"],"general":["memory","analyst","verification","writer"]}.get(c,["memory","analyst","verification"])
