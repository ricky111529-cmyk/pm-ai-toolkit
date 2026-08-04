# QA 자동화 시스템 — Phase 6 사용 가이드

## 🎯 목적

Chat AIP의 프레젠테이션 생성 품질을 **자동으로 검증**하고 **결과를 분석**하는 시스템.

## 📋 검증 항목 (25개)

### Rule-based (9개)
- R-01: JSON 파싱 성공
- R-02: 필수 키 존재
- R-03/R-10: 페이지 수 범위
- R-04: L1-L2 계층 구조
- R-06: 빈 message 없음
- R-07: 중복 페이지 번호 없음
- R-08: contentLanguage 일치
- R-09: 언어 순수성

### LLM-based (16개)
- **스토리라인** (L-01~L-12): 내용 정확성, 순서 준수, 중복 제거 등
- **텍스트 응답** (T-01~T-05): 언어 순수성, 요약 정확도 등

## 🚀 사용법

### 1. 단일 TC 실행

```python
from qa import run_tc, save_excel

# TC-001 실행
result = run_tc("TC-001")
print(result)

# Excel로 저장
save_excel([result], output_dir="./reports")
```

**결과 구조:**
```python
{
    "tc_id": "TC-001",
    "turn": 1,
    "rule": {
        "R-01": {"pass": True, "detail": "JSON 파싱 성공"},
        "R-02": {"pass": True, "detail": "필수 키 존재"},
        ...
    },
    "llm_story": {
        "L-01": {"pass": True, "reason": "..."},
        ...
    },
    "llm_text": {
        "T-01": {"pass": True, "reason": "..."},
        ...
    }
}
```

### 2. 멀티턴 TC 실행

```python
from qa import run_tc_multiturn

# TC-M01 (2턴) 실행
result = run_tc_multiturn("TC-M01")

# result는 여러 턴의 결과를 포함
print(f"Turn 1: {result[0]}")
print(f"Turn 2: {result[1]}")
```

### 3. 전체 TC 자동 수집 & 분석 (Phase 6)

```python
from qa import collect_all_results, analyze_failures, print_analysis, save_excel
from openpyxl import Workbook
from qa.analytics import generate_analysis_sheet

# 모든 TC 자동 실행 (TC-001~TC-012, TC-M01~TC-M05)
all_results = collect_all_results()

# 분석 실행
analytics = analyze_failures(all_results)

# 콘솔에 분석 결과 출력
print_analysis(all_results)

# Excel 생성 (상세 + 분석 시트 포함)
wb = Workbook()
save_excel(all_results, output_dir="./reports")  # 시트 1: 상세 결과, 시트 2: 요약
wb.save("./reports/qa_report_full.xlsx")
```

### 4. 특정 TC만 실행

```python
from qa import collect_all_results

# TC-001, TC-002, TC-M01만 실행
tc_list = ["TC-001", "TC-002", "TC-M01"]
results = collect_all_results(tc_list=tc_list)
```

### 5. 동적 TC 생성 & 실행

```python
from qa import generate_tcs, run_tc

# "짧은주제" 유형 3개 생성
tcs = generate_tcs("짧은주제", n=3)

# 생성된 TC 실행
for tc in tcs:
    result = run_tc(tc["tc_id"])
    print(f"{tc['tc_id']}: {result}")
```

## 📊 분석 결과 해석

### PASS율
```
PASS율 = PASS 항목 / (PASS + FAIL) × 100%
- 90% 이상: 양호 ✓
- 70~90%: 개선 필요 ⚠️
- 70% 미만: 긴급 조치 필수 🚨
```

### FAIL 항목별 분석
```
항목별 FAIL 빈도를 보면:
- 자주 실패하는 항목: 시스템 문제 또는 검증 기준 검토
- 특정 TC에서만 실패: 입력 데이터 문제

예:
  L-05 (챕터 제목 대표성): 8회 FAIL
  → 챕터 이름 생성 로직 검토 필요
```

### 카테고리별 분석
```
Rule-based 🔴 8회 FAIL
  → 구조적 문제 (JSON 형식, 필수 키 등)

LLM-Story 🟠 32회 FAIL
  → 내용 정확성 문제 (요약, 순서, 중복 등)

LLM-Text 🟡 24회 FAIL
  → 텍스트 응답 품질 문제 (언어, 요약 등)
```

## ⚙️ 필수 설정

### .env 파일

```bash
# Gemini API
GEMINI_API_KEY=sk-...

# Miricanvas API 쿠키 (JWT)
AIP_API_COOKIE_VALUE=eyJ...

# (선택) 캐시 설정
CACHE_ENABLED=true
CACHE_DIR=./data/cache
CACHE_EXPIRY_HOURS=168
```

## 📁 결과 저장 위치

```
/chat-aip-qa/
├── reports/
│   ├── qa_report_20260401_143522.xlsx  (상세 + 요약)
│   ├── qa_report_20260401_143522.html  (대시보드, 선택)
│   └── ...
└── data/
    ├── cache/       (API 응답 캐시)
    └── metrics/     (토큰 사용량)
```

## 🔍 다음 단계

### Phase 6 고도화
- [ ] HTML 대시보드 생성 (선택)
- [ ] 성과 추적 (PASS율 추세)
- [ ] CI/CD 통합 (자동 QA 파이프라인)
- [ ] Slack 알림 (실패 알림)

### 개선 방향
1. 실패 원인 자동 분류
2. 항목별 히스토리 추적
3. 회귀 테스트 자동화
4. 품질 메트릭 대시보드

## 📞 문제 해결

### API 키 에러
```
Error: GEMINI_API_KEY not found
→ .env 파일에 GEMINI_API_KEY 추가 필수
```

### 쿠키 만료
```
Error: 401 Unauthorized
→ <AUTH_COOKIE_NAME> 토큰 갱신 필요
→ AIP_API_COOKIE_VALUE 업데이트
```

### 타임아웃
```
Error: Request timeout
→ TC 1개씩 실행하기
→ collect_all_results(verbose=True)로 진행 상황 확인
```
