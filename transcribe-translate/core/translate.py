from __future__ import annotations
import json, urllib.request
from typing import Callable
from .config import require_openai_key
Progress=Callable[[str],None]
def chunks(text,size=12000):
    if len(text)<=size:return [text]
    out=[];cur=[];n=0
    for p in text.split("\n"):
        if n+len(p)+1>size and cur: out.append("\n".join(cur));cur=[];n=0
        cur.append(p);n+=len(p)+1
    if cur:out.append("\n".join(cur))
    return out
class OllamaTextProvider:
    def __init__(self,url,model,progress=print):self.url=url.rstrip("/");self.model=model;self.progress=progress
    def _call(self,prompt):
        body=json.dumps({"model":self.model,"messages":[{"role":"user","content":prompt}],"stream":False}).encode()
        req=urllib.request.Request(self.url+"/api/chat",body,{"Content-Type":"application/json"})
        with urllib.request.urlopen(req,timeout=3600) as r:return str(json.loads(r.read())["message"]["content"]).strip()
    def translate(self,text,target):
        return "\n\n".join(self._call("Translate faithfully into "+target+". Preserve names, numbers, voting terms, speakers and uncertainty. Do not summarize.\n\n"+p) for p in chunks(text))
    def summarize(self,text,language):
        return self._call("Summarize this meeting transcript in "+language+". Preserve decisions, proposals, objections, votes, named speakers and agenda/procedural issues. Do not invent facts.\n\n"+text)
