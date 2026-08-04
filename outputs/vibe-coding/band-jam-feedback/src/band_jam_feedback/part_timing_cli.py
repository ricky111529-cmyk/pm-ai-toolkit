"""CLI for stem-based relative timing candidates."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .part_timing import analyze_stem_timing


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Estimate part timing candidates relative to a drum stem.")
    parser.add_argument("stems_dir", type=Path, help="Directory containing drums.wav and other stem WAV files")
    parser.add_argument("segments_report", type=Path, help="Tempo report JSON; its highlights become analysis segments")
    parser.add_argument("--output", "-o", type=Path, required=True, help="Destination JSON report")
    parser.add_argument("--reference-part", default="drums", help="Stem filename to use as reference (default: drums)")
    parser.add_argument("--max-offset-ms", type=int, default=200, help="Maximum lag to inspect (default: 200)")
    parser.add_argument(
        "--parts",
        help="Comma-separated stem names to analyze (for example: drums,bass,vocals,guitar)",
    )
    return parser


def main() -> None:
    args = _parser().parse_args()
    tempo_report = json.loads(args.segments_report.read_text(encoding="utf-8"))
    highlights = tempo_report.get("highlights", [])
    if not highlights:
        raise ValueError("Tempo report contains no highlights to analyze")
    stem_paths = {
        path.stem: path
        for path in args.stems_dir.glob("*.wav")
        if path.stem in {"drums", "bass", "vocals", "guitar", "other", "piano"}
    }
    if args.parts:
        requested_parts = {part.strip() for part in args.parts.split(",") if part.strip()}
        missing_parts = requested_parts - stem_paths.keys()
        if missing_parts:
            raise ValueError(f"Requested stems are missing: {', '.join(sorted(missing_parts))}")
        stem_paths = {part: path for part, path in stem_paths.items() if part in requested_parts}
    report = analyze_stem_timing(
        stem_paths,
        highlights,
        reference_part=args.reference_part,
        max_offset_ms=args.max_offset_ms,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Saved part timing candidates to {args.output}")


if __name__ == "__main__":
    main()
