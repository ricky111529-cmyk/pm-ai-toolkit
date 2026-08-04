"""Grounded LLM request contract for rehearsal feedback.

This module deliberately does not call an LLM provider. It turns measured tempo
and stem-timing evidence into a provider-neutral prompt and strict JSON schema
that the later API layer can submit to any chosen model.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any


def _timestamp(seconds: float) -> str:
    seconds = max(0, round(seconds))
    return f"{seconds // 60}:{seconds % 60:02d}"


def _matching_timing_parts(
    timing_report: Mapping[str, Any], start_seconds: float, end_seconds: float
) -> Mapping[str, Any]:
    for segment in timing_report.get("segments", []):
        if (
            abs(float(segment["start_seconds"]) - start_seconds) < 0.1
            and abs(float(segment["end_seconds"]) - end_seconds) < 0.1
        ):
            return segment.get("parts", {})
    return {}


def feedback_response_schema() -> dict[str, Any]:
    """JSON contract that keeps feedback tied to detected segments."""
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["segment_feedback", "overall_feedback"],
        "properties": {
            "segment_feedback": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["start_seconds", "end_seconds", "headline", "feedback", "practice_action"],
                    "properties": {
                        "start_seconds": {"type": "number"},
                        "end_seconds": {"type": "number"},
                        "headline": {"type": "string"},
                        "feedback": {"type": "string"},
                        "practice_action": {"type": "string"},
                    },
                },
            },
            "overall_feedback": {"type": "string"},
        },
    }


def build_feedback_request(
    tempo_report: Mapping[str, Any],
    timing_report: Mapping[str, Any],
    *,
    session_parts: Sequence[str],
    max_segments: int = 3,
) -> dict[str, Any]:
    """Create a provider-neutral structured-output request for a Korean coach."""
    all_highlights = list(tempo_report.get("highlights", []))
    ranked_highlights: list[tuple[float, Mapping[str, Any]]] = []
    for highlight in all_highlights:
        start_seconds = float(highlight["start_seconds"])
        end_seconds = float(highlight["end_seconds"])
        part_candidates = _matching_timing_parts(timing_report, start_seconds, end_seconds)
        timing_signal = sum(
            2 if candidate.get("confidence") == "high" else 1 if candidate.get("confidence") == "medium" else 0
            for candidate in part_candidates.values()
            if not candidate.get("at_offset_limit", False)
        )
        score = timing_signal + abs(float(highlight["peak_drift_bpm"])) / 100
        ranked_highlights.append((score, highlight))
    highlights = [highlight for _, highlight in sorted(ranked_highlights, key=lambda item: item[0], reverse=True)[:max_segments]]
    highlights.sort(key=lambda highlight: float(highlight["start_seconds"]))
    evidence: list[dict[str, Any]] = []
    for highlight in highlights:
        start_seconds = float(highlight["start_seconds"])
        end_seconds = float(highlight["end_seconds"])
        evidence.append(
            {
                "time_range": f"{_timestamp(start_seconds)}–{_timestamp(end_seconds)}",
                "start_seconds": start_seconds,
                "end_seconds": end_seconds,
                "tempo_observation": {
                    "direction": highlight["direction"],
                    "peak_drift_bpm": highlight["peak_drift_bpm"],
                    "baseline_bpm": tempo_report.get("baseline_bpm"),
                },
                "part_timing_candidates": _matching_timing_parts(timing_report, start_seconds, end_seconds),
            }
        )

    instructions = """당신은 초보 밴드를 위한 합주 복기 코치입니다. 반드시 제공된 분석 근거만 사용해 한국어로 답하세요.

규칙:
1. 구간별 피드백을 먼저 제시하고, 마지막에 총평 하나만 작성합니다.
2. 각 구간은 데이터 관찰 → 그 구간을 다시 들어볼 이유 → 다음 합주에서 해볼 행동 1개 순서로 씁니다.
3. confidence가 low이거나 at_offset_limit이 true인 악기별 후보는 수치·원인을 단정하지 마세요. "추정", "확인 후보", "원본과 스템을 함께 들어보세요"로 표현합니다.
4. confidence가 medium 이상인 후보만 수치(ms)를 언급할 수 있습니다. 그래도 멤버 개인의 실수·원인·주법을 단정하지 마세요.
5. 세션 구성에 없는 악기를 언급하지 마세요. 기타가 두 명이어도 분석 단위가 guitar이면 "기타 파트"라고만 표현하세요.
6. "누가 틀렸다", "문제의 원인은" 같은 비난·인과 표현을 쓰지 마세요.
7. feedback은 2문장 이내, practice_action은 실제 다음 합주에서 할 수 있는 한 문장으로 씁니다.
8. overall_feedback은 2~3문장으로, 반복된 패턴과 다음 합주의 한 가지 우선 목표만 정리합니다."""

    return {
        "system_instruction": instructions,
        "response_schema": feedback_response_schema(),
        "input": {
            "session_parts": list(session_parts),
            "tempo_baseline_bpm": tempo_report.get("baseline_bpm"),
            "segments": evidence,
        },
        "user_message": "아래 분석 근거를 바탕으로 합주 리포트를 생성하세요. JSON 스키마를 정확히 따르세요.\n\n"
        + json.dumps({"session_parts": list(session_parts), "segments": evidence}, ensure_ascii=False),
    }
