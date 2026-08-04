/**
 * 검증 결과 페이지 스크립트
 */

let currentPage = 1;
let totalPages = 1;
let charts = {};

// 페이지 로드
document.addEventListener('DOMContentLoaded', function() {
    loadStats();
    loadFailures();
    loadSessions();

    // 필터 버튼
    document.getElementById('apply-filter-btn').addEventListener('click', loadFailures);
    document.getElementById('reset-filter-btn').addEventListener('click', resetFilters);
});

/**
 * 통계 로드
 */
function loadStats() {
    fetch('/api/stats')
        .then(r => r.json())
        .then(data => {
            document.getElementById('stat-total').textContent = data.total_failures;
            document.getElementById('stat-resolved').textContent = data.resolved_failures;
            document.getElementById('stat-rate').textContent = data.resolution_rate + '%';
            document.getElementById('stat-sessions').textContent = data.latest_sessions.length;

            // 필터 옵션 업데이트
            updateTypeFilter(data.by_type);

            // 차트 업데이트
            drawCharts(data.by_type, data.by_category);
        })
        .catch(err => console.error('통계 로드 실패:', err));
}

/**
 * 오류 목록 로드
 */
function loadFailures(page = 1) {
    const tc_type = document.getElementById('filter-type').value;
    const category = document.getElementById('filter-category').value;
    const resolved = document.getElementById('filter-status').value;

    const params = new URLSearchParams({
        page: page,
        per_page: 20
    });

    if (tc_type) params.append('tc_type', tc_type);
    if (category) params.append('category', category);
    if (resolved !== '') params.append('resolved', resolved);

    fetch(`/api/failures?${params}`)
        .then(r => r.json())
        .then(data => {
            displayFailures(data.failures);
            updatePagination(data.page, data.pages, data.total);
            document.getElementById('failures-count').textContent = data.total;
        })
        .catch(err => console.error('오류 로드 실패:', err));
}

/**
 * 오류 표시
 */
function displayFailures(failures) {
    const tbody = document.getElementById('failures-body');
    tbody.innerHTML = '';

    if (failures.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-4">오류 없음</td></tr>';
        return;
    }

    failures.forEach(failure => {
        const row = document.createElement('tr');

        const categoryBadge = getCategoryBadge(failure.failure_category);
        const timestamp = new Date(failure.timestamp).toLocaleString('ko-KR');

        row.innerHTML = `
            <td><code>${failure.tc_id}</code></td>
            <td><span class="badge bg-info">${failure.tc_type}</span></td>
            <td>${categoryBadge}</td>
            <td>
                <small>${failure.failure_reason}</small>
                ${failure.user_input ? `<br><small class="text-muted">입력: ${failure.user_input.substring(0, 50)}...</small>` : ''}
            </td>
            <td><small>${timestamp}</small></td>
        `;

        row.style.cursor = 'pointer';
        row.addEventListener('click', () => showFailureDetail(failure));

        tbody.appendChild(row);
    });
}

/**
 * 카테고리 배지
 */
function getCategoryBadge(category) {
    const badges = {
        'format': '<span class="badge bg-danger">형식 오류</span>',
        'quality': '<span class="badge bg-warning text-dark">품질 오류</span>',
        'type_rule': '<span class="badge bg-secondary">규칙 오류</span>',
        'other': '<span class="badge bg-secondary">기타</span>'
    };
    return badges[category] || badges['other'];
}

/**
 * 페이지네이션 업데이트
 */
function updatePagination(page, pages, total) {
    const pagination = document.getElementById('pagination');
    pagination.innerHTML = '';

    if (pages <= 1) return;

    // 이전 버튼
    if (page > 1) {
        const li = document.createElement('li');
        li.className = 'page-item';
        li.innerHTML = `<a class="page-link" href="#" onclick="loadFailures(${page - 1})">이전</a>`;
        pagination.appendChild(li);
    }

    // 페이지 번호
    for (let i = 1; i <= pages; i++) {
        const li = document.createElement('li');
        li.className = `page-item ${i === page ? 'active' : ''}`;
        li.innerHTML = `<a class="page-link" href="#" onclick="loadFailures(${i})">${i}</a>`;
        pagination.appendChild(li);
    }

    // 다음 버튼
    if (page < pages) {
        const li = document.createElement('li');
        li.className = 'page-item';
        li.innerHTML = `<a class="page-link" href="#" onclick="loadFailures(${page + 1})">다음</a>`;
        pagination.appendChild(li);
    }
}

