"""생성된 TC의 형식, 중복, 품질 검증 모듈"""

import re
from datetime import datetime
from typing import Tuple, List, Dict, Any

# 지원되는 TC 유형 및 언어 코드
SUPPORTED_TYPES = [
    "짧은주제", "기획안", "raw텍스트", "연혁", "페이지지정",
    "언어지정", "PDF형", "수정요청", "모호한입력", "복합조건"
]

SUPPORTED_LANGUAGES = ["ko", "en", "zh", "ja", "pt", "es", "fr", "de"]

# 유형별 검증 규칙
TYPE_RULES = {
    "페이지지정": {
        "requires_expected_pages": True,
        "expected_pages_min": 3,
        "expected_pages_max": 50
    },
    "언어지정": {
        "requires_expected_language": True,
        "expected_language_not": ["ko"]
    },
    "복합조건": {
        "requires_expected_pages": True,
        "requires_expected_language": True,
        "expected_language_not": ["ko"]
    }
}

# ===== 개별 검증 함수 =====

def validate_tc_format(tc: Dict[str, Any]) -> Tuple[bool, str]:
    """
    TC 형식 검증 (필수 필드 완전성)

    Args:
        tc: 테스트 케이스 dict

    Returns:
        (is_valid, message)
    """
    required_fields = ["tc_id", "tc_type", "user_input", "slide_count"]

    # 필수 필드 존재 확인
    for field in required_fields:
        if field not in tc:
            return False, f"필수 필드 누락: {field}"

    # tc_id 형식 검증
    tc_id = tc.get("tc_id", "")
    if not isinstance(tc_id, str) or not tc_id.strip():
        return False, "tc_id는 비어있지 않은 문자열이어야 함"

    # TC ID 형식: TC-DYN-XXX 또는 TC-M??
    if not re.match(r"^TC-[A-Z0-9_-]+$", tc_id):
        return False, f"tc_id 형식 오류: {tc_id} (TC-DYN-001 또는 TC-M01 형식 필요)"

    # tc_type 검증
    tc_type = tc.get("tc_type", "")
    if tc_type not in SUPPORTED_TYPES:
        return False, f"지원하지 않는 tc_type: {tc_type}"

    # user_input 검증
    user_input = tc.get("user_input", "")
    if not isinstance(user_input, str) or not user_input.strip():
        return False, "user_input은 비어있지 않은 문자열이어야 함"

    # slide_count 검증
    slide_count = tc.get("slide_count", "")
    if not isinstance(slide_count, str) or not slide_count.strip():
        return False, "slide_count는 비어있지 않은 문자열이어야 함"
    if slide_count not in ["auto"] and not slide_count.isdigit():
        return False, f"slide_count는 'auto' 또는 숫자여야 함: {slide_count}"

    # optional 필드 검증
    if "expected_pages" in tc:
        val = tc["expected_pages"]
        if val is not None and not isinstance(val, int):
            return False, "expected_pages는 None 또는 정수여야 함"

    if "expected_language" in tc:
        val = tc.get("expected_language", "ko")
        if not isinstance(val, str) or val not in SUPPORTED_LANGUAGES:
            return False, f"expected_language는 지원하는 언어 코드여야 함: {val}"

    return True, "형식 검증 통과"


