from __future__ import annotations
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from core.config import AppConfig, ROOT, load_config
from core.pipeline import run_job

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SS Transcribe-Translate")
        self.geometry("980x720")
        self.minsize(850, 620)
        self.source = tk.StringVar()
        self.language = tk.StringVar(value="auto")
        self.asr = tk.StringVar(value="local")
        self.model = tk.StringVar(value="large-v3")
        self.diarize = tk.BooleanVar(value=False)
        self.text_provider = tk.StringVar(value="ollama")
        self.target = tk.StringVar(value="en")
        self.output = tk.StringVar(value=str(ROOT / "output"))
        self.status = tk.StringVar(value="Ready")
        self._build()

    def _build(self):
        root = ttk.Frame(self, padding=16); root.pack(fill="both", expand=True)
        ttk.Label(root, text="SS Transcribe-Translate", font=("Segoe UI", 18, "bold")).pack(anchor="w")
        ttk.Label(root, text="Local-first transcription • translation • bilingual summary").pack(anchor="w", pady=(0,14))

        box = ttk.LabelFrame(root, text="Input", padding=10); box.pack(fill="x")
        ttk.Label(box, text="File or YouTube URL").grid(row=0,column=0,sticky="w")
        ttk.Entry(box, textvariable=self.source).grid(row=1,column=0,sticky="ew",padx=(0,8))
        ttk.Button(box, text="Browse…", command=self.browse).grid(row=1,column=1)
        box.columnconfigure(0, weight=1)

        opts = ttk.LabelFrame(root, text="Processing", padding=10); opts.pack(fill="x", pady=10)
        self.combo(opts,"Source language",self.language,["auto","ca","es","en","fr","de","it"],0)
        self.combo(opts,"ASR backend",self.asr,["local","openai"],1)
        self.combo(opts,"Local Whisper model",self.model,["tiny","base","small","medium","large-v2","large-v3","large-v3-turbo"],2)
        self.combo(opts,"Text provider",self.text_provider,["ollama","openai"],3)
        self.combo(opts,"Target language",self.target,["en","ca","es","fr","de","it"],4)
        ttk.Checkbutton(opts,text="Speaker diarization (requires HF_TOKEN for local ASR)",variable=self.diarize).grid(row=0,column=2,columnspan=2,sticky="w",padx=12)
        ttk.Label(opts,text="Output folder").grid(row=1,column=2,sticky="w",padx=12)
        ttk.Entry(opts,textvariable=self.output).grid(row=1,column=3,sticky="ew",padx=12)
        opts.columnconfigure(3,weight=1)

        action=ttk.Frame(root); action.pack(fill="x",pady=8)
        ttk.Button(action,text="START TRANSCRIPTION",command=self.start).pack(side="left")
        ttk.Button(action,text="Open output folder",command=self.open_output).pack(side="left",padx=8)
        ttk.Label(action,textvariable=self.status).pack(side="right")

        logbox=ttk.LabelFrame(root,text="Progress / errors",padding=8); logbox.pack(fill="both",expand=True)
        self.log=tk.Text(logbox,wrap="word",font=("Consolas",10))
        self.log.pack(fill="both",expand=True)

    def combo(self,parent,label,var,values,row):
        ttk.Label(parent,text=label).grid(row=row,column=0,sticky="w",pady=3)
        ttk.Combobox(parent,textvariable=var,values=values,state="readonly",width=24).grid(row=row,column=1,sticky="w",pady=3)

    def browse(self):
        p=filedialog.askopenfilename(title="Choose media",filetypes=[("Media","*.mp4 *.mkv *.mov *.avi *.webm *.m4v *.mp3 *.m4a *.wav *.flac *.ogg"),("All files","*.*")])
        if p:self.source.set(p)

    def logmsg(self,msg):
        self.after(0,lambda:(self.log.insert("end",msg+"\n"),self.log.see("end"),self.status.set(msg[:140])))

    def start(self):
        if not self.source.get().strip():
            messagebox.showerror("Input required","Choose a media file or paste a YouTube URL.")
            return
        cfg=load_config(ROOT/"config.json")
        cfg.asr_backend=self.asr.get(); cfg.local_model=self.model.get(); cfg.language=self.language.get()
        cfg.diarize=self.diarize.get(); cfg.text_provider=self.text_provider.get(); cfg.target_language=self.target.get()
        if self.asr.get()=="openai" and not __import__("os").getenv("OPENAI_API_KEY"):
            messagebox.showerror("OpenAI key missing","Set OPENAI_API_KEY before selecting OpenAI ASR.")
            return
        self.status.set("Running…")
        threading.Thread(target=self.worker,args=(self.source.get().strip(),cfg),daemon=True).start()

    def worker(self,source,cfg):
        try:
            out=run_job(source,cfg,Path(self.output.get()),self.logmsg)
            self.after(0,lambda:messagebox.showinfo("Complete",f"Job finished:\n{out}"))
        except Exception as exc:
            self.logmsg("ERROR: "+str(exc))
            self.after(0,lambda:messagebox.showerror("Processing failed",str(exc)))
            self.after(0,lambda:self.status.set("Failed"))

    def open_output(self):
        import os
        Path(self.output.get()).mkdir(parents=True,exist_ok=True)
        os.startfile(Path(self.output.get()))

if __name__=="__main__":
    App().mainloop()
