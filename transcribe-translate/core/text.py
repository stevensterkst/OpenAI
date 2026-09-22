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

class OllamaTextProvider:
    def __init__(self, url: str, model: str, progress: Progress = print):
        self.url = url.rstrip("/")
        self.model = model
        self.progress = progress

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

    def translate(self, text: str, target_language: str) -> str:
        outputs = []
        parts = chunk_text(text)
        for index, part in enumerate(parts, 1):
            self.progress(f"Local translation: part {index}/{len(parts)} -> {target_language}")
            outputs.append(self._call(
                f"Translate this transcript faithfully into {target_language}. "
                "Do not summarize. Preserve names, numbers, dates, legal/voting terminology, "
                "uncertainty, negation and speaker meaning. Do not add commentary.\n\n"
                f"{part}"
            ))
        return "\n\n".join(outputs)

    def summarize(self, text: str, language: str) -> str:
        self.progress(f"Local summary: {language}")
        return self._call(
            f"Summarize this transcript in {language}. Preserve concrete decisions, proposals, "
            "objections, votes, named people, dates, amounts and procedural issues. "
            "Do not invent facts or infer unstated conclusions.\n\n"
            f"{text}"
        )
