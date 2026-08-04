# 프로젝트 가이드

> Codex가 이 프로젝트 진입 시 가장 먼저 읽는 파일.
> 역할·라우팅·핵심 규칙만. 상세 내용은 각 경로로 분산.
> **200줄·1,000토큰 이내 유지**.

---

## 내 역할 (Role)

나는 PM/AIP스쿼드를 위한 AI 작업 파트너입니다.
주요 업무: PRD 작성 / 기획 문서 작성 / 리서치 / 코드 작성 / 데이터 분석 / POC 제작

---

## 파일 저장 결정 트리 (강제)

| 파일 성격 | 저장 위치 |
|---|---|
| 기획서·PRD·명세서 | `outputs/specs/{주제}/YYYY-MM-DD_vN.md` |
| 정책서·운영 규칙 | `outputs/policies/{주제}/YYYY-MM-DD_vN.md` |
| POC 코드·프로토타입 | `outputs/vibe-coding/{kebab-slug}/` |
| 리서치 보고서 | `outputs/research/{주제}/YYYY-MM-DD_vN.md` |
| 디자인 산출물 | `outputs/designs/{주제}/` |
| 진행 중 멀티파일 작업 | `projects/{프로젝트명}/` |
| 외부 참고 자료 (입력) | `docs/` |
| 폐기·과거 버전 | `archive/YYYY-MM-DD_{사유}/` |

### 금지
- 루트에 파일 직접 저장 (폴더만 둘 것)
- `outputs/`, `projects/` 루트에 파일 직접 저장 (주제별 하위 폴더 필수)
- 한글 폴더/파일명 (모두 kebab-case 또는 snake_case)
- `_최신` 외 구버전 무한 축적 — 분기 종료 시 `archive/`로

---

## AGENTS.md 3티어 구조

| 티어 | 위치 | 로드 방식 |
|---|---|---|
| Tier 1 | `AGENTS.md` (이 파일) | 항상 자동 로드 |
| Tier 2 | `.Codex/prompts/`, `.Codex/design.md`, `.Codex/memory/` | `@파일경로`로 수동 참조 |
| Tier 3 | `docs/`, `outputs/`, `projects/*/AGENTS.md` | 필요 시 직접 읽기 |

> "이 줄이 없으면 Codex가 실수하는가?" No면 삭제. 코드에서 읽히는 정보 넣지 말 것.

---

## 라우팅

| 요청 | 참조 경로 |
|---|---|
| **PRD·Epic 작성** | `.Codex/prompts/prd-template.md` (양식 강제 — 아래 규칙 참조) |
| **리서치·분석·설문·실험·루브릭 작성** | `.Codex/prompts/templates/README.md` (유형별 구조 강제 — 아래 규칙 참조) |
| **UX 리서치 (리서치 질문·가설·인터뷰 설계)** | `.Codex/prompts/ux-research-guideline.md` (질문 설계 프레임워크 — 항상 참고) |
| 디자인·UI·톤앤매너 | `.Codex/design.md` (최소 버전: `design-minimal.md`) |
| 프롬프트 템플릿 | `.Codex/prompts/README.md` |
| 과거 결정·맥락 | `.Codex/memory/MEMORY.md` |
| 프로젝트 상세 | `projects/{프로젝트명}/AGENTS.md` |
| 입력 참고 자료 | `docs/` |
| 완성 산출물 | `outputs/{유형}/` |

**규칙**: 위 표에서 해당 경로만 읽기. 전체 폴더 스캔 금지.

---

## PRD 작성 규칙 (강제)

PRD·Epic 작성 요청 시 **반드시 `.Codex/prompts/prd-template.md` 양식을 그대로 따른다**.

- **구조**: 헤더 표(항목·내용) 하나로 운영. 상세가 필요한 항목만 표 아래 `▽ 옵션 블록`을 `## 섹션`으로 꺼내 쓴다 (기본 생략).
- **확장 옵션(6)**: As-Is · Phase · 유저 스토리 · 엣지 케이스 · 성공 지표 · 기존 시스템 연관 — 헤더 표로 협업이 풀리면 추가하지 않는다.
- **제목**: PRD는 `[PRD] <제목>`, Epic이면 `[Epic] <영역> <연차>`.
- **플레이스홀더**: `( )` 지우고 작성 · `—` 아직 없음/게재 후 · `예:` 예시값.
- **PS(slug 동일)** 있으면 문제/현황 셀에 링크하고 본문에 중복 작성 금지.
- **저장**: 완성본은 `outputs/specs/{주제}/YYYY-MM-DD_vN.md` (`.Codex/prompts/prd-template.md`는 양식 원본이므로 덮어쓰지 말 것).

---

## 문서 유형별 구조 (강제)

산출물 작성 요청 시 **유형을 먼저 판별하고, 매칭 템플릿 구조를 그대로 따른다**. 색인: `.Codex/prompts/templates/README.md`.

