import requests
import json
import re
import sys
from tc_generator import generate_tcs
from dotenv import load_dotenv
from rule_validator import run_all_checks
from llm_validator import run_llm_checks_storyline, run_llm_checks_text, print_llm_results
from reporter import save_excel, print_summary

load_dotenv()

# ===== 설정 =====
URL = "https://<YOUR_API_HOST>/<YOUR_CHAT_ENDPOINT>?domain=staging&language=ja"

cookies = {
    "<AUTH_COOKIE_NAME>": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJoZWxwX21vZGUiOmZhbHNlLCJ1aWQiOiJjMjIzNDVlZi03MzZlLTZlZTctMTEwYy0wY2EzOTIwN2Q1NDYiLCJhY2NvdW50X2lkIjoyMTA0NjgwMSwiYWRtaW5faWQiOjAsInNlc3Npb25faWQiOiIzZDExYzNlMy05ZGQxLTRhNWQtYjVhMi0yODNjMTUyYjljMzUiLCJleHAiOjE3NzQ5MjMwODZ9.uWBLpgBdunC-OwbSqxhDL2lu6_ESrjOpNB6tpVC825Q"
}

headers = {
    "Content-Type": "application/json"
}

# ===== AIP 단일턴 호출 =====
def call_aip(user_input, slide_count="auto"):
    print("AIP 호출 중...")
    payload = {
        "language": "ja",
        "message": json.dumps({
            "slideCount": slide_count,
            "userInput": user_input
        })
    }
    response = requests.post(URL, json=payload, headers=headers, cookies=cookies)
    print("AIP 응답 완료!")
    return response.text

# ===== AIP 멀티턴 호출 =====
def call_aip_multiturn(user_input, session_id):
    print("AIP 멀티턴 호출 중...")
    payload = {
        "language": "ja",
        "sessionId": session_id,
        "message": json.dumps({
            "userInput": user_input
        })
    }
    response = requests.post(URL, json=payload, headers=headers, cookies=cookies)
    print("AIP 응답 완료!")
    return response.text

# ===== chunk content 전체 합치기 =====
def get_full_content(response_text):
    content = ""
    for line in response_text.strip().split("\n"):
        try:
            chunk = json.loads(line)
            if chunk.get("type") == "chunk":
                content += chunk.get("content", "")
        except:
            pass
    return content

# ===== 세션 ID 추출 =====
def get_session_id(response_text):
    for line in response_text.strip().split("\n"):
        try:
            chunk = json.loads(line)
            if chunk.get("type") == "complete":
                return chunk.get("content", "")
        except:
            pass
    return None

# ===== 텍스트 응답 추출 (JSON 뒷부분) =====
def extract_text(response_text):
    content = get_full_content(response_text)
    if "--STORYLINE_JSON--" in content:
        after_json = content.split("--STORYLINE_JSON--")[1]
        try:
            json_start = after_json.index("{")
            decoder = json.JSONDecoder()
            _, end_idx = decoder.raw_decode(after_json, json_start)
            text = after_json[end_idx:].strip()
        except:
            text = ""
    else:
        text = content.strip()
    return text

# ===== 스토리라인 JSON 추출 =====
def extract_json(response_text):
    content = get_full_content(response_text)
    if "--STORYLINE_JSON--" not in content:
        return None

    json_start = content.index("--STORYLINE_JSON--") + len("--STORYLINE_JSON--")
    json_str = content[json_start:].strip()

    brace_start = json_str.index("{")
    json_str = json_str[brace_start:]

    depth = 0
    end_idx = 0
    for i, ch in enumerate(json_str):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        if depth == 0:
            end_idx = i + 1
            break

    return json_str[:end_idx]

