"""Generate an LLM-ready feedback request from analysis reports."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .feedback import build_feedback_request


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create an LLM-ready Korean rehearsal feedback request.")
    parser.add_argument("tempo_report", type=Path)
    parser.add_argument("timing_report", type=Path)
    parser.add_argument("--session-parts", required=True, help="Comma-separated session parts")
    parser.add_argument("--output", "-o", type=Path, required=True)
    return parser


def main() -> None:
    args = _parser().parse_args()
    request = build_feedback_request(
        json.loads(args.tempo_report.read_text(encoding="utf-8")),
        json.loads(args.timing_report.read_text(encoding="utf-8")),
        session_parts=[part.strip() for part in args.session_parts.split(",") if part.strip()],
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(request, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Saved feedback request to {args.output}")


if __name__ == "__main__":
    main()
