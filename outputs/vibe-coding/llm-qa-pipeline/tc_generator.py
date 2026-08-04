import json
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

TC_TYPE_DESCRIPTIONS = {
    "짧은주제": "짧은 키워드나 주제 한 줄 입력 (예: '마케팅 전략', '환경 보호의 중요성'). slideCount는 'auto'.",
    "기획안": "미리 시리즈 가상 기업(미리○○)의 상세 기획안. 시스템 페르소나 + 제약조건 + 기업 현황 + 페이지 구성 포함. 다양한 업종으로 생성.",
    "raw텍스트": "긴 단락 구분형 텍스트. 회사 소개, 사업 현황 등을 여러 단락으로 나눠 붙여넣는 형태. '이 내용을 바탕으로 발표자료를 만들어줘'로 마무리.",
    "연혁": "시간 순서 연혁 데이터. 연도/월별 주요 이벤트를 나열하고 시간 순서로 슬라이드 구성 요청.",
    "페이지지정": "정확한 페이지 수를 지정하는 요청. expected_pages 값도 함께 설정. 표지/목차 포함 N장 형태.",
    "언어지정": "특정 언어(영어, 중국어 등)로 작성 요청. expected_language를 해당 언어 코드로 설정 (en, zh 등).",
    "PDF형": "긴 문서나 보고서를 그대로 붙여넣는 케이스. 실제 문서처럼 긴 내용을 userInput에 포함.",
    "수정요청": "이미 만들어진 자료를 고쳐달라는 케이스. '기존 자료를 바탕으로 수정해줘' 형태.",
    "모호한입력": "너무 짧거나 맥락 없는 입력. 한 단어나 의미가 불분명한 입력으로 AIP가 어떻게 처리하는지 테스트.",
    "복합조건": "페이지 수 + 언어 동시 지정 등 여러 조건을 동시에 요청. expected_pages와 expected_language 모두 설정.",
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

def generate_tcs(tc_type: str, n: int) -> list:
    """Gemini를 사용해 TC를 동적으로 생성"""
    if tc_type not in TC_TYPE_DESCRIPTIONS:
        print(f"지원하지 않는 유형: {tc_type}")
        print(f"사용 가능한 유형: {list(TC_TYPE_DESCRIPTIONS.keys())}")
        return []

    prompt = GENERATE_PROMPT.format(
        tc_type=tc_type,
        tc_type_description=TC_TYPE_DESCRIPTIONS[tc_type],
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