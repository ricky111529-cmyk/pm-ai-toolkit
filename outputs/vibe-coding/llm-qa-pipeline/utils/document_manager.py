"""MD 파일 크기 자동 관리 및 압축 시스템."""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

from utils.config import Config


class DocumentManager:
    """MD 파일 크기 제한 및 자동 아카이브."""

    # 파일별 제한
    LIMITS = {
        "README.md": {"lines": 50, "chars": 3000},
        "config.yaml": {"lines": 30, "chars": 2000},
        "*.md": {"lines": 100, "chars": 8000},  # 기본값
    }

    def __init__(self):
        self.config = Config
        self.config.ensure_directories()
        self.archive_root = Path(__file__).parent.parent / "archive"
        self.archive_root.mkdir(exist_ok=True)

    def get_limit(self, filename: str) -> Dict[str, int]:
        """파일명으로 제한 가져오기."""
        if filename in self.LIMITS:
            return self.LIMITS[filename]
        return self.LIMITS.get("*.md", {"lines": 100, "chars": 8000})

    def check_file_size(self, filepath: Path) -> Dict:
        """파일 크기 체크."""
        if not filepath.exists():
            return {"status": "not_found"}

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            lines = content.split("\n")

        limit = self.get_limit(filepath.name)
        line_count = len(lines)
        char_count = len(content)

        exceeds_lines = line_count > limit["lines"]
        exceeds_chars = char_count > limit["chars"]

        return {
            "status": "ok",
            "lines": line_count,
            "chars": char_count,
            "limit_lines": limit["lines"],
            "limit_chars": limit["chars"],
            "exceeds_lines": exceeds_lines,
            "exceeds_chars": exceeds_chars,
            "exceeds": exceeds_lines or exceeds_chars,
        }

    def compress_content(self, content: str) -> str:
        """내용 압축: 빈 줄 제거, 주석 정리."""
        lines = content.split("\n")

        # 1. 연속 빈 줄 제거
        compressed = []
        prev_empty = False
        for line in lines:
            if not line.strip():
                if not prev_empty:
                    compressed.append("")
                prev_empty = True
            else:
                compressed.append(line)
                prev_empty = False

        # 2. 불필요한 공백 제거
        result = "\n".join(compressed).strip()

        return result

    def split_content(self, filepath: Path) -> Tuple[str, str]:
        """
        내용 분할: 앞부분 2/3을 archive로, 뒷부분 1/3만 유지.

        Returns:
            (유지할_내용, 아카이브할_내용)
        """
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        lines = content.split("\n")
        total_lines = len(lines)
        split_point = int(total_lines * 2 / 3)

        archive_part = "\n".join(lines[:split_point])
        keep_part = "\n".join(lines[split_point:])

        return keep_part, archive_part

    def archive_content(self, filepath: Path, archive_content: str) -> Path:
        """내용을 archive 폴더로 저장."""
        relative_path = filepath.relative_to(filepath.parent.parent)
        archive_path = self.archive_root / relative_path.with_suffix(
            ".archive_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".txt"
        )

        archive_path.parent.mkdir(parents=True, exist_ok=True)

        with open(archive_path, "w", encoding="utf-8") as f:
            f.write(archive_content)

        return archive_path

    def manage_file(self, filepath: Path) -> Dict:
        """
        파일 크기 확인 및 자동 정리.

        Process:
        1. 크기 체크
        2. 초과 → 압축 시도
        3. 여전히 초과 → 앞부분 2/3 아카이브
        """
        if not filepath.exists():
            return {"status": "error", "message": "File not found"}

        status = self.check_file_size(filepath)

        if not status["exceeds"]:
            return {"status": "ok", "message": "Within limits", "stats": status}

        # 압축 시도
        with open(filepath, "r", encoding="utf-8") as f:
            original = f.read()

        compressed = self.compress_content(original)
        compressed_lines = len(compressed.split("\n"))
        compressed_chars = len(compressed)

        # 압축된 내용으로 파일 업데이트
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(compressed)

        limit = self.get_limit(filepath.name)
        still_exceeds = (
            compressed_lines > limit["lines"]
            or compressed_chars > limit["chars"]
        )

        if not still_exceeds:
            return {
                "status": "compressed",
                "message": f"Compressed {len(original) - len(compressed)} chars",
                "before": {"lines": len(original.split('\n')), "chars": len(original)},
                "after": {"lines": compressed_lines, "chars": compressed_chars},
            }

        # 여전히 초과 → 앞부분 2/3 아카이브
        keep_part, archive_part = self.split_content(filepath)
        archive_path = self.archive_content(filepath, archive_part)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(keep_part)

        keep_lines = len(keep_part.split("\n"))
        keep_chars = len(keep_part)

        return {
            "status": "archived",
            "message": f"Archived to {archive_path.name}",
            "archive_path": str(archive_path),
            "after": {"lines": keep_lines, "chars": keep_chars},
        }

    def manage_all_files(self, root_dir: Path) -> List[Dict]:
        """프로젝트 전체 MD 파일 정리."""
        results = []

        for md_file in root_dir.rglob("*.md"):
            # archive 폴더 제외
            if "archive" in md_file.parts:
                continue

            result = self.manage_file(md_file)
            result["file"] = str(md_file.relative_to(root_dir))
            results.append(result)

        return results

    def get_archive_stats(self) -> Dict:
        """아카이브 통계."""
        if not self.archive_root.exists():
            return {"total_archives": 0, "total_size_bytes": 0}

        archive_files = list(self.archive_root.rglob("*"))
        archive_files = [f for f in archive_files if f.is_file()]

        total_size = sum(f.stat().st_size for f in archive_files)

        return {
            "total_archives": len(archive_files),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / 1024 / 1024, 2),
            "archive_root": str(self.archive_root),
        }
