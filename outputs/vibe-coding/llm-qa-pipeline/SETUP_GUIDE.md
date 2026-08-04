# 🚀 Chat AIP QA 시스템 — 초기 설정 가이드

> Phase 6 Option A + B 완성 (2026-04-01)

## 📋 준비물

### 1. Gemini API 키
- **출처**: https://console.cloud.google.com
- **설정**: `.env`에 `GEMINI_API_KEY=sk-...` 추가

### 2. Miricanvas 인증 토큰
- **출처**: Miricanvas 로그인 후 개발자 도구 → Application → Cookies
- **찾기**: `<AUTH_COOKIE_NAME>` 쿠키의 값 복사
- **설정**: `.env`에 `AIP_API_COOKIE_VALUE=eyJ...` 추가

## ⚙️ 설정 단계

### Step 1: 토큰 획득

#### Gemini API 키
```bash
# 1. https://console.cloud.google.com 접속
# 2. 프로젝트 생성 또는 선택
# 3. "API 및 서비스" > "사용자 인증 정보" 접속
# 4. "API 키" 생성
```

#### Miricanvas 토큰
```bash
# 1. https://<YOUR_API_HOST> 로그인
# 2. 개발자 도구 열기 (F12)
# 3. Application > Cookies > <YOUR_API_HOST>
# 4. "<AUTH_COOKIE_NAME>" 쿠키 값 복사
```

### Step 2: .env 파일 수정

```bash
vi <YOUR_PATH>/chat-aip-qa/.env
```

**필수 항목** (아래만 수정하세요):
```
# Line 5: Gemini API 키 (실제 키로 교체)
GEMINI_API_KEY=sk-YOUR_ACTUAL_KEY_HERE

# Line 11: Miricanvas JWT 토큰 (실제 토큰으로 교체)
AIP_API_COOKIE_VALUE=eyJ...YOUR_ACTUAL_TOKEN...
```

### Step 3: 설치 확인

```bash
python3 -c "from qa import collect_all_results; print('✅ 설정 완료')"
```

**에러가 나면:**
```
❌ AIP_API_COOKIE_VALUE 환경변수가 설정되지 않았습니다.

→ .env 파일의 AIP_API_COOKIE_VALUE 값이 올바른지 확인하세요
```

## 🎯 실행하기

### Option A: Excel 리포트 생성
```bash
python3 qa_run_full.py --excel-only
```

**결과:**
- `reports/qa_report_YYYYMMDD_HHMMSS.xlsx` 생성
- 2개 시트: "상세 결과" + "요약"

### Option B: HTML 대시보드 생성
```bash
python3 qa_run_full.py --html-only
```

**결과:**
- `reports/qa_dashboard_YYYYMMDD_HHMMSS.html` 생성
- 브라우저에서 열어 확인

### Option A+B: 둘 다 생성 (권장)
```bash
python3 qa_run_full.py
```

**결과:**
- Excel + HTML 동시 생성
- 약 5~10분 소요 (17개 TC × 25개 검증 항목)

## 📊 출력 결과 해석

### Excel 시트 설명

#### 시트 1: 상세 결과
- 각 TC의 모든 검증 항목 (PASS/FAIL/SKIP)
- 색상 구분:
  - 🟢 초록색 = PASS
  - 🔴 빨간색 = FAIL
  - ⚪ 회색 = SKIP

#### 시트 2: 요약
- 전체 PASS율
- 항목별 FAIL 빈도 (상위 15개)
- 카테고리별 분석

### HTML 대시보드 해석

- 📊 PASS/FAIL 비율 차트 (도넛)
- 🔴 상위 FAIL 항목 (막대 그래프)
- 📂 카테고리별 분석 (카테고리별 FAIL 수)
- 📋 상세 테이블 (FAIL 항목 리스트)

## 🚨 문제 해결

### 1. 토큰 만료
```
Error: 401 Unauthorized
```
**해결:**
- Miricanvas에 다시 로그인
- 새로운 `<AUTH_COOKIE_NAME>` 토큰 복사
- `.env` 업데이트

### 2. Gemini API 에러
```
Error: INVALID_API_KEY
```
**해결:**
- API 키 확인 (sk-로 시작)
- https://console.cloud.google.com에서 API 활성화 확인
- 할당량 확인 (일일 무료 할당량 제한)

### 3. 네트워크 타임아웃
```
Error: Request timeout
```
**해결:**
- 인터넷 연결 확인
- 개별 TC 실행: `python3 qa_run_full.py TC-001`
- AIP 서버 상태 확인

## 📁 디렉토리 구조

```
/chat-aip-qa/
├── .env                    (필수 설정)
├── qa_run_full.py          (실행 스크립트)
├── qa/
│   ├── __init__.py
│   ├── qa_pipeline.py      (AIP 호출)
│   ├── rule_validator.py   (규칙 검증)
│   ├── llm_validator.py    (LLM 검증)
│   ├── reporter.py         (Excel)
│   ├── analytics.py        (분석)
│   ├── dashboard.py        (HTML)
│   └── USAGE.md            (상세 사용법)
└── reports/                (생성된 결과)
    ├── qa_report_*.xlsx
    └── qa_dashboard_*.html
```

## ✅ 체크리스트

- [ ] `.env` 파일 생성 완료
- [ ] `GEMINI_API_KEY` 입력 완료
- [ ] `AIP_API_COOKIE_VALUE` 입력 완료
- [ ] `python3 -c "from qa import collect_all_results; print('✅')"` 성공
- [ ] `python3 qa_run_full.py` 실행 완료
- [ ] `reports/` 폴더에 Excel/HTML 확인

## 📞 다음 단계

- [x] Option A: Excel 리포팅
- [x] Option B: HTML 대시보드
- [ ] Option C: CI/CD 통합 (GitHub Actions)
- [ ] 성과 추적 (주간/월간)
- [ ] Slack 알림 연동

## 🎓 더 배우기

- **상세 사용법**: `qa/USAGE.md`
- **프로젝트 정보**: `CLAUDE.md`
- **API 문서**: `qa/USAGE.md` → "API 문서"
