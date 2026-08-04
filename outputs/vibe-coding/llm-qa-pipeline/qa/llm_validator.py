import os
import json
import concurrent.futures
from dotenv import load_dotenv
from google import genai
from openai import OpenAI

load_dotenv()

gemini_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# ===== 프롬프트 =====

STORYLINE_PROMPT = """
당신은 AI 프레젠테이션 생성 서비스의 QA 전문가입니다.
아래 [유저 입력]과 [스토리라인 JSON]을 분석하여 각 항목을 평가하세요.

[유저 입력]
{user_input}

[스토리라인 JSON]
{storyline_json}

[평가 항목]
L-01: L2 message가 해당 페이지 주제를 1문장으로 명확하게 요약하는가
L-02: 유저 입력 내 수치·고유명사·브랜드명이 L2에 정확히 반영되었는가
L-03: 유저 입력의 순서(시간순·단락순)가 L2 페이지 순서에 반영되었는가
L-04: 유사한 주제의 L2가 불필요하게 중복 생성되지 않았는가
L-05: L1 챕터 제목이 하위 L2 내용을 적절히 대표하는가
L-06: 챕터/페이지 순서가 논리적으로 자연스러운가
L-07: 기획안 입력 시 페이지 구조가 원문 목차와 일치하는가 (기획안이 아닌 경우 true)
L-08: 생성된 전체 스토리라인이 논리적 흐름을 갖추는가
L-09: 유사한 내용의 페이지가 불필요하게 반복되지 않는가
L-10: 특정 챕터에 페이지가 과도하게 몰리거나 너무 적지 않은가
L-11: 유저 입력의 핵심 내용이 스토리라인에 빠짐없이 반영되었는가
L-12: 구체적 수치나 고유명사가 있음에도 추상적으로만 서술되지 않았는가

반드시 아래 JSON 형식으로만 응답하라. 다른 텍스트는 절대 포함하지 마라.
{{
  "L-01": {{"pass": true, "reason": "평가 이유"}},
  "L-02": {{"pass": true, "reason": "평가 이유"}},
  "L-03": {{"pass": true, "reason": "평가 이유"}},
  "L-04": {{"pass": true, "reason": "평가 이유"}},
  "L-05": {{"pass": true, "reason": "평가 이유"}},
  "L-06": {{"pass": true, "reason": "평가 이유"}},
  "L-07": {{"pass": true, "reason": "평가 이유"}},
  "L-08": {{"pass": true, "reason": "평가 이유"}},
  "L-09": {{"pass": true, "reason": "평가 이유"}},
  "L-10": {{"pass": true, "reason": "평가 이유"}},
  "L-11": {{"pass": true, "reason": "평가 이유"}},
  "L-12": {{"pass": true, "reason": "평가 이유"}}
}}
"""

TEXT_PROMPT = """
당신은 AI 프레젠테이션 생성 서비스의 QA 전문가입니다.
아래 [유저 입력]과 [텍스트 응답]을 분석하여 각 항목을 평가하세요.

[유저 입력]
{user_input}

[텍스트 응답]
{text_response}

[환경 언어]
{language}

[평가 항목]
T-01: 텍스트 응답이 환경 언어({language})로만 작성되었는가.
      단 한 글자라도 다른 언어(특히 한국어)가 섞여있으면 FAIL.
T-02: 텍스트 응답이 생성된 스토리라인 내용을 정확히 요약하는가
T-03: 텍스트 응답이 부적절한 내용(욕설, 혐오, 무관한 내용 등)을 포함하지 않는가
T-04: 텍스트 응답이 유저 입력과 관련 없는 내용을 포함하지 않는가
T-05: 텍스트 응답에 형식적·내용적으로 이상하거나 비정상적인 부분이 없는가.

반드시 아래 JSON 형식으로만 응답하라. 다른 텍스트는 절대 포함하지 마라.
{{
  "T-01": {{"pass": true, "reason": "평가 이유"}},
  "T-02": {{"pass": true, "reason": "평가 이유"}},
  "T-03": {{"pass": true, "reason": "평가 이유"}},
  "T-04": {{"pass": true, "reason": "평가 이유"}},
  "T-05": {{"pass": true, "reason": "평가 이유"}}
}}
"""

