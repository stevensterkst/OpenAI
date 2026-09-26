from __future__ import annotations
import json
import csv
from dataclasses import asdict
from pathlib import Path
from .asr import Transcript

def _ts(seconds: float, comma: bool = True) -> str:
    seconds = max(0.0, float(seconds))
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds - int(seconds)) * 1000))
    if ms == 1000:
        s += 1
        ms = 0
    sep = "," if comma else "."
    return f"{h:02d}:{m:02d}:{s:02d}{sep}{ms:03d}"

def _body(segment) -> str:
    return f"[{segment.speaker}] {segment.text}" if segment.speaker else segment.text

def write_transcript_outputs(transcript: Transcript, directory: Path, source: str) -> None:
    """Persist the transcript immediately, before any optional AI stage runs."""
    directory.mkdir(parents=True, exist_ok=True)
    transcript_lines=["# Transcript", "", f"**Language:** {transcript.language or 'detected'}", ""]
    for segment in transcript.segments:
        transcript_lines.append(
            f"- **{_ts(segment.start, False)} → {_ts(segment.end, False)}** {_body(segment)}"
        )
    (directory / "original.txt").write_text(
        "\n".join(_body(s) for s in transcript.segments) + "\n", encoding="utf-8"
    )
    (directory / "transcript.md").write_text(
        "\n".join(transcript_lines) + "\n", encoding="utf-8"
    )
    with (directory / "segments.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        writer=csv.writer(fh)
        writer.writerow(["start","end","speaker","text"])
        for s in transcript.segments:
            writer.writerow([s.start,s.end,s.speaker or "",s.text])
    payload = {
        "source": source, "language": transcript.language, "backend": transcript.backend,
        "text": transcript.text, "model": transcript.model,
        "word_timestamps": any(bool(s.words) for s in transcript.segments),
        "speaker_labels": any(bool(s.speaker) for s in transcript.segments),
        "segments": [asdict(s) for s in transcript.segments],
    }
    (directory / "original.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    srt=[]; vtt=["WEBVTT",""]
    for i, segment in enumerate(transcript.segments, 1):
        body=_body(segment)
        srt.extend([str(i), f"{_ts(segment.start)} --> {_ts(segment.end)}", body, ""])
        vtt.extend([f"{_ts(segment.start, False)} --> {_ts(segment.end, False)}", body, ""])
    (directory / "original.srt").write_text("\n".join(srt), encoding="utf-8")
    (directory / "original.vtt").write_text("\n".join(vtt), encoding="utf-8")
    write_output_file_index(directory, source)

def write_source_summary(summary: str, source_language: str, directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "source_summary.md").write_text(
        f"# Source-language summary ({source_language})\n\n{summary.strip()}\n",
        encoding="utf-8"
    )

def write_english_summary(summary: str, directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "english_summary.md").write_text(
        "# English summary (translation of source-language summary)\n\n"
        + summary.strip() + "\n", encoding="utf-8"
    )

OUTPUT_FILE_DESCRIPTIONS = {
    "original.txt": ("Literal Source Transcript In Spoken Language", "The complete literal transcript of spoken content, preserving source language without LLM translation or paraphrase."),
    "original.json": ("Machine Readable Source Transcript With Provenance", "Structured source transcript containing language, model, segments, timestamps, speakers, source reference, and provenance metadata."),
    "original.srt": ("Timestamped Source Transcript For Subtitle Players", "Standard SRT subtitle file containing the original spoken transcript with precise segment start and end timestamps."),
    "original.vtt": ("Timestamped Source Transcript For Web Video Players", "Standard WebVTT subtitle file containing the original spoken transcript and synchronized segment timestamps."),
    "transcript.md": ("Human Readable Source Transcript With Timestamps", "Readable Markdown transcript showing detected language, chronological timestamps, and the literal spoken text."),
    "segments.csv": ("Spreadsheet Of Every Transcript Segment And Speaker", "CSV table containing each transcript segment's start time, end time, speaker label, and literal spoken text."),
    "source_summary.md": ("Concise Factual Summary In The Original Spoken Language", "Source-language summary containing only material facts, arguments, questions, actions, dates, names, decisions, uncertainties, and unresolved points evidenced by the transcript."),
    "english_summary.md": ("Faithful English Translation Of The Source Language Summary", "English translation of the approved source-language summary, without independently inventing or changing its factual content."),
    "translation.txt": ("Complete Optional Translation Of The Original Source Transcript", "Full optional translation of the literal source transcript into the selected target language without summarizing or omitting substantive details."),
    "analysis_source.md": ("Source Grounded Analysis Preserving Original Language Evidence", "Optional evidence-grounded analysis in the original language with timestamps, topics, proposals, decisions, objections, contradictions, and unresolved issues."),
    "analysis.md": ("Translated Source Grounded Analysis For Human Review", "Optional analysis translated into the selected analysis language while remaining grounded exclusively in the source evidence."),
    "search_report.json": ("Structured Search And Knowledge Extraction Report", "Machine-readable report containing requested search results and extracted terms associated with the processed transcript."),
    "qa.md": ("Transcript Grounded Answer To The User Question", "Optional answer to the supplied question using only transcript evidence, with supporting timestamps and explicit uncertainty."),
    "output_manifest.json": ("Complete Output Inventory With Exact File Contents", "Machine-readable inventory identifying every generated file, its exact purpose, whether it is optional, and the source job."),
    "FILE_INDEX.md": ("Human Readable Index Explaining Every Generated Output File", "Human-readable index giving a clear title and a concise ten-plus-word description of every file generated for this job."),
}

def write_output_file_index(directory: Path, source: str) -> None:
    lines = [
        "# Generated Output Files — Exact Contents And Purpose",
        "",
        f"Source job: {source}",
        "",
        "Every listed file has a specific purpose; optional files appear only when their feature is enabled.",
        "",
    ]
    for name, (title, description) in OUTPUT_FILE_DESCRIPTIONS.items():
        lines.append(f"## {title}")
        lines.append(f"**File:** `{name}`")
        lines.append(f"**Contains:** {description}")
        lines.append("")
    (directory / "FILE_INDEX.md").write_text("\n".join(lines), encoding="utf-8")

def write_job_error(stage: str, error: str, directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "job_error.md").write_text(
        f"# Job stopped during: {stage}\n\n{error.strip()}\n",
        encoding="utf-8"
    )

def write_outputs(
    transcript: Transcript, translation: str, source_summary: str,
    english_summary: str, analysis_source: str, analysis_translated: str,
    search_report: dict, qa_answer: str, qa_question: str, qa_language: str,
    directory: Path, source: str, translated: bool = False, target_language: str = "",
    analysis_created: bool = False, analysis_language: str = "source",
) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    transcript_lines=["# Transcript", "", f"**Language:** {transcript.language or 'detected'}", ""]
    for s in transcript.segments:
        transcript_lines.append(f"- **{_ts(s.start, False)} → {_ts(s.end, False)}** {_body(s)}")
    (directory / "original.txt").write_text("\n".join(_body(s) for s in transcript.segments) + "\n", encoding="utf-8")
    (directory / "transcript.md").write_text("\n".join(transcript_lines) + "\n", encoding="utf-8")
    with (directory / "segments.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        writer=csv.writer(fh); writer.writerow(["start","end","speaker","text"])
        for s in transcript.segments: writer.writerow([s.start,s.end,s.speaker or "",s.text])
    (directory / "source_summary.md").write_text(
        f"# Source-language summary ({transcript.language or 'detected language'})\n\n{source_summary}\n", encoding="utf-8")
    (directory / "english_summary.md").write_text(
        "# English summary (translation of source-language summary)\n\n" + f"{english_summary}\n", encoding="utf-8")

    if analysis_created:
        (directory / "analysis_source.md").write_text(
            "# Source-grounded analysis — original language\n\n" + f"{analysis_source}\n", encoding="utf-8")
        (directory / "analysis.md").write_text(
            f"# Source-grounded analysis — {analysis_language}\n\n"
            f"{analysis_translated if analysis_translated else analysis_source}\n", encoding="utf-8")

    (directory / "search_report.json").write_text(json.dumps(search_report, ensure_ascii=False, indent=2), encoding="utf-8")
    if qa_question.strip():
        (directory / "qa.md").write_text(
            f"# Transcript-grounded Q&A\n\n**Question:** {qa_question}\n\n"
            f"**Answer language:** {qa_language}\n\n{qa_answer}\n", encoding="utf-8")
    if translated:
        (directory / "translation.txt").write_text(translation + "\n", encoding="utf-8")

    payload = {
        "source": source, "language": transcript.language, "backend": transcript.backend, "text": transcript.text,
        "model": transcript.model, "word_timestamps": any(bool(s.words) for s in transcript.segments),
        "speaker_labels": any(bool(s.speaker) for s in transcript.segments),
        "segments": [asdict(s) for s in transcript.segments],
    }
    (directory / "original.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    srt: list[str] = []
    vtt: list[str] = ["WEBVTT", ""]
    for i, segment in enumerate(transcript.segments, 1):
        body = _body(segment)
        srt.extend([str(i), f"{_ts(segment.start)} --> {_ts(segment.end)}", body, ""])
        vtt.extend([f"{_ts(segment.start, False)} --> {_ts(segment.end, False)}", body, ""])
    (directory / "original.srt").write_text("\n".join(srt), encoding="utf-8")
    (directory / "original.vtt").write_text("\n".join(vtt), encoding="utf-8")

    write_output_file_index(directory, source)

    manifest = {
        "translation_created": translated, "translation_target": target_language if translated else None,
        "analysis_created": analysis_created, "analysis_language": analysis_language if analysis_created else None,
        "search_report_created": True, "qa_created": bool(qa_question.strip()),
        "word_timestamps_available": any(bool(s.words) for s in transcript.segments),
        "speaker_labels_available": any(bool(s.speaker) for s in transcript.segments),
        "primary_outputs": ["original.txt","original.json","original.srt","original.vtt","transcript.md","segments.csv","source_summary.md","english_summary.md"],
        "analysis_outputs": (["analysis_source.md","analysis.md","search_report.json"] if analysis_created else ["search_report.json"]),
        "optional_outputs": ([ "translation.txt" ] if translated else []) + ([ "qa.md" ] if qa_question.strip() else []),
        "file_descriptions": {name: {"title": pair[0], "description": pair[1]} for name, pair in OUTPUT_FILE_DESCRIPTIONS.items() if (directory / name).exists()},
    }
    (directory / "output_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
