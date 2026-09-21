from __future__ import annotations
import json
from typing import Callable
import requests

from .config import AppConfig, require_openai_key

Progress = Callable[[str], None]

def chunks(text: str, size: int = 12000) -> list[str]:
    text = text.strip()
    if len(text) <= size:
        return [text]
    result, current = [], []
    length = 0
    for paragraph in text.split("\n"):
        if length + len(paragraph) + 1 > size and current:
            result.append("\n".join(current))
            current, length = [], 0
        current.append(paragraph)
        length += len(paragraph) + 1
    if current:
        result.append("\n".join(current))
    return result

class TextProvider:
    def translate(self, text: str, target_language: str) -> str:
        raise NotImplementedError
    def summarize(self, text: str, language: str) -> str:
        raise NotImplementedError

class OllamaTextProvider(TextProvider):
    def __init__(self, url: str, model: str, progress: Progress = print):
        self.url = url.rstrip("/")
        self.model = model
        self.progress = progress

    def _call(self, prompt: str) -> str:
        r = requests.post(f"{self.url}/api/chat", json={
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }, timeout=3600)
        if r.status_code >= 400:
            raise RuntimeError(f"Ollama request failed ({r.status_code}): {r.text[:2000]}")
        return str(r.json().get("message", {}).get("content", "")).strip()

    def translate(self, text: str, target_language: str) -> str:
        parts = [self._call(f"Translate the following transcript faithfully into {target_language}. Preserve names, numbers, voting terms and uncertainty. Do not summarize.\n\n{text_part}") for text_part in chunks(text)]
        return "\n\n".join(parts)

    def summarize(self, text: str, language: str) -> str:
        return self._call(f"Summarize this meeting transcript in {language}. Preserve decisions, proposals, objections, votes, named speakers and agenda/procedural issues. Do not invent facts.\n\n{text}")

class OpenAITextProvider(TextProvider):
    def __init__(self, model: str, progress: Progress = print):
        self.model = model
        self.progress = progress
        self.key = require_openai_key()

    def _call(self, prompt: str) -> str:
        r = requests.post(
            "https://api.openai.com/v1/responses",
            headers={"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"},
            json={"model": self.model, "input": prompt},
            timeout=3600,
        )
        if r.status_code >= 400:
            raise RuntimeError(f"OpenAI text request failed ({r.status_code}): {r.text[:3000]}")
        data = r.json()
        if data.get("output_text"):
            return str(data["output_text"]).strip()
        pieces = []
        for item in data.get("output", []):
            for content in item.get("content", []):
                if content.get("type") == "output_text":
                    pieces.append(content.get("text", ""))
        return "".join(pieces).strip()

    def translate(self, text: str, target_language: str) -> str:
        return "\n\n".join(self._call(
            f"Translate this transcript faithfully into {target_language}. Preserve names, numbers, voting terms and uncertainty. Do not summarize.\n\n{part}"
        ) for part in chunks(text))

    def summarize(self, text: str, language: str) -> str:
        return self._call(f"Summarize this meeting transcript in {language}. Preserve decisions, proposals, objections, votes, named speakers and agenda/procedural issues. Do not invent facts.\n\n{text}")