# ===== 단일턴 TC 실행 =====
def run_tc(tc_id, user_input, slide_count="auto", expected_pages=None, expected_language="ko"):
    print(f"\n{'='*50}")
    print(f"TC: {tc_id}")
    print(f"input: {user_input[:50]}...")
    print(f"{'='*50}")

    response_text = call_aip(user_input, slide_count)

    text_response = extract_text(response_text)
    if text_response:
        print(f"텍스트 응답: {text_response}")

    session_id = get_session_id(response_text)
    print(f"세션 ID: {session_id}")

    storyline_json = extract_json(response_text)
    if not storyline_json:
        print("JSON 추출 실패")
        return {
            "session_id": session_id,
            "result": {"tc_id": tc_id, "turn": 1, "rule": None, "llm_story": None, "llm_text": None}
        }

    # Rule-based 검증
    print("\n=== Rule-based 검증 ===")
    results = run_all_checks(
        storyline_json,
        expected_pages=expected_pages,
        expected_language=expected_language,
        text_response=text_response,
        environment_language="ja"
    )
    for code, result in results.items():
        status = "PASS" if result["pass"] else "FAIL"
        print(f"{code}: {status} - {result['detail']}")

    # LLM-based 검증 (스토리라인)
    print("\n=== LLM 평가 (스토리라인) ===")
    llm_results = run_llm_checks_storyline(user_input, storyline_json)
    print_llm_results(llm_results)

    # LLM-based 검증 (텍스트 응답)
    llm_text_results = None
    if text_response:
        print("\n=== LLM 평가 (텍스트 응답) ===")
        llm_text_results = run_llm_checks_text(user_input, text_response, language="ja")
        print_llm_results(llm_text_results)

    return {
        "session_id": session_id,
        "result": {
            "tc_id": tc_id,
            "turn": 1,
            "rule": results,
            "llm_story": llm_results,
            "llm_text": llm_text_results,
        }
    }

# ===== 멀티턴 TC 실행 =====
def run_tc_multiturn(tc_id, turns):
    print(f"\n{'='*50}")
    print(f"TC: {tc_id} (멀티턴)")
    print(f"{'='*50}")

    session_id = None
    turn_results = []

    for i, turn in enumerate(turns):
        print(f"\n--- 턴 {i+1} ---")
        print(f"input: {turn['input'][:50]}...")

        if i == 0:
            response_text = call_aip(
                turn["input"],
                turn.get("slide_count", "auto")
            )
        else:
            if not session_id:
                print("세션 ID 없음 - 멀티턴 불가")
                return turn_results
            response_text = call_aip_multiturn(turn["input"], session_id)

        session_id = get_session_id(response_text)
        print(f"세션 ID: {session_id}")

        text_response = extract_text(response_text)
        if text_response:
            print(f"텍스트 응답: {text_response}")

        storyline_json = extract_json(response_text)
        if not storyline_json:
            print("JSON 추출 실패")
            turn_results.append({
                "tc_id": tc_id,
                "turn": i + 1,
                "rule": None,
                "llm_story": None,
                "llm_text": None,
            })
            continue

        # Rule-based 검증
        print("\n=== Rule-based 검증 ===")
        results = run_all_checks(
            storyline_json,
            expected_pages=turn.get("expected_pages"),
            expected_language=turn.get("expected_language", "ko"),
            text_response=text_response,
            environment_language="ja"
        )
        for code, result in results.items():
            status = "PASS" if result["pass"] else "FAIL"
            print(f"{code}: {status} - {result['detail']}")

        # LLM-based 검증 (스토리라인)
        print("\n=== LLM 평가 (스토리라인) ===")
        llm_results = run_llm_checks_storyline(turn["input"], storyline_json)
        print_llm_results(llm_results)

        # LLM-based 검증 (텍스트 응답)
        llm_text_results = None
        if text_response:
            print("\n=== LLM 평가 (텍스트 응답) ===")
            llm_text_results = run_llm_checks_text(turn["input"], text_response, language="ja")
            print_llm_results(llm_text_results)

        turn_results.append({
            "tc_id": tc_id,
            "turn": i + 1,
            "rule": results,
            "llm_story": llm_results,
            "llm_text": llm_text_results,
        })

    return turn_results

