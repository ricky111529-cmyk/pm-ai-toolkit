# Between Us

> 생성: 2026-07-29 | 작성자: 김민섭+Codex | 맥락: 두 사람이 세션 코드로 입장해 각자의 답을 원하는 순간에 공개하는 대화 여정

성격 점수나 유형으로 상대를 판정하지 않고, 서로에게 바로 닿지 않는 마음을 천천히 알아가는 Next.js 대화 카드 앱입니다.

## 포함 기능

- `이해하기 어려운 우리 → 지금의 나 → 미래의 우리` 3장으로 이어지는 공통 질문 18장
- 이메일 매직링크 로그인으로 브라우저·기기가 달라져도 같은 참여자로 복귀
- 세션 코드는 두 사람을 처음 연결하거나, 다른 기기에서 세션을 다시 여는 용도
- 카드별 답변 초안을 자동 저장하고, 상대에게는 `작성 중 / 답변 완료 / 공개됨` 상태만 표시
- 답변 내용은 작성자가 직접 `공개하기`를 누른 뒤에만 상대에게 표시
- 앱은 Supabase DB에 비공개 초안을 보관하고, 브라우저에는 본인 세션 접근 토큰만 저장

## 실행

```bash
npm install
npm run dev
```

`SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`를 `.env.local`에 넣어야 로그인·세션 생성·초안 저장 기능이 동작합니다. 공개 키(`NEXT_PUBLIC_SUPABASE_ANON_KEY`)는 브라우저에서 사용하는 키이며, service role 키와 다릅니다.

## Supabase 설정

1. [Supabase](https://supabase.com/)에서 새 프로젝트를 만듭니다.
2. **SQL Editor**에서 [schema.sql](./supabase/schema.sql)의 전체 내용을 한 번 실행합니다.
3. Project Settings의 API에서 URL, `service_role` 키, `anon` 키를 가져옵니다.
4. `.env.example`를 `.env.local`로 복사하고 네 값을 채웁니다.
5. Authentication → URL Configuration에서 Site URL과 Redirect URL에 배포 주소를 등록합니다.

`service_role` 키는 RLS를 우회하므로 절대 브라우저 코드·GitHub·공개 문서에 넣으면 안 됩니다. 이 앱은 Next.js 서버 API만 이 키를 사용하고, Supabase 테이블은 브라우저에서 직접 읽거나 쓸 수 없게 설정합니다.

## Vercel 배포

1. 이 폴더를 별도 GitHub 저장소로 올립니다.
2. Vercel에서 저장소를 Import합니다.
3. **Settings → Environment Variables**에 `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`를 등록합니다.
4. Deploy를 누릅니다.

## 다음 단계

현재는 가입 없는 익명 세션 방식입니다. 브라우저 데이터를 지우면 자신이 참여한 세션에 다시 접근할 수 없으므로, 다음 단계에서 선택형 매직링크 로그인 또는 복구 코드를 추가할 수 있습니다.
