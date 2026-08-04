#!/usr/bin/env python3
"""
Chat AIP QA 시스템 — 전체 자동 실행 (Phase 6 Option A+B)

사용:
  python3 qa_run_full.py              # 모든 TC 실행, Excel + HTML 생성
  python3 qa_run_full.py --excel-only # Excel만 생성
  python3 qa_run_full.py --html-only  # HTML만 생성
  python3 qa_run_full.py TC-001 TC-002  # 특정 TC만 실행
"""

import sys
import os
from datetime import datetime
from openpyxl import Workbook
from qa import (
    collect_all_results,
    analyze_failures,
    print_analysis,
    save_excel,
    generate_analysis_sheet,
    generate_html_dashboard,
    print_dashboard_info,
)


def main():
    """메인 실행 함수"""

    # 인자 파싱
    args = sys.argv[1:] if len(sys.argv) > 1 else []
    excel_only = "--excel-only" in args
    html_only = "--html-only" in args

    # 특정 TC 지정
    tc_list = [arg for arg in args if arg.startswith("TC-")]

    print("\n" + "="*70)
    print("🚀 Chat AIP QA 시스템 — 전체 자동 실행")
    print("="*70)
    print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if tc_list:
        print(f"대상 TC: {', '.join(tc_list)}")
    else:
        print("대상 TC: 전체 (TC-001~TC-012, TC-M01~TC-M05)")

    print("="*70 + "\n")

    # Step 1: 모든 TC 실행 및 수집
    if not html_only:
        print("📝 Step 1: 모든 TC 실행 및 결과 수집...")
        try:
            all_results = collect_all_results(tc_list=tc_list if tc_list else None, verbose=True)
            print(f"\n✅ {len(all_results)}개 TC 실행 완료\n")
        except ValueError as e:
            print(f"\n❌ 에러: {e}")
            print("\n💡 해결 방법:")
            print("  1. .env 파일에서 AIP_API_COOKIE_VALUE 확인")
            print("  2. 새로운 토큰이 필요하면 업데이트하세요")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ 예상치 못한 에러: {e}")
            sys.exit(1)

    # Step 2: 분석 실행 및 콘솔 출력
    print("\n📊 Step 2: QA 결과 분석...")
    try:
        print_analysis(all_results)
    except Exception as e:
        print(f"⚠️ 분석 실패: {e}")

    # Step 3: Excel 생성 (상세 + 분석)
    if not html_only:
        print("📊 Step 3: Excel 리포트 생성...")
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = "./reports"
            os.makedirs(output_dir, exist_ok=True)

            # Excel 생성
            excel_file = os.path.join(output_dir, f"qa_report_{timestamp}.xlsx")
            save_excel(all_results, output_dir=output_dir)

            # 분석 시트 추가
            wb = Workbook()
            save_excel(all_results, output_dir=output_dir)

            print(f"✅ Excel 생성 완료")
            print(f"   📂 {excel_file}\n")
        except Exception as e:
            print(f"❌ Excel 생성 실패: {e}\n")

    # Step 4: HTML 대시보드 생성
    if not excel_only:
        print("🌐 Step 4: HTML 대시보드 생성...")
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = "./reports"
            os.makedirs(output_dir, exist_ok=True)

            html_file = os.path.join(output_dir, f"qa_dashboard_{timestamp}.html")
            generate_html_dashboard(all_results, output_file=html_file)
            print_dashboard_info(html_file)
        except Exception as e:
            print(f"❌ HTML 생성 실패: {e}\n")

    # Step 5: 완료
    print("="*70)
    print("✅ 모든 작업 완료!")
    print("="*70)
    print(f"\n📁 결과 저장 위치: ./reports/")
    print(f"⏰ 완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")


if __name__ == "__main__":
    main()
