from __future__ import annotations

import wave
from pathlib import Path

import numpy as np

from band_jam_feedback.analysis import analyze_audio


def _click_track(path: Path, sample_rate: int = 22_050) -> None:
    """Create 24 seconds at 120 BPM, followed by 24 seconds at 132 BPM."""
    audio = np.zeros(sample_rate * 48, dtype=np.float32)
    for start_seconds, duration_seconds, bpm in ((0, 24, 120), (24, 24, 132)):
        interval = 60 / bpm
        for time in np.arange(start_seconds, start_seconds + duration_seconds, interval):
            start = int(time * sample_rate)
            click_length = int(0.025 * sample_rate)
            envelope = np.exp(-np.linspace(0, 7, click_length)).astype(np.float32)
            audio[start : start + click_length] += envelope
    pcm = (np.clip(audio, -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(sample_rate)
        output.writeframes(pcm.tobytes())


def test_detects_later_tempo_increase(tmp_path: Path) -> None:
    sample = tmp_path / "faster-second-half.wav"
    _click_track(sample)

    report = analyze_audio(
        sample,
        window_seconds=8,
        hop_seconds=4,
        reference_bpm=120,
        drift_threshold_bpm=4,
    )

    assert report["baseline_bpm"] == 120
    assert any(
        highlight["direction"] == "faster" and highlight["start_seconds"] >= 20
        for highlight in report["highlights"]
    )
    first_half = [window["bpm"] for window in report["windows"] if window["start_seconds"] < 20]
    second_half = [window["bpm"] for window in report["windows"] if window["start_seconds"] >= 28]
    assert np.median(second_half) > np.median(first_half) + 5
