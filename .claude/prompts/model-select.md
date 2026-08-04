# 프롬프트: 모델 선택 가이드

> Haiku / Sonnet / Opus — 언제 무엇을 쓸지 결정 트리.

---

## 한눈에 보는 선택 기준

| 모델 | 언제 | 비용 | 예시 |
|------|------|------|------|
| **Haiku** | 단순·반복·빠른 확인 | 최저 | 변수명 제안, 짧은 Q&A, 번역, 포맷 변환 |
| **Sonnet** | 대부분의 일반 작업 | 중간 | 코드 구현, 문서 작성, 디버깅, 리서치 정리 |
| **Opus** | 설계·판단·복잡한 추론 | 최고 | 아키텍처 설계, 복잡한 리팩토링, 핵심 의사결정 |

---

## 결정 트리

```
작업이 단순 반복이거나 답이 짧은가?
  └─ Yes → Haiku

복잡한 설계·아키텍처·핵심 의사결정인가?
  └─ Yes → Opus (또는 OpusPlan 전략)

그 외 일반적인 작업
  └─ Sonnet (기본값)
```

---

## OpusPlan 전략

비용은 아끼고 설계 품질은 높이는 방법.

**단계:**
1. Plan Mode에서 **Opus**로 설계·계획 수립
2. 사용자 승인
3. **Sonnet**으로 전환해서 실제 구현

**효과:**
- 전체 비용: Sonnet 수준 유지
- 설계 품질: Opus 수준 확보
- 복잡한 기능 설계·시스템 아키텍처에 특히 유효

---

## 모델 전환 방법

```bash
# Claude Code에서 모델 변경 (버전 번호는 최신으로 교체 필요)
claude --model claude-opus-4-7      # Opus
claude --model claude-sonnet-4-6    # Sonnet
claude --model claude-haiku-4-5     # Haiku
```

또는 대화 중 `/model` 명령 사용.

> 모델 버전 확인: `claude --version` 또는 https://docs.anthropic.com/en/docs/models-overview
> 위 버전 번호는 예시입니다. 실제 사용 시 최신 모델명으로 교체하세요.

---

## 실전 판단 예시

| 요청 | 선택 | 이유 |
|------|------|------|
| "이 함수 변수명 뭐가 좋아?" | Haiku | 단순 제안 |
| "이 기획서 초안 써줘" | Sonnet | 일반 문서 작성 |
| "이 API 구조 어떻게 설계할지 검토해줘" | Opus | 아키텍처 판단 |
| "로그인 기능 구현해줘" | Sonnet | 일반 구현 |
| "전체 DB 스키마 리팩토링 계획 세워줘" | Opus → 승인 → Sonnet | OpusPlan 전략 |
