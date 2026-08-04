"""Main entry point."""

from pathlib import Path
from core import RequestRouter, get_token_logger
from processors import CachedProcessor, RealTimeProcessor
from utils import Config, DocumentManager


def setup():
    """초기화."""
    Config.ensure_directories()
    router = RequestRouter()
    router.register("cached_result", CachedProcessor)
    router.register("summary", CachedProcessor)
    router.register("analysis", RealTimeProcessor)
    return router


def cleanup_files():
    """MD 파일 크기 자동 정리."""
    manager = DocumentManager()
    root = Path(__file__).parent
    results = manager.manage_all_files(root)

    for result in results:
        if result["status"] != "ok":
            print(f"[{result['status']}] {result['file']}: {result['message']}")

    stats = manager.get_archive_stats()
    print(f"Archive: {stats['total_archives']} files, {stats['total_size_mb']}MB")


def print_metrics():
    """토큰 사용량 출력."""
    logger = get_token_logger()
    logger.print_summary()


if __name__ == "__main__":
    router = setup()
    cleanup_files()

    # 예시 요청
    request = {"type": "analysis", "tc_id": "TC-001", "payload": {}}
    result = router.process(request)
    print_metrics()
