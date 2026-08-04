from band_jam_feedback.feedback import build_feedback_request


def test_builds_grounded_korean_feedback_request() -> None:
    tempo_report = {
        "baseline_bpm": 160,
        "highlights": [
            {"start_seconds": 120, "end_seconds": 144, "direction": "slower", "peak_drift_bpm": -8}
        ],
    }
    timing_report = {
        "segments": [
            {
                "start_seconds": 120,
                "end_seconds": 144,
                "parts": {"guitar": {"offset_ms": 46, "confidence": "medium", "at_offset_limit": False}},
            }
        ]
    }

    request = build_feedback_request(
        tempo_report,
        timing_report,
        session_parts=["drums", "bass", "vocals", "guitar"],
    )

    assert request["input"]["segments"][0]["time_range"] == "2:00–2:24"
    assert "confidence가 low" in request["system_instruction"]
    assert request["response_schema"]["required"] == ["segment_feedback", "overall_feedback"]


def test_prioritises_segment_with_usable_part_candidate() -> None:
    tempo_report = {
        "highlights": [
            {"start_seconds": 0, "end_seconds": 12, "direction": "slower", "peak_drift_bpm": -8},
            {"start_seconds": 20, "end_seconds": 32, "direction": "slower", "peak_drift_bpm": -8},
            {"start_seconds": 40, "end_seconds": 52, "direction": "slower", "peak_drift_bpm": -8},
            {"start_seconds": 60, "end_seconds": 72, "direction": "slower", "peak_drift_bpm": -8},
        ]
    }
    timing_report = {
        "segments": [
            {
                "start_seconds": 60,
                "end_seconds": 72,
                "parts": {"guitar": {"confidence": "medium", "at_offset_limit": False}},
            }
        ]
    }

    request = build_feedback_request(tempo_report, timing_report, session_parts=["drums", "guitar"], max_segments=3)

    starts = [segment["start_seconds"] for segment in request["input"]["segments"]]
    assert 60 in starts
