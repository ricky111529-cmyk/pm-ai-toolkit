"""휴리스틱 기반 TC 생성 모듈 - 패턴 학습 및 예측적 생성"""

import os
import json
from datetime import datetime
from typing import List, Dict, Tuple, Any
from collections import defaultdict
from dotenv import load_dotenv
from google import genai

from .tc_generator import generate_tcs
from .tc_validator import batch_validate, SUPPORTED_TYPES

load_dotenv()

# Gemini 클라이언트 초기화
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# 패턴 저장소 경로
PATTERNS_FILE = ".cache/tc_patterns.json"


def _ensure_cache_dir():
    """캐시 디렉토리 생성"""
    os.makedirs(".cache", exist_ok=True)


def load_patterns(cache_file: str = PATTERNS_FILE) -> Dict[str, Any]:
    """
    패턴 저장소 로드

    Args:
        cache_file: 저장 파일 경로

    Returns:
        {
            "patterns": {
                "tc_type|code": {"fail_count": int, "pass_count": int, "fail_ratio": float, ...}
            },
            "metadata": {"total_iterations": int, "updated_at": str}
        }
    """
    _ensure_cache_dir()

    if not os.path.exists(cache_file):
        return {
            "patterns": {},
            "metadata": {
                "total_iterations": 0,
                "total_executions": 0,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        }

    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️  패턴 파일 로드 오류: {e}")
        return {
            "patterns": {},
            "metadata": {
                "total_iterations": 0,
                "updated_at": datetime.now().isoformat()
            }
        }


def save_patterns(
    patterns: Dict[str, Any],
    cache_file: str = PATTERNS_FILE
) -> bool:
    """패턴 저장소 저장"""
    _ensure_cache_dir()

    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(patterns, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"⚠️  패턴 저장 오류: {e}")
        return False


def record_execution_result(
    tc_type: str,
    validation_results: Dict[str, Any],
    cache_file: str = PATTERNS_FILE
) -> None:
    """
    TC 실행 결과를 패턴 저장소에 기록

    Args:
        tc_type: TC 유형 (예: "짧은주제", "기획안")
        validation_results: {code: {pass: bool, ...}}
            (run_tc() 또는 rule_validator.run_all_checks() 형식)
        cache_file: 저장 파일 경로
    """
    patterns_data = load_patterns(cache_file)
    patterns = patterns_data.get("patterns", {})

    # validation_results의 모든 코드 순회
    for code, result in validation_results.items():
        # 결과가 dict이고 "pass" 필드가 있는지 확인
        if isinstance(result, dict) and "pass" in result:
            is_pass = result.get("pass", None)
            if is_pass is None:
                continue  # SKIP 처리

            # 패턴 키: "tc_type|code"
            pattern_key = f"{tc_type}|{code}"

            if pattern_key not in patterns:
                patterns[pattern_key] = {
                    "fail_count": 0,
                    "pass_count": 0,
                    "total": 0,
                    "fail_ratio": 0.0,
                    "first_seen": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat()
                }

            # 카운팅
            if is_pass:
                patterns[pattern_key]["pass_count"] += 1
            else:
                patterns[pattern_key]["fail_count"] += 1

            patterns[pattern_key]["total"] += 1
            patterns[pattern_key]["fail_ratio"] = (
                patterns[pattern_key]["fail_count"] / patterns[pattern_key]["total"]
            )
            patterns[pattern_key]["last_updated"] = datetime.now().isoformat()

    # 메타데이터 업데이트
    if "metadata" not in patterns_data:
        patterns_data["metadata"] = {}

    patterns_data["metadata"]["updated_at"] = datetime.now().isoformat()

    # 저장
    patterns_data["patterns"] = patterns
    save_patterns(patterns_data, cache_file)


def analyze_patterns(
    min_samples: int = 2,
    cache_file: str = PATTERNS_FILE
) -> List[Tuple[str, str, float, int]]:
    """
    상위 FAIL 패턴 분석

    Args:
        min_samples: 최소 샘플 수 (이 이상이어야 분석 대상)
        cache_file: 패턴 파일 경로

    Returns:
        [(tc_type, code, fail_ratio, sample_count), ...]
        정렬: fail_ratio 내림차순 (높은 FAIL 비율부터)
    """
    patterns_data = load_patterns(cache_file)
    patterns = patterns_data.get("patterns", {})

    result = []
    for pattern_key, stats in patterns.items():
        if stats.get("total", 0) < min_samples:
            continue

        # 패턴 키 파싱: "tc_type|code"
        parts = pattern_key.split("|")
        if len(parts) != 2:
            continue

        tc_type, code = parts
        fail_ratio = stats.get("fail_ratio", 0.0)
        total = stats.get("total", 0)

        result.append((tc_type, code, fail_ratio, total))

    # fail_ratio 기준 내림차순 정렬
    result.sort(key=lambda x: x[2], reverse=True)

    return result


def recommend_next_types(
    top_n: int = 5,
    cache_file: str = PATTERNS_FILE
) -> List[str]:
    """
    다음에 생성할 TC 유형 추천

    Args:
        top_n: 상위 몇 개 추천할지
        cache_file: 패턴 파일 경로

    Returns:
        추천 유형 리스트
    """
    patterns = analyze_patterns(min_samples=2, cache_file=cache_file)

    # 각 유형별 평균 FAIL 비율 계산
    type_stats = defaultdict(lambda: {"total_ratio": 0.0, "count": 0})

    for tc_type, code, fail_ratio, total in patterns:
        type_stats[tc_type]["total_ratio"] += fail_ratio
        type_stats[tc_type]["count"] += 1

    # 평균 FAIL 비율 계산
    type_recommendations = []
    for tc_type, stats in type_stats.items():
        if stats["count"] > 0:
            avg_fail_ratio = stats["total_ratio"] / stats["count"]
            type_recommendations.append((tc_type, avg_fail_ratio, stats["count"]))

    # 평균 FAIL 비율 내림차순 정렬
    type_recommendations.sort(key=lambda x: x[1], reverse=True)

    # 상위 top_n개 유형 반환
    return [t[0] for t in type_recommendations[:top_n]]


def format_targeted_prompt(
    tc_type: str,
    target_patterns: List[Tuple[str, str, float, int]],
    n_per_pattern: int = 2
) -> str:
    """
    패턴 기반 맞춤 프롬프트 생성

    Args:
        tc_type: 생성할 TC 유형
        target_patterns: [(tc_type, code, fail_ratio, total), ...]
        n_per_pattern: 각 패턴당 생성 개수

    Returns:
        Gemini API에 보낼 프롬프트
    """
    # tc_type과 관련된 패턴만 필터링
    relevant_patterns = [p for p in target_patterns if p[0] == tc_type]

    if not relevant_patterns:
        relevant_patterns = target_patterns[:3]

    # 패턴 설명
    pattern_descriptions = "\n".join([
        f"  • {code}: {fail_ratio*100:.1f}% FAIL율 (샘플: {total}회)"
        for _, code, fail_ratio, total in relevant_patterns[:5]
    ])

    prompt = f"""당신은 AI 프레젠테이션 생성 서비스의 QA 전문가입니다.

[목표]
과거 여러 QA 사이클에서 수집된 패턴을 기반으로 효과적인 테스트 케이스를 생성하세요.

[발견된 패턴]
유형 "{tc_type}"에서 자주 FAIL하는 검증 항목:
{pattern_descriptions}

[생성 전략]
위의 FAIL 패턴을 재현하거나 보완할 수 있는 테스트 케이스를 생성하세요.
- 높은 FAIL 비율 항목을 명시적으로 테스트
- 패턴에서 발견된 문제점을 엣지 케이스로 포함
- 새로운 각도에서 문제 유발 가능한 입력값

[주의사항]
- user_input은 10자 이상 500자 이하
- 실제 사용자가 입력할 법한 자연스러운 한국어
- 유형별 규칙 준수

생성 개수: {n_per_pattern}개

반드시 아래 JSON 배열 형식으로만 응답하세요.
[
  {{
    "tc_id": "TC-DYN-HEUR-001",
    "tc_type": "{tc_type}",
    "user_input": "...",
    "slide_count": "auto",
    "expected_pages": null,
    "expected_language": "ko"
  }}
]
"""

    return prompt


def generate_targeted_tcs(
    n_per_pattern: int = 2,
    top_patterns: int = 5,
    cache_file: str = PATTERNS_FILE
) -> List[Dict[str, Any]]:
    """
    상위 FAIL 패턴 대상 TC 생성

    Args:
        n_per_pattern: 각 패턴당 생성 개수
        top_patterns: 상위 몇 개 패턴 대상
        cache_file: 패턴 파일 경로

    Returns:
        생성된 TC 리스트 (자동 검증 포함)
    """
    # 상위 FAIL 패턴 분석
    all_patterns = analyze_patterns(min_samples=2, cache_file=cache_file)
    target_patterns = all_patterns[:top_patterns]

    if not target_patterns:
        print("⚠️  분석 가능한 패턴이 없습니다. (샘플 수 부족)")
        return []

    # 각 유형별 추천 확인
    recommended_types = recommend_next_types(top_n=3, cache_file=cache_file)

    if not recommended_types:
        # 추천 유형이 없으면 패턴에서 유형 추출
        recommended_types = list(set([p[0] for p in target_patterns[:3]]))

    print(f"\n🎯 휴리스틱 기반 TC 생성")
    print(f"   타겟 패턴: {top_patterns}개")
    print(f"   추천 유형: {recommended_types}")
    print(f"   각 유형당: {n_per_pattern}개")

    all_generated_tcs = []

    for tc_type in recommended_types:
        if tc_type not in SUPPORTED_TYPES:
            continue

        prompt = format_targeted_prompt(
            tc_type=tc_type,
            target_patterns=target_patterns,
            n_per_pattern=n_per_pattern
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
            print(f"   ✓ {tc_type}: {len(tcs)}개 생성")

        except Exception as e:
            print(f"   ✗ {tc_type}: 생성 실패 - {str(e)[:50]}")
            continue

    # 검증
    if all_generated_tcs:
        print(f"\n   📊 검증 중...")
        validation_result = batch_validate(all_generated_tcs)
        valid_tcs = [
            all_generated_tcs[detail["index"]]
            for detail in validation_result["details"]
            if detail["status"] == "VALID"
        ]

        print(f"      유효: {validation_result['valid']}/{validation_result['total']}")
        return valid_tcs
    else:
        return []


def print_pattern_analysis(
    cache_file: str = PATTERNS_FILE,
    top_n: int = 10
) -> None:
    """패턴 분석 결과 출력"""

    patterns_data = load_patterns(cache_file)
    metadata = patterns_data.get("metadata", {})
    patterns = patterns_data.get("patterns", {})

    print("\n" + "="*60)
    print("📊 휴리스틱 패턴 분석")
    print("="*60)

    print(f"\n📈 메타데이터:")
    print(f"   전체 반복: {metadata.get('total_iterations', 'N/A')}")
    print(f"   총 실행: {metadata.get('total_executions', 'N/A')}")
    print(f"   마지막 업데이트: {metadata.get('updated_at', 'N/A')[:19]}")

    print(f"\n🔴 상위 FAIL 패턴 (top {top_n}):")

    high_fail_patterns = analyze_patterns(min_samples=1, cache_file=cache_file)[:top_n]

    if high_fail_patterns:
        for idx, (tc_type, code, fail_ratio, total) in enumerate(high_fail_patterns, 1):
            bar_length = int(fail_ratio * 30)
            bar = "█" * bar_length + "░" * (30 - bar_length)
            print(f"   {idx:2d}. {tc_type}|{code}: {fail_ratio*100:5.1f}% [{bar}] ({total}회)")
    else:
        print("   (데이터 부족)")

    print(f"\n✨ 추천 생성 유형 (top 5):")
    recommended = recommend_next_types(top_n=5, cache_file=cache_file)
    if recommended:
        for idx, tc_type in enumerate(recommended, 1):
            print(f"   {idx}. {tc_type}")
    else:
        print("   (데이터 부족)")

    print("\n" + "="*60 + "\n")