def validate_tc_quality(tc: Dict[str, Any]) -> Tuple[bool, str]:
    """
    TC user_input 품질 검증
    - 길이: 10~500자
    - 한글 포함 여부 및 언어 적절성
    - 의미성 (단어 반복 비율 등)

    Args:
        tc: 테스트 케이스 dict

    Returns:
        (is_valid, message)
    """
    user_input = tc.get("user_input", "").strip()

    # 길이 검증
    if len(user_input) < 10:
        return False, f"user_input이 너무 짧음 ({len(user_input)}/10자 이상)"

    if len(user_input) > 500:
        return False, f"user_input이 너무 길음 ({len(user_input)}/500자 이하)"

    # 한글 포함 여부 확인 (기본적으로 한글 입력이어야 함)
    # 단, 영어나 다른 언어만 있는 경우는 "언어지정" 유형일 가능성 높음
    korean_pattern = r"[가-힣]"
    has_korean = bool(re.search(korean_pattern, user_input))

    tc_type = tc.get("tc_type", "")

    # 언어지정 유형이 아닌데 한글이 전혀 없는 경우 경고
    if tc_type != "언어지정" and not has_korean:
        # 영문만 있어도 가능하지만, 경고는 함
        # (실제로는 통과하되 주의)
        pass

    # 의미성 검증: 같은 단어/문구 반복이 과도하지 않은지
    # 간단히 단어 토크나이징 후 중복 비율 확인
    words = user_input.split()
    if len(words) > 0:
        unique_words = len(set(words))
        repetition_ratio = 1 - (unique_words / len(words))
        if repetition_ratio > 0.5:  # 50% 이상 같은 단어 반복
            return False, f"단어 반복이 과도함 ({repetition_ratio*100:.1f}%)"

    # 특수문자 과다 검증 (연속된 특수문자 3개 이상)
    if re.search(r"[!@#$%^&*]{3,}", user_input):
        return False, "특수문자가 과도함"

    return True, "품질 검증 통과"


def validate_by_type(tc: Dict[str, Any]) -> Tuple[bool, str]:
    """
    유형별 맞춤 규칙 검증

    Args:
        tc: 테스트 케이스 dict

    Returns:
        (is_valid, message)
    """
    tc_type = tc.get("tc_type", "")

    # 규칙이 정의되지 않은 유형은 통과
    if tc_type not in TYPE_RULES:
        return True, f"유형별 규칙 검증 통과 ({tc_type})"

    rules = TYPE_RULES[tc_type]

    # expected_pages 검증
    if rules.get("requires_expected_pages", False):
        expected_pages = tc.get("expected_pages")
        if expected_pages is None:
            return False, f"'{tc_type}' 유형은 expected_pages가 필수"
        if not isinstance(expected_pages, int):
            return False, f"expected_pages는 정수여야 함: {expected_pages}"
        min_pages = rules.get("expected_pages_min", 1)
        max_pages = rules.get("expected_pages_max", 50)
        if not (min_pages <= expected_pages <= max_pages):
            return False, f"expected_pages는 {min_pages}~{max_pages} 범위여야 함: {expected_pages}"

    # expected_language 검증
    if rules.get("requires_expected_language", False):
        expected_language = tc.get("expected_language", "ko")
        if expected_language is None:
            return False, f"'{tc_type}' 유형은 expected_language가 필수"

        not_allowed = rules.get("expected_language_not", [])
        if expected_language in not_allowed:
            return False, f"'{tc_type}' 유형에서 expected_language는 {not_allowed}가 아니어야 함: {expected_language}"

    return True, f"유형 규칙 검증 통과 ({tc_type})"


def detect_duplicates(tc_list: List[Dict[str, Any]], tc_type: str = None) -> List[int]:
    """
    동일 유형 내 중복 user_input 탐지

    Args:
        tc_list: TC 리스트
        tc_type: 특정 유형만 검사 (None이면 전체)

    Returns:
        중복 TC의 인덱스 리스트
    """
    duplicates = []
    seen = {}

    for idx, tc in enumerate(tc_list):
        current_type = tc.get("tc_type", "")
        user_input = tc.get("user_input", "").strip()

        # 유형 필터링
        if tc_type is not None and current_type != tc_type:
            continue

        # 입력이 비어있으면 스킵
        if not user_input:
            continue

        # 정규화: 공백 제거, 소문자 변환
        normalized = " ".join(user_input.split()).lower()
        key = (current_type, normalized)

        # 이미 본 입력이면 중복 기록
        if key in seen:
            # 이전 인덱스와 현재 인덱스 모두 기록
            if seen[key] not in duplicates:
                duplicates.append(seen[key])
            duplicates.append(idx)
        else:
            seen[key] = idx

    return sorted(list(set(duplicates)))


