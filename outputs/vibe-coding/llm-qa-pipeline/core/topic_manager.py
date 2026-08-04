"""주제별 폴더 및 설정 관리."""

import json
from pathlib import Path
from datetime import datetime


class TopicManager:
    """주제별 폴더 생성 및 메타데이터 관리."""

    def __init__(self, root: Path = None):
        if root is None:
            root = Path(__file__).parent.parent
        self.root = root
        self.topics_dir = root / "topics"
        self.topics_dir.mkdir(exist_ok=True)

    def get_or_create(self, topic_id: str) -> Path:
        """주제 폴더 생성/가져오기."""
        topic_dir = self.topics_dir / topic_id
        if not topic_dir.exists():
            topic_dir.mkdir(parents=True, exist_ok=True)

            # README
            readme = f"# {topic_id}\n\n[Topic folder auto-created]"
            (topic_dir / "README.txt").write_text(readme)

            # config.json
            config = {
                "topic_id": topic_id,
                "created_at": datetime.now().isoformat(),
                "requests": [],
                "metadata": {}
            }
            (topic_dir / "config.json").write_text(json.dumps(config, indent=2))

            # data 폴더
            (topic_dir / "data").mkdir(exist_ok=True)

        return topic_dir

    def link_request(self, request_id: str, topic_id: str) -> None:
        """요청과 주제 연결."""
        topic_dir = self.get_or_create(topic_id)
        config_file = topic_dir / "config.json"

        with open(config_file) as f:
            config = json.load(f)

        if request_id not in config["requests"]:
            config["requests"].append(request_id)

        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)

    def get_config(self, topic_id: str) -> dict:
        """주제 설정 조회."""
        topic_dir = self.topics_dir / topic_id
        config_file = topic_dir / "config.json"

        if not config_file.exists():
            return {}

        with open(config_file) as f:
            return json.load(f)

    def list_topics(self) -> list:
        """전체 주제 목록."""
        return [d.name for d in self.topics_dir.iterdir() if d.is_dir()]
