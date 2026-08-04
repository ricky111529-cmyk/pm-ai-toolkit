# 프롬프트 템플릿 모음

> **주의**: 이 폴더는 Claude Code의 공식 **skill 시스템이 아닙니다**.
> 자주 쓰는 작업 패턴을 프롬프트 템플릿으로 모아둔 **수동 참조용** 문서입니다.
> 사용할 때 `@.claude/prompts/[파일명]` 형태로 명시 참조해야 로드됩니다.

---

## 진짜 skill로 승격하고 싶다면

Claude Code 공식 skill은 `SKILL.md` + frontmatter(`name`, `description`) 구조가 필요합니다.
자주 쓰는 템플릿이 정착되면 공식 skill로 변환하는 걸 권장합니다.
공식 문서: https://docs.anthropic.com/en/docs/claude-code/skills

---

## 등록된 템플릿

| 파일명 | 용도 | 호출 예시 |
|--------|------|----------|
| `confluence-upload.md` | Confluence 업로드 절차·환경변수 | "@.claude/prompts/confluence-upload.md 보고 업로드해줘" |
| `context-optimize.md` | 토큰·컨텍스트 관리 체크리스트 | 세션 시작/중간 점검 시 참조 |
| `model-select.md` | 모델 선택 결정 트리 (Haiku/Sonnet/Opus) | 작업 시작 전 모델 고를 때 |
| `qa-loop.md` | 무한루프 QA — 98점까지 자동 개선 | POC·문서 완성 후 품질 검증 |
| `spec-template.md` | 기획서·PRD 템플릿 | "기획서 써줘" 요청 시 |

---

## 템플릿 추가 방법

1. `.claude/prompts/[파일명].md` 생성
2. 프롬프트 템플릿 또는 체크리스트 작성
3. 이 README 표에 한 줄 추가

---

## 제거한 파일 (2026-04-23 정리)

- `sequential-request.md`, `doc-summary.md` → CLAUDE.md 하단 "작업 팁" 섹션으로 흡수
