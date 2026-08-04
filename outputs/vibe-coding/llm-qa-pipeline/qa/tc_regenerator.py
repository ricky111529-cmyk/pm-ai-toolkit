"""FAIL 기반 TC 반복 생성 모듈"""

import os
import json
from typing import List, Dict, Tuple, Any
from collections import Counter
from dotenv import load_dotenv
from google import genai

from .tc_validator import batch_validate, SUPPORTED_TYPES
from .tc_generator import generate_tcs

load_dotenv()

# Gemini 클라이언트 초기화
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# FAIL 코드 → TC 유형 매핑
# 어떤 FAIL을 테스트하기 위해 어떤 유형의 TC를 생성할지 결정
FAIL_TYPE_MAPPING = {
    "R-01": {
        "description": "JSON 파싱 실패",
        "suggested_types": ["raw텍스트", "PDF형"],
        "priority": 1
    },
    "R-02": {
        "description": "필수 키 누락",
        "suggested_types": ["raw텍스트", "PDF형", "복합조건"],
        "priority": 2
    },
    "R-03/R-10": {
        "description": "페이지 수 범위/지정 오류",
        "suggested_types": ["페이지지정", "복합조건"],
        "priority": 1
    },
    "R-04": {
        "description": "L1-L2 계층 구조 정합성 오류",
        "suggested_types": ["기획안", "raw텍스트"],
        "priority": 2
    },
    "R-06": {
        "description": "빈 메시지 포함",
        "suggested_types": ["raw텍스트", "PDF형", "모호한입력"],
        "priority": 3
    },
    "R-07": {
        "description": "중복 페이지 번호",
        "suggested_types": ["기획안", "raw텍스트"],
        "priority": 2
    },
    "R-08": {
        "description": "언어 코드 불일치",
        "suggested_types": ["언어지정", "복합조건"],
        "priority": 2
    },
    "R-09": {
        "description": "환경 언어 문자 순수성 위반",
        "suggested_types": ["언어지정", "복합조건"],
        "priority": 1
    },
    "L-01": {
        "description": "L2 메시지가 페이지 주제 미요약",
        "suggested_types": ["짧은주제", "모호한입력"],
        "priority": 2
    },
    "L-02": {
        "description": "수치/고유명사/브랜드명 미반영",
        "suggested_types": ["기획안", "raw텍스트"],
        "priority": 2
    },
    "L-03": {
        "description": "유저 입력 순서 미반영",
        "suggested_types": ["연혁", "raw텍스트"],
        "priority": 2
    },
    "L-04": {
        "description": "유사 주제 L2 중복",
        "suggested_types": ["짧은주제", "기획안"],
        "priority": 2
    },
    "L-05": {
        "description": "L1 챕터 제목이 L2 내용 미대표",
        "suggested_types": ["기획안", "raw텍스트", "PDF형"],
        "priority": 1
    },
    "L-06": {
        "description": "챕터/페이지 순서 논리성 부족",
        "suggested_types": ["연혁", "복합조건"],
        "priority": 2
    },
    "L-07": {
        "description": "기획안 페이지 구조 미일치",
        "suggested_types": ["기획안", "PDF형"],
        "priority": 2
    },
    "L-08": {
        "description": "논리적 흐름 부족",
        "suggested_types": ["raw텍스트", "복합조건"],
        "priority": 2
    },
    "L-09": {
        "description": "유사 내용 페이지 반복",
        "suggested_types": ["기획안", "짧은주제"],
        "priority": 2
    },
    "L-10": {
        "description": "특정 챕터 페이지 과다",
        "suggested_types": ["기획안", "PDF형"],
        "priority": 3
    },
    "L-11": {
        "description": "핵심 내용 누락",
        "suggested_types": ["raw텍스트", "PDF형"],
        "priority": 2
    },
    "L-12": {
        "description": "구체 수치/고유명사 추상화",
        "suggested_types": ["기획안", "raw텍스트"],
        "priority": 2
    },
    "T-01": {
        "description": "텍스트 언어 순수성 위반",
        "suggested_types": ["언어지정", "복합조건"],
        "priority": 1
    },
    "T-02": {
        "description": "텍스트가 스토리라인 미요약",
        "suggested_types": ["raw텍스트", "PDF형"],
        "priority": 2
    },
    "T-03": {
        "description": "부적절한 내용 포함",
        "suggested_types": ["모호한입력", "raw텍스트"],
        "priority": 3
    },
    "T-04": {
        "description": "유저 입력과 무관한 내용",
        "suggested_types": ["짧은주제", "모호한입력"],
        "priority": 3
    },
    "T-05": {
        "description": "형식/내용 이상 (미치환 변수 등)",
        "suggested_types": ["raw텍스트", "PDF형"],
        "priority": 2
    }
}


