"""Command-line entry point for the W1 prototype."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .analysis import analyze_audio


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze tempo drift in a band rehearsal recording.")
    parser.add_argument("audio_file", type=Path, help="Path to a rehearsal recording")
    parser.add_argument("--output", "-o", type=Path, help="Write the JSON report to this path")
    parser.add_argument("--window-seconds", type=float, default=12.0, help="Analysis window length (default: 12)")
    parser.add_argument("--hop-seconds", type=float, default=6.0, help="Distance between analysis windows (default: 6)")
    parser.add_argument("--reference-bpm", type=float, help="Optional known song tempo")
    parser.add_argument("--drift-threshold-bpm", type=float, default=4.0, help="Highlight threshold (default: 4)")
    return parser


def main() -> None:
    args = _parser().parse_args()
    report = analyze_audio(
        args.audio_file,
        window_seconds=args.window_seconds,
        hop_seconds=args.hop_seconds,
        reference_bpm=args.reference_bpm,
        drift_threshold_bpm=args.drift_threshold_bpm,
    )
    payload = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
        print(f"Saved report to {args.output}")
    else:
        print(payload)


if __name__ == "__main__":
    main()