FEEDBACK_PROMPT = """
당신은 AI 프레젠테이션 QA 전문가입니다.
아래 항목들에 대해 두 평가자의 의견이 엇갈렸습니다.
상대방의 평가 근거를 검토한 후, 당신의 최종 입장을 결정하세요.

[원본 데이터]
유저 입력: {user_input}
스토리라인: {content}

[불일치 항목]
{conflict_details}

각 항목에 대해 당신의 최종 판단을 내리세요.
근거가 충분하다면 입장을 바꿔도 됩니다.

반드시 아래 JSON 형식으로만 응답하라.
{format_example}
"""

JUDGE_PROMPT = """
당신은 최종 심판자(Judge) AI입니다.
두 평가자가 아래 항목들에 대해 3라운드 후에도 합의하지 못했습니다.
원본 데이터를 직접 분석하여 최종 판단을 내리세요.

[원본 데이터]
유저 입력: {user_input}
스토리라인: {content}

[불일치 항목 및 각 평가자 의견]
{conflict_details}

각 항목에 대해 명확한 근거와 함께 최종 판단을 내리세요.

반드시 아래 JSON 형식으로만 응답하라.
{format_example}
"""


# ===== 모델별 호출 함수 =====

def _call_gemini(prompt: str) -> dict:
    try:
        response = gemini_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        raw = response.text.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(raw)
    except Exception as e:
        return {"error": f"Gemini 오류: {str(e)}"}


def _call_openai(prompt: str) -> dict:
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        raw = response.choices[0].message.content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        return json.loads(raw)
    except Exception as e:
        return {"error": f"OpenAI 오류: {str(e)}"}


def _call_gpt4o_judge(prompt: str) -> dict:
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
        )
        raw = response.choices[0].message.content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        return json.loads(raw)
    except Exception as e:
        return {"error": f"GPT-4o Judge 오류: {str(e)}"}


# ===== 핵심 로직 =====

def _find_conflicts(result_a: dict, result_b: dict) -> list:
    """두 결과에서 pass 값이 다른 항목 추출"""
    conflicts = []
    for code in result_a:
        if code in result_b:
            if result_a[code].get("pass") != result_b[code].get("pass"):
                conflicts.append(code)
    return conflicts


def _build_conflict_details(conflicts: list, result_a: dict, result_b: dict,
                             label_a="Gemini", label_b="OpenAI") -> str:
    lines = []
    for code in conflicts:
        a = result_a.get(code, {})
        b = result_b.get(code, {})
        lines.append(
            f"{code}:\n"
            f"  [{label_a}] {'PASS' if a.get('pass') else 'FAIL'} - {a.get('reason','')}\n"
            f"  [{label_b}] {'PASS' if b.get('pass') else 'FAIL'} - {b.get('reason','')}"
        )
    return "\n".join(lines)


def _build_format_example(codes: list) -> str:
    items = [f'  "{code}": {{"pass": true, "reason": "판단 이유"}}' for code in codes]
    return "{{\n" + ",\n".join(items) + "\n}}"


def _run_parallel(prompt: str) -> tuple[dict, dict]:
    """Gemini + OpenAI 동일 프롬프트 병렬 호출"""
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f_gemini = executor.submit(_call_gemini, prompt)
        f_openai = executor.submit(_call_openai, prompt)
        return f_gemini.result(), f_openai.result()


def _run_parallel_asymmetric(prompt_gemini: str, prompt_openai: str) -> tuple[dict, dict]:
    """Gemini + OpenAI 각자 다른 프롬프트로 병렬 호출 (Round 2 피드백 교환용)"""
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f_gemini = executor.submit(_call_gemini, prompt_gemini)
        f_openai = executor.submit(_call_openai, prompt_openai)
        return f_gemini.result(), f_openai.result()


def _build_feedback_prompt_for_model(
    my_label: str, opponent_label: str,
    conflicts: list, my_results: dict, opponent_results: dict,
    user_input: str, content: str,
) -> str:
    """각 모델이 상대방의 반론만 받아 재평가하는 비대칭 피드백 프롬프트 생성"""
    lines = []
    for code in conflicts:
        my = my_results.get(code, {})
        opp = opponent_results.get(code, {})
        lines.append(
            f"{code}:\n"
            f"  [당신({my_label})] {'PASS' if my.get('pass') else 'FAIL'} - {my.get('reason', '')}\n"
            f"  [{opponent_label}의 반론] {'PASS' if opp.get('pass') else 'FAIL'} - {opp.get('reason', '')}"
        )
    conflict_detail = "\n".join(lines)
    format_ex = _build_format_example(conflicts)
    return FEEDBACK_PROMPT.format(
        user_input=user_input[:500],
        content=content[:1000],
        conflict_details=conflict_detail,
        format_example=format_ex,
    )


