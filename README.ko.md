# 김민섭 — Product / UX Research

**한국어** · [日本語](README.md)

유저의 "왜"를 파고들어 가설을 세우고, 데이터로 검증하면서 제품을 밀고 나갑니다.
디자인 SaaS 기업에서 일본 시장향 AI 제품 기획(Assistant PdM)을 하고 있습니다.

📄 **케이스 스터디** → [포트폴리오](outputs/vibe-coding/portfolio-aisaac)
🖱 **바로 만져보기** → [디자인 평가 뷰어 데모](https://ricky111529-cmyk.github.io/pm-ai-toolkit/outputs/vibe-coding/design-eval-viewer/) — `샘플 불러오기`를 누르면 데이터 없이 바로 동작합니다

---

## 이 저장소는 무엇인가

**기획자가 자기 작업환경을 직접 설계한 기록입니다.**

AI와 페어로 일하면서 가장 비효율적이었던 건 매번 맥락을 다시 설명하는 일이었습니다. 그래서 규칙을 파일로 고정했습니다 — 어떤 문서를 어디에 저장하고, 어떤 유형이면 어떤 골격을 쓰고, 무엇을 되물어야 하는지.

| | |
|---|---|
| [`CLAUDE.md`](CLAUDE.md) | 진입 시 항상 읽는 규칙. 저장 위치 결정 트리 · 문서 유형별 강제 구조 · 라우팅 |
| [`.claude/prompts/templates/`](.claude/prompts/templates) | 문서 유형 8종의 골격 — PRD · 기능 스펙 · VoC 분석 · 경쟁사 리서치 · 데이터 분석 · 설문 · 실험 · 평가 루브릭 |
| [`.claude/prompts/ux-research-guideline.md`](.claude/prompts/ux-research-guideline.md) | 리서치 질문·가설·인터뷰 설계 프레임워크 (질문 6기준 + 인사이트 4질문) |
| [`.claude/skills/`](.claude/skills) | Databricks SQL · Unity Catalog · Genie |

설계 원칙은 하나입니다. **"이 줄이 없으면 AI가 실수하는가? No면 삭제."** 코드나 파일 구조에서 읽히는 정보는 넣지 않습니다. 그래서 `CLAUDE.md`는 200줄을 넘기지 않습니다.

---

## 어떻게 일하는가

**가설과 검증** — 무엇이·왜 일어나는지 찾아내고 데이터로 확인합니다.
AI 슬라이드 생성의 초기 실패를 3만 건 분석해 세 갈래(되묻기 / 부적절한 거부 / 빈 응답)로 분류하고, 13.4% → 5.1%로 낮췄습니다. 발견부터 검증까지 혼자 닫아본 경험입니다.

**오너십** — 지시를 기다리지 않고 문제를 정의합니다.
기획이 통하지 않는 이유를 파보니 팀이 유저를 깊이 이해하지 못하는 게 근본이었습니다. 1on1에서 문제를 제기해 UX 리서치를 직접 시작했습니다. 현재 진행 중입니다.

**직접 만든다** — 기획만 하지 않고 검증 도구를 만듭니다.
LLM 품질 평가 파이프라인을 Python으로 자작했습니다([코드와 회고](outputs/vibe-coding/llm-qa-pipeline)). 자사 API로 슬라이드를 자동 생성하고 외부 LLM이 PASS/FAIL을 판정하는 2층 구조(규칙 기반 + LLM 기반)였습니다. **실운용까지는 가지 못했습니다** — "LLM으로 LLM을 평가하는" 판정 정확도를 담보하지 못한 게 벽이었습니다. 이 회고가 다음 도구의 설계가 됐습니다 → [`design-eval-viewer`](outputs/vibe-coding/design-eval-viewer): 자동 판정을 먼저 만들지 않고, **사람이 실물을 보고 판단을 남기는 환경**을 먼저 만들었습니다.

---

## 만든 것

| | |
|---|---|
| [`band-jam-feedback`](outputs/vibe-coding/band-jam-feedback) | 밴드 합주 녹음에서 파트별 타이밍을 분석하는 도구. Python · demucs로 소스 분리 · librosa로 온셋 검출 |
| [`between-us`](outputs/vibe-coding/between-us) | 두 사람이 세션 코드로 입장해 각자의 답을 원하는 순간에 공개하는 대화 웹앱. Next.js |
| [`habit-app-retention-analysis`](outputs/vibe-coding/habit-app-retention-analysis) | 습관 형성 앱의 리텐션 분석 |
| [`travel-stamp-diary`](outputs/vibe-coding/travel-stamp-diary) | 여행 스탬프 기록. 의존성 없는 단일 HTML |
| [`design-eval-viewer`](outputs/vibe-coding/design-eval-viewer) | AI 결과물을 전 페이지 썸네일 + 맥락과 함께 보고 **페이지 단위로** 평가를 남기는 단일 HTML 앱. 큰 gz 를 브라우저에서 스트리밍 해제 · 점진 렌더링 · 컬럼 자동 분류. [**데모 열기 ↗**](https://ricky111529-cmyk.github.io/pm-ai-toolkit/outputs/vibe-coding/design-eval-viewer/) |
| [`llm-qa-pipeline`](outputs/vibe-coding/llm-qa-pipeline) | AI 채팅 응답 품질을 자동 검증하는 파이프라인. 2층 판정(규칙 + LLM) · 멀티턴 자동화 · Flask UI. **실운용까지는 가지 못했습니다** — [회고](outputs/vibe-coding/llm-qa-pipeline/PORTFOLIO.md) |
| [`portfolio-aisaac`](outputs/vibe-coding/portfolio-aisaac) | 포트폴리오 사이트 |

---

## 다룰 수 있는 것

정직하게 적습니다.

| | |
|---|---|
| 기획·리서치 | PRD·기능 스펙 작성, 인터뷰 설계, 정성 분석, VoC 분류 체계 |
| 데이터 | SQL(Databricks). 기술통계·퍼널·코호트·A/B 결과 해석은 스스로 / **가설검정·회귀는 개념 수준이며 AI 보조로 씁니다** / 모델링은 아직 못 합니다 |
| 만들기 | Python(오디오 분석·LLM 파이프라인), 단일 HTML 앱, Next.js 기초 |
| 언어 | 한국어 · 일본어 (JLPT N1) |
| 학습 중 | [ADsP](projects/adsp-study) · [Google Data Analytics Certificate](projects/google-data-analytics) |

---

## 담지 않은 것

회사 업무 산출물(기획서·리서치 보고서·고객 데이터·사내 인프라 설정)은 들어 있지 않습니다. 재사용 가능한 **방법**만 옮겼고, 사내 스키마·호스트·경로는 플레이스홀더로 치환했습니다.

## 연락

ricky111529@gmail.com
