from __future__ import annotations
from typing import Callable
import requests

Progress = Callable[[str], None]

def chunk_text(text: str, size: int = 10000) -> list[str]:
    text = text.strip()
    if not text:
        return [""]
    if len(text) <= size:
        return [text]
    parts: list[str] = []
    current: list[str] = []
    length = 0
    for paragraph in text.split("\n"):
        extra = len(paragraph) + 1
        if current and length + extra > size:
            parts.append("\n".join(current))
            current, length = [], 0
        current.append(paragraph)
        length += extra
    if current:
        parts.append("\n".join(current))
    return parts

MODEL_HINTS = {
    "phi4-mini": ("precision", "Strongest of the currently known local choices for careful translation/analysis; slower."),
    "qwen3": ("balanced", "Good multilingual/speed compromise; usually much faster than the larger Phi model."),
    "llama3.2": ("fast", "Small and fast; useful when turnaround matters more than maximum translation precision."),
    "gemma3": ("fast", "Small and fast; useful for quick summaries and lightweight translation."),
}

def model_advice(model: str) -> tuple[str, str]:
    name = model.lower()
    for key, value in MODEL_HINTS.items():
        if key in name:
            return value
    return ("unknown", "No preset recommendation; benchmark this model on your material before relying on it.")

class OllamaTextProvider:
    def __init__(self, url: str, model: str, progress: Progress = print):
        self.url = url.rstrip("/")
        self.model = model
        self.progress = progress

    def list_models(self) -> list[str]:
        try:
            response = requests.get(f"{self.url}/api/tags", timeout=10)
            response.raise_for_status()
            return [str(m.get("name")) for m in response.json().get("models", []) if m.get("name")]
        except requests.RequestException as exc:
            raise RuntimeError(f"Cannot reach Ollama at {self.url}: {exc}") from exc

    def _call(self, prompt: str) -> str:
        response = requests.post(
            f"{self.url}/api/chat",
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "options": {"temperature": 0},
            },
            timeout=3600,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"Ollama request failed ({response.status_code}): {response.text[:3000]}")
        content = str(response.json().get("message", {}).get("content", "")).strip()
        if not content:
            raise RuntimeError("Ollama returned an empty response.")
        return content

    def summarize_source(self, transcript: str, source_language: str) -> str:
        self.progress(f"Source-language summary: {source_language} [{self.model}]")
        return self._call(
            f"Produce a comprehensive summary in {source_language} of the transcript below. "
            "This is the PRIMARY summary. Base it only on the transcript. Preserve all material facts, "
            "important arguments, decisions, proposals, objections, questions, named people or organisations, "
            "dates, amounts, conditions, votes or voting positions when stated, action items, deadlines, "
            "uncertainties and unresolved issues. Do not invent, infer, or silently omit material information. "
            "Keep the structure useful for later knowledge-management and legal/meeting review.\n\n"
            f"{transcript}"
        )

    def translate(self, text: str, target_language: str, purpose: str = "transcript") -> str:
        outputs = []
        parts = chunk_text(text)
        for index, part in enumerate(parts, 1):
            self.progress(f"Local {purpose} translation: part {index}/{len(parts)} -> {target_language} [{self.model}]")
            outputs.append(self._call(
                f"Translate this {purpose} faithfully into {target_language}. "
                "Do not summarize. Preserve names, numbers, dates, legal/voting terminology, "
                "uncertainty, negation, speaker meaning and all substantive details. Do not add commentary.\n\n"
                f"{part}"
            ))
        return "\n\n".join(outputs)

    def translate_summary_to_english(self, source_summary: str, source_language: str) -> str:
        return self.translate(source_summary, "English", purpose=f"{source_language} summary")