def map_failure_to_types(failure_code: str) -> Dict[str, Any]:
    """
    FAIL 코드 → TC 유형 및 설명 조회

    Args:
        failure_code: FAIL 코드 (예: "L-05", "R-03/R-10")

    Returns:
        {
            "description": str,
            "suggested_types": [str],
            "priority": int
        }
    """
    if failure_code in FAIL_TYPE_MAPPING:
        return FAIL_TYPE_MAPPING[failure_code]
    else:
        return {
            "description": f"알 수 없는 FAIL 코드: {failure_code}",
            "suggested_types": [],
            "priority": 999
        }


def calculate_priority(
    analysis_result: Dict[str, Any],
    weight_strategy: str = "frequency"
) -> List[Tuple[str, int, List[str], str]]:
    """
    FAIL 빈도 기준 우선순위 정렬

    Args:
        analysis_result: analytics.analyze_failures() 결과
        weight_strategy: "frequency" (빈도) | "impact" (우선순위 × 빈도)

    Returns:
        [(code, fail_count, suggested_types, description), ...]
        정렬: 우선순위 높은 순 (frequency가 많은 순)
    """
    failures_by_code = analysis_result.get("failures_by_code", {})

    result = []
    for code, fail_count in failures_by_code.items():
        mapping = map_failure_to_types(code)
        suggested_types = mapping.get("suggested_types", [])
        description = mapping.get("description", "")
        priority = mapping.get("priority", 999)

        if weight_strategy == "impact":
            # priority 낮을수록 높은 우선순위 (1이 최고)
            # fail_count와 곱해서 정렬
            weight = fail_count * (1000 - priority)
        else:  # "frequency"
            weight = fail_count

        result.append({
            "code": code,
            "fail_count": fail_count,
            "suggested_types": suggested_types,
            "description": description,
            "priority": priority,
            "weight": weight
        })

    # weight 기준 내림차순 정렬
    result.sort(key=lambda x: x["weight"], reverse=True)

    return [(r["code"], r["fail_count"], r["suggested_types"], r["description"]) for r in result]


def format_regeneration_prompt(
    failure_code: str,
    tc_type: str,
    fail_count: int,
    fail_description: str,
    existing_tcs: List[Dict[str, Any]] = None
) -> str:
    """
    재생성용 맞춤 프롬프트 생성

    Args:
        failure_code: FAIL 코드 (예: "L-05")
        tc_type: 생성할 TC 유형 (예: "기획안")
        fail_count: 해당 코드의 FAIL 횟수
        fail_description: FAIL 설명
        existing_tcs: 이미 생성된 TC 리스트 (중복 회피용)

    Returns:
        Gemini API에 보낼 프롬프트
    """
    existing_inputs = ""
    if existing_tcs:
        # 같은 유형의 기존 TC 입력값들
        same_type_tcs = [t for t in existing_tcs if t.get("tc_type") == tc_type]
        if same_type_tcs:
            existing_inputs = "\n".join([f"  • {t.get('user_input', '')[:80]}" for t in same_type_tcs[:5]])

    prompt = f"""당신은 AI 프레젠테이션 생성 서비스의 QA 전문가입니다.

[목표]
이전 QA 실행에서 특정 검증 항목이 자주 FAIL했습니다.
해당 항목을 테스트하기 위한 테스트 케이스를 3개 생성하세요.

[FAIL 항목]
코드: {failure_code}
설명: {fail_description}
이전 FAIL 횟수: {fail_count}회

[생성할 유형]
{tc_type}

[생성 가이드]
- {failure_code}를 FAIL시킬 수 있는 엣지 케이스나 상황을 의도적으로 포함
- {tc_type} 유형의 특성상 발생할 수 있는 문제 상황
- 이전과는 다른 신선한 입력값 사용

[이전에 생성된 입력값 (피해야 할 중복)]
{existing_inputs if existing_inputs else "  (없음)"}

[주의사항]
- user_input은 10자 이상 500자 이하
- 실제 사용자가 입력할 법한 자연스러운 한국어
- 유형별 규칙 준수 (예: 페이지지정은 expected_pages 필수)

반드시 아래 JSON 배열 형식으로만 응답하세요. 다른 텍스트는 절대 포함하지 마세요.
[
  {{
    "tc_id": "TC-DYN-{failure_code}-001",
    "tc_type": "{tc_type}",
    "user_input": "...",
    "slide_count": "auto",
    "expected_pages": null,
    "expected_language": "ko"
  }}
]
"""

    return prompt


