---
description: Databricks JP VoC를 불러와 자동 분류(3계층) 후 voc-classification.xlsx에 누적 + 회차별 이력시트 생성 (반자동·사람 검토)
argument-hint: "[--backfill | --file <csv경로>]"
allowed-tools: Bash, Read, Write, Edit, Glob, mcp__databricks__execute_sql
---

# /voc-update — JP VoC 자동 분류·누적 (3계층)

너는 PM의 VoC 분석 파트너다. 새 VoC를 불러와 **자동 분류**하고 VoC 분류 워크북에 **누적**한다.

- 대상 워크북: `outputs/research/voc-classification/` 의 최신 `*_voc-classification_v*.xlsx` (현재 `2026-06-16_voc-classification_v3.xlsx`)
- 분류 기준: `outputs/research/voc-classification/classification-guide.md` (**v3 — 호출 시마다 반드시 먼저 읽고 그 규칙대로 분류**)
- 설계 근거: `outputs/specs/voc-backlog-pipeline/2026-06-08_voc-update-design_v2.md`

인자: `$ARGUMENTS`

## 분류 체계 (v3, 3계층)

- **대분류**: 긍정 / 부정 / 중립 (추이 그래프용)
- **중분류**: part1 내용품질 / part2 시각화품질 / part3 그외·UX / part0 공통·종합 / 신규기능 요청 / (없음) / 중립 (팀 파트 = 책임 소재)
- **소분류**: 01~47 통번호 — **분류는 이 번호로 기록.** 대분류·중분류는 번호로 자동 결정(guide 표 참조).
- 코드는 텍스트('01' 형식, 앞 0 유지). 신규기능 요청(40)은 **부정**이며 품질 3파트와 분리 집계.

## 0. 모드 판별

> ⚠️ **현재 운영(2026-06-12~)**: bronze+user_info 조인이 MCP 60초 타임아웃에 걸려 **`--file <csv>` 가 기본**. PM이 DA 쿼리 결과 CSV를 전달 → 이 모드로 처리. (직접 조회 자동화는 CLI 비동기 폴링 도입 시 전환)

- `--file <csv>` → **(기본 권장)** Databricks 대신 해당 CSV 사용.
  - CSV는 보통 **전체 국가**. 컬럼: `날짜, accountId, user_type, country, language_setting, 피드백, score` (+ 있으면 `트리거`/`phase`).
  - **반드시 필터**: `country == 'JP'` + `피드백` 비어있지 않음 + `날짜`가 워크북 `voc_classified` 최댓값 다음날 이후(증분, 중복 방지).
  - 그 후 ③ 번역·분류부터 진행.
- `--backfill` → 기간 `2026-01-01` ~ 오늘. (쿼리 직접 시 월별 분할/CLI 비동기 필요)
- 인자 없음(기본 증분) → 기간 = (워크북 `voc_classified` `날짜` 최댓값 + 1일) ~ 오늘.

## 1. 준비

1. 분류 기준서(`classification-guide.md`, v3)를 읽는다.
2. 대상 워크북을 찾아 `voc_classified` 시트의 기존 `날짜` 최댓값을 구한다(증분 시작점). 워크북이 없으면 사용자에게 알리고 중단.

## 2. VoC 조회 (폴백 모드면 CSV 로드)

`mcp__databricks__execute_sql`로 아래 확정 쿼리 실행. `{start}`/`{end}` 치환.

⚠️ **소스**: `bronze.<workspace>_user_feedback.mc_user_feedback` (gold는 6/2 적재 중단). AIP 필터 `option.preset_key.S='AI_PRESENTATION'`, 피드백 `comment`, 시각 `feedbackTime`(포맷 제각각 try_to_timestamp 다중), 트리거 `option.phase.S`(generating/completed, **6/9~ 적재**).
⚠️ `<app>_user_info_hst`(228억행)는 `p_date=MAX` + 필요 컬럼만. 조인 무거워 **60초 타임아웃 위험** → 증분은 며칠치 OK, 넓은 기간은 CLI 비동기(`databricks api post /api/2.0/sql/statements`, warehouse `f851823d32e682bc`).

