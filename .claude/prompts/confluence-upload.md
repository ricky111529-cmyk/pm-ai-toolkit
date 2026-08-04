# 프롬프트: Confluence 자동 업로드

> 완성된 문서를 Confluence 페이지로 자동 업로드합니다.
> 실행 전 환경변수 설정 필수.

---

## 실행 조건

- `CONFLUENCE_URL`, `CONFLUENCE_TOKEN` 환경변수 필요
- Claude Code (터미널) 환경에서 실행

---

## 환경변수 설정 방법

```bash
export CONFLUENCE_URL="https://[팀명].atlassian.net"
export CONFLUENCE_TOKEN="[Atlassian API 토큰]"
```

API 토큰 발급: https://id.atlassian.com/manage-profile/security/api-tokens

> 팁: `.env` 파일에 저장해두고 매 세션에서 `source .env`로 불러오면 편합니다.
> `.env`는 반드시 `.gitignore`에 추가하세요.

---

## 프롬프트 템플릿

```
아래 내용을 Confluence에 페이지로 올려줘.

페이지 제목: [제목]
Space: [SPACE_KEY]
내용:
[여기에 내용 붙여넣기 또는 파일 경로 지정]

Parent 페이지: [있으면 페이지 ID 또는 제목 / 없으면 생략]
```

---

## 실전 예시

```
outputs/specs/2026-04-18_onboarding-spec_v1.md 파일을
Confluence에 업로드해줘.

Space: PROD
Parent 페이지: 온보딩 기획
```

---

## 주의사항

- 같은 제목의 페이지가 이미 있으면 덮어쓰기됩니다 — 사전 확인 필요
- Confluence Cloud 기준 (Server 버전은 API 경로가 다를 수 있음)
- 업로드 완료 후 URL을 `MEMORY.md` 또는 해당 산출물 파일 상단에 기록하세요
