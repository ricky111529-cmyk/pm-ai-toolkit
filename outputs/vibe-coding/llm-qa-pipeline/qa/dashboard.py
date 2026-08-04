"""
HTML 대시보드 생성 (Phase 6 Option B)

기능:
  - PASS/FAIL 비율 차트
  - 항목별 FAIL 빈도 차트
  - 카테고리별 분석
  - 상세 결과 테이블
"""

import json
from datetime import datetime
from .analytics import analyze_failures, RULE_CODES, LLM_STORY_CODES, LLM_TEXT_CODES


def generate_html_dashboard(all_results, output_file="dashboard.html"):
    """
    HTML 대시보드 생성

    Args:
        all_results: collect_all_results() 반환값
        output_file: 생성될 HTML 파일 경로

    Returns:
        HTML 파일 경로
    """

    analytics = analyze_failures(all_results)

    # 데이터 준비
    total = len(all_results)
    pass_rate = analytics['overall_pass_rate'] * 100
    fail_rate = 100 - pass_rate

    # 항목별 FAIL (상위 15개)
    sorted_failures = sorted(
        analytics['failures_by_code'].items(),
        key=lambda x: x[1],
        reverse=True
    )[:15]

    # 카테고리별
    category_data = []
    for cat in ["Rule-based", "LLM-Story", "LLM-Text"]:
        failures = analytics['failures_by_category'].get(cat, {})
        fail_count = sum(failures.values())
        category_data.append({
            'name': cat,
            'fail_count': fail_count,
            'codes': list(failures.keys())
        })

    # HTML 생성
    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chat AIP QA 대시보드</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            padding: 20px;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}

        header {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}

        h1 {{
            color: #667eea;
            margin-bottom: 10px;
        }}

        .timestamp {{
            color: #999;
            font-size: 14px;
        }}

        .metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .metric-card {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            text-align: center;
        }}

        .metric-value {{
            font-size: 32px;
            font-weight: bold;
            color: #667eea;
            margin: 10px 0;
        }}

        .metric-label {{
            font-size: 14px;
            color: #999;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .charts {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 30px;
            margin-bottom: 30px;
        }}

        .chart-container {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}

        .chart-title {{
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 20px;
            color: #333;
        }}

        .chart {{
            position: relative;
            height: 300px;
        }}

        .details {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}

        .details-title {{
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 20px;
            color: #333;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
        }}

        th {{
            background: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
        }}

        td {{
            padding: 12px;
            border-bottom: 1px solid #eee;
        }}

        tr:hover {{
            background: #f9f9f9;
        }}

        .pass {{
            color: #22c55e;
            font-weight: bold;
        }}

        .fail {{
            color: #ef4444;
            font-weight: bold;
        }}

        footer {{
            text-align: center;
            color: white;
            margin-top: 40px;
            font-size: 12px;
        }}

        @media (max-width: 768px) {{
            .charts {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 Chat AIP QA 대시보드</h1>
            <p class="timestamp">생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </header>

        <div class="metrics">
            <div class="metric-card">
                <div class="metric-label">총 TC</div>
                <div class="metric-value">{total}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">PASS율</div>
                <div class="metric-value" style="color: #22c55e;">{pass_rate:.1f}%</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">FAIL 항목</div>
                <div class="metric-value" style="color: #ef4444;">{analytics['fail_count']}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">검증 항목</div>
                <div class="metric-value">{analytics['total_checks']}</div>
            </div>
        </div>

        <div class="charts">
            <div class="chart-container">
                <div class="chart-title">✓ 전체 PASS/FAIL 비율</div>
                <div class="chart">
                    <canvas id="pieChart"></canvas>
                </div>
            </div>

            <div class="chart-container">
                <div class="chart-title">🔴 상위 FAIL 항목</div>
                <div class="chart">
                    <canvas id="failChart"></canvas>
                </div>
            </div>

            <div class="chart-container">
                <div class="chart-title">📂 카테고리별 분석</div>
                <div class="chart">
                    <canvas id="categoryChart"></canvas>
                </div>
            </div>
        </div>

        <div class="details">
            <div class="details-title">상위 15개 FAIL 항목 상세</div>
            <table>
                <thead>
                    <tr>
                        <th>항목 코드</th>
                        <th>FAIL 횟수</th>
                        <th>비율</th>
                    </tr>
                </thead>
                <tbody>
"""

    for code, count in sorted_failures:
        percentage = (count / analytics['fail_count'] * 100) if analytics['fail_count'] > 0 else 0
        html += f"""
                    <tr>
                        <td><span class="fail">{code}</span></td>
                        <td>{count}</td>
                        <td>{percentage:.1f}%</td>
                    </tr>
"""

    html += """
                </tbody>
            </table>
        </div>

        <footer>
            <p>Chat AIP QA 시스템 | Phase 6 대시보드</p>
        </footer>
    </div>

    <script>
        // Pie Chart (PASS/FAIL)
        const pieCtx = document.getElementById('pieChart').getContext('2d');
        new Chart(pieCtx, {
            type: 'doughnut',
            data: {
                labels: ['PASS', 'FAIL'],
                datasets: [{
                    data: [""" + f"{pass_rate:.1f}, {fail_rate:.1f}" + """],
                    backgroundColor: ['#22c55e', '#ef4444'],
                    borderColor: ['#16a34a', '#dc2626'],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });

        // Bar Chart (Top Failures)
        const failCtx = document.getElementById('failChart').getContext('2d');
        new Chart(failCtx, {
            type: 'bar',
            data: {
                labels: """ + json.dumps([code for code, _ in sorted_failures]) + """,
                datasets: [{
                    label: 'FAIL 횟수',
                    data: """ + json.dumps([count for _, count in sorted_failures]) + """,
                    backgroundColor: '#ef4444',
                    borderColor: '#dc2626',
                    borderWidth: 1
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true
                    }
                }
            }
        });

        // Bar Chart (Category)
        const categoryCtx = document.getElementById('categoryChart').getContext('2d');
        new Chart(categoryCtx, {
            type: 'bar',
            data: {
                labels: """ + json.dumps([cat['name'] for cat in category_data]) + """,
                datasets: [{
                    label: 'FAIL 횟수',
                    data: """ + json.dumps([cat['fail_count'] for cat in category_data]) + """,
                    backgroundColor: ['#667eea', '#764ba2', '#f59e0b'],
                    borderColor: ['#5568d3', '#6b3a8a', '#d97706'],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    </script>
</body>
</html>
"""

    # 파일 저장
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    return output_file


def print_dashboard_info(output_file):
    """대시보드 생성 완료 메시지"""
    print(f"\n✅ HTML 대시보드 생성 완료!")
    print(f"📂 파일: {output_file}")
    print(f"🌐 브라우저에서 열어서 확인하세요")
    print(f"   (파일 > 열기 또는 더블클릭)\n")