def batch_validate(tc_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    전체 TC 배치 검증

    Args:
        tc_list: 검증할 TC 리스트

    Returns:
        {
            "total": int,
            "valid": int,
            "invalid": int,
            "duplicates": int,
            "details": [
                {"tc_id": str, "tc_type": str, "status": str, "reason": str}
            ]
        }
    """
    details = []
    valid_count = 0
    invalid_count = 0
    duplicate_indices = set(detect_duplicates(tc_list))

    for idx, tc in enumerate(tc_list):
        tc_id = tc.get("tc_id", f"UNKNOWN_{idx}")
        tc_type = tc.get("tc_type", "UNKNOWN")

        detail = {
            "tc_id": tc_id,
            "tc_type": tc_type,
            "index": idx,
            "status": "",
            "reason": ""
        }

        # 중복 검사
        if idx in duplicate_indices:
            detail["status"] = "DUPLICATE"
            detail["reason"] = "동일 유형 내 중복 입력"
            invalid_count += 1
            details.append(detail)
            continue

        # 형식 검증
        is_valid, msg = validate_tc_format(tc)
        if not is_valid:
            detail["status"] = "INVALID"
            detail["reason"] = f"형식 오류: {msg}"
            invalid_count += 1
            details.append(detail)
            continue

        # 품질 검증
        is_valid, msg = validate_tc_quality(tc)
        if not is_valid:
            detail["status"] = "INVALID"
            detail["reason"] = f"품질 오류: {msg}"
            invalid_count += 1
            details.append(detail)
            continue

        # 유형별 규칙 검증
        is_valid, msg = validate_by_type(tc)
        if not is_valid:
            detail["status"] = "INVALID"
            detail["reason"] = f"유형 규칙 오류: {msg}"
            invalid_count += 1
            details.append(detail)
            continue

        # 모든 검증 통과
        detail["status"] = "VALID"
        detail["reason"] = "모든 검증 통과"
        valid_count += 1
        details.append(detail)

    return {
        "timestamp": datetime.now().isoformat(),
        "total": len(tc_list),
        "valid": valid_count,
        "invalid": invalid_count,
        "duplicates": len(duplicate_indices),
        "valid_percentage": round(valid_count / len(tc_list) * 100, 1) if tc_list else 0.0,
        "details": details
    }


def filter_valid_tcs(tc_list: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    유효한 TC만 필터링

    Args:
        tc_list: 검증할 TC 리스트

    Returns:
        (valid_tc_list, validation_result)
    """
    validation_result = batch_validate(tc_list)
    valid_tcs = [
        tc_list[detail["index"]]
        for detail in validation_result["details"]
        if detail["status"] == "VALID"
    ]

    return valid_tcs, validation_result


# ===== 고급 함수 =====

def print_validation_report(validation_result: Dict[str, Any]) -> None:
    """검증 결과를 보기 좋게 출력"""

    print("\n" + "="*60)
    print("📋 TC 검증 결과 리포트")
    print("="*60)

    print(f"\n📊 통계:")
    print(f"  전체: {validation_result['total']}")
    print(f"  유효: {validation_result['valid']} ({validation_result['valid_percentage']:.1f}%)")
    print(f"  무효: {validation_result['invalid']}")
    print(f"  중복: {validation_result['duplicates']}")

    # 상태별 분류
    invalid_details = [d for d in validation_result['details'] if d['status'] != 'VALID']

    if invalid_details:
        print(f"\n⚠️  무효한 TC ({len(invalid_details)}개):")
        for detail in invalid_details[:10]:  # 최대 10개만 표시
            print(f"  • {detail['tc_id']} ({detail['tc_type']})")
            print(f"    사유: {detail['reason']}")

        if len(invalid_details) > 10:
            print(f"  ... 외 {len(invalid_details) - 10}개")
    else:
        print("\n✅ 모든 TC가 유효합니다!")

    print("\n" + "="*60 + "\n")
