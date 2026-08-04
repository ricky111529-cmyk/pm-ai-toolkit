import json
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

TC_TYPE_DESCRIPTIONS = {
    # 단일턴 (Single-turn)
    "짧은주제": {
        "type": "single-turn",
        "description": "짧은 키워드나 주제 한 줄 입력 (예: '마케팅 전략', '환경 보호의 중요성'). slideCount는 'auto'."
    },
    "기획안": {
        "type": "single-turn",
        "description": "미리 시리즈 가상 기업(미리○○)의 상세 기획안. 시스템 페르소나 + 제약조건 + 기업 현황 + 페이지 구성 포함. 다양한 업종으로 생성."
    },
    "raw텍스트": {
        "type": "single-turn",
        "description": "긴 단락 구분형 텍스트. 회사 소개, 사업 현황 등을 여러 단락으로 나눠 붙여넣는 형태. '이 내용을 바탕으로 발표자료를 만들어줘'로 마무리."
    },
    "연혁": {
        "type": "single-turn",
        "description": "시간 순서 연혁 데이터. 연도/월별 주요 이벤트를 나열하고 시간 순서로 슬라이드 구성 요청."
    },
    "페이지지정": {
        "type": "single-turn",
        "description": "정확한 페이지 수를 지정하는 요청. expected_pages 값도 함께 설정. 표지/목차 포함 N장 형태."
    },
    "언어지정": {
        "type": "single-turn",
        "description": "특정 언어(영어, 중국어 등)로 작성 요청. expected_language를 해당 언어 코드로 설정 (en, zh 등)."
    },
    "PDF형": {
        "type": "single-turn",
        "description": "긴 문서나 보고서를 그대로 붙여넣는 케이스. 실제 문서처럼 긴 내용을 userInput에 포함."
    },
    "모호한입력": {
        "type": "single-turn",
        "description": "너무 짧거나 맥락 없는 입력. 한 단어나 의미가 불분명한 입력으로 AIP가 어떻게 처리하는지 테스트."
    },
    "복합조건": {
        "type": "single-turn",
        "description": "페이지 수 + 언어 동시 지정 등 여러 조건을 동시에 요청. expected_pages와 expected_language 모두 설정."
    },

    # 멀티턴 (Multi-turn)
    "수정요청": {
        "type": "multi-turn",
        "description": "기존 자료를 고쳐달라는 2턴 요청. 첫 턴: '이 내용으로 발표자료 만들어줘', 두 번째 턴: '레이아웃 변경해줘' 또는 '내용 수정' 형태."
    },
}

GENERATE_PROMPT = """
당신은 AI 프레젠테이션 생성 서비스의 QA 전문가입니다.
아래 [유형 설명]에 맞는 테스트 케이스를 {n}개 생성하세요.

[유형]
{tc_type}

[유형 설명]
{tc_type_description}

[주의사항]
- 각 TC는 서로 다른 주제나 소재를 사용하세요.
- user_input은 실제 사용자가 입력할 법한 자연스러운 한국어로 작성하세요.
- expected_pages는 페이지 수를 지정하는 경우에만 숫자로 설정하고, 나머지는 null로 설정하세요.
- expected_language는 특정 언어를 지정하는 경우에만 언어 코드로 설정하고, 나머지는 "ko"로 설정하세요.
- tc_id는 "TC-DYN-001" 형식으로 순번을 매기세요.

반드시 아래 JSON 배열 형식으로만 응답하라. 다른 텍스트는 절대 포함하지 마라.
[
  {{
    "tc_id": "TC-DYN-001",
    "tc_type": "{tc_type}",
    "user_input": "...",
    "slide_count": "auto",
    "expected_pages": null,
    "expected_language": "ko"
  }}
]
"""

# ===== 고정 수정 질문 2개 =====
FIXED_FOLLOWUP_QUESTIONS = [
    "전체 흐름을 좀 더 논리적으로 재구성해줘. 중간 페이지들이 앞뒤 내용과 자연스럽게 이어지도록 수정해줘.",
    "마지막 페이지를 결론 및 제안 페이지로 수정해줘. 전체 내용을 요약하고 청중에게 명확한 다음 단계를 제시해줘.",
]