| 문서 유형 | 템플릿 |
|---|---|
| PRD·기획서 | `.Codex/prompts/prd-template.md` |
| 기능 스펙 | `.Codex/prompts/spec-template.md` |
| VoC·정성분석 보고서 | `.Codex/prompts/templates/voc-analysis-template.md` |
| 경쟁사 리서치 | `.Codex/prompts/templates/competitor-research-template.md` |
| 데이터 분석 보고서 | `.Codex/prompts/templates/data-analysis-template.md` |
| 설문 설계서 | `.Codex/prompts/templates/survey-template.md` |
| 실험 설계서 | `.Codex/prompts/templates/experiment-template.md` |
| 평가 루브릭 | `.Codex/prompts/templates/rubric-template.md` |

- **판별 애매 시**: 검증/판정 대상으로 결정(피드백 분류→VoC, 로그·수치→데이터분석, 제품 비교→경쟁사, 조건별 실행→실험, 반복 판정 기준→루브릭). 그래도 애매하면 데이터 분석 골격.
- **리서치/분석 공통 골격**: 요약(TL;DR) → 본문 → 시사점·액션 → 부록(데이터·한계). 모수(n)·출처·기간·한계 항상 명시, 추론은 "가설:" 표기.
- **템플릿 원본은 덮어쓰지 말 것** (`.Codex/prompts/` 하위는 양식).
- career 폴더(개인 문서)는 구조 표준화 대상 아님.

---

## 산출물 파일명 규칙

**파일명**: `YYYY-MM-DD_{주제}_vN.{확장자}` (예: `2026-04-18_onboarding-spec_v1.md`)
**최신본**: 현재 최종 버전에만 `_최신` 접미사. 새 버전 생성 시 이전 `_최신` 제거.

**파일 첫 줄 메타데이터 (필수)**:
```
> 생성: YYYY-MM-DD | 작성자: [이름]+Codex | 맥락: [한 줄 배경]
```

산출물 저장 후 해당 폴더 `README.md` 인덱스 표에 한 줄 추가.

---

## 컨텍스트 관리

- **50% 도달**: `/compact Focus on [작업명], drop [불필요한 내용]`
- **70% 도달**: `/compact` 또는 `/clear` 반드시 실행
- **세션 이어가기**: `Codex -c` (또는 `Codex --continue`) — 프롬프트 캐시 유지로 토큰 90% 절감

### /compact 시 반드시 보존
- 수정·생성된 파일 전체 목록 (경로 포함)
- 현재 진행 중인 태스크 상태
- 결정된 방향·정책 (번복 방지)
- 발생한 에러와 해결 방법

---

## 모델 선택

기본값: **Sonnet**. 결정 트리: `.Codex/prompts/model-select.md`

| 모델 | 언제 |
|---|---|
| Haiku | 단순 반복·짧은 Q&A |
| Sonnet | 기본값. 구현·문서화 |
| Opus | 설계·아키텍처·복잡한 리팩토링 |

**OpusPlan**: Plan Mode → Opus 설계 → Sonnet 구현 (비용 절감 + 설계 품질 유지)

---

## MCP 서버

- 서버 1개 = 메시지당 100~8,000토큰. 5개 조합 = 최대 20,000토큰
- **2주 이상 미사용 → 즉시 비활성화**
- 프로젝트별 `.mcp.json` (전역 등록 지양)

---

## 메모리 두 가지

1. **Anthropic auto-memory** (자동): `~/.Codex/projects/{프로젝트경로}/memory/MEMORY.md`. user/feedback/project/reference 타입 파일 자동 생성·업데이트.
2. **수동 MEMORY.md** (선택): `.Codex/memory/MEMORY.md`. 팀 공유용 인덱스. 50줄 초과 시 `archive.md`로 이동.

두 시스템이 중복되지 않도록: **수동 MEMORY.md는 팀 공유·Git 추적용**, **auto-memory는 개인 맥락 누적용**으로 구분.

---

## GitHub 규칙

```bash
# 초기 설정
git init && git remote add origin https://github.com/[유저명]/[레포명].git
echo ".env" >> .gitignore && git add . && git commit -m "init" && git push -u origin main

# 작업 루틴 — 기능 단위 완성 시마다 의미 있는 커밋 메시지로
git add outputs/[파일] && git commit -m "feat: [작업 내용]" && git push
```

- **기능 단위 완성 시점에 커밋** (오타·한 줄 수정 중간 상태는 push 금지)
- 커밋 메시지는 "무엇을·왜" 중심

---

## 작업 팁

### 후속 요청 순서 관리
동시에 여러 요청 보낼 때는 반드시 포함:
```
지금 진행 중인 작업을 다 마친 후에 이 요청을 읽어줘.
```
안 지키면 파일 덮어쓰기·계획 누락·품질 저하 발생.

### 문서 요약 요청
```
[파일경로 또는 내용] 요약해줘.
구조: 핵심 3줄 / 섹션별 한 줄 / 다음 액션
```

---

## 기본 소통 규칙

- 언어: 한국어 (고유명사·기술용어 제외)
- 어조: 두괄식·간결·개조식
- 위험 작업(삭제·force push·외부 전송): 반드시 사전 확인
- 긴 작업: Explore → Plan → 컨펌 → 실행
