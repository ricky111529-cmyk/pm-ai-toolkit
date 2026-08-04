"""Audio analysis primitives used by the local CLI and later API."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import median
from typing import Literal

import librosa
import numpy as np


Direction = Literal["faster", "slower"]


@dataclass(frozen=True)
class TempoWindow:
    start_seconds: float
    end_seconds: float
    bpm: float
    drift_bpm: float
    drift_percent: float


@dataclass(frozen=True)
class TempoHighlight:
    start_seconds: float
    end_seconds: float
    direction: Direction
    peak_drift_bpm: float


def _estimate_window_bpm(beat_times: np.ndarray, start_seconds: float, end_seconds: float) -> float | None:
    """Estimate local BPM from a single beat grid built for the whole track.

    Estimating every window independently causes a common music-analysis
    failure: the same 3/4 or 6/8 passage gets interpreted as half-time or
    double-time in neighbouring windows. One global beat grid keeps the beat
    unit consistent; local beat intervals then express only relative drift.
    """
    window_beats = beat_times[(beat_times >= start_seconds) & (beat_times <= end_seconds)]
    intervals = np.diff(window_beats)
    valid_intervals = intervals[(intervals >= 0.25) & (intervals <= 1.5)]
    if valid_intervals.size < 3:
        return None
    return float(np.median(60 / valid_intervals))


def _merge_highlights(
    windows: list[TempoWindow],
    threshold_bpm: float,
    min_consecutive_windows: int,
) -> list[TempoHighlight]:
    """Combine adjacent meaningful deviations into readable song sections."""
    highlights: list[TempoHighlight] = []
    active: list[TempoWindow] = []
    direction: Direction | None = None

    def flush() -> None:
        nonlocal active, direction
        if len(active) >= min_consecutive_windows and direction is not None:
            peak = max(active, key=lambda window: abs(window.drift_bpm))
            highlights.append(
                TempoHighlight(
                    start_seconds=active[0].start_seconds,
                    end_seconds=active[-1].end_seconds,
                    direction=direction,
                    peak_drift_bpm=peak.drift_bpm,
                )
            )
        active = []
        direction = None

    for window in windows:
        candidate_direction: Direction | None = None
        if window.drift_bpm >= threshold_bpm:
            candidate_direction = "faster"
        elif window.drift_bpm <= -threshold_bpm:
            candidate_direction = "slower"

        if candidate_direction is None:
            flush()
        elif direction in (None, candidate_direction):
            direction = candidate_direction
            active.append(window)
        else:
            flush()
            direction = candidate_direction
            active.append(window)
    flush()
    return highlights


def analyze_audio(
    audio_path: str | Path,
    *,
    window_seconds: float = 12.0,
    hop_seconds: float = 6.0,
    reference_bpm: float | None = None,
    drift_threshold_bpm: float = 4.0,
    min_consecutive_windows: int = 2,
) -> dict[str, object]:
    """Return relative tempo drift for an audio file.

    ``reference_bpm`` is optional. Without it, the robust median of all valid
    windows becomes the baseline, which is the v0 product behaviour.
    """
    if window_seconds <= 0 or hop_seconds <= 0:
        raise ValueError("window_seconds and hop_seconds must be positive")
    if reference_bpm is not None and reference_bpm <= 0:
        raise ValueError("reference_bpm must be positive")

    path = Path(audio_path)
    if not path.is_file():
        raise FileNotFoundError(f"Audio file not found: {path}")

    audio, sample_rate = librosa.load(path, sr=22_050, mono=True)
    duration_seconds = len(audio) / sample_rate
    hop_length = 512
    _, beat_frames = librosa.beat.beat_track(
        y=audio,
        sr=sample_rate,
        hop_length=hop_length,
        trim=False,
        sparse=True,
    )
    beat_times = librosa.frames_to_time(beat_frames, sr=sample_rate, hop_length=hop_length)
    if beat_times.size < 4:
        raise ValueError("Tempo could not be estimated. Try a clearer or longer recording.")

    hop_samples = int(hop_seconds * sample_rate)

    raw_windows: list[tuple[float, float, float]] = []
    for start_sample in range(0, len(audio), hop_samples):
        start_seconds = start_sample / sample_rate
        end_seconds = min(start_seconds + window_seconds, duration_seconds)
        if end_seconds - start_seconds < 4:
            continue
        bpm = _estimate_window_bpm(beat_times, start_seconds, end_seconds)
        if bpm is not None:
            raw_windows.append(
                (start_seconds, end_seconds, bpm)
            )

    if not raw_windows:
        raise ValueError("Tempo could not be estimated. Try a clearer or longer recording.")

    baseline_bpm = float(reference_bpm) if reference_bpm else float(median(bpm for _, _, bpm in raw_windows))
    windows = [
        TempoWindow(
            start_seconds=round(start, 2),
            end_seconds=round(end, 2),
            bpm=round(bpm, 2),
            drift_bpm=round(bpm - baseline_bpm, 2),
            drift_percent=round((bpm - baseline_bpm) / baseline_bpm * 100, 2),
        )
        for start, end, bpm in raw_windows
    ]
    highlights = _merge_highlights(windows, drift_threshold_bpm, min_consecutive_windows)

    return {
        "source_file": path.name,
        "duration_seconds": round(duration_seconds, 2),
        "baseline_bpm": round(baseline_bpm, 2),
        "baseline_type": "reference" if reference_bpm else "recording_median",
        "analysis": {
            "window_seconds": window_seconds,
            "hop_seconds": hop_seconds,
            "drift_threshold_bpm": drift_threshold_bpm,
        },
        "windows": [asdict(window) for window in windows],
        "highlights": [asdict(highlight) for highlight in highlights],
    }
