# PM AI Toolkit

PM 업무에 AI를 붙여 쓰기 위해 만든 작업환경과, 개인 사이드 프로젝트를 모아둔 저장소입니다.

## 왜 이 저장소가 있나

기획·리서치·데이터 분석·프로토타이핑을 AI와 페어로 하면서, **매번 다시 설명하지 않아도 되는 상태**를 만드는 게 목표였습니다. 그래서 규칙을 파일로 고정했습니다 — 어떤 문서를 어디에 저장하고, 어떤 유형이면 어떤 골격을 쓰고, 무엇을 물어봐야 하는지.

## 무엇이 들어 있나

### AI 작업환경 (`CLAUDE.md`, `AGENTS.md`, `.claude/`, `.agents/`, `.codex/`)

| | |
|---|---|
| `CLAUDE.md` | 진입 시 항상 읽는 규칙. 저장 위치 결정 트리 · 문서 유형별 강제 구조 · 라우팅. 200줄 이내로 유지 |
| `.claude/prompts/templates/` | 문서 유형별 골격 — PRD · 기능 스펙 · VoC 분석 · 경쟁사 리서치 · 데이터 분석 · 설문 · 실험 · 평가 루브릭 |
| `.claude/prompts/ux-research-guideline.md` | 리서치 질문·가설·인터뷰 설계 프레임워크 |
| `.claude/commands/` | 반복 작업 슬래시 커맨드 |
| `.claude/skills/`, `.agents/skills/` | Databricks SQL · Unity Catalog · Genie 스킬 |
| `.claude/design.md` | 디자인 토큰 참고 (공개 웹사이트를 브라우저 computed style로 추출한 것) |

설계 원칙 하나만 꼽으면 **"이 줄이 없으면 AI가 실수하는가? No면 삭제"** 입니다. 코드나 파일 구조에서 읽히는 정보는 넣지 않습니다.

### 사이드 프로젝트 (`outputs/vibe-coding/`)

| | |
|---|---|
| `band-jam-feedback` | 밴드 합주 녹음을 받아 파트별 타이밍을 분석하는 도구 (Python · demucs · librosa) |
| `between-us` | 두 사람이 세션 코드로 입장해 각자의 답을 원하는 순간에 공개하는 대화 웹앱 (Next.js) |
| `habit-app-retention-analysis` | 습관 형성 앱의 리텐션 분석 연습 |
| `travel-stamp-diary` | 여행 스탬프 기록 (단일 HTML) |
| `portfolio-aisaac` | 포트폴리오 사이트 |

### 학습 기록 (`projects/`)

- `adsp-study` — ADsP 학습 플랜
- `google-data-analytics` — Google Data Analytics Certificate 진행 기록

## 담지 않은 것

회사 업무 산출물(기획서·리서치 보고서·고객 데이터·사내 인프라 설정)은 들어 있지 않습니다. 템플릿과 규칙 같은 **방법**만 옮겼고, 사내 스키마·호스트·경로는 플레이스홀더로 치환했습니다.

## 라이선스

미정입니다. 참고하실 분은 자유롭게 보셔도 됩니다.
