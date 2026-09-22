from __future__ import annotations
import threading, tkinter as tk, os
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from core.config import ROOT, load_config
from core.pipeline import run_job

class App(tk.Tk):
    def __init__(self):
        super().__init__(); self.title("SS Transcribe-Translate"); self.geometry("900x650")
        self.source=tk.StringVar(); self.language=tk.StringVar(value="auto"); self.diarize=tk.BooleanVar(value=True)
        self.target=tk.StringVar(value="en"); self.status=tk.StringVar(value="Ready"); self._build()
    def _build(self):
        root=ttk.Frame(self,padding=16); root.pack(fill="both",expand=True)
        ttk.Label(root,text="SS Transcribe-Translate",font=("Segoe UI",18,"bold")).pack(anchor="w")
        box=ttk.LabelFrame(root,text="Input",padding=10); box.pack(fill="x",pady=10)
        ttk.Entry(box,textvariable=self.source).pack(side="left",fill="x",expand=True)
        ttk.Button(box,text="Browse...",command=self.browse).pack(side="left",padx=8)
        opts=ttk.Frame(root); opts.pack(fill="x")
        ttk.Label(opts,text="Language").pack(side="left"); ttk.Combobox(opts,textvariable=self.language,values=["auto","ca","es","en","fr","de","it"],state="readonly",width=8).pack(side="left",padx=6)
        ttk.Label(opts,text="Translate to").pack(side="left",padx=(18,0)); ttk.Combobox(opts,textvariable=self.target,values=["en","ca","es","fr","de","it"],state="readonly",width=8).pack(side="left",padx=6)
        ttk.Checkbutton(opts,text="Speaker identification",variable=self.diarize).pack(side="left",padx=18)
        ttk.Button(root,text="START TRANSCRIPTION",command=self.start).pack(anchor="w",pady=10)
        ttk.Label(root,textvariable=self.status).pack(anchor="w")
        self.log=tk.Text(root,wrap="word",font=("Consolas",10)); self.log.pack(fill="both",expand=True)
    def browse(self):
        d=filedialog.askopenfilename(filetypes=[("Media","*.mp4 *.mkv *.mov *.webm *.m4a *.mp3 *.wav *.flac"),("All files","*.*")])
        if d:self.source.set(d)
    def logmsg(self,msg):
        self.after(0,lambda:(self.log.insert("end",msg+"\n"),self.log.see("end"),self.status.set(msg[:140])))
    def start(self):
        if not self.source.get().strip(): messagebox.showerror("Input required","Choose a file or paste a YouTube URL."); return
        if not os.getenv("OPENAI_API_KEY"): messagebox.showerror("API key missing","Put OPENAI_API_KEY in .env."); return
        cfg=load_config(ROOT/"config.json"); cfg.language=self.language.get(); cfg.diarize=self.diarize.get(); cfg.target_language=self.target.get()
        threading.Thread(target=self.worker,args=(self.source.get().strip(),cfg),daemon=True).start()
    def worker(self,source,cfg):
        try:
            out=run_job(source,cfg,ROOT/"output",self.logmsg); self.after(0,lambda:messagebox.showinfo("Complete",str(out)))
        except Exception as e: self.logmsg("ERROR: "+str(e))
    def open_output(self): os.startfile(ROOT/"output")
if __name__=="__main__": App().mainloop()
