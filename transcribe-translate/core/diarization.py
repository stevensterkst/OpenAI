from __future__ import annotations
from pathlib import Path
import wave

def diarize_audio(
    audio_path: Path,
    segmentation_model: str,
    embedding_model: str,
    num_speakers: int = 0,
    threshold: float = 0.5,
    progress=print,
) -> list[dict]:
    try:
        import sherpa_onnx
    except ImportError as exc:
        raise RuntimeError(
            "Speaker diarization is enabled but sherpa-onnx is not installed. "
            "Install the local sherpa-onnx package only; this feature does not use Torch, WhisperX, "
            "a cloud service or a paid API."
        ) from exc

    seg = Path(segmentation_model)
    emb = Path(embedding_model)
    if not seg.is_file():
        raise RuntimeError(f"Speaker segmentation model not found: {seg}")
    if not emb.is_file():
        raise RuntimeError(f"Speaker embedding model not found: {emb}")

    with wave.open(str(audio_path), "rb") as wf:
        if wf.getnchannels() != 1 or wf.getsampwidth() != 2:
            raise RuntimeError("Diarization expects the application's 16 kHz mono PCM WAV.")
        sample_rate = wf.getframerate()
        raw = wf.readframes(wf.getnframes())

    import numpy as np
    samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0

    config = sherpa_onnx.OfflineSpeakerDiarizationConfig()
    config.segmentation.pyannote.model = str(seg)
    config.segmentation.pyannote.window_shift_ratio = 0.1
    config.embedding.model = str(emb)
    if num_speakers > 0:
        config.clustering.num_clusters = int(num_speakers)
    else:
        config.clustering.threshold = float(threshold)
    config.min_duration_on = 0.3
    config.min_duration_off = 0.5

    if not config.validate():
        raise RuntimeError("Invalid sherpa-onnx diarization configuration or missing model files.")

    diarizer = sherpa_onnx.OfflineSpeakerDiarization(config)
    if sample_rate != diarizer.sample_rate:
        raise RuntimeError(
            f"Diarization model expects {diarizer.sample_rate} Hz; audio is {sample_rate} Hz."
        )

    progress("Local speaker diarization: offline ONNX segmentation + embeddings + clustering")
    result = diarizer.process(samples)
    result = result.sort_by_start_time()
    return [
        {"start": float(x.start), "end": float(x.end), "speaker": f"Speaker {int(x.speaker) + 1}"}
        for x in result
    ]

def assign_speakers(segments, diarization_segments: list[dict]) -> None:
    for segment in segments:
        best_speaker = None
        best_overlap = 0.0
        for d in diarization_segments:
            overlap = max(0.0, min(segment.end, d["end"]) - max(segment.start, d["start"]))
            if overlap > best_overlap:
                best_overlap = overlap
                best_speaker = d["speaker"]
        segment.speaker = best_speaker
