# 🌐 Flask 웹 인터페이스 - TC 검증 시스템

Flask 기반의 웹 인터페이스로 miri-access 토큰을 입력하고 TC 검증 결과를 한 페이지에서 확인할 수 있습니다.

## 🚀 시작하기

### 1. 의존성 설치

```bash
cd <YOUR_PATH>/chat-aip-qa
pip install -r requirements.txt
```

### 2. 앱 실행

```bash
python app.py
```

앱이 `http://localhost:5000`에서 실행됩니다.

### 3. 브라우저에서 접속

```
http://localhost:5000
```

## 📋 주요 기능

### 메인 페이지 (/)
- **miri-access 토큰 입력**: <AUTH_COOKIE_NAME> 쿠키의 JWT 토큰 입력
- **TC 유형 선택**: 검증할 10가지 유형 중 선택 (복수 선택 가능)
- **개수 설정**: 각 유형당 생성할 TC 개수 (1-10)
- **실시간 진행**: 검증 진행 상황을 진행률 바로 표시
- **결과 요약**: 전체/유효/무효/중복 수 시각화

### 결과 조회 페이지 (/results)
- **통계 대시보드**: 오류 수, 해결율, 최근 세션 표시
- **필터링**: 유형/카테고리/상태별 필터링
- **테이블**: 실패한 TC 목록 (페이지네이션 지원)
- **차트**: 유형별/카테고리별 오류율 시각화
- **세션 히스토리**: 최근 검증 세션 기록

## 🔑 토큰 획득 방법

1. 브라우저 개발자 도구 열기 (F12)
2. 응용 프로그램(Application) 탭
3. 쿠키(Cookies) → <YOUR_API_HOST>
4. `<AUTH_COOKIE_NAME>` 항목의 값 복사
5. 웹 페이지의 입력 필드에 붙여넣기

## 💾 데이터베이스

- **SQLite**: `database.db` 파일로 자동 생성
- **테이블**:
  - `failure_records`: 실패한 TC 저장
  - `validation_sessions`: 검증 세션 기록

## 🔄 API 엔드포인트

```
POST   /api/validate          - TC 검증 (SSE 스트림)
GET    /api/failures          - 실패한 TC 조회 (필터링/페이징)
GET    /api/stats             - 통계 정보
GET    /api/sessions          - 검증 세션 히스토리
PATCH  /api/failure/<id>      - 오류 해결됨 표시
DELETE /api/failure/<id>      - 오류 삭제
```

## 🛠️ 파일 구조

```
<YOUR_PATH>/chat-aip-qa/
├── app.py                    # Flask 메인 앱
├── models.py                 # SQLAlchemy 모델
├── requirements.txt          # 의존성
├── database.db               # SQLite 데이터베이스 (자동 생성)
├── templates/
│   ├── base.html            # 기본 레이아웃
│   ├── index.html           # 메인 페이지
│   └── results.html         # 결과 조회 페이지
└── static/
    ├── css/
    │   └── style.css        # 커스텀 스타일
    └── js/
        ├── app.js           # 메인 페이지 스크립트
        └── results.js       # 결과 페이지 스크립트
```

## 🎯 사용 예시

### 1. 검증 실행
1. 메인 페이지 방문
2. miri-access 토큰 입력
3. 확인할 TC 유형 선택 (예: "짧은주제", "기획안")
4. 개수 입력 (기본: 2개)
5. "검증 시작" 클릭
6. 실시간 진행 상황 확인

### 2. 결과 분석
1. 검증 완료 후 "결과 상세 보기" 클릭
2. 결과 페이지에서:
   - 통계 카드로 개요 확인
   - 필터로 특정 유형/카테고리만 보기
   - 차트로 오류율 분석
   - 테이블에서 상세 정보 확인

### 3. 오류 추적
- 테이블의 행을 클릭해 오류 상세 정보 확인
- "해결됨" 체크로 진행 상황 추적
- 오류 삭제 기능으로 관리

## ⚙️ 환경 설정

`.env` 파일이 필요하지 않습니다. 웹 페이지에서 직접 토큰을 입력합니다.

## 🔐 보안 주의사항

- 토큰은 password 입력 필드에 입력되어 화면에 표시되지 않습니다
- SQLite 데이터베이스는 로컬에 저장됩니다
- 프로덕션 환경에서는 HTTPS와 인증을 추가하세요

## 🐛 문제 해결

### 포트 5000이 이미 사용 중인 경우
```bash
# app.py의 마지막 줄 수정:
app.run(debug=True, port=8000, host='0.0.0.0')
```

### 토큰 오류
- 토큰이 만료되었을 수 있습니다
- 브라우저 개발자 도구에서 최신 토큰 다시 복사

### 데이터베이스 초기화
```bash
# database.db 삭제 후 재실행
rm database.db
python app.py
```

## 📊 성능 팁

- **일반적인 검증**: 각 유형당 2-3개 TC 생성 (약 5-10분)
- **상세 검증**: 각 유형당 5개 이상 (약 20-30분)
- 여러 유형을 동시에 검증할 수 있습니다

## 📝 버전

- **Version**: 1.0.0
- **Last Updated**: 2026-04-14
- **Flask**: 2.3.3+
- **Python**: 3.9+

---

**문제가 생기면 이슈를 등록해주세요!** 🚀