/**
 * 세션 로드
 */
function loadSessions() {
    fetch('/api/sessions?per_page=5')
        .then(r => r.json())
        .then(data => {
            const tbody = document.getElementById('sessions-body');
            tbody.innerHTML = '';

            data.sessions.forEach(session => {
                const row = document.createElement('tr');
                const types = JSON.parse(session.selected_types).join(', ');
                const startTime = new Date(session.start_time).toLocaleString('ko-KR');

                row.innerHTML = `
                    <td><code class="small">${session.session_id.substring(0, 8)}...</code></td>
                    <td><small>${types}</small></td>
                    <td>${session.total_generated}</td>
                    <td><span class="badge bg-success">${session.total_valid}</span></td>
                    <td><span class="badge bg-danger">${session.total_invalid}</span></td>
                    <td><span class="badge bg-warning">${session.total_failures_saved}</span></td>
                    <td><small>${startTime}</small></td>
                `;

                tbody.appendChild(row);
            });
        })
        .catch(err => console.error('세션 로드 실패:', err));
}

/**
 * 필터 옵션 업데이트
 */
function updateTypeFilter(byType) {
    const select = document.getElementById('filter-type');

    // 첫 번째 옵션 유지
    const firstOption = select.firstElementChild;

    // 기존 옵션 제거
    while (select.options.length > 1) {
        select.remove(1);
    }

    // 새 옵션 추가
    Object.keys(byType).sort().forEach(type => {
        const option = document.createElement('option');
        option.value = type;
        option.textContent = `${type} (${byType[type]})`;
        select.appendChild(option);
    });
}

/**
 * 필터 초기화
 */
function resetFilters() {
    document.getElementById('filter-type').value = '';
    document.getElementById('filter-category').value = '';
    document.getElementById('filter-status').value = 'false';
    loadFailures();
}

/**
 * 오류 상세 보기
 */
function showFailureDetail(failure) {
    const detail = `
TC ID: ${failure.tc_id}
유형: ${failure.tc_type}
실패 사유: ${failure.failure_reason}
입력: ${failure.user_input}
발생일: ${new Date(failure.timestamp).toLocaleString('ko-KR')}
    `;

    alert(detail);
}

/**
 * 차트 그리기
 */
function drawCharts(byType, byCategory) {
    // 유형별 차트
    const typeCtx = document.getElementById('chart-by-type');
    if (typeCtx) {
        if (charts.byType) {
            charts.byType.destroy();
        }

        const typeLabels = Object.keys(byType).sort();
        const typeData = typeLabels.map(t => byType[t]);

        charts.byType = new Chart(typeCtx, {
            type: 'bar',
            data: {
                labels: typeLabels,
                datasets: [{
                    label: '오류 수',
                    data: typeData,
                    backgroundColor: 'rgba(220, 53, 69, 0.6)',
                    borderColor: 'rgb(220, 53, 69)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { display: true }
                },
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
    }

    // 카테고리별 차트
    const categoryCtx = document.getElementById('chart-by-category');
    if (categoryCtx) {
        if (charts.byCategory) {
            charts.byCategory.destroy();
        }

        const categoryLabels = Object.keys(byCategory).map(c => {
            const labels = {
                'format': '형식 오류',
                'quality': '품질 오류',
                'type_rule': '규칙 오류',
                'other': '기타'
            };
            return labels[c] || c;
        });
        const categoryData = Object.values(byCategory);

        charts.byCategory = new Chart(categoryCtx, {
            type: 'doughnut',
            data: {
                labels: categoryLabels,
                datasets: [{
                    data: categoryData,
                    backgroundColor: [
                        'rgba(220, 53, 69, 0.6)',
                        'rgba(255, 193, 7, 0.6)',
                        'rgba(108, 117, 125, 0.6)',
                        'rgba(23, 162, 184, 0.6)'
                    ]
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { position: 'bottom' } }
            }
        });
    }
}
