from __future__ import annotations
import os
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
import webbrowser

from core.config import ROOT, load_config, save_local_config
from core.media import find_ytdlp_command, is_url
from core.pipeline import run_job
from core.batch import discover_media, run_batch
from core.library import reindex, search_jobs
from core.watch import watch_folder
from core.text import OllamaTextProvider, model_advice

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SS Transcribe-Translate — Free Local")
        self.geometry("1200x1020")
        self.minsize(1040, 900)
        self.source = tk.StringVar(value=os.environ.get("SS_TRANSCRIBE_SOURCE", ""))
        initial=load_config(ROOT / "config.json")
        self.ytdlp_path = tk.StringVar(value=initial.ytdlp_path)
        self.language = tk.StringVar(value=initial.language)
        self.model = tk.StringVar(value=initial.local_model)
        self.ollama_model = tk.StringVar()
        self.target = tk.StringVar(value="English")
        self.analysis_language = tk.StringVar(value="source")
        self.hotwords = tk.StringVar()
        self.search_query = tk.StringVar()
        self.top_terms = tk.IntVar(value=30)
        self.qa_question = tk.StringVar()
        self.qa_language = tk.StringVar(value="English")
        self.word_timestamps = tk.BooleanVar(value=True)
        self.translate_transcript = tk.BooleanVar(value=False)
        self.analysis = tk.BooleanVar(value=True)
        self.diarization = tk.BooleanVar(value=initial.diarization)
        self.diarization_segmentation_model = tk.StringVar(value=initial.diarization_segmentation_model)
        self.diarization_embedding_model = tk.StringVar(value=initial.diarization_embedding_model)
        self.diarization_num_speakers = tk.IntVar(value=initial.diarization_num_speakers)
        self.diarization_threshold = tk.DoubleVar(value=initial.diarization_threshold)
        self.output = tk.StringVar(value=str((ROOT / initial.output_dir).resolve() if not Path(initial.output_dir).is_absolute() else initial.output_dir))
        self.status = tk.StringVar(value="Ready — source transcript + source summary are primary; no paid API")
        self.advice = tk.StringVar(value="")
        self.watch_stop = None
        self._build()
        self.refresh_ollama()
        self.detect_ytdlp()
        self.detect_diarization_models()

    def _build(self):
        root = ttk.Frame(self, padding=16); root.pack(fill="both", expand=True)
        ttk.Label(root, text="SS Transcribe-Translate", font=("Segoe UI", 18, "bold")).pack(anchor="w")
        ttk.Label(root, text="PRIMARY: local source transcript + source-language summary. English summary is only a translation. Full translation and analysis are optional.").pack(anchor="w", pady=(0,14))

        box = ttk.LabelFrame(root, text="Input", padding=10); box.pack(fill="x")
        ttk.Label(box, text="Local media file or YouTube URL").grid(row=0,column=0,sticky="w")
        ttk.Entry(box,textvariable=self.source).grid(row=1,column=0,sticky="ew",padx=(0,8))
        ttk.Button(box,text="Browse…",command=self.browse).grid(row=1,column=1)
        ttk.Label(box,text="Existing yt-dlp.exe (YouTube only)").grid(row=2,column=0,sticky="w",pady=(8,0))
        ttk.Entry(box,textvariable=self.ytdlp_path).grid(row=3,column=0,sticky="ew",padx=(0,8))
        ttk.Button(box,text="Browse yt-dlp…",command=self.browse_ytdlp).grid(row=3,column=1)
        ttk.Label(box,text="Auto-detected when possible; the app never installs or modifies it.").grid(row=4,column=0,columnspan=2,sticky="w")
        box.columnconfigure(0,weight=1)

        opts = ttk.LabelFrame(root,text="Processing",padding=10); opts.pack(fill="x",pady=10)
        ttk.Label(opts,text="Source language").grid(row=0,column=0,sticky="w",pady=3)
        ttk.Entry(opts,textvariable=self.language,width=16).grid(row=0,column=1,sticky="w",pady=3)
        ttk.Label(opts,text="auto or any Whisper-supported ISO code").grid(row=0,column=2,sticky="w",padx=(18,0))
        ttk.Label(opts,text="Whisper model").grid(row=1,column=0,sticky="w",pady=3)
        ttk.Combobox(opts,textvariable=self.model,values=["tiny","base","small","medium","large-v3"],state="readonly",width=16).grid(row=1,column=1,sticky="w",pady=3)
        ttk.Label(opts,text="Ollama model").grid(row=0,column=3,sticky="w",padx=(30,8))
        self.ollama_combo=ttk.Combobox(opts,textvariable=self.ollama_model,state="readonly",width=28)
        self.ollama_combo.grid(row=0,column=4,sticky="w"); self.ollama_combo.bind("<<ComboboxSelected>>",lambda _e:self.update_advice())
        ttk.Button(opts,text="Refresh",command=self.refresh_ollama).grid(row=1,column=3,sticky="w",padx=(30,0))
        ttk.Label(opts,textvariable=self.advice,wraplength=360).grid(row=1,column=4,sticky="w",padx=(8,0))

        ttk.Label(opts,text="Vocabulary / names").grid(row=2,column=0,sticky="w",pady=(8,3))
        ttk.Entry(opts,textvariable=self.hotwords,width=48).grid(row=2,column=1,sticky="w",pady=(8,3))
        ttk.Label(opts,text="Comma-separated names, organisations or specialist terms to bias recognition.",wraplength=520).grid(row=2,column=2,columnspan=3,sticky="w",padx=(28,0),pady=(8,3))
        ttk.Checkbutton(opts,text="Keep word-level timestamps",variable=self.word_timestamps).grid(row=3,column=0,columnspan=2,sticky="w",pady=3)
        ttk.Checkbutton(opts,text="Run source-grounded meeting/evidence analysis",variable=self.analysis).grid(row=4,column=0,columnspan=2,sticky="w",pady=3)

        ttk.Label(opts,text="Analysis output language").grid(row=4,column=2,sticky="w",padx=(28,8))
        ttk.Entry(opts,textvariable=self.analysis_language,width=32).grid(row=4,column=3,sticky="w")
        ttk.Label(opts,text="source = original language; otherwise any Ollama-supported language.").grid(row=4,column=4,sticky="w")
        ttk.Label(opts,text="Search transcript").grid(row=5,column=0,sticky="w",pady=3)
        ttk.Entry(opts,textvariable=self.search_query,width=48).grid(row=5,column=1,sticky="w")
        ttk.Label(opts,text="Exact text search; results include timestamps. Counts/top terms are language-neutral.",wraplength=520).grid(row=5,column=2,columnspan=3,sticky="w",padx=(28,0))
        ttk.Label(opts,text="Top terms").grid(row=6,column=0,sticky="w")
        ttk.Spinbox(opts,from_=5,to=200,textvariable=self.top_terms,width=8).grid(row=6,column=1,sticky="w")

        ttk.Label(opts,text="Transcript-grounded Q&A").grid(row=7,column=0,sticky="w",pady=3)
        ttk.Entry(opts,textvariable=self.qa_question,width=48).grid(row=7,column=1,sticky="w")
        ttk.Label(opts,text="Optional question answered only from this recording.").grid(row=7,column=2,columnspan=3,sticky="w",padx=(28,0))
        ttk.Label(opts,text="Q&A language").grid(row=8,column=0,sticky="w")
        ttk.Entry(opts,textvariable=self.qa_language,width=32).grid(row=8,column=1,sticky="w")

        ttk.Checkbutton(opts,text="Also translate the FULL source transcript",variable=self.translate_transcript).grid(row=9,column=0,columnspan=2,sticky="w",pady=3)
        ttk.Label(opts,text="Target language").grid(row=9,column=2,sticky="w",padx=(28,8))
        ttk.Entry(opts,textvariable=self.target,width=32).grid(row=9,column=3,sticky="w")
        ttk.Label(opts,text="Any language supported by the selected Ollama model.").grid(row=9,column=4,sticky="w")

        diar=ttk.LabelFrame(root,text="Optional local speaker diarization — no cloud / no Torch / no WhisperX",padding=10); diar.pack(fill="x",pady=(0,10))
        ttk.Checkbutton(diar,text="Enable speaker diarization",variable=self.diarization).grid(row=0,column=0,sticky="w")
        ttk.Label(diar,text="Segmentation ONNX model").grid(row=1,column=0,sticky="w")
        ttk.Entry(diar,textvariable=self.diarization_segmentation_model,width=80).grid(row=1,column=1,columnspan=3,sticky="ew")
        ttk.Label(diar,text="Speaker embedding ONNX model").grid(row=2,column=0,sticky="w")
        ttk.Entry(diar,textvariable=self.diarization_embedding_model,width=80).grid(row=2,column=1,columnspan=3,sticky="ew")
        ttk.Label(diar,text="Known speakers (0 = automatic clustering)").grid(row=3,column=0,sticky="w")
        ttk.Spinbox(diar,from_=0,to=50,textvariable=self.diarization_num_speakers,width=8).grid(row=3,column=1,sticky="w")
        ttk.Label(diar,text="Auto cluster threshold").grid(row=3,column=2,sticky="w")
        ttk.Spinbox(diar,from_=0.1,to=1.0,increment=0.05,textvariable=self.diarization_threshold,width=8).grid(row=3,column=3,sticky="w")
        diar.columnconfigure(1,weight=1)

        ttk.Label(opts,text="Cost").grid(row=10,column=2,sticky="w",padx=(28,8))
        ttk.Label(opts,text="$0 / €0 paid API — this application does not call OpenAI APIs").grid(row=10,column=3,columnspan=2,sticky="w")
        ttk.Label(opts,text="Output").grid(row=11,column=0,sticky="w",pady=(8,0))
        ttk.Entry(opts,textvariable=self.output).grid(row=11,column=1,columnspan=4,sticky="ew",pady=(8,0)); opts.columnconfigure(3,weight=1)

        actions=ttk.Frame(root); actions.pack(fill="x",pady=8)
        ttk.Button(actions,text="START",command=self.start).pack(side="left")
        ttk.Button(actions,text="Batch folder…",command=self.batch_folder).pack(side="left",padx=8)
        ttk.Button(actions,text="Library…",command=self.library).pack(side="left")
        ttk.Button(actions,text="Watch folder…",command=self.start_watch).pack(side="left",padx=8)
        ttk.Button(actions,text="Stop watch",command=self.stop_watch).pack(side="left")
        ttk.Button(actions,text="Open output folder",command=self.open_output).pack(side="left",padx=8)
        ttk.Label(actions,textvariable=self.status).pack(side="right")
        logbox=ttk.LabelFrame(root,text="Progress / errors",padding=8); logbox.pack(fill="both",expand=True)
        self.log=tk.Text(logbox,wrap="word",font=("Consolas",10)); self.log.pack(fill="both",expand=True)

    def combo(self,parent,label,var,values,row,column):
        ttk.Label(parent,text=label).grid(row=row,column=column,sticky="w",pady=3)
        ttk.Combobox(parent,textvariable=var,values=values,state="readonly",width=24).grid(row=row,column=column+1,sticky="w",pady=3)

    def refresh_ollama(self):
        def worker():
            try:
                models=OllamaTextProvider(load_config().ollama_url,"",self.logmsg).list_models()
                self.after(0,lambda:self.set_models(models))
            except Exception as exc: self.logmsg("Ollama model discovery failed: "+str(exc))
        threading.Thread(target=worker,daemon=True).start()

    def set_models(self,models):
        self.ollama_combo["values"]=models
        configured=load_config().ollama_model
        if configured in models: self.ollama_model.set(configured)
        elif models: self.ollama_model.set(models[0])
        self.update_advice(); self.logmsg(f"Ollama models available: {', '.join(models) if models else 'none'}")

    def update_advice(self):
        tier,note=model_advice(self.ollama_model.get()); self.advice.set(f"{tier.upper()}: {note}")

    def browse(self):
        path=filedialog.askopenfilename(title="Choose media",filetypes=[("Media","*.mp4 *.mkv *.mov *.avi *.webm *.m4v *.mp3 *.m4a *.wav *.flac *.ogg"),("All files","*.*")])
        if path: self.source.set(path)

    def browse_ytdlp(self):
        path=filedialog.askopenfilename(
            title="Select your existing standalone yt-dlp.exe",
            filetypes=[("yt-dlp executable","yt-dlp.exe"),("Executable","*.exe"),("All files","*.*")]
        )
        if path:
            self.ytdlp_path.set(path)
            self.logmsg("Using existing yt-dlp: " + path)

    def detect_ytdlp(self):
        try:
            command=find_ytdlp_command(self.ytdlp_path.get().strip(), self.logmsg)
            if len(command) == 1:
                self.ytdlp_path.set(command[0])
                self.logmsg("yt-dlp found: " + command[0])
            else:
                self.ytdlp_path.set("Python package (existing local yt-dlp)")
            return command
        except FileNotFoundError:
            self.logmsg("No yt-dlp executable/package was found automatically.")
            return []

    def detect_diarization_models(self):
        seg=ROOT/"models"/"diarization"/"sherpa-onnx-pyannote-segmentation-3-0"/"model.onnx"
        emb=ROOT/"models"/"diarization"/"3dspeaker_speech_eres2net_base_sv_zh-cn_3dspeaker_16k.onnx"
        if seg.is_file(): self.diarization_segmentation_model.set(str(seg))
        if emb.is_file(): self.diarization_embedding_model.set(str(emb))
        if seg.is_file() and emb.is_file(): self.logmsg("Local diarization models detected.")

    def start_watch(self):
        folder=filedialog.askdirectory(title="Choose watch folder")
        if not folder: return
        import threading as _threading
        model=self.ollama_model.get().strip()
        if not model: messagebox.showerror("Ollama required","No Ollama model is available."); return
        cfg=load_config(ROOT/"config.json")
        cfg.language=self.language.get().strip() or "auto"; cfg.local_model=self.model.get(); cfg.ollama_model=model
        cfg.hotwords=self.hotwords.get().strip(); cfg.word_timestamps=self.word_timestamps.get()
        cfg.analysis=self.analysis.get(); cfg.analysis_language=self.analysis_language.get().strip() or "source"
        cfg.search_query=self.search_query.get().strip(); cfg.top_terms=max(5,int(self.top_terms.get()))
        cfg.qa_question=self.qa_question.get().strip(); cfg.qa_language=self.qa_language.get().strip() or "English"
        cfg.target_language=self.target.get().strip() or "English"; cfg.translate_transcript=self.translate_transcript.get()
        cfg.diarization=self.diarization.get(); cfg.diarization_segmentation_model=self.diarization_segmentation_model.get().strip()
        cfg.diarization_embedding_model=self.diarization_embedding_model.get().strip(); cfg.diarization_num_speakers=max(0,int(self.diarization_num_speakers.get())); cfg.diarization_threshold=float(self.diarization_threshold.get())
        self.stop_watch(); self.watch_stop=_threading.Event()
        threading.Thread(target=watch_folder,args=(Path(folder),cfg,Path(self.output.get()),self.watch_stop,self.logmsg),daemon=True).start()
        self.logmsg("Watch started: "+folder)
    def stop_watch(self):
        if self.watch_stop: self.watch_stop.set(); self.watch_stop=None; self.logmsg("Watch stopped.")
    
    def batch_folder(self):
        folder=filedialog.askdirectory(title="Choose folder containing media to transcribe")
        if not folder: return
        model=self.ollama_model.get().strip()
        if not model:
            messagebox.showerror("Ollama required","No Ollama model is available."); return
        sources=discover_media(Path(folder))
        if not sources:
            messagebox.showinfo("No media","No supported audio/video files were found."); return
        cfg=load_config(ROOT/"config.json")
        cfg.language=self.language.get().strip() or "auto"; cfg.local_model=self.model.get(); cfg.ollama_model=model
        cfg.hotwords=self.hotwords.get().strip(); cfg.word_timestamps=self.word_timestamps.get()
        cfg.analysis=self.analysis.get(); cfg.analysis_language=self.analysis_language.get().strip() or "source"
        cfg.search_query=self.search_query.get().strip(); cfg.top_terms=max(5,int(self.top_terms.get()))
        cfg.qa_question=self.qa_question.get().strip(); cfg.qa_language=self.qa_language.get().strip() or "English"
        cfg.target_language=self.target.get().strip() or "English"; cfg.translate_transcript=self.translate_transcript.get()
        cfg.diarization=self.diarization.get(); cfg.diarization_segmentation_model=self.diarization_segmentation_model.get().strip()
        cfg.diarization_embedding_model=self.diarization_embedding_model.get().strip(); cfg.diarization_num_speakers=max(0,int(self.diarization_num_speakers.get())); cfg.diarization_threshold=float(self.diarization_threshold.get())
        self.status.set(f"Batch: {len(sources)} files")
        threading.Thread(target=lambda: self.batch_worker(sources,cfg),daemon=True).start()

    def batch_worker(self,sources,cfg):
        results=run_batch(sources,cfg,Path(self.output.get()),self.logmsg)
        self.logmsg(f"BATCH COMPLETE: {len(results)}/{len(sources)} succeeded")
        self.after(0,lambda:messagebox.showinfo("Batch complete",f"{len(results)} of {len(sources)} jobs completed."))

    def library(self):
        root=Path(self.output.get()); root.mkdir(parents=True,exist_ok=True); reindex(root)
        win=tk.Toplevel(self); win.title("SS Transcribe-Translate — Local Library"); win.geometry("1000x600")
        top=ttk.Frame(win,padding=10); top.pack(fill="x")
        q=tk.StringVar(); ttk.Entry(top,textvariable=q,width=70).pack(side="left",fill="x",expand=True)
        tree=ttk.Treeview(win,columns=("created","source","language","duration","speakers"),show="headings")
        for col,w in (("created",150),("source",500),("language",100),("duration",90),("speakers",80)):
            tree.heading(col,text=col.title()); tree.column(col,width=w)
        tree.pack(fill="both",expand=True,padx=10,pady=10)
        def refresh():
            for item in tree.get_children(): tree.delete(item)
            for row in search_jobs(root,q.get()):
                tree.insert("", "end", iid=row["job_dir"], values=(row["created"],row["source"],row["language"],f'{row["duration"]:.1f}s',row["speakers"]))
        ttk.Button(top,text="Search",command=refresh).pack(side="left",padx=8)
        def open_selected():
            sel=tree.selection()
            if not sel: return
            player=Path(sel[0])/"player.html"
            if player.exists(): webbrowser.open(player.as_uri())
            else: messagebox.showerror("Player missing","This job has no player.html.")
        ttk.Button(top,text="Open synchronized player",command=open_selected).pack(side="left")
        refresh()

    def logmsg(self,msg):
        self.after(0,lambda:(self.log.insert("end",msg+"\n"),self.log.see("end"),self.status.set(msg[:150])))

    def start(self):
        source=self.source.get().strip(); model=self.ollama_model.get().strip()
        if not source: messagebox.showerror("Input required","Choose a media file or paste a YouTube URL."); return
        if not model: messagebox.showerror("Ollama required","No Ollama model is available. Start Ollama and click Refresh models."); return
        cfg=load_config(ROOT/"config.json")
        cfg.language=self.language.get().strip() or "auto"; cfg.local_model=self.model.get(); cfg.ollama_model=model
        cfg.ytdlp_path=self.ytdlp_path.get().strip()
        if is_url(source):
            command = self.detect_ytdlp()
            if not command:
                path=filedialog.askopenfilename(
                    title="Select your existing standalone yt-dlp.exe",
                    filetypes=[("yt-dlp executable","yt-dlp.exe"),("Executable","*.exe"),("All files","*.*")]
                )
                if not path:
                    messagebox.showerror("yt-dlp required","No existing yt-dlp executable or Python package was found. Select your existing standalone yt-dlp.exe; the app will not install or modify it.")
                    return
                self.ytdlp_path.set(path)
            cfg.ytdlp_path=self.ytdlp_path.get().strip()
        cfg.hotwords=self.hotwords.get().strip(); cfg.word_timestamps=self.word_timestamps.get()
        cfg.analysis_language=self.analysis_language.get().strip() or "source"
        cfg.search_query=self.search_query.get().strip(); cfg.top_terms=max(5,int(self.top_terms.get()))
        cfg.qa_question=self.qa_question.get().strip(); cfg.qa_language=self.qa_language.get().strip() or "English"
        cfg.target_language=self.target.get().strip() or "English"; cfg.translate_transcript=self.translate_transcript.get(); cfg.analysis=self.analysis.get()
        cfg.diarization=self.diarization.get(); cfg.diarization_segmentation_model=self.diarization_segmentation_model.get().strip()
        cfg.diarization_embedding_model=self.diarization_embedding_model.get().strip(); cfg.diarization_num_speakers=max(0,int(self.diarization_num_speakers.get()))
        cfg.diarization_threshold=float(self.diarization_threshold.get())
        cfg.output_dir=self.output.get().strip() or str(ROOT / "output")
        save_local_config(cfg)
        if cfg.diarization and (not cfg.diarization_segmentation_model or not cfg.diarization_embedding_model):
            messagebox.showerror("Diarization models required","Provide both local ONNX model paths before enabling diarization."); return
        self.status.set("Running locally…"); threading.Thread(target=self.worker,args=(source,cfg),daemon=True).start()

    def worker(self,source,cfg):
        try:
            output=run_job(source,cfg,Path(self.output.get()),self.logmsg)
            self.after(0,lambda:messagebox.showinfo("Complete",f"Job finished:\n{output}"))
        except Exception as exc:
            self.logmsg("ERROR: "+str(exc)); self.after(0,lambda:messagebox.showerror("Processing failed",str(exc))); self.after(0,lambda:self.status.set("Failed"))

    def open_output(self):
        import os
        path=Path(self.output.get()); path.mkdir(parents=True,exist_ok=True); os.startfile(path)

if __name__=="__main__":
    App().mainloop()
