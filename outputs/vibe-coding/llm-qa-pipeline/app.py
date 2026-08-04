"""Flask Web Interface for TC Validation"""

import os
import json
import uuid
from flask import Flask, render_template, jsonify, request, Response
from dotenv import load_dotenv

from models import db, FailureRecord, ValidationSession
from qa import (
    generate_tcs,
    generate_followup_question,
    FIXED_FOLLOWUP_QUESTIONS,
    TC_TYPE_DESCRIPTIONS,
    call_aip,
    call_aip_multiturn,
    run_all_checks,
    run_llm_checks_storyline,
    run_llm_checks_text,
)
from qa.qa_pipeline import get_session_id, extract_json, extract_text

load_dotenv()

# Flask 앱 초기화
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)


def check_token_format(token):
    """JWT 토큰 형식 확인"""
    if not isinstance(token, str):
        return False
    if len(token) < 20:
        return False
    # JWT는 3개 파트로 나뉨 (header.payload.signature)
    if token.count('.') != 2:
        return False
    return True


@app.route('/')
def index():
    """메인 페이지"""
    # TC 유형 분류
    single_turn_types = [
        "짧은주제", "기획안", "raw텍스트", "연혁",
        "페이지지정", "언어지정", "PDF형", "모호한입력", "복합조건"
    ]
    multi_turn_types = ["수정요청"]

    return render_template(
        'index.html',
        single_turn_types=single_turn_types,
        multi_turn_types=multi_turn_types
    )


@app.route('/results')
def results():
    """결과 조회 페이지"""
    return render_template('results.html')


