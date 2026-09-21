from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.config import load_config
from core.outputs import _ts
from core.translate import chunks

def test_timestamp():
    assert _ts(65.125) == "00:01:05,125"

def test_chunks():
    result = chunks("a\n" * 100, size=10)
    assert len(result) > 1

def test_config_defaults(tmp_path):
    cfg = load_config(tmp_path / "missing.json")
    assert cfg.asr_backend == "local"
    assert cfg.local_model == "large-v3"
    assert cfg.target_language == "en"