def regenerate_from_failures(
    analysis_result: Dict[str, Any],
    n_per_code: int = 3,
    max_codes: int = 5,
    existing_tcs: List[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    FAIL 기반 TC 재생성

    Args:
        analysis_result: analytics.analyze_failures() 결과
        n_per_code: 각 FAIL 코드당 생성할 TC 개수
        max_codes: 처리할 최대 FAIL 코드 개수
        existing_tcs: 중복 회피 위한 기존 TC 리스트

    Returns:
        생성된 TC 리스트 (자동 검증 포함)
    """
    # FAIL 우선순위 계산
    priority_list = calculate_priority(analysis_result, weight_strategy="frequency")

    # 상위 max_codes개 처리
    priority_list = priority_list[:max_codes]

    all_generated_tcs = []
    print(f"\n🔄 FAIL 기반 TC 재생성 시작")
    print(f"   대상 FAIL 코드: {len(priority_list)}개")
    print(f"   각 코드당 생성: {n_per_code}개")

    for idx, (code, fail_count, suggested_types, description) in enumerate(priority_list, 1):
        if not suggested_types:
            print(f"\n⚠️  {idx}. {code}: 생성할 유형 미정")
            continue

        # 각 유형에서 1~2개씩 생성 (균형 유지)
        n_per_type = max(1, n_per_code // len(suggested_types))

        print(f"\n📌 {idx}. {code} ({fail_count}회 FAIL)")
        print(f"   설명: {description}")
        print(f"   생성 유형: {suggested_types}")

        for tc_type in suggested_types:
            if tc_type not in SUPPORTED_TYPES:
                continue

            # 프롬프트 생성 및 TC 생성
            prompt = format_regeneration_prompt(
                failure_code=code,
                tc_type=tc_type,
                fail_count=fail_count,
                fail_description=description,
                existing_tcs=existing_tcs or []
            )

            try:
                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt
                )
                raw = response.text.strip()
                raw = raw.replace("```json", "").replace("```", "").strip()

                tcs = json.loads(raw)
                all_generated_tcs.extend(tcs)
                print(f"      ✓ {tc_type}: {len(tcs)}개 생성")

            except Exception as e:
                print(f"      ✗ {tc_type}: 생성 실패 - {str(e)[:50]}")
                continue

    # 검증
    if all_generated_tcs:
        print(f"\n📊 생성된 TC 검증 중...")
        validation_result = batch_validate(all_generated_tcs)
        valid_tcs = [
            all_generated_tcs[detail["index"]]
            for detail in validation_result["details"]
            if detail["status"] == "VALID"
        ]

        print(f"   전체: {validation_result['total']}")
        print(f"   유효: {validation_result['valid']} ({validation_result['valid_percentage']:.1f}%)")
        print(f"   무효: {validation_result['invalid']}")

        return valid_tcs
    else:
        return []


def print_regeneration_summary(
    original_analysis: Dict[str, Any],
    generated_tcs: List[Dict[str, Any]],
    validation_result: Dict[str, Any] = None
) -> None:
    """재생성 결과 요약 출력"""

    print("\n" + "="*60)
    print("🔄 FAIL 기반 TC 재생성 요약")
    print("="*60)

    # 원본 FAIL 분석
    print(f"\n📊 원본 FAIL 현황:")
    print(f"   전체 FAIL: {original_analysis.get('fail_count', 0)}")
    print(f"   상위 FAIL 코드 5개:")
    failures = original_analysis.get("failures_by_code", {})
    for code, count in sorted(failures.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"      • {code}: {count}회")

    # 생성된 TC
    print(f"\n✨ 생성된 TC:")
    print(f"   총 개수: {len(generated_tcs)}")

    # 유형별 집계
    type_counter = Counter([tc.get("tc_type") for tc in generated_tcs])
    print(f"   유형별 분포:")
    for tc_type, count in sorted(type_counter.items(), key=lambda x: x[1], reverse=True):
        print(f"      • {tc_type}: {count}개")

    # 검증 결과
    if validation_result:
        print(f"\n✅ 검증 결과:")
        print(f"   유효: {validation_result['valid']}/{validation_result['total']}")
        print(f"   비율: {validation_result['valid_percentage']:.1f}%")

    print("\n" + "="*60 + "\n")
