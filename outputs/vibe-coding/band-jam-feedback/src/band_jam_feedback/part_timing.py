"""Stem-based relative timing candidates for rehearsal recordings.

The estimates in this module are deliberately phrased as candidates, not
verdicts. Source separation artefacts and bleed can make an onset correlation
look more certain than it is.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

import librosa
import numpy as np


def _onset_envelope(audio: np.ndarray, sample_rate: int, hop_length: int) -> np.ndarray:
    envelope = librosa.onset.onset_strength(y=audio, sr=sample_rate, hop_length=hop_length)
    if envelope.size < 8 or float(np.max(envelope)) < 1e-7:
        return np.array([], dtype=float)
    return envelope.astype(float)


def _normalised_correlation(reference: np.ndarray, candidate: np.ndarray) -> float | None:
    if reference.size < 8 or candidate.size < 8:
        return None
    centered_reference = reference - np.mean(reference)
    centered_candidate = candidate - np.mean(candidate)
    denominator = np.linalg.norm(centered_reference) * np.linalg.norm(centered_candidate)
    if denominator < 1e-9:
        return None
    return float(np.dot(centered_reference, centered_candidate) / denominator)


def estimate_relative_offset(
    reference_audio: np.ndarray,
    candidate_audio: np.ndarray,
    sample_rate: int,
    *,
    max_offset_ms: int = 200,
    hop_length: int = 256,
) -> dict[str, float | int | str]:
    """Estimate candidate onset lag relative to a reference part.

    A positive offset means the candidate's onset pattern is later than the
    reference. The result measures the dominant pattern in a segment; it does
    not identify a particular musician's error.
    """
    if max_offset_ms <= 0:
        raise ValueError("max_offset_ms must be positive")

    reference = _onset_envelope(reference_audio, sample_rate, hop_length)
    candidate = _onset_envelope(candidate_audio, sample_rate, hop_length)
    length = min(reference.size, candidate.size)
    if length < 8:
        return {
            "offset_ms": 0,
            "direction": "unavailable",
            "peak_correlation": 0.0,
            "confidence": "low",
            "confidence_score": 0.0,
        }

    reference = reference[:length]
    candidate = candidate[:length]
    max_lag_frames = max(1, round(max_offset_ms / 1000 * sample_rate / hop_length))
    correlations: list[tuple[int, float]] = []
    for lag in range(-max_lag_frames, max_lag_frames + 1):
        if lag > 0:
            correlation = _normalised_correlation(reference[:-lag], candidate[lag:])
        elif lag < 0:
            correlation = _normalised_correlation(reference[-lag:], candidate[:lag])
        else:
            correlation = _normalised_correlation(reference, candidate)
        if correlation is not None:
            correlations.append((lag, correlation))

    if not correlations:
        return {
            "offset_ms": 0,
            "direction": "unavailable",
            "peak_correlation": 0.0,
            "confidence": "low",
            "confidence_score": 0.0,
        }

    best_lag, peak_correlation = max(correlations, key=lambda item: item[1])
    median_correlation = float(np.median([value for _, value in correlations]))
    peak_margin = peak_correlation - median_correlation
    confidence_score = float(np.clip(peak_correlation * min(1.0, peak_margin / 0.12), 0, 1))
    at_offset_limit = abs(best_lag) == max_lag_frames
    if peak_correlation >= 0.5 and peak_margin >= 0.12:
        confidence = "high"
    elif peak_correlation >= 0.3 and peak_margin >= 0.05:
        confidence = "medium"
    else:
        confidence = "low"
    if at_offset_limit:
        confidence = "low"

    offset_ms = round(best_lag * hop_length / sample_rate * 1000)
    if abs(offset_ms) <= 20:
        direction = "aligned"
    elif offset_ms > 0:
        direction = "later"
    else:
        direction = "earlier"
    return {
        "offset_ms": offset_ms,
        "direction": direction,
        "peak_correlation": round(peak_correlation, 3),
        "confidence": confidence,
        "confidence_score": round(confidence_score, 3),
        "at_offset_limit": at_offset_limit,
    }


def analyze_stem_timing(
    stem_paths: Mapping[str, str | Path],
    segments: Sequence[Mapping[str, float]],
    *,
    reference_part: str = "drums",
    max_offset_ms: int = 200,
) -> dict[str, object]:
    """Compare each supplied stem with the reference stem for every segment."""
    if reference_part not in stem_paths:
        raise ValueError(f"Reference part '{reference_part}' is missing from stem_paths")
    if not segments:
        raise ValueError("At least one segment is required")

    sample_rate = 22_050
    loaded: dict[str, np.ndarray] = {}
    for part, raw_path in stem_paths.items():
        path = Path(raw_path)
        if not path.is_file():
            raise FileNotFoundError(f"Stem not found for {part}: {path}")
        loaded[part], _ = librosa.load(path, sr=sample_rate, mono=True)

    report_segments: list[dict[str, object]] = []
    for segment in segments:
        start_seconds = float(segment["start_seconds"])
        end_seconds = float(segment["end_seconds"])
        if end_seconds <= start_seconds:
            raise ValueError("Each segment must end after it starts")
        start_sample = max(0, round(start_seconds * sample_rate))
        end_sample = round(end_seconds * sample_rate)
        reference_audio = loaded[reference_part][start_sample:end_sample]
        parts: dict[str, dict[str, float | int | str]] = {}
        for part, audio in loaded.items():
            if part == reference_part:
                continue
            parts[part] = estimate_relative_offset(
                reference_audio,
                audio[start_sample:end_sample],
                sample_rate,
                max_offset_ms=max_offset_ms,
            )
        report_segments.append(
            {
                "start_seconds": round(start_seconds, 2),
                "end_seconds": round(end_seconds, 2),
                "reference_part": reference_part,
                "parts": parts,
            }
        )

    return {
        "analysis_type": "stem_onset_correlation_candidate",
        "reference_part": reference_part,
        "max_offset_ms": max_offset_ms,
        "warning": "Offsets are stem-based candidates. Separation bleed and recording quality can reduce reliability.",
        "segments": report_segments,
    }