# ===== TC 맵 =====
def build_tc_map():
    return {
        "TC-001": lambda: run_tc("TC-001", """[시스템 페르소나]
너는 브랜드 전략 전문가이자 광고 제안서 작가다.
아래 제공된 [미리애드 사업 현황]을 분석하여,
클라이언트의 신뢰를 얻을 8페이지 분량의 에이전시 소개 스토리라인을 생성하라.

[엄격 제약 조건]
- 데이터 보존: 설립 연도(2019년), 직원 수(32명), 연간 집행 광고비(약 240억 원) 수정 불가.
- 페이지 구성: 챕터 구분 없이 아래 8페이지를 순서대로 구성하라.
- 금지 사항: '창의적인', '열정적인' 같은 추상적 표현 금지.

[미리애드 사업 현황]
- 에이전시명: 미리애드(MiriAd)
- 설립: 2019년 / 서울 마포구 소재
- 인원: 기획 12명 / 디자인 10명 / 미디어 바잉 7명 / 데이터 분석 3명 (총 32명)
- 연간 광고비 집행 규모: 약 240억 원 (2024년 기준)
- 주요 클라이언트: 뷰티, 식음료, 모바일 게임 버티컬 특화
- 핵심 강점: 퍼포먼스 마케팅 + 브랜딩 통합 운용, 자체 데이터 분석 플랫폼 '미리인사이트' 보유
- 수상: 2023 대한민국 광고대상 디지털 부문 금상

[지정된 8페이지 구성]
P1. 표지 / P2. 미리애드 한눈에 보기 / P3. 집중 버티컬
P4. 통합 운용 방식 / P5. 미리인사이트 소개 / P6. 캠페인 성과
P7. 팀 구성 및 역할 / P8. 협업 제안""", expected_pages=8),

        "TC-002": lambda: run_tc("TC-002", """[시스템 페르소나]
너는 바이오 투자 분야 전문 IR 컨설턴트다.
아래 [미리바이오 IR 자료]를 분석하여,
시리즈B 투자자의 의사결정을 이끌어낼 12페이지 IR 덱 스토리라인을 생성하라.

[엄격 제약 조건]
- 데이터 보존: 목표 조달액(150억 원), 파이프라인 수(3개), 임상 단계(2a상) 수정 불가.
- 챕터 구조: 아래 4개 챕터와 소속 페이지를 100% 준수하라.
- 금지 사항: '혁신적인 신약', '글로벌 시장 공략' 같은 공허한 표현 금지.

[미리바이오 IR 자료]
- 기업명: 미리바이오(MiriBio) / 설립: 2021년 / KAIST 기술 스핀오프
- 핵심 기술: 표적 단백질 분해(TPD) 플랫폼 기반 항암제 개발
- 주요 파이프라인:
  · MB-101: KRAS G12C 변이 고형암 / 임상 2a상 진입
  · MB-202: STAT3 타겟 혈액암 / IND 제출 완료
  · MB-303: 전임상 단계 (면역항암 병용)
- 특허: 국내 7건, PCT 출원 3건
- 기조달: 시드 30억(2021), 시리즈A 80억(2023)
- 이번 목표: 시리즈B 150억 원 조달

[챕터 및 페이지 구성]
[챕터 1: 문제와 기회] P1~P3
[챕터 2: 미리바이오 기술] P4~P6
[챕터 3: 임상 성과] P7~P9
[챕터 4: 투자 제안] P10~P12""", expected_pages=12),

        "TC-003": lambda: run_tc("TC-003", """[시스템 페르소나]
너는 20년 경력의 정부 R&D 과제 전문 제안서 컨설턴트다.
아래 [미리핀테크 과제 기획안]을 분석하여,
표지와 목차를 포함한 정확히 10페이지 분량의 제안 스토리라인을 생성하라.

[엄격 제약 조건]
- 데이터 보존: 과제 예산(25억 원), 수행 기간(18개월), 목표 지표(금융 소외 계층 10만 명 접근성 개선) 수정 불가.
- 페이지 수: 표지(P1) + 목차(P2) 포함 반드시 정확히 10페이지.

[미리핀테크 과제 기획안]
- 기업명: 미리핀테크(MiriFintech) / 설립: 2020년 / 서울 여의도 소재
- 핵심 서비스: 중·저신용자 대상 AI 신용 스코어링 및 소액 대출 중개 플랫폼
- 과제 예산: 25억 원 (정부 출연 18억 / 민간 부담 7억)
- 수행 기간: 18개월
- 핵심 목표: 금융 소외 계층 10만 명 신용 서비스 접근성 개선

[지정된 10페이지 구성]
P1. 표지 / P2. 목차 / P3. 문제 정의 / P4. 제안 솔루션
P5. 기술적 차별성 / P6. 수행 체계 / P7. 추진 일정
P8. 예산 계획 / P9. 성과 지표 / P10. 기대 효과 및 확산 계획""", expected_pages=10),

        "TC-004": lambda: run_tc("TC-004", """아래 사업 개요 텍스트를 바탕으로 미리로지스 사업 소개 발표자료를 만들어줘.
내용 구조는 네가 판단해서 챕터를 나눠줘.

미리로지스는 2017년 설립된 중견 물류 솔루션 기업으로, 현재 국내 제조·유통사 180개사에 WMS와 TMS를 통합 공급하고 있다.
ARR 480억 원, 전년 대비 27% 성장. 자체 AI 수요 예측 엔진 '미리옵스(MiriOps)' 보유.
고객사 A사 적용 결과 재고 회전율 34% 개선, 폐기 손실 19% 감소.
2026년 동남아 시장 진출 예정. 베트남·태국 3PL 파트너 총판 계약 완료.
임직원 230명, R&D 89명(39%). NRR 118% (업계 평균 105%)."""),

        "TC-005": lambda: run_tc("TC-005", """[시스템 페르소나]
너는 교육부·과기정통부 정책 사업 수주 전문가이자 제안서 전문 작가다.
아래 제공된 [미리에듀 사업 제안 개요]를 분석하여,
3개 챕터, 총 12페이지 스토리라인을 생성하라.

[엄격 제약 조건]
- 데이터 보존: 사업 예산(45억 원), 목표 수혜 학생 수(전국 중학생 5만 명) 수정 불가.
- 챕터 구조: 아래 지정된 3개 챕터와 12개 페이지를 100% 준수하라.

[미리에듀 사업 제안 개요]
- 기업명: 미리에듀(MiriEdu) / 설립: 2018년 / 경기 판교 소재
- 플랫폼: AI 기반 중·고등 수학·과학 학습 플랫폼 '미리클래스'
- MAU 41만 명 / 누적 학습 데이터 2.3억 건
- 예산: 45억 원 (국비 35억 / 기업 부담 10억)
- 수혜 대상: 전국 중학교 500개교, 학생 5만 명
- 핵심 목표: 기초학력 미달 학생 비율 12.7% → 7% 이하

[챕터 및 페이지 구성]
[챕터 1: 문제 진단 및 정책 정합성] P1~P4
[챕터 2: 솔루션 및 수행 계획] P5~P9
[챕터 3: 성과 및 지속가능성] P10~P12""", expected_pages=12),

        "TC-006": lambda: run_tc("TC-006", "인공지능이 바꾸는 미래 일자리"),
        "TC-007": lambda: run_tc("TC-007", "기후변화 대응을 위한 기업의 역할"),
        "TC-008": lambda: run_tc("TC-008", "스타트업 창업 준비 가이드"),

        "TC-009": lambda: run_tc("TC-009", "우리 회사는 2018년 설립 이후 꾸준히 성장해왔습니다. 첫 번째 단락: 설립 초기 핵심 제품 개발과 초기 고객 확보에 집중했습니다. 두 번째 단락: 2020년 Series A 투자 유치 후 팀을 확장하고 제품 라인업을 다각화했습니다. 세 번째 단락: 2022년부터 해외 시장에 진출하여 현재 5개국에서 서비스를 제공하고 있습니다. 네 번째 단락: 2024년 현재 연 매출 100억을 달성하며 흑자 전환에 성공했습니다. 이 내용을 바탕으로 발표자료를 만들어줘."),

        "TC-010": lambda: run_tc("TC-010", "아래 연혁 데이터를 바탕으로 발표자료를 만들어줘. 반드시 시간 순서에 따라 슬라이드를 구성해야 해. 2019년 3월: 법인 설립. 2020년 6월: 첫 제품 출시, 월 사용자 1만 명 돌파. 2021년 9월: 시리즈A 투자 유치 (30억 원). 2022년 4월: 일본 법인 설립. 2023년 11월: 누적 사용자 100만 명 달성. 2024년 7월: 코스닥 상장 준비 시작."),

        "TC-011": lambda: run_tc("TC-011", "ESG 경영의 핵심 원칙과 기업 도입 효과에 대해 표지와 목차를 포함하여 정확히 10장 분량의 발표자료를 만들어줘.", expected_pages=10),

        "TC-012": lambda: run_tc("TC-012", "K-POP 산업이 전 세계에 미치는 영향과 성공 요인에 대해 영어로 작성해줘.", expected_language="en"),

        "TC-M01": lambda: run_tc_multiturn("TC-M01", [
            {
                "input": """미리애드 에이전시 소개 발표자료 스토리라인을 8페이지로 만들어줘.

[미리애드 현황]
- 설립: 2019년 / 인원: 32명 / 연간 광고비 집행: 240억 원
- 버티컬: 뷰티, 식음료, 모바일 게임
- 핵심 강점: 퍼포먼스+브랜딩 통합, 자체 플랫폼 '미리인사이트'
- 수상: 2023 대한민국 광고대상 디지털 부문 금상

[8페이지 구성]
P1. 표지 / P2. 미리애드 한눈에 보기 / P3. 집중 버티컬
P4. 통합 운용 방식 / P5. 미리인사이트 소개 / P6. 캠페인 성과
P7. 팀 구성 및 역할 / P8. 협업 제안""",
                "expected_pages": 8
            },
            {
                "input": "P6 캠페인 성과 페이지를 수정해줘. 뷰티 버티컬 캠페인 사례를 강조하고, 구체적인 ROAS 수치(예: 뷰티 캠페인 ROAS 680%)를 헤드라인에 포함해줘.",
                "expected_pages": 8
            }
        ]),

        "TC-M02": lambda: run_tc_multiturn("TC-M02", [
            {
                "input": """미리바이오 시리즈B IR 덱 스토리라인을 4개 챕터, 총 12페이지로 만들어줘.

[챕터 구성]
챕터 1: 문제와 기회 (P1~P3)
챕터 2: 미리바이오 기술 (P4~P6)
챕터 3: 임상 성과 (P7~P9)
챕터 4: 투자 제안 (P10~P12)

[주요 데이터]
- 파이프라인: MB-101 (KRAS G12C, 임상 2a상), MB-202 (STAT3, IND 완료), MB-303 (전임상)
- 목표 조달: 시리즈B 150억 원 / 특허: 국내 7건, PCT 3건""",
                "expected_pages": 12
            },
            {
                "input": "챕터 3 임상 성과 파트에 페이지를 하나 추가해줘. MB-202의 IND 제출 배경과 향후 임상 설계를 다루는 페이지를 기존 P9(경쟁 약물 포지셔닝) 앞에 넣어줘.",
                "expected_pages": 13
            }
        ]),

        "TC-M03": lambda: run_tc_multiturn("TC-M03", [
            {
                "input": """미리핀테크 정부 과제 제안서 스토리라인을 표지/목차 포함 총 10페이지로 만들어줘.

[구성]
P1. 표지 / P2. 목차 / P3. 문제 정의 / P4. 제안 솔루션
P5. 기술적 차별성 / P6. 수행 체계 / P7. 추진 일정
P8. 예산 계획 / P9. 성과 지표 / P10. 기대 효과 및 확산 계획

[주요 데이터]
- 과제 예산: 25억 원 (정부 18억 / 민간 7억) / 수행 기간: 18개월
- 목표: 금융 소외 계층 10만 명 신용 서비스 접근성 개선""",
                "expected_pages": 10
            },
            {
                "input": "P6 수행 체계 페이지는 빼줘. 분량이 너무 많아서 다른 페이지와 합칠 예정이야.",
                "expected_pages": 9
            }
        ]),

        "TC-M04": lambda: run_tc_multiturn("TC-M04", [
            {
                "input": """미리에듀 교육부 AI 교육 혁신 사업 제안서 스토리라인을 3개 챕터, 총 12페이지로 만들어줘.

[챕터 구성]
챕터 1: 문제 진단 및 정책 정합성 (P1~P4)
챕터 2: 솔루션 및 수행 계획 (P5~P9)
챕터 3: 성과 및 지속가능성 (P10~P12)

[주요 데이터]
- 예산: 45억 원 (국비 35억 / 기업 10억)
- 수혜 학생: 전국 중학교 500개교, 5만 명
- 목표: 기초학력 미달 비율 12.7% → 7% 이하
- 핵심 기술: LLM 기반 개인화 학습 경로 추천 / 미리티처 AI 교원 도구""",
                "expected_pages": 12
            },
            {
                "input": "P10 핵심 KPI 페이지 수정해줘. 기초학력 미달 비율 목표를 7% 이하가 아니라 6% 이하로 바꾸고, 측정 주기를 '학기 1회'로 명시해줘.",
                "expected_pages": 12
            },
            {
                "input": "아까 P10 수정한 거 다시 바꿔줘. 목표 수치는 원래대로 7% 이하로 돌리고, 측정 주기는 '학기 1회' 대신 '분기 1회'로 변경해줘.",
                "expected_pages": 12
            }
        ]),

        "TC-M05": lambda: run_tc_multiturn("TC-M05", [
            {
                "input": """아래 미리로지스 사업 개요를 바탕으로 발표자료 스토리라인을 만들어줘.
챕터 구분은 네가 판단해서 나눠줘.

미리로지스는 2017년 설립된 물류 솔루션 기업으로 국내 180개사에 WMS/TMS를 공급 중이다.
ARR 480억 원, 전년 대비 27% 성장. 자체 AI 수요 예측 엔진 '미리옵스' 보유.
고객사 A사 적용 결과 재고 회전율 34% 개선, 폐기 손실 19% 감소.
2026년 동남아 시장 진출 예정. 베트남·태국 3PL 파트너 총판 계약 완료.
임직원 230명, R&D 89명(39%). NRR 118% (업계 평균 105%)."""
            },
            {
                "input": "동남아 진출 챕터에서 베트남·태국 파트너 계약 내용을 더 구체적으로 써줘. 총판 계약 파트너사 수(3개사)와 2027년 현지 법인 설립 계획도 명시해줘."
            },
            {
                "input": "조직 소개 챕터는 빼줘. 내용이 내부 자료라서 외부 발표용에는 안 맞을 것 같아."
            }
        ]),
    }

