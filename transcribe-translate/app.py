from __future__ import annotations
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from core.config import ROOT, load_config
from core.pipeline import run_job
from core.text import OllamaTextProvider, model_advice

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SS Transcribe-Translate — Free Local")
        self.geometry("1180x900")
        self.minsize(1000, 800)
        self.source = tk.StringVar()
        self.language = tk.StringVar(value="auto")
        self.model = tk.StringVar(value="small")
        self.ollama_model = tk.StringVar()
        self.target = tk.StringVar(value="English")
        self.analysis_language = tk.StringVar(value="source")
        self.hotwords = tk.StringVar()
        self.search_query = tk.StringVar()
        self.top_terms = tk.IntVar(value=30)
        self.word_timestamps = tk.BooleanVar(value=True)
        self.translate_transcript = tk.BooleanVar(value=False)
        self.analysis = tk.BooleanVar(value=True)
        self.output = tk.StringVar(value=str(ROOT / "output"))
        self.status = tk.StringVar(value="Ready — source transcript + source summary are primary; no paid API")
        self.advice = tk.StringVar(value="")
        self._build()
        self.refresh_ollama()

    def _build(self):
        root = ttk.Frame(self, padding=16)
        root.pack(fill="both", expand=True)
        ttk.Label(root, text="SS Transcribe-Translate", font=("Segoe UI", 18, "bold")).pack(anchor="w")
        ttk.Label(root, text="PRIMARY: local source transcript + source-language summary. English summary is only a translation. Full translation and analysis are optional.").pack(anchor="w", pady=(0, 14))

        box = ttk.LabelFrame(root, text="Input", padding=10)
        box.pack(fill="x")
        ttk.Label(box, text="Local media file or YouTube URL").grid(row=0, column=0, sticky="w")
        ttk.Entry(box, textvariable=self.source).grid(row=1, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(box, text="Browse…", command=self.browse).grid(row=1, column=1)
        box.columnconfigure(0, weight=1)

        opts = ttk.LabelFrame(root, text="Processing", padding=10)
        opts.pack(fill="x", pady=10)
        self.combo(opts, "Source language", self.language, ["auto","ca","es","en","fr","de","it","nl","pt","pl","ru","uk"], 0, 0)
        self.combo(opts, "Whisper model", self.model, ["tiny","base","small","medium","large-v3"], 1, 0)

        ttk.Label(opts, text="Ollama model").grid(row=0, column=2, sticky="w", padx=(28, 8))
        self.ollama_combo = ttk.Combobox(opts, textvariable=self.ollama_model, state="readonly", width=32)
        self.ollama_combo.grid(row=0, column=3, sticky="w")
        self.ollama_combo.bind("<<ComboboxSelected>>", lambda _e: self.update_advice())
        ttk.Button(opts, text="Refresh models", command=self.refresh_ollama).grid(row=0, column=4, padx=8)

        ttk.Label(opts, text="Recommendation").grid(row=1, column=2, sticky="w", padx=(28, 8))
        ttk.Label(opts, textvariable=self.advice, wraplength=600).grid(row=1, column=3, columnspan=2, sticky="w")

        ttk.Label(opts, text="Vocabulary / names").grid(row=2, column=0, sticky="w", pady=(8, 3))
        ttk.Entry(opts, textvariable=self.hotwords, width=48).grid(row=2, column=1, sticky="w", pady=(8, 3))
        ttk.Label(opts, text="Comma-separated names, organisations or specialist terms to bias recognition.", wraplength=520).grid(row=2, column=2, columnspan=3, sticky="w", padx=(28, 0), pady=(8, 3))

        ttk.Checkbutton(opts, text="Keep word-level timestamps", variable=self.word_timestamps).grid(row=3, column=0, columnspan=2, sticky="w", pady=3)
        ttk.Checkbutton(opts, text="Run source-grounded meeting/evidence analysis", variable=self.analysis).grid(row=4, column=0, columnspan=2, sticky="w", pady=3)

        ttk.Label(opts, text="Analysis output language").grid(row=4, column=2, sticky="w", padx=(28, 8))
        ttk.Entry(opts, textvariable=self.analysis_language, width=32).grid(row=4, column=3, sticky="w")
        ttk.Label(opts, text="source = original language; otherwise any Ollama-supported language.").grid(row=4, column=4, sticky="w")

        ttk.Label(opts, text="Search transcript").grid(row=5, column=0, sticky="w", pady=3)
        ttk.Entry(opts, textvariable=self.search_query, width=48).grid(row=5, column=1, sticky="w")
        ttk.Label(opts, text="Exact text search; results include timestamps. Counts/top terms are language-neutral.", wraplength=520).grid(row=5, column=2, columnspan=3, sticky="w", padx=(28,0))

        ttk.Label(opts, text="Top terms").grid(row=6, column=0, sticky="w")
        ttk.Spinbox(opts, from_=5, to=200, textvariable=self.top_terms, width=8).grid(row=6, column=1, sticky="w")

        ttk.Checkbutton(opts, text="Also translate the FULL source transcript", variable=self.translate_transcript).grid(row=7, column=0, columnspan=2, sticky="w", pady=3)
        ttk.Label(opts, text="Target language").grid(row=7, column=2, sticky="w", padx=(28, 8))
        ttk.Entry(opts, textvariable=self.target, width=32).grid(row=7, column=3, sticky="w")
        ttk.Label(opts, text="Any language supported by the selected Ollama model.").grid(row=7, column=4, sticky="w")

        ttk.Label(opts, text="Cost").grid(row=8, column=2, sticky="w", padx=(28, 8))
        ttk.Label(opts, text="$0 / €0 paid API — this application does not call OpenAI APIs").grid(row=8, column=3, columnspan=2, sticky="w")

        ttk.Label(opts, text="Output").grid(row=9, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(opts, textvariable=self.output).grid(row=9, column=1, columnspan=4, sticky="ew", pady=(8, 0))
        opts.columnconfigure(3, weight=1)

        actions = ttk.Frame(root)
        actions.pack(fill="x", pady=8)
        ttk.Button(actions, text="START", command=self.start).pack(side="left")
        ttk.Button(actions, text="Open output folder", command=self.open_output).pack(side="left", padx=8)
        ttk.Label(actions, textvariable=self.status).pack(side="right")

        logbox = ttk.LabelFrame(root, text="Progress / errors", padding=8)
        logbox.pack(fill="both", expand=True)
        self.log = tk.Text(logbox, wrap="word", font=("Consolas", 10))
        self.log.pack(fill="both", expand=True)

    def combo(self, parent, label, var, values, row, column):
        ttk.Label(parent, text=label).grid(row=row, column=column, sticky="w", pady=3)
        ttk.Combobox(parent, textvariable=var, values=values, state="readonly", width=24).grid(row=row, column=column + 1, sticky="w", pady=3)

    def refresh_ollama(self):
        def worker():
            try:
                models = OllamaTextProvider(load_config().ollama_url, "", self.logmsg).list_models()
                self.after(0, lambda: self.set_models(models))
            except Exception as exc:
                self.logmsg("Ollama model discovery failed: " + str(exc))
        threading.Thread(target=worker, daemon=True).start()

    def set_models(self, models):
        self.ollama_combo["values"] = models
        configured = load_config().ollama_model
        if configured in models:
            self.ollama_model.set(configured)
        elif models:
            self.ollama_model.set(models[0])
        self.update_advice()
        self.logmsg(f"Ollama models available: {', '.join(models) if models else 'none'}")

    def update_advice(self):
        tier, note = model_advice(self.ollama_model.get())
        self.advice.set(f"{tier.upper()}: {note}")

    def browse(self):
        path = filedialog.askopenfilename(title="Choose media", filetypes=[("Media", "*.mp4 *.mkv *.mov *.avi *.webm *.m4v *.mp3 *.m4a *.wav *.flac *.ogg"), ("All files", "*.*")])
        if path:
            self.source.set(path)

    def logmsg(self, msg):
        self.after(0, lambda: (self.log.insert("end", msg + "\n"), self.log.see("end"), self.status.set(msg[:150])))

    def start(self):
        source = self.source.get().strip()
        model = self.ollama_model.get().strip()
        if not source:
            messagebox.showerror("Input required", "Choose a media file or paste a YouTube URL.")
            return
        if not model:
            messagebox.showerror("Ollama required", "No Ollama model is available. Start Ollama and click Refresh models.")
            return
        cfg = load_config(ROOT / "config.json")
        cfg.language = self.language.get()
        cfg.local_model = self.model.get()
        cfg.ollama_model = model
        cfg.hotwords = self.hotwords.get().strip()
        cfg.word_timestamps = self.word_timestamps.get()
        cfg.analysis_language = self.analysis_language.get().strip() or "source"
        cfg.search_query = self.search_query.get().strip()
        cfg.top_terms = max(5, int(self.top_terms.get()))
        cfg.target_language = self.target.get().strip() or "English"
        cfg.translate_transcript = self.translate_transcript.get()
        cfg.analysis = self.analysis.get()
        self.status.set("Running locally…")
        threading.Thread(target=self.worker, args=(source, cfg), daemon=True).start()

    def worker(self, source, cfg):
        try:
            output = run_job(source, cfg, Path(self.output.get()), self.logmsg)
            self.after(0, lambda: messagebox.showinfo("Complete", f"Job finished:\n{output}"))
        except Exception as exc:
            self.logmsg("ERROR: " + str(exc))
            self.after(0, lambda: messagebox.showerror("Processing failed", str(exc)))
            self.after(0, lambda: self.status.set("Failed"))

    def open_output(self):
        import os
        path = Path(self.output.get())
        path.mkdir(parents=True, exist_ok=True)
        os.startfile(path)

if __name__ == "__main__":
    App().mainloop()
