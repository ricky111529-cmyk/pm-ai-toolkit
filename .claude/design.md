# 디자인 톤앤매너

> Claude가 UI 코드, 문서 포맷, 시각 자료를 만들 때 참조합니다.
> **미리캔버스(www.miricanvas.com) 실측 기준** — 2026-07-29에 브라우저 computed style로 추출했습니다.
> 추측값이 아니라 실제 사이트 값이니 그대로 쓰면 됩니다.

---

## 브랜드 컬러

```
Primary:      #21AFBF   /* 청록. 주 버튼·강조. 흰 글씨와 조합 */
Primary-dark: #1C95A2   /* hover·아웃라인 버튼 테두리·텍스트 */
Primary-tint: #E7F9FB   /* 아주 연한 청록. 섹션 배경·배지 */
Accent:       #26C7D9   /* 밝은 청록. 포인트 블록 */
Background:   #FFFFFF   /* 기본 배경 */
Surface:      #F1F2F3   /* 카드·패널·섹션 구분 배경 (#F1F2F4도 혼용) */
Text:         #16181D   /* 본문·제목 */
Text-nav:     #23242A   /* 내비게이션·보조 링크 */
Text-dim:     #8F93A3   /* 보조 텍스트·placeholder */
Ink:          #586276   /* 어두운 블록 배경 */
```

> Primary(#21AFBF) 위 흰 글씨는 대비율 약 2.5:1로 **본문에는 부적합**합니다.
> 버튼 라벨(굵기 500+, 14px 이상)에만 쓰고, 본문 텍스트는 #16181D를 씁니다.

> 접근성 기준: 본문 텍스트와 배경 대비율 **최소 4.5:1 (WCAG AA)** 확보 필수.
> 체크 도구: https://webaim.org/resources/contrastchecker/

---

## 타이포그래피

```
폰트 스택 (실측 그대로):
  "Pretendard Variable", Figtree, "IBM Plex Sans JP",
  "Pretendard JP Variable", "Pretendard Std Variable",
  -apple-system, BlinkMacSystemFont, sans-serif

  → 일본어(IBM Plex Sans JP)가 스택에 포함. JP 화면도 같은 스택으로.

폰트 크기 (실측):
  - 대제목(H1): 48px / weight 700 / letter-spacing normal
  - 리드 문장:  24px / line-height 32px (1.33)
  - 본문:       16px
  - 보조:       13~14px

폰트 굵기:
  - 제목: 700
  - 버튼·내비: 500   ← 미리캔버스는 버튼도 500. 600~700 쓰지 말 것
  - 본문: 400~500
```

---

## 어조·문체

```
기본 어조: [예: 친근하고 직접적인 / 전문적이고 간결한]

문장 규칙:
  - 한 문장 40자 이내 권장
  - 두괄식 (결론 먼저)
  - 개조식 선호 (서술형 최소화)

금지 표현:
  - [예: ~드립니다 (딱딱함)]
  - [예: ~인 것 같습니다 (불확실성 느낌)]
  - 수동태 남용

호칭:
  - 사용자 지칭: [예: 사용자 / 고객님 / 팀원]
  - 서비스 지칭: [예: 서비스명]
```

---

## UI 컴포넌트 기준

```
버튼:
  - radius: **8px** (기본) / **12px** (큰 CTA)
  - padding: [12px 20px]
  - 주요 액션: 배경 #21AFBF + 흰 글씨 + weight 500
  - 보조 액션: 배경 흰색 + 테두리·글씨 #1C95A2 (아웃라인)
  - 보조 액션: outline 또는 ghost

카드:
  - border: 1px solid [border 색상]
  - radius: [12px]
  - padding: [20~24px]

입력 필드:
  - border: 1px solid [border 색상]
  - radius: [8px]
  - focus: Primary 색상 outline

간격 시스템:
  - 4의 배수 사용 (4, 8, 12, 16, 24, 32, 48px)
```

---

## 레이아웃 원칙

- 여백이 크면 콘텐츠 볼륨을 키울 것 (빈 공간 = 낭비)
- 기본: 2열 그리드. 정보량 많으면 3열
- 모바일: 단열, 터치 타겟 최소 44px
- 최대 너비: [1280px 또는 지정값]
- 기본 좌우 여백: [80px (데스크탑) / 20px (모바일)]

---

## 금지 사항

- 과도한 그림자 (flat 기반 디자인 유지)
- 무분별한 그라디언트
- 접근성 기준 미달 대비율
- 3가지 이상의 폰트 혼용
- 의미 없는 애니메이션 (UX 목적 없는 장식)