# ===== 실행 =====
def collect_result(ret) -> list:
    if ret is None:
        return []
    if isinstance(ret, dict) and "result" in ret:
        return [ret["result"]]
    if isinstance(ret, list):
        return ret
    return []


if __name__ == "__main__":
    tc_map = build_tc_map()
    all_results = []

    if len(sys.argv) > 1:
        # --generate 옵션
        if sys.argv[1] == "--generate":
            if len(sys.argv) < 4:
                print("사용법: python3 qa_pipeline.py --generate [유형] [개수]")
                print(f"사용 가능한 유형: 짧은주제, 기획안, raw텍스트, 연혁, 페이지지정, 언어지정, PDF형, 수정요청, 모호한입력, 복합조건")
            else:
                tc_type = sys.argv[2]
                n = int(sys.argv[3])
                tcs = generate_tcs(tc_type, n)
                for tc in tcs:
                    ret = run_tc(
                        tc["tc_id"],
                        tc["user_input"],
                        slide_count=tc.get("slide_count", "auto"),
                        expected_pages=tc.get("expected_pages"),
                        expected_language=tc.get("expected_language", "ko")
                    )
                    all_results.extend(collect_result(ret))

        # 특정 TC 실행
        else:
            tc_id = sys.argv[1].upper()
            if tc_id in tc_map:
                ret = tc_map[tc_id]()
                all_results = collect_result(ret)
            else:
                print(f"TC를 찾을 수 없어요: {tc_id}")
                print(f"사용 가능한 TC: {list(tc_map.keys())}")

    # 전체 실행
    else:
        for tc in tc_map.values():
            ret = tc()
            all_results.extend(collect_result(ret))

    if all_results:
        print_summary(all_results)
        save_excel(all_results, output_dir=".")