@app.route('/api/validate', methods=['GET'])
def validate_tcs():
    """TC 검증 (Server-Sent Events로 실시간 전송)"""

    # request는 generator 밖에서 미리 읽어야 함 (SSE는 request context 없음)
    miri_access = request.args.get('miri_access', '').strip()
    selected_types = request.args.getlist('types')
    n_per_type = int(request.args.get('n_per_type', 2))

    def generate_validation():
        try:

            # 입력 검증
            if not miri_access or not selected_types:
                yield f"data: {json.dumps({'status': 'Error: Invalid input', 'progress': 0, 'error': True})}\n\n"
                return

            if not check_token_format(miri_access):
                yield f"data: {json.dumps({'status': 'Error: Invalid token format', 'progress': 0, 'error': True})}\n\n"
                return

            # Step 1: .env 업데이트
            yield f"data: {json.dumps({'status': '토큰 설정 중...', 'progress': 5})}\n\n"
            os.environ['AIP_API_COOKIE_VALUE'] = miri_access

            all_results = []
            all_tcs = []
            multiturn_failures = []
            has_multiturn = "수정요청" in selected_types

            # Step 2: 단일턴 TC 생성 및 검증
            if has_multiturn:
                single_types = [t for t in selected_types if t != "수정요청"]
            else:
                single_types = selected_types

            if single_types:
                yield f"data: {json.dumps({'status': '단일턴 TC 생성 중...', 'progress': 10})}\n\n"
                all_tcs = []
                tc_results = []   # ← if all_tcs 블록 밖에서 초기화 (NameError 방지)
                total_types = len(single_types)

                for idx, tc_type in enumerate(single_types, 1):
                    progress = 10 + (idx / total_types * 20)
                    yield f"data: {json.dumps({'status': f'{tc_type} 생성 중... ({idx}/{total_types})', 'progress': int(progress)})}\n\n"

                    try:
                        tcs = generate_tcs(tc_type, n_per_type)
                        all_tcs.extend(tcs)
                    except Exception as e:
                        yield f"data: {json.dumps({'status': f'⚠️  {tc_type} 생성 실패: {str(e)[:50]}', 'progress': int(progress)})}\n\n"
                        continue

                if all_tcs:
                    total_tc_count = len(all_tcs)
                    # tc_results는 위에서 이미 초기화됨 (NameError 방지용)
                    failures = []

                    for tc_idx, tc in enumerate(all_tcs, 1):
                        tc_id = tc['tc_id']
                        tc_type = tc['tc_type']
                        user_input = tc['user_input']
                        progress = 35 + int(tc_idx / total_tc_count * 40)

                        yield f"data: {json.dumps({'status': f'[{tc_idx}/{total_tc_count}] {tc_id} AIP 호출 중...', 'progress': progress})}\n\n"
                        try:
                            # 실제 AIP 호출
                            response_text = call_aip(user_input, tc.get('slide_count', 'auto'))
                            storyline_json = extract_json(response_text)
                            text_response = extract_text(response_text)

                            if not storyline_json:
                                # 토큰 만료 여부 확인
                                if 'expired' in response_text or '401' in response_text or 'Unauthorized' in response_text:
                                    yield f"data: {json.dumps({'status': '❌ 토큰이 만료되었습니다. 새 토큰을 입력하세요', 'progress': 0, 'error': True})}\n\n"
                                    return
                                failures.append({
                                    'tc_id': tc_id,
                                    'tc_type': tc_type,
                                    'user_input': user_input,
                                    'failure_reason': 'JSON 추출 실패 (AIP 응답 없음)',
                                    'failure_category': 'format',
                                })
                                yield f"data: {json.dumps({'status': f'⚠️  {tc_id} JSON 추출 실패', 'progress': progress})}\n\n"
                                continue

                            # Rule-based 검증
                            rule_results = run_all_checks(
                                storyline_json,
                                expected_pages=tc.get('expected_pages'),
                                expected_language=tc.get('expected_language', 'ko'),
                                text_response=text_response,
                                environment_language='ja',
                                user_input=user_input,
                            )
                            rule_fails = [code for code, r in rule_results.items() if not r.get('pass', True)]

                            # LLM 검증 (스토리라인)
                            llm_story_results = run_llm_checks_storyline(user_input, storyline_json)
                            # error 키가 있으면 LLM 호출 자체 실패 → 검증 스킵
                            if 'error' in llm_story_results:
                                llm_fails = []
                                llm_story_results = {}
                            else:
                                llm_fails = [code for code, r in llm_story_results.items() if not r.get('pass', True)]

                            # LLM 검증 (텍스트)
                            llm_text_fails = []
                            llm_text_results = {}
                            if text_response:
                                llm_text_results = run_llm_checks_text(user_input, text_response, language='ja')
                                if 'error' not in llm_text_results:
                                    llm_text_fails = [code for code, r in llm_text_results.items() if not r.get('pass', True)]

                            all_fails = rule_fails + llm_fails + llm_text_fails

                            if all_fails:
                                fail_msgs = []
                                for code in rule_fails:
                                    fail_msgs.append(f"{code}: {rule_results[code].get('detail','')}")
                                for code in llm_fails:
                                    # llm_validator는 'reason' 키 사용
                                    fail_msgs.append(f"{code}: {llm_story_results[code].get('reason','')}")
                                failures.append({
                                    'tc_id': tc_id,
                                    'tc_type': tc_type,
                                    'user_input': user_input,
                                    'failure_reason': ' | '.join(fail_msgs[:3]),
                                    'failure_category': 'type_rule' if rule_fails else 'quality',
                                })
                                fail_summary = ', '.join(all_fails[:3])
                                yield f"data: {json.dumps({'status': f'❌ {tc_id} 검증 실패: {fail_summary}', 'progress': progress})}\n\n"
                            else:
                                yield f"data: {json.dumps({'status': f'✅ {tc_id} 검증 통과', 'progress': progress})}\n\n"

                            tc_results.append({
                                'tc_id': tc_id,
                                'tc_type': tc_type,
                                'user_input': user_input[:80],
                                'passed': len(all_fails) == 0,
                                'rule': {code: {'pass': r['pass'], 'detail': r.get('detail', '')} for code, r in rule_results.items()},
                                'llm': {code: {'pass': r['pass'], 'reason': r.get('reason', '')} for code, r in llm_story_results.items()},
                                'llm_text': {code: {'pass': r['pass'], 'reason': r.get('reason', '')} for code, r in llm_text_results.items()} if llm_text_results else {},
                            })

                        except Exception as e:
                            failures.append({
                                'tc_id': tc_id,
                                'tc_type': tc_type,
                                'user_input': user_input,
                                'failure_reason': f'AIP 호출 오류: {str(e)[:80]}',
                                'failure_category': 'format',
                            })
                            yield f"data: {json.dumps({'status': f'⚠️  {tc_id} 오류: {str(e)[:40]}', 'progress': progress})}\n\n"

                    valid_count = sum(1 for r in tc_results if r['passed'])
                    all_results.append(('single', {
                        'total': len(all_tcs),
                        'valid': valid_count,
                        'invalid': len(all_tcs) - valid_count,
                        'duplicates': 0,
                        'details': [],
                        'failures': failures,
                    }, all_tcs))

            # Step 3: 멀티턴 실행 (단일턴 TC에 수정 질문 3개 추가 = 총 4턴)
            if has_multiturn and not all_tcs:
                # 단일턴이 선택되지 않은 경우 → 에러
                yield f"data: {json.dumps({'status': 'Error: 수정요청은 단일턴 TC와 함께 선택하세요', 'progress': 45, 'error': True})}\n\n"
                has_multiturn = False  # 멀티턴 통계에서 제외

            if has_multiturn and all_tcs:
                # 단일턴 TC 중 첫 번째를 기반으로 멀티턴 실행
                base_tc = all_tcs[0]
                initial_input = base_tc.get('user_input', '')

                yield f"data: {json.dumps({'status': '멀티턴 시작: AIP에 첫 번째 요청 전송 중...', 'progress': 40})}\n\n"

                try:
                    # 1턴: 초기 요청 → AIP 호출
                    try:
                        first_response = call_aip(initial_input)
                        if not first_response or len(first_response) < 10:
                            yield f"data: {json.dumps({'status': 'Error: AIP 응답이 비어있습니다. 토큰을 확인하세요', 'progress': 45, 'error': True})}\n\n"
                            return
                    except Exception as api_err:
                        yield f"data: {json.dumps({'status': f'Error: AIP 호출 실패 - {str(api_err)[:60]}', 'progress': 45, 'error': True})}\n\n"
                        return

                    session_id_val = get_session_id(first_response)

                    if not session_id_val:
                        yield f"data: {json.dumps({'status': 'Error: 세션 ID를 추출할 수 없습니다. 토큰 또는 입력을 확인하세요', 'progress': 45, 'error': True})}\n\n"
                    else:
                        yield f"data: {json.dumps({'status': '✅ 1턴 완료 (초기 생성)', 'progress': 45})}\n\n"

                        # 수정 질문 3개 준비: 고정 2개 + LLM 생성 1개
                        yield f"data: {json.dumps({'status': 'LLM 수정 질문 생성 중...', 'progress': 50})}\n\n"
                        llm_question = generate_followup_question(initial_input)
                        followup_questions = FIXED_FOLLOWUP_QUESTIONS + [llm_question]

                        # 2~4턴: 수정 요청 순서대로 실행
                        for turn_idx, question in enumerate(followup_questions, 2):
                            progress = 50 + (turn_idx / 4 * 30)
                            yield f"data: {json.dumps({'status': f'{turn_idx}턴 수정 요청 전송 중...', 'progress': int(progress)})}\n\n"

                            try:
                                turn_response = call_aip_multiturn(question, session_id_val)

                                # JSON 추출
                                storyline_json = extract_json(turn_response)
                                if not storyline_json:
                                    multiturn_failures.append({
                                        'tc_id': f"MT-TURN{turn_idx}",
                                        'tc_type': '수정요청',
                                        'user_input': question,
                                        'failure_reason': 'JSON 추출 실패',
                                        'failure_category': 'format',
                                    })
                                    yield f"data: {json.dumps({'status': f'⚠️  {turn_idx}턴 JSON 추출 실패', 'progress': int(progress)})}\n\n"
                                    continue

                                # 검증: 추출된 JSON을 검증
                                text_response = extract_text(turn_response)
                                try:
                                    checks = run_all_checks(storyline_json, expected_pages=None, text_response=text_response, environment_language="ja", user_input=question)
                                    # run_all_checks는 {"R-01": {"pass": True, "detail": "..."}} 형식 반환
                                    failed = [code for code, result in checks.items() if not result.get('pass', True)]

                                    if failed:
                                        failure_messages = [f"{code}: {checks[code].get('detail', 'Unknown')}" for code in failed]
                                        multiturn_failures.append({
                                            'tc_id': f"MT-TURN{turn_idx}",
                                            'tc_type': '수정요청',
                                            'user_input': question,
                                            'failure_reason': " | ".join(failure_messages),
                                            'failure_category': 'type_rule',
                                        })
                                        yield f"data: {json.dumps({'status': f'⚠️  {turn_idx}턴 검증 실패 ({len(failed)}건)', 'progress': int(progress)})}\n\n"
                                    else:
                                        yield f"data: {json.dumps({'status': f'✅ {turn_idx}턴 완료', 'progress': int(progress)})}\n\n"

                                except Exception as ve:
                                    # 검증 오류
                                    yield f"data: {json.dumps({'status': f'⚠️  {turn_idx}턴 검증 오류: {str(ve)[:40]}', 'progress': int(progress)})}\n\n"

                            except Exception as e:
                                yield f"data: {json.dumps({'status': f'⚠️  {turn_idx}턴 API 오류: {str(e)[:50]}', 'progress': int(progress)})}\n\n"

                except Exception as e:
                    yield f"data: {json.dumps({'status': f'⚠️  멀티턴 실행 오류: {str(e)[:80]}', 'progress': 45})}\n\n"

            # Step 4: 통계 계산 (DB 저장은 나중에)
            yield f"data: {json.dumps({'status': '결과 정리 중...', 'progress': 85})}\n\n"

            single_total = sum(r[1]['total'] for r in all_results if r[0] == 'single') if all_results else 0
            single_valid = sum(r[1]['valid'] for r in all_results if r[0] == 'single') if all_results else 0
            mt_total = 3 if has_multiturn else 0

            single_failures = []
            for result_type, *rdata in all_results:
                if result_type == 'single':
                    validation_result, tcs = rdata
                    single_failures.extend(validation_result.get('failures', []))

            total_failures = len(single_failures) + len(multiturn_failures)

            session_id = str(uuid.uuid4())

            # tc_results 수집
            all_tc_details = list(tc_results)  # 단일턴 결과 복사
            # 멀티턴 실패도 포함
            for mf in multiturn_failures:
                all_tc_details.append({
                    'tc_id': mf['tc_id'],
                    'tc_type': mf['tc_type'],
                    'user_input': mf['user_input'][:80],
                    'passed': False,
                    'rule': {},
                    'llm': {},
                    'llm_text': {},
                    'failure_reason': mf['failure_reason'],
                })

            # 최종 결과
            yield f"data: {json.dumps({'status': '완료', 'progress': 100, 'results': {'total': single_total + mt_total, 'valid': single_valid + (mt_total - len(multiturn_failures)), 'invalid': len(all_tcs) - single_valid + len(multiturn_failures), 'duplicates': 0, 'failures_saved': total_failures, 'session_id': session_id, 'tc_details': all_tc_details}})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'status': f'오류: {str(e)[:100]}', 'progress': 0, 'error': True})}\n\n"

    return Response(generate_validation(), mimetype='text/event-stream')


