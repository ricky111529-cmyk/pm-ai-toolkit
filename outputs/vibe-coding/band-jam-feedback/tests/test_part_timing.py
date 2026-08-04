from __future__ import annotations

import soundfile as sf
import numpy as np

from band_jam_feedback import part_timing
from band_jam_feedback.part_timing import analyze_stem_timing


def _clicks(duration_seconds: float, offset_seconds: float, sample_rate: int = 22_050) -> np.ndarray:
    audio = np.zeros(round(duration_seconds * sample_rate), dtype=np.float32)
    for time in np.arange(0.5 + offset_seconds, duration_seconds - 0.1, 0.5):
        start = round(time * sample_rate)
        length = round(0.02 * sample_rate)
        audio[start : start + length] = np.exp(-np.linspace(0, 8, length)).astype(np.float32)
    return audio


def test_detects_candidate_later_than_drums(tmp_path) -> None:
    sample_rate = 22_050
    drums = tmp_path / "drums.wav"
    bass = tmp_path / "bass.wav"
    sf.write(drums, _clicks(12, 0), sample_rate)
    sf.write(bass, _clicks(12, 0.1), sample_rate)

    report = analyze_stem_timing(
        {"drums": drums, "bass": bass},
        [{"start_seconds": 0, "end_seconds": 12}],
    )

    candidate = report["segments"][0]["parts"]["bass"]
    assert candidate["direction"] == "later"
    assert 60 <= candidate["offset_ms"] <= 130


def test_marks_limit_offset_as_low_confidence(monkeypatch) -> None:
    reference_audio = np.array([1.0])
    candidate_audio = np.array([2.0])
    reference_envelope = np.array([0.2, 0.7, 0.1, 1.0, 0.3, 0.8, 0.05, 0.9, 0.4, 0.6])
    candidate_envelope = np.concatenate([np.zeros(2), reference_envelope[:-2]])
    envelopes = {id(reference_audio): reference_envelope, id(candidate_audio): candidate_envelope}
    monkeypatch.setattr(part_timing, "_onset_envelope", lambda audio, *_: envelopes[id(audio)])

    candidate = part_timing.estimate_relative_offset(
        reference_audio,
        candidate_audio,
        sample_rate=1_000,
        hop_length=100,
        max_offset_ms=200,
    )

    assert candidate["at_offset_limit"] is True
    assert candidate["confidence"] == "low"
