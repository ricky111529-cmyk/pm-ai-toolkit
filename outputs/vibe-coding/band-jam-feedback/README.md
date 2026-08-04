> 생성: 2026-07-24 | 작성자: 김민섭+Codex | 맥락: 밴드 합주 AI 피드백 v0의 W1 오디오 분석 프로토타입

# Band Jam Feedback — W1 분석기

합주 녹음에서 시간대별 템포를 추정하고, 곡 내부 기준 BPM으로부터 크게 벗어난 구간을 찾는 로컬 CLI입니다.

## 현재 범위

- 지원 입력: `wav`, `mp3`, `m4a` 등 `librosa`가 디코딩할 수 있는 오디오
- 출력: 기준 BPM, 시간대별 BPM/드리프트, 자동 감지한 흔들림 구간을 담은 JSON
- 분석 방식: 녹음 전체에서 하나의 비트 그리드를 먼저 잡고, 구간별 비트 간격으로 상대적 템포 변화를 계산합니다. 구간마다 박자 단위를 달리 잡아 생기는 하프·더블 템포 오인을 줄이기 위함입니다.
- 원칙: 특정 멤버의 실수나 연주 품질을 판정하지 않고, 녹음의 상대적인 템포 변화를 보여줍니다.

## 실행

```bash
uv run band-jam-analyze path/to/rehearsal.m4a --output result.json
```

옵션:

```bash
# 기본 12초 분석창 대신 8초 창으로 더 촘촘히 보기
uv run band-jam-analyze rehearsal.wav --window-seconds 8

# 기준 BPM이 알려진 곡인 경우에만 명시
uv run band-jam-analyze rehearsal.wav --reference-bpm 120
```

## 출력 예시

```json
{
  "baseline_bpm": 119.8,
  "windows": [{"start_seconds": 0, "bpm": 118.7, "drift_bpm": -1.1}],
  "highlights": [{"start_seconds": 72, "end_seconds": 96, "direction": "faster"}]
}
```

## 설치·검증

```bash
uv sync
uv run pytest
```

`tests/`는 120 BPM에서 132 BPM으로 빨라지는 합성 클릭 트랙을 만들어, 분석기가 후반 가속을 감지하는지 확인합니다.

## W1.5 — 악기 분리 가능성 검증

악기별 타이밍 피드백을 만들기 전에, 실제 합주 녹음에서 분리된 스템이 분석 근거로 쓸 만한지 검증한다.

```bash
# Demucs가 안정적으로 읽을 수 있는 WAV 입력으로 변환한 뒤 실행
uv run python -m demucs.separate -n htdemucs --out /private/tmp/band-jam-stems /private/tmp/band-jam-source.wav
```

- 세션 구성에 `guitar` 또는 `piano`가 포함되면 6-stem 모델을 우선 시험한다.

```bash
uv run python -m demucs.separate -n htdemucs_6s --out /private/tmp/band-jam-stems-6s /private/tmp/band-jam-source.wav
```

- 4-stem 모델 출력: `drums`, `bass`, `vocals`, `other`
- 6-stem 모델 출력: `drums`, `bass`, `vocals`, `guitar`, `piano`, `other`
- 주의: `guitar`는 **기타 1·2가 합쳐진 스템**이다. 사용자 입력으로 기타가 두 명이라는 사실은 피드백 해석에는 쓰되, 두 기타를 개별로 분리하지는 못한다.
- 세션 구성 입력의 역할: 지원 모델 선택, 존재하지 않는 악기에 대한 LLM 추론 방지, 결과 라벨링. 입력만으로 분리 음질이 높아지지는 않는다.
- **v0 결정**: 상용 분리 API는 사용하지 않고 로컬 Demucs를 사용한다. 품질이 낮아도 악기별 타이밍 후보·피드백을 실험적으로 제공하되, `추정`·`분리 신뢰도`를 표시하고 원본과 스템을 함께 재생하게 한다. 기타 1·2처럼 개별 연주자 원인을 판정하지 않는다.

## W1.6 — 드럼 기준 파트별 타이밍 후보

`band-jam-part-timing`은 각 하이라이트 구간에서 드럼 스템의 온셋 패턴과 다른 스템을 비교한다. 양수 `offset_ms`는 해당 파트가 드럼보다 늦게 들리는 후보를 뜻한다.

```bash
uv run band-jam-part-timing \
  /private/tmp/band-jam-stems-6s/htdemucs_6s/band-jam-source \
  reports/baekbeomro-1gil-7.json \
  --parts drums,bass,vocals,guitar \
  --output reports/baekbeomro-1gil-7-part-timing.json
```

출력은 `offset_ms`, `direction`, `peak_correlation`, `confidence`, `at_offset_limit`를 포함한다. 분석 범위 한계(기본 ±200ms)에 붙은 값은 자동으로 저신뢰 처리한다. 이는 **분리 스템의 온셋 상관관계에 근거한 후보**이며, 멤버 개인의 실수나 원인을 판정하지 않는다.

## W1.7 — 근거 기반 LLM 피드백 계약

`band-jam-feedback-request`는 템포·파트 타이밍 JSON을 LLM 호출용 구조화 요청으로 바꾼다. 이 단계는 API 키나 특정 LLM에 의존하지 않는다.

```bash
uv run band-jam-feedback-request \
  reports/baekbeomro-1gil-7.json \
  reports/baekbeomro-1gil-7-part-timing.json \
  --session-parts drums,bass,vocals,guitar \
  --output reports/baekbeomro-1gil-7-feedback-request.json
```

계약은 구간별 피드백을 먼저, 마지막 총평 하나를 강제한다. 저신뢰·분석 한계 후보는 반드시 `추정`·`확인 후보`로 표현하도록 지시한다.
- 통과 기준: 실제 느껴지는 진입·리듬을 각 스템에서 식별할 수 있고, 드럼 대비 상대 타이밍 후보를 만들 만큼 누출·왜곡이 낮은가.
- 실패 시: 악기별 코칭은 v0에서 제외하고, 밴드 전체 구간 피드백에 한정한다.

## 다음 단계

W1.5 분리 품질을 실제 청취로 확인한 뒤, 통과하면 드럼을 기준으로 한 구간별 상대 타이밍 분석을 추가합니다. 그 다음 W2에서 이 JSON을 FastAPI 엔드포인트와 모바일 리포트 화면에 연결합니다.