```sql
WITH user_info AS (
  SELECT a.account_id,
         COALESCE(a.main_user_type,'설문미제출') AS user_type,
         COALESCE(c.country_code, a.country, 'KR') AS country,
         COALESCE(a.language_setting,'ko') AS language_setting
  FROM (SELECT account_id, main_user_type, country, language_setting
        FROM gold.<workspace>_analytics.<app>_user_info_hst
        WHERE p_date = (SELECT MAX(p_date) FROM gold.<workspace>_analytics.<app>_user_info_hst)) a
  LEFT JOIN gold.<workspace>_analytics.<app>_sign_up_session_ga_hst b ON a.account_id = b.account_id
  LEFT JOIN gold.<workspace>_analytics.country_code_mapping_ref c ON b.country = c.country_name
),
fb AS (
  SELECT a.accountId AS account_id, a.score, a.comment AS reason,
         CASE a.option.phase.S WHEN 'generating' THEN '생성화면(T1)'
              WHEN 'completed' THEN '결과물(T2)' ELSE '' END AS trigger_phase,
         from_utc_timestamp(COALESCE(
           try_to_timestamp(a.feedbackTime,"yyyy.MM.dd HH:mm:ss"),
           try_to_timestamp(a.feedbackTime,"yyyy-MM-dd'T'HH:mm:ss.SSS'Z'"),
           try_to_timestamp(a.feedbackTime)),'Asia/Seoul') AS local_ts
  FROM bronze.<workspace>_user_feedback.mc_user_feedback a
  WHERE a.option.preset_key.S = 'AI_PRESENTATION' AND a.comment IS NOT NULL
)
SELECT DATE(fb.local_ts) AS `날짜`, fb.account_id, b.user_type, b.country, b.language_setting,
       fb.score, fb.reason AS `피드백`, fb.trigger_phase AS `트리거`
FROM fb
INNER JOIN user_info b ON fb.account_id = b.account_id
WHERE b.country = 'JP'
  AND DATE(fb.local_ts) BETWEEN DATE('{start}') AND DATE('{end}')
ORDER BY `날짜`
```

조회 건수를 먼저 보고. (기간 넓으면 월별 분할)

## 3. 자동 분류 + 번역

각 `피드백`(reason 일본어)에 대해:
- **한국어 번역**을 만들어 `피드백(한국어)` 채운다.
- **분류 기준서(v3) 규칙대로** 소분류 번호 `분류코드`(01~46) 부여. `분류명`·`대분류`·`중분류`는 guide 매핑으로 자동 결정(소분류 번호로 정해짐).
- `월`=날짜[:7].
- **트리거**: CSV에 `트리거`/`phase` 컬럼 있으면 그대로. 없으면 account_id+피드백 원문으로 bronze(6/9~)와 매칭해 채운다(매칭 안 되면 공백, 6/9 이전은 공백).
- 빈 피드백·노이즈는 분류코드 공백(='')으로 두어 집계 제외(번역도 공백).
- 애매한 건은 따로 표시(검토용). 특히 **04 지시미반영↔05 정확도**(유저가 먼저 말한 것), **40 신규기능(없는 기능)↔기존 기능 부실** 경계 주의.

## 4. ⚠️ 사람 검토 게이트 (필수 — 여기서 멈춤)

분류 결과를 표로 제시하고 승인 대기. 승인 없이 저장 금지.
- "신규 N건 / 대분류(긍·부·중) / 중분류(part)별 분포" 요약
- 애매·경계 분류 건은 별도 표시해 확인 요청
사용자가 수정하면 반영 후 재제시. 승인 시 5로.

## 5. 워크북에 누적 (openpyxl, Bash로 python 실행)

기존 워크북을 `load_workbook`으로 열어 **서식·수식 보존**하며 작업:

