"""QA 자동화 시스템: 규칙 기반 + LLM 기반 검증 + 분석 리포팅"""

from .qa_pipeline import (
    call_aip,
    call_aip_multiturn,
    extract_json,
    extract_text,
    run_tc,
    run_tc_multiturn,
)
from .rule_validator import run_all_checks
from .llm_validator import (
    run_llm_checks_storyline,
    run_llm_checks_text,
    print_llm_results,
)
from .reporter import save_excel, print_summary
from .tc_generator import (
    generate_tcs,
    generate_multiturn_tc,
    generate_followup_question,
    FIXED_FOLLOWUP_QUESTIONS,
    TC_TYPE_DESCRIPTIONS,
)
from .analytics import collect_all_results, analyze_failures, generate_analysis_sheet, print_analysis
from .dashboard import generate_html_dashboard, print_dashboard_info
from .tc_validator import (
    batch_validate,
    filter_valid_tcs,
    validate_tc_format,
    validate_tc_quality,
    validate_by_type,
    detect_duplicates,
    print_validation_report,
)
from .tc_regenerator import (
    regenerate_from_failures,
    map_failure_to_types,
    calculate_priority,
    print_regeneration_summary,
)
from .tc_heuristic import (
    load_patterns,
    record_execution_result,
    analyze_patterns,
    recommend_next_types,
    generate_targeted_tcs,
    print_pattern_analysis,
)
from .tc_orchestrator import (
    generate_all_types,
    auto_qa_cycle,
    save_cycle_report,
)

__all__ = [
    # Pipeline
    "call_aip",
    "call_aip_multiturn",
    "extract_json",
    "extract_text",
    "run_tc",
    "run_tc_multiturn",
    # Validation (Rule-based)
    "run_all_checks",
    "run_llm_checks_storyline",
    "run_llm_checks_text",
    "print_llm_results",
    # Reporting
    "save_excel",
    "print_summary",
    # Analytics
    "collect_all_results",
    "analyze_failures",
    "generate_analysis_sheet",
    "print_analysis",
    # Dashboard
    "generate_html_dashboard",
    "print_dashboard_info",
    # TC Generation & Validation (Phase 6+)
    "generate_tcs",
    "generate_multiturn_tc",
    "generate_followup_question",
    "FIXED_FOLLOWUP_QUESTIONS",
    "TC_TYPE_DESCRIPTIONS",
    "batch_validate",
    "filter_valid_tcs",
    "validate_tc_format",
    "validate_tc_quality",
    "validate_by_type",
    "detect_duplicates",
    "print_validation_report",
    # TC Regeneration (Phase 6+)
    "regenerate_from_failures",
    "map_failure_to_types",
    "calculate_priority",
    "print_regeneration_summary",
    # TC Heuristic (Phase 6+)
    "load_patterns",
    "record_execution_result",
    "analyze_patterns",
    "recommend_next_types",
    "generate_targeted_tcs",
    "print_pattern_analysis",
    # TC Orchestration (Phase 6+)
    "generate_all_types",
    "auto_qa_cycle",
    "save_cycle_report",
]
