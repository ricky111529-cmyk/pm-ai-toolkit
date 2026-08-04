import os
import json
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

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
      예: 일본어 텍스트 안에 한글이 섞인 경우 (예: 「인工知能」→ FAIL)
T-02: 텍스트 응답이 생성된 스토리라인 내용을 정확히 요약하는가
T-03: 텍스트 응답이 부적절한 내용(욕설, 혐오, 무관한 내용 등)을 포함하지 않는가
T-04: 텍스트 응답이 유저 입력과 관련 없는 내용을 포함하지 않는가
T-05: 텍스트 응답에 형식적·내용적으로 이상하거나 비정상적인 부분이 없는가.
      (예: {{변수명}} 형태의 미치환 변수, 깨진 문자, 언어 혼용,
      문맥에 맞지 않는 내용, 불완전한 문장 등 예상치 못한 모든 이상 징후)

반드시 아래 JSON 형식으로만 응답하라. 다른 텍스트는 절대 포함하지 마라.
{{
  "T-01": {{"pass": true, "reason": "평가 이유"}},
  "T-02": {{"pass": true, "reason": "평가 이유"}},
  "T-03": {{"pass": true, "reason": "평가 이유"}},
  "T-04": {{"pass": true, "reason": "평가 이유"}},
  "T-05": {{"pass": true, "reason": "평가 이유"}}
}}
"""

def run_llm_checks_storyline(user_input, storyline_json):
    prompt = STORYLINE_PROMPT.format(
        user_input=user_input,
        storyline_json=storyline_json
    )
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        raw = response.text.strip()
        # ```json 같은 마크다운 제거
        raw = raw.replace("```json", "").replace("```", "").strip()
        results = json.loads(raw)
        return results
    except Exception as e:
        return {"error": str(e)}

def run_llm_checks_text(user_input, text_response, language="ja"):
    if not text_response:
        return {"error": "텍스트 응답 없음"}
    
    prompt = TEXT_PROMPT.format(
        user_input=user_input,
        text_response=text_response,
        language=language
    )
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        raw = response.text.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        results = json.loads(raw)
        return results
    except Exception as e:
        return {"error": str(e)}

def print_llm_results(results):
    if "error" in results:
        print(f"LLM 평가 오류: {results['error']}")
        return
    for code, result in results.items():
        status = "PASS" if result.get("pass") else "FAIL"
        reason = result.get("reason", "")
        print(f"{code}: {status} - {reason}")