1. **voc_classified 시트**: 신규 행 append. 컬럼 순서(14컬럼):
   `날짜·account_id·user_type·country·language_setting·score·피드백·피드백(한국어)·월·분류코드(01~46)·분류명·대분류·중분류·트리거`. 폰트 Arial. 트리거는 생성화면(T1)=노랑·결과물(T2)=파랑 배경.
2. **pivot_카테고리x월 재생성** (매 회차 전체 재작성, `ws._charts=[]`·`ws._images=[]`·셀 클리어 후):
   - ⚠️ **pivot은 트리거(phase) 무관 — 긍/부/중 3표만.** 트리거별 분석은 pivot이 아닌 **증분 이력시트에만** 넣는다(아래 3번). 이유: 6/9 이전 데이터는 트리거 미상이라 pivot 누적 집계엔 부적합(5/26 이전은 결과물 단독이나 5/26~6/8은 불명).
   - **표 3개 분리**: 【긍정 피드백】(초록 헤더) / 【부정 피드백】(빨강 헤더) / 【중립】(회색). 각 표는 중분류 part 그룹(■ part 소계 + 소분류 행) + 표 합계.
     - 긍정표: part1(01~03)·part2(11~12)·part3(23~29,**38 PPTX호환**)·part0(39~40)·막연감탄·추천(42~43)
     - 부정표: part1(04~10)·part2(13~22)·part3(30~37)·**신규기능(41)**·막연부정(44)
     - 중립표: 45~47
     - 집계는 `=COUNTIFS(voc_classified!$I:$I,"2026-0N",voc_classified!$J:$J,"NN")` (월=I열, 코드=J열, 코드는 텍스트 "01")
   - **그래프 3개 PNG**(matplotlib AppleGothic, `figures/voc_trend_v3.png`, `ws.add_image`): ①전체 피드백 추이(대분류 긍/부/중) ②중분류 긍정 추이(part1/2/3/0) ③중분류 부정 추이(part1/2/3+신규기능). 1×3 가로.
   - **신규기능 raw 표** (K열~): `월 / 원문(일본어) / 한국어 번역`, 분류코드='41' 건 전체. 원문·번역 wrap_text.
3. **회차 이력 시트 생성 (요약 전용 — raw 미포함)**: 시트명 `update_{오늘}` (중복 시 suffix).
   - 1행: `업데이트 요약 — {오늘}` (볼드)
   - 2행: `기간 {start}~{end} · JP · 신규 {N}건 · 소스 bronze · raw는 voc_classified 참조` (이탤릭)
   - 4행: `긍정 {pos} / 부정 {neg} / 중립 {neu}` 대분류 소계 (볼드)
   - 6행: 중분류(part)별 소계 `part1 {n} / part2 {n} / part3 {n} / part0 {n} / 신규기능 {n}`
   - 8행~: **소분류별 집계 표** (헤더 `분류코드·분류명·대분류·중분류·건수`, 긍정=초록·부정=빨강·중립=회색, 맨끝 합계).
   - **★ 트리거(진입점)별 표** (이력시트 하단에 추가 — pivot 아님): ①트리거 × 대분류 매트릭스(생성화면(T1)·결과물(T2) × 긍/부/중) ②트리거별 소분류 집계(긍정·부정·중립 각 T1/T2). **증분 데이터는 트리거가 다 있으므로(6/9~) 직접 카운트**. T1=노랑·T2=파랑.
4. 같은 파일명으로 저장(덮어쓰기).

## 6. 마무리

- README(`outputs/research/voc-classification/README.md`) 인덱스/메모 갱신
- 최종 요약 보고: 신규 건수, 대분류·중분류 분포, 생성된 이력 시트명, 저장 경로

## 원칙

- 분류는 **반드시 classification-guide.md(v3)** 기준 (일관성). 소분류 번호로 기록.
- 증분만 처리(백필 1회 제외) — 기존 날짜 이전 재조회 금지
- PII: 피드백·집계만 사용, account_id는 식별 아닌 참조용. account_id 포함 → 외부 공유 시 주의.
- 비가역 없음: 작업 전 워크북 백업 권장(`cp`), 항상 검토 후 저장