def _dual_evaluate(prompt: str, user_input: str, content: str) -> dict:
    """
    방식 B: 3라운드 평가
    Round 1: 병렬 평가
    Round 2: 불일치 항목 비대칭 피드백 교환 (각 모델이 상대방 반론만 수신)
    Round 3: 여전히 불일치 → GPT-4o 최종 judge
    """
    # Round 1: 병렬 평가
    gemini_r1, openai_r1 = _run_parallel(prompt)

    if "error" in gemini_r1 and "error" in openai_r1:
        return gemini_r1  # 둘 다 실패

    # 한쪽만 실패 시 성공한 쪽 반환
    if "error" in gemini_r1:
        return openai_r1
    if "error" in openai_r1:
        return gemini_r1

    conflicts_r1 = _find_conflicts(gemini_r1, openai_r1)
    if not conflicts_r1:
        # 완전 합의 → 바로 반환
        return _annotate_agreement(gemini_r1, source="합의(R1)")

    # Round 2: 불일치 항목 비대칭 피드백 교환
    # Gemini는 OpenAI의 반론을, OpenAI는 Gemini의 반론을 각각 전달
    prompt_for_gemini = _build_feedback_prompt_for_model(
        "Gemini", "OpenAI", conflicts_r1, gemini_r1, openai_r1, user_input, content
    )
    prompt_for_openai = _build_feedback_prompt_for_model(
        "OpenAI", "Gemini", conflicts_r1, openai_r1, gemini_r1, user_input, content
    )

    gemini_r2, openai_r2 = _run_parallel_asymmetric(prompt_for_gemini, prompt_for_openai)

    # Round 2 결과를 Round 1에 덮어쓰기
    if "error" not in gemini_r2:
        for code in conflicts_r1:
            if code in gemini_r2:
                gemini_r1[code] = gemini_r2[code]

    if "error" not in openai_r2:
        for code in conflicts_r1:
            if code in openai_r2:
                openai_r1[code] = openai_r2[code]

    conflicts_r2 = _find_conflicts(gemini_r1, openai_r1)
    if not conflicts_r2:
        return _annotate_agreement(gemini_r1, source="합의(R2)")

    # Round 3: GPT-4o 최종 judge
    conflict_detail_r2 = _build_conflict_details(conflicts_r2, gemini_r1, openai_r1)
    format_ex_r2 = _build_format_example(conflicts_r2)

    judge_prompt = JUDGE_PROMPT.format(
        user_input=user_input[:500],
        content=content[:1000],
        conflict_details=conflict_detail_r2,
        format_example=format_ex_r2,
    )

    judge_result = _call_gpt4o_judge(judge_prompt)

    # 최종 합의: judge 결과로 불일치 항목 덮어쓰기
    final = dict(gemini_r1)
    if "error" not in judge_result:
        for code in conflicts_r2:
            if code in judge_result:
                final[code] = judge_result[code]
                final[code]["_judge"] = "GPT-4o(R3)"

    return final


def _annotate_agreement(results: dict, source: str) -> dict:
    """합의된 결과에 출처 태그 추가"""
    for code in results:
        results[code]["_source"] = source
    return results


# ===== 공개 API =====

def run_llm_checks_storyline(user_input: str, storyline_json: str) -> dict:
    prompt = STORYLINE_PROMPT.format(
        user_input=user_input,
        storyline_json=storyline_json
    )
    return _dual_evaluate(prompt, user_input, storyline_json)


def run_llm_checks_text(user_input: str, text_response: str, language: str = "ja") -> dict:
    if not text_response:
        return {"error": "텍스트 응답 없음"}
    prompt = TEXT_PROMPT.format(
        user_input=user_input,
        text_response=text_response,
        language=language
    )
    return _dual_evaluate(prompt, user_input, text_response)


def print_llm_results(results: dict):
    if "error" in results:
        print(f"LLM 평가 오류: {results['error']}")
        return
    for code, result in results.items():
        status = "PASS" if result.get("pass") else "FAIL"
        reason = result.get("reason", "")
        source = result.get("_source", "")
        judge = result.get("_judge", "")
        tag = f" [{judge or source}]" if (judge or source) else ""
        print(f"{code}: {status}{tag} - {reason}")
