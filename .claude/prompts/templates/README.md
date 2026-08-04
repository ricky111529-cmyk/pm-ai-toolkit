# 문서 유형별 템플릿

> outputs 산출물의 **유형별 구조 표준**. 해당 유형 문서를 새로 만들 땐 반드시 매칭 템플릿을 따른다.
> 템플릿은 "앞으로 작성분" 기준 — 기존 문서 소급 개편은 별도 작업.

## 매칭 표

| 문서 유형 | 저장 위치 | 템플릿 |
|---|---|---|
| PRD·기획서 | `outputs/specs/{주제}/` | [../prd-template.md](../prd-template.md) |
| 기능 스펙 | `outputs/specs/{주제}/` | [../spec-template.md](../spec-template.md) |
| VoC·정성분석 보고서 | `outputs/research/{주제}/` | [voc-analysis-template.md](voc-analysis-template.md) |
| 경쟁사 리서치 | `outputs/research/{주제}/` | [competitor-research-template.md](competitor-research-template.md) |
| 데이터 분석 보고서 | `outputs/research/{주제}/` | [data-analysis-template.md](data-analysis-template.md) |
| 설문 설계서 | `outputs/specs/{주제}/` | [survey-template.md](survey-template.md) |
| 실험 설계서 | `outputs/specs/{주제}/` | [experiment-template.md](experiment-template.md) |
| 평가 루브릭 | `outputs/specs/{주제}/` | [rubric-template.md](rubric-template.md) |

## 공통 규칙 (모든 유형)

- 첫 줄 메타데이터 필수: `> 생성: YYYY-MM-DD | 작성자: [이름]+Claude | 맥락: [한 줄]`
- 파일명: `YYYY-MM-DD_{주제}_vN.md`, 최신본만 `_최신`
- 리서치/분석은 **요약(TL;DR) → 본문 → 시사점·액션 → 부록(데이터·한계)** 골격 공유
- 모수(n)·출처·기간·한계를 항상 명시. 추론은 "가설:" 표기
- 저장 후 해당 폴더 README 인덱스에 한 줄 추가

## 유형 판별이 애매하면

- "무엇을 검증/판정하려는가"로 정한다: 피드백 분류 → VoC, 로그·수치 → 데이터 분석, 제품 비교 → 경쟁사, 가설을 조건별로 돌려봄 → 실험, 반복 판정 기준 → 루브릭.
- 그래도 애매하면 데이터 분석 보고서 골격을 기본으로 쓴다.