# ===== LLM 수정 질문 생성 프롬프트 =====
FOLLOWUP_PROMPT = """
당신은 AIP 프레젠테이션 생성 서비스를 테스트하는 QA 전문가입니다.
아래 초기 요청으로 만들어진 발표자료에 대한 자연스러운 수정 요청 1개를 생성하세요.

[초기 요청]
{initial_input}

[요구사항]
- 이미 생성된 발표자료에 대한 구체적인 수정 요청이어야 함
- 아래 유형 중 하나로 생성:
  * 특정 페이지의 내용 수정 (예: "3페이지 헤드라인을 더 강렬하게 바꿔줘")
  * 페이지 추가 또는 삭제 (예: "경쟁사 분석 페이지를 하나 추가해줘")
  * 특정 수치나 데이터 업데이트 (예: "성장률을 15%에서 23%로 바꿔줘")
- 자연스러운 한국어로 작성
- 1,500자 이하

반드시 아래 JSON 형식으로만 응답하라.
{{"followup_question": "수정 요청 내용"}}
"""


def generate_followup_question(initial_input: str) -> str:
    """초기 입력을 기반으로 LLM이 수정 질문 1개 생성"""
    try:
        prompt = FOLLOWUP_PROMPT.format(initial_input=initial_input[:500])
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        raw = response.text.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        data = json.loads(raw)
        return data.get("followup_question", "전체적인 내용을 좀 더 간결하게 정리해줘.")
    except Exception as e:
        print(f"수정 질문 생성 오류: {e}")
        return "전체적인 내용을 좀 더 간결하게 정리해줘."


def generate_tcs(tc_type: str, n: int) -> list:
    """Gemini를 사용해 TC를 동적으로 생성"""
    if tc_type not in TC_TYPE_DESCRIPTIONS:
        print(f"지원하지 않는 유형: {tc_type}")
        print(f"사용 가능한 유형: {list(TC_TYPE_DESCRIPTIONS.keys())}")
        return []

    tc_info = TC_TYPE_DESCRIPTIONS[tc_type]
    tc_description = tc_info["description"]

    prompt = GENERATE_PROMPT.format(
        tc_type=tc_type,
        tc_type_description=tc_description,
        n=n
    )

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        raw = response.text.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        tcs = json.loads(raw)
        print(f"\n[TC 생성 완료] {tc_type} 유형 {len(tcs)}개")
        for tc in tcs:
            print(f"  - {tc['tc_id']}: {tc['user_input'][:60]}...")
        return tcs
    except Exception as e:
        print(f"TC 생성 오류: {e}")
        return []


# ===== 멀티턴 TC 생성 프롬프트 =====
MULTITURN_PROMPT = """
당신은 AI 프레젠테이션 생성 서비스의 QA 전문가입니다.
아래 조건에 맞는 '수정요청' 타입의 4턴 멀티턴 테스트 케이스를 생성하세요.

[요구사항]
- 첫 번째 턴: 특정 주제와 페이지 수를 지정하여 발표자료 스토리라인 요청
- 두 번째 턴: 특정 페이지의 내용 수정 요청
- 세 번째 턴: 페이지 추가 또는 삭제 요청
- 네 번째 턴: 제목이나 구성을 다시 수정하는 요청

[주의사항]
- 각 턴의 user_input은 자연스러운 한국어로 작성하세요
- 페이지 수는 첫 턴에서 명확히 지정하고, 2~4턴에서는 변경하거나 유지하세요
- expected_pages: 첫 턴에서의 페이지 수, 세 번째 턴에서 추가/삭제 시 업데이트
- expected_language는 모두 "ko"로 설정

반드시 아래 JSON 배열 형식으로만 응답하라. 다른 텍스트는 절대 포함하지 마라.
[
  {{
    "tc_id": "TC-MT-4TURN",
    "tc_type": "수정요청",
    "turns": [
      {{
        "turn": 1,
        "user_input": "...",
        "expected_pages": 10
      }},
      {{
        "turn": 2,
        "user_input": "...",
        "expected_pages": 10
      }},
      {{
        "turn": 3,
        "user_input": "...",
        "expected_pages": 11
      }},
      {{
        "turn": 4,
        "user_input": "...",
        "expected_pages": 11
      }}
    ]
  }}
]
"""


def generate_multiturn_tc():
    """Gemini를 사용해 4턴 멀티턴 TC를 동적으로 생성"""
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=MULTITURN_PROMPT
        )
        raw = response.text.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        tcs = json.loads(raw)

        if tcs and len(tcs) > 0:
            tc = tcs[0]
            print(f"\n[멀티턴 TC 생성 완료] {tc['tc_id']}")
            print(f"  - 4턴 멀티턴 TC (수정요청)")
            return tc
        return None
    except Exception as e:
        print(f"멀티턴 TC 생성 오류: {e}")
        return None