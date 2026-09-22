from __future__ import annotations
from datetime import datetime
from pathlib import Path
import json, shutil
from typing import Callable
from .asr import OpenAIASR
from .config import AppConfig
from .media import chunk_audio, download_youtube, extract_audio, is_url
from .outputs import write_transcript
from .translate import OllamaTextProvider

LANGUAGE_NAMES={"ca":"Catalan","es":"Spanish","en":"English","fr":"French","de":"German","it":"Italian"}
def run_job(source:str,cfg:AppConfig,output_root:Path,progress:Callable[[str],None]=print)->Path:
    stamp=datetime.now().strftime("%Y-%m-%d_%H%M%S"); job=output_root/f"{stamp}_{'youtube' if is_url(source) else Path(source).stem[:80]}"; work=job/"_work"; work.mkdir(parents=True,exist_ok=True)
    if is_url(source): progress("Downloading YouTube media..."); media=download_youtube(source,work)
    else:
        media=Path(source).expanduser().resolve()
        if not media.exists(): raise FileNotFoundError(media)
        shutil.copy2(media,work/media.name); media=work/media.name
    progress("Extracting audio..."); audio=extract_audio(media,work/"audio.wav")
    transcript=OpenAIASR("gpt-4o-transcribe",cfg.language,cfg.diarize,progress).transcribe_chunks(chunk_audio(audio,work/"chunks"))
    write_transcript(transcript,job,"original")
    provider=OllamaTextProvider(cfg.ollama_url,cfg.ollama_model,progress)
    target=LANGUAGE_NAMES.get(cfg.target_language,cfg.target_language); source_name=LANGUAGE_NAMES.get(transcript.language or cfg.language,"the source language")
    progress("Translating..."); translation=provider.translate(transcript.text,target); (job/f"{cfg.target_language}.txt").write_text(translation,encoding="utf-8")
    progress("Summarising..."); s1=provider.summarize(transcript.text,source_name); s2=provider.summarize(translation,target)
    (job/"bilingual-summary.md").write_text(f"# {source_name} summary\n\n{s1}\n\n# {target} summary\n\n{s2}\n",encoding="utf-8")
    (job/"summary.md").write_text(s2+"\n",encoding="utf-8")
    (job/"job.json").write_text(json.dumps({"source":source,"asr":"OpenAI","asr_model":transcript.model,"language":transcript.language,"translation":target,"diarization":cfg.diarize,"text_provider":"Ollama","text_model":cfg.ollama_model},ensure_ascii=False,indent=2),encoding="utf-8")
    progress("COMPLETE: "+str(job)); return job