@app.route('/api/failures', methods=['GET'])
def get_failures():
    """저장된 실패 TC 조회"""
    try:
        # 필터링
        tc_type = request.args.get('tc_type')
        category = request.args.get('category')
        resolved = request.args.get('resolved', 'false').lower() == 'true'

        query = FailureRecord.query.filter_by(is_resolved=resolved)

        if tc_type:
            query = query.filter_by(tc_type=tc_type)
        if category:
            query = query.filter_by(failure_category=category)

        # 정렬 및 페이징
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))

        paginated = query.order_by(FailureRecord.timestamp.desc()).paginate(
            page=page, per_page=per_page
        )

        return jsonify({
            'total': paginated.total,
            'page': page,
            'per_page': per_page,
            'pages': paginated.pages,
            'failures': [f.to_dict() for f in paginated.items]
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """통계 정보 조회"""
    try:
        total_failures = FailureRecord.query.filter_by(is_resolved=False).count()
        resolved_failures = FailureRecord.query.filter_by(is_resolved=True).count()

        # 유형별 실패율
        by_type = db.session.query(
            FailureRecord.tc_type,
            db.func.count(FailureRecord.id).label('count')
        ).filter_by(is_resolved=False).group_by(FailureRecord.tc_type).all()

        by_type_dict = {t: c for t, c in by_type}

        # 카테고리별 실패율
        by_category = db.session.query(
            FailureRecord.failure_category,
            db.func.count(FailureRecord.id).label('count')
        ).filter_by(is_resolved=False).group_by(FailureRecord.failure_category).all()

        by_category_dict = {c: cnt for c, cnt in by_category}

        # 최근 검증 세션
        latest_sessions = ValidationSession.query.order_by(
            ValidationSession.start_time.desc()
        ).limit(5).all()

        return jsonify({
            'total_failures': total_failures,
            'resolved_failures': resolved_failures,
            'resolution_rate': round(
                (resolved_failures / (total_failures + resolved_failures) * 100)
                if (total_failures + resolved_failures) > 0 else 0
            ),
            'by_type': by_type_dict,
            'by_category': by_category_dict,
            'latest_sessions': [s.to_dict() for s in latest_sessions]
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/failure/<int:failure_id>', methods=['PATCH'])
def mark_failure_resolved(failure_id):
    """실패 TC를 해결됨으로 표시"""
    try:
        failure = FailureRecord.query.get(failure_id)
        if not failure:
            return jsonify({'error': 'Not found'}), 404

        data = request.get_json()
        failure.is_resolved = data.get('is_resolved', True)
        failure.notes = data.get('notes')

        db.session.commit()

        return jsonify(failure.to_dict())

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@app.route('/api/failure/<int:failure_id>', methods=['DELETE'])
def delete_failure(failure_id):
    """실패 TC 삭제"""
    try:
        failure = FailureRecord.query.get(failure_id)
        if not failure:
            return jsonify({'error': 'Not found'}), 404

        db.session.delete(failure)
        db.session.commit()

        return jsonify({'success': True})

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@app.route('/api/sessions', methods=['GET'])
def get_sessions():
    """이전 검증 세션 조회"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))

        paginated = ValidationSession.query.order_by(
            ValidationSession.start_time.desc()
        ).paginate(page=page, per_page=per_page)

        return jsonify({
            'total': paginated.total,
            'page': page,
            'per_page': per_page,
            'pages': paginated.pages,
            'sessions': [s.to_dict() for s in paginated.items]
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.errorhandler(404)
def not_found(error):
    """404 에러 핸들러"""
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def server_error(error):
    """500 에러 핸들러"""
    db.session.rollback()
    return jsonify({'error': 'Server error'}), 500


if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    app.run(debug=True, port=5000, host='0.0.0.0')
