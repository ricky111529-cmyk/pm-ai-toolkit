import json

def parse_json(response_text):
    """R-01: JSON 파싱"""
    try:
        data = json.loads(response_text)
        return True, data
    except json.JSONDecodeError as e:
        return False, str(e)

def check_required_keys(data):
    """R-02: 필수 키 존재 여부"""
    errors = []
    if "chapters" not in data:
        errors.append("'chapters' 키 없음")
    else:
        for i, chapter in enumerate(data["chapters"]):
            if "chapterTitle" not in chapter:
                errors.append(f"chapters[{i}]에 'chapterTitle' 없음")
            if "pages" not in chapter:
                errors.append(f"chapters[{i}]에 'pages' 없음")
            else:
                for j, page in enumerate(chapter["pages"]):
                    if "page" not in page:
                        errors.append(f"chapters[{i}].pages[{j}]에 'page' 없음")
                    if "message" not in page:
                        errors.append(f"chapters[{i}].pages[{j}]에 'message' 없음")
    return len(errors) == 0, errors

def check_page_count(data, expected=None, min_pages=1, max_pages=50):
    """R-03 / R-10: 페이지 수 범위 및 지정 수 준수"""
    all_pages = [p for ch in data["chapters"] for p in ch["pages"]]
    total = len(all_pages)
    if expected:
        ok = total == expected
        return ok, f"총 {total}페이지 (기대값: {expected})"
    ok = min_pages <= total <= max_pages
    return ok, f"총 {total}페이지"

def check_hierarchy(data):
    """R-04: L1-L2 계층 구조 정합성"""
    errors = []
    for i, chapter in enumerate(data["chapters"]):
        if not chapter.get("pages"):
            errors.append(f"chapters[{i}] '{chapter.get('chapterTitle')}' 아래 페이지 없음")
    return len(errors) == 0, errors

def check_no_empty_message(data):
    """R-06: 빈 메시지 없음"""
    errors = []
    for ch in data["chapters"]:
        for p in ch.get("pages", []):
            if not p.get("message", "").strip():
                errors.append(f"page {p.get('page')}의 message가 비어 있음")
    return len(errors) == 0, errors

def check_no_duplicate_pages(data):
    """R-07: 중복 페이지 번호 없음"""
    page_nums = [p["page"] for ch in data["chapters"] for p in ch["pages"]]
    duplicates = [n for n in page_nums if page_nums.count(n) > 1]
    duplicates = list(set(duplicates))
    return len(duplicates) == 0, duplicates

def check_content_language(data, expected_language):
    """R-08: contentLanguage가 입력 언어와 일치하는지"""
    content_language = data.get("presentationBrief", {}).get("contentLanguage", "")
    ok = content_language == expected_language
    return ok, f"contentLanguage: {content_language} (기대값: {expected_language})"

def check_language_purity(text_response, environment_language="ja"):
    """R-09: 텍스트 응답이 환경 언어 이외의 문자를 포함하지 않는가"""
    import re

    # 환경 언어별 허용 문자 패턴 (공통: 숫자, 기호, 공백 허용)
    allowed_patterns = {
        "ja": r'[^\u3000-\u9FFF\uF900-\uFAFF\uFF00-\uFFEF\d\s\W]',  # 일본어(히라가나/카타카나/한자)
        "en": r'[^\x00-\x7F\d\s\W]',   # 영어 (ASCII)
        "pt": r'[^\x00-\x7F\u00C0-\u024F\d\s\W]',  # 포르투갈어
    }

    pattern = allowed_patterns.get(environment_language)
    if not pattern:
        return True, f"지원하지 않는 언어: {environment_language}"

    found = re.findall(pattern, text_response)
    if found:
        return False, f"환경 언어({environment_language}) 외 문자 감지: {''.join(set(found))}"
    return True, f"환경 언어({environment_language}) 문자만 사용됨"

def run_all_checks(response_text, expected_pages=None, expected_language="ko", text_response=None, environment_language="ja"):
    """전체 Rule-based 검증 실행"""
    results = {}

    # R-01
    ok, data = parse_json(response_text)
    results["R-01"] = {"pass": ok, "detail": "JSON 파싱 성공" if ok else data}
    if not ok:
        return results

    # R-02
    ok, errors = check_required_keys(data)
    results["R-02"] = {"pass": ok, "detail": errors if not ok else "필수 키 모두 존재"}

    # R-03 / R-10
    ok, detail = check_page_count(data, expected=expected_pages)
    results["R-03/R-10"] = {"pass": ok, "detail": detail}

    # R-04
    ok, errors = check_hierarchy(data)
    results["R-04"] = {"pass": ok, "detail": errors if not ok else "L1-L2 계층 정상"}

    # R-06
    ok, errors = check_no_empty_message(data)
    results["R-06"] = {"pass": ok, "detail": errors if not ok else "빈 메시지 없음"}

    # R-07
    ok, duplicates = check_no_duplicate_pages(data)
    results["R-07"] = {"pass": ok, "detail": f"중복 페이지: {duplicates}" if not ok else "페이지 번호 중복 없음"}

    # R-08
    ok, detail = check_content_language(data, expected_language)
    results["R-08"] = {"pass": ok, "detail": detail}

 # R-09 (text_response가 있을 때만)
    if text_response:
        ok, detail = check_language_purity(text_response, environment_language)
        results["R-09"] = {"pass": ok, "detail": detail}

    return results