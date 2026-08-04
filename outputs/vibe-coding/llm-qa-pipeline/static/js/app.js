/**
 * TC 검증 메인 페이지 스크립트
 */

// 검증 시작 버튼
document.getElementById('validate-btn').addEventListener('click', startValidation);

// 다시 검증 버튼
document.getElementById('validate-again-btn').addEventListener('click', resetForm);

// 결과 상세 보기 버튼
document.getElementById('view-results-btn').addEventListener('click', function() {
    window.location.href = '/results';
});

/**
 * 검증 시작
 */
function startValidation() {
    const miriAccess = document.getElementById('miri-access').value.trim();
    const selectedTypes = Array.from(
        document.querySelectorAll('input[name="tc-type"]:checked')
    ).map(el => el.value);
    const nPerType = parseInt(document.getElementById('n-per-type').value);

    // 입력 검증
    if (!miriAccess) {
        showError('miri-access 토큰을 입력하세요');
        return;
    }

    if (selectedTypes.length === 0) {
        showError('최소 1개 이상의 TC 유형을 선택하세요');
        return;
    }

    if (nPerType < 1 || nPerType > 10) {
        showError('TC 개수는 1~10 사이여야 합니다');
        return;
    }

    // UI 업데이트
    document.getElementById('validate-btn').disabled = true;
    document.getElementById('progress-section').style.display = 'block';
    document.getElementById('result-section').style.display = 'none';
    document.getElementById('progress-log').innerHTML = '';

    // API 호출
    const payload = {
        miri_access: miriAccess,
        types: selectedTypes,
        n_per_type: nPerType
    };

    // SSE 연결
    const eventSource = new EventSource(
        '/api/validate?' + new URLSearchParams(payload).toString()
    );

    eventSource.onmessage = function(event) {
        const data = JSON.parse(event.data);

        // 진행률 업데이트
        const progress = data.progress || 0;
        document.getElementById('progress-bar').style.width = progress + '%';
        document.getElementById('progress-text').textContent = progress + '%';

        // 로그 업데이트
        appendLog(data.status);

        // 완료 확인
        if (data.progress === 100) {
            eventSource.close();
            showResults(data.results);
            document.getElementById('validate-btn').disabled = false;
        }
    };

    eventSource.onerror = function() {
        eventSource.close();
        showError('오류가 발생했습니다. 토큰을 확인하세요.');
        document.getElementById('validate-btn').disabled = false;
    };
}

/**
 * 로그 추가
 */
function appendLog(message) {
    const log = document.getElementById('progress-log');
    const timestamp = new Date().toLocaleTimeString('ko-KR');
    const entry = document.createElement('div');
    entry.textContent = `[${timestamp}] ${message}`;
    log.appendChild(entry);
    log.scrollTop = log.scrollHeight;
}

/**
 * 결과 표시
 */
function showResults(results) {
    document.getElementById('result-section').style.display = 'block';

    // 통계 업데이트
    animateCounter('result-total', 0, results.total);
    animateCounter('result-valid', 0, results.valid);
    animateCounter('result-invalid', 0, results.invalid);
    animateCounter('result-duplicate', 0, results.duplicates);
    document.getElementById('failures-count').textContent = results.failures_saved;

    // TC별 상세 결과
    if (results.tc_details && results.tc_details.length > 0) {
        renderTcDetails(results.tc_details);
    }
}

/**
 * TC별 상세 결과 렌더링
 */
