import os,subprocess,json,shutil,psutil,requests
OLLAMA=os.getenv("OLLAMA_BASE_URL","http://127.0.0.1:11434").rstrip("/")
def gb(x): return round(x/1024**3,2)
def models():
    try:return requests.get(OLLAMA+"/api/tags",timeout=2).json().get("models",[])
    except:return []
def loaded():
    try:return requests.get(OLLAMA+"/api/ps",timeout=2).json().get("models",[])
    except:return []
def gpu():
    x={"detected":False,"acceleration_verified":False,"evidence":[]}
    try:
        p=subprocess.run(["powershell","-NoProfile","-Command","Get-CimInstance Win32_VideoController | Select Name,AdapterRAM,DriverVersion | ConvertTo-Json -Compress"],capture_output=True,text=True,timeout=4)
        if p.stdout.strip():
            x["detected"]=True;x["devices"]=json.loads(p.stdout);x["evidence"].append("Windows GPU device reported.")
    except Exception as e:x["evidence"].append(str(e))
    x["evidence"].append("Shared GPU memory is NOT counted as extra system RAM.")
    return x
def snapshot():
    v=psutil.virtual_memory();s=psutil.swap_memory()
    return {"ram_total_gb":gb(v.total),"ram_available_gb":gb(v.available),"ram_used_gb":gb(v.used),"ram_percent":v.percent,"swap_total_gb":gb(s.total),"swap_used_gb":gb(s.used),"cpu_percent":psutil.cpu_percent(.1),"gpu":gpu(),"ollama_installed":[x.get("name") for x in models()],"ollama_loaded":[x.get("name") for x in loaded()]}
def roots():
    out=[]
    for d in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        p=d+":\\"
        if os.path.exists(p):
            try:
                u=shutil.disk_usage(p);out.append({"path":p,"free_gb":gb(u.free),"total_gb":gb(u.total)})
            except:out.append({"path":p})
    return out
def inventory(root):
    if not os.path.isdir(root): return {"status":"BLOCKED","root":root,"error":"Root does not exist or is not a directory."}
    out=[]; n=0
    for dp,ds,fs in os.walk(root):
        for f in fs:
            p=os.path.join(dp,f)
            try:
                s=os.stat(p);out.append({"path":p,"name":f,"size":s.st_size,"created":s.st_ctime,"modified":s.st_mtime});n+=1
                if n>=50000:return {"status":"READY","root":root,"count":n,"truncated":True,"files":out}
            except:pass
    return {"status":"READY","root":root,"count":n,"truncated":False,"files":out}
