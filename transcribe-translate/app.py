from __future__ import annotations
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from core.config import ROOT, load_config
from core.pipeline import run_job

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SS Transcribe-Translate — Free Local")
        self.geometry("980x720")
        self.minsize(850, 620)
        self.source = tk.StringVar()
        self.language = tk.StringVar(value="auto")
        self.model = tk.StringVar(value="small")
        self.target = tk.StringVar(value="en")
        self.output = tk.StringVar(value=str(ROOT / "output"))
        self.status = tk.StringVar(value="Ready — local transcription + Ollama; no API")
        self._build()

    def _build(self):
        root = ttk.Frame(self, padding=16)
        root.pack(fill="both", expand=True)
        ttk.Label(root, text="SS Transcribe-Translate", font=("Segoe UI", 18, "bold")).pack(anchor="w")
        ttk.Label(root, text="100% local processing: faster-whisper → Ollama").pack(anchor="w", pady=(0, 14))

        box = ttk.LabelFrame(root, text="Input", padding=10)
        box.pack(fill="x")
        ttk.Label(box, text="Local media file or YouTube URL").grid(row=0, column=0, sticky="w")
        ttk.Entry(box, textvariable=self.source).grid(row=1, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(box, text="Browse…", command=self.browse).grid(row=1, column=1)
        box.columnconfigure(0, weight=1)

        opts = ttk.LabelFrame(root, text="Local processing", padding=10)
        opts.pack(fill="x", pady=10)
        self.combo(opts, "Source language", self.language, ["auto", "ca", "es", "en", "fr", "de", "it"], 0)
        self.combo(opts, "Whisper model", self.model, ["tiny", "base", "small", "medium", "large-v3"], 1)
        self.combo(opts, "Target language", self.target, ["en", "ca", "es", "fr", "de", "it"], 2)
        ttk.Label(opts, text="Ollama model").grid(row=0, column=2, sticky="w", padx=12)
        ttk.Label(opts, text=load_config().ollama_model).grid(row=0, column=3, sticky="w")
        ttk.Label(opts, text="Cost").grid(row=1, column=2, sticky="w", padx=12)
        ttk.Label(opts, text="€0 / $0 API — no OpenAI API call").grid(row=1, column=3, sticky="w")
        ttk.Label(opts, text="Output").grid(row=2, column=2, sticky="w", padx=12)
        ttk.Entry(opts, textvariable=self.output).grid(row=2, column=3, sticky="ew", padx=12)
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

    def combo(self, parent, label, var, values, row):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=3)
        ttk.Combobox(parent, textvariable=var, values=values, state="readonly", width=24).grid(
            row=row, column=1, sticky="w", pady=3
        )

    def browse(self):
        path = filedialog.askopenfilename(
            title="Choose media",
            filetypes=[("Media", "*.mp4 *.mkv *.mov *.avi *.webm *.m4v *.mp3 *.m4a *.wav *.flac *.ogg"),
                       ("All files", "*.*")]
        )
        if path:
            self.source.set(path)

    def logmsg(self, msg):
        self.after(0, lambda: (
            self.log.insert("end", msg + "\n"),
            self.log.see("end"),
            self.status.set(msg[:150])
        ))

    def start(self):
        source = self.source.get().strip()
        if not source:
            messagebox.showerror("Input required", "Choose a media file or paste a YouTube URL.")
            return
        cfg = load_config(ROOT / "config.json")
        cfg.language = self.language.get()
        cfg.local_model = self.model.get()
        cfg.target_language = self.target.get()
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