function renderTcDetails(tcDetails) {
    const section = document.getElementById('detail-section');
    const container = document.getElementById('tc-detail-list');
    section.style.display = 'block';
    container.innerHTML = '';

    tcDetails.forEach(tc => {
        const passed = tc.passed;
        const headerColor = passed ? 'bg-success' : 'bg-danger';
        const icon = passed ? '✅' : '❌';

        // Rule 결과 행 생성
        const ruleRows = Object.entries(tc.rule || {}).map(([code, r]) => `
            <tr class="${r.pass ? '' : 'table-danger'}">
                <td><span class="badge bg-secondary">${code}</span></td>
                <td>${r.pass ? '<span class="text-success fw-bold">PASS</span>' : '<span class="text-danger fw-bold">FAIL</span>'}</td>
                <td class="text-muted small">${r.detail || ''}</td>
            </tr>
        `).join('');

        // LLM 결과 행 생성
        const llmRows = Object.entries(tc.llm || {}).map(([code, r]) => `
            <tr class="${r.pass ? '' : 'table-warning'}">
                <td><span class="badge bg-info text-dark">${code}</span></td>
                <td>${r.pass ? '<span class="text-success fw-bold">PASS</span>' : '<span class="text-danger fw-bold">FAIL</span>'}</td>
                <td class="text-muted small">${r.reason || ''}</td>
            </tr>
        `).join('');

        // LLM 텍스트 결과 행 생성
        const llmTextRows = Object.entries(tc.llm_text || {}).map(([code, r]) => `
            <tr class="${r.pass ? '' : 'table-warning'}">
                <td><span class="badge bg-purple" style="background-color:#6f42c1">${code}</span></td>
                <td>${r.pass ? '<span class="text-success fw-bold">PASS</span>' : '<span class="text-danger fw-bold">FAIL</span>'}</td>
                <td class="text-muted small">${r.reason || ''}</td>
            </tr>
        `).join('');

        const card = document.createElement('div');
        card.className = 'border-bottom';
        card.innerHTML = `
            <div class="${headerColor} text-white px-4 py-2 d-flex justify-content-between align-items-center"
                 style="cursor:pointer;" onclick="toggleDetail('${tc.tc_id}')">
                <span>${icon} <strong>${tc.tc_id}</strong> [${tc.tc_type}] — ${tc.user_input}</span>
                <span id="chevron-${tc.tc_id}">▼</span>
            </div>
            <div id="detail-${tc.tc_id}" style="display:none;">
                <table class="table table-sm mb-0">
                    <thead class="table-light">
                        <tr>
                            <th style="width:15%">코드</th>
                            <th style="width:10%">결과</th>
                            <th>상세 내용</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${ruleRows || '<tr><td colspan="3" class="text-muted text-center">Rule 결과 없음</td></tr>'}
                        ${llmRows || ''}
                        ${llmTextRows || ''}
                    </tbody>
                </table>
            </div>
        `;
        container.appendChild(card);
    });
}

/**
 * 상세 결과 토글
 */
function toggleDetail(tcId) {
    const detail = document.getElementById('detail-' + tcId);
    const chevron = document.getElementById('chevron-' + tcId);
    if (detail.style.display === 'none') {
        detail.style.display = 'block';
        chevron.textContent = '▲';
    } else {
        detail.style.display = 'none';
        chevron.textContent = '▼';
    }
}

/**
 * 숫자 애니메이션
 */
function animateCounter(elementId, start, end) {
    const element = document.getElementById(elementId);
    const duration = 500; // ms
    const steps = 30;
    const stepValue = (end - start) / steps;
    let current = start;

    const interval = setInterval(() => {
        current += stepValue;
        if (current >= end) {
            element.textContent = end;
            clearInterval(interval);
        } else {
            element.textContent = Math.floor(current);
        }
    }, duration / steps);
}

/**
 * 폼 초기화
 */
function resetForm() {
    document.getElementById('miri-access').value = '';
    document.querySelectorAll('input[name="tc-type"]').forEach(el => el.checked = false);
    document.getElementById('n-per-type').value = '2';
    document.getElementById('progress-section').style.display = 'none';
    document.getElementById('result-section').style.display = 'none';
    document.getElementById('validate-btn').disabled = false;
}

/**
 * 에러 표시
 */
function showError(message) {
    alert('❌ ' + message);
}
