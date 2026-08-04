"""주제 자동 분류 및 감지."""

import re
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

from llm_clients import GeminiClient


@dataclass
class ClassificationResult:
    """분류 결과."""
    topic: Optional[str] = None
    confidence: float = 0.0
    keywords: List[str] = None
    confirmation_needed: bool = False
    suggestions: List[Tuple[str, float]] = None
    reason: str = ""

    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []
        if self.suggestions is None:
            self.suggestions = []


class TopicClassifier:
    """주제 자동 분류 (키워드 + LLM)."""

    def __init__(self, config_path: Optional[Path] = None):
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "topics.yaml"

        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

        self.topics = self.config.get("topics", {})
        self.gemini = GeminiClient()

    def extract_keywords(self, text: str) -> List[str]:
        """텍스트에서 키워드 추출."""
        # 대문자/단어 추출
        words = re.findall(r'[A-Z][a-z]+|[A-Z]+|[a-z]+', text.lower())
        return list(set(words))

    def calculate_match_score(
        self, keywords: List[str], topic_keywords: List[str]
    ) -> float:
        """키워드 매칭 점수 계산 (0-1)."""
        if not keywords or not topic_keywords:
            return 0.0

        matches = sum(1 for kw in keywords if kw in topic_keywords)
        return matches / len(topic_keywords)

    def classify(self, text: str) -> ClassificationResult:
        """
        주제 분류 (3단계).
        1. 키워드 매칭 (>0.8 → 확정)
        2. LLM 보조 (0.5-0.8)
        3. 사용자 확인 (<0.5)
        """
        keywords = self.extract_keywords(text)

        # 1단계: 키워드 매칭
        scores = {}
        for topic_id, topic_config in self.topics.items():
            score = self.calculate_match_score(
                keywords, topic_config.get("keywords", [])
            )
            scores[topic_id] = score

        max_score = max(scores.values()) if scores else 0.0
        best_topic = max(scores, key=scores.get) if scores else None

        if max_score > 0.8:
            return ClassificationResult(
                topic=best_topic,
                confidence=max_score,
                keywords=keywords,
                confirmation_needed=False,
                reason="High keyword match"
            )

        # 2단계: LLM 보조
        if max_score > 0.5:
            return self._llm_verify(text, keywords, scores)

        # 3단계: 사용자 확인 필요
        top_3 = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
        return ClassificationResult(
            topic=None,
            confidence=max_score,
            keywords=keywords,
            confirmation_needed=True,
            suggestions=top_3,
            reason="Low confidence - user confirmation needed"
        )

    def _llm_verify(
        self, text: str, keywords: List[str], scores: Dict[str, float]
    ) -> ClassificationResult:
        """LLM으로 주제 검증."""
        prompt = f"""텍스트를 보고 가장 관련있는 주제를 고르세요:

텍스트: "{text}"

주제 옵션:
{chr(10).join(f"- {topic_id}: {config['name']}" for topic_id, config in self.topics.items())}

가장 관련있는 주제 ID를 답하세요. 한 글자만."""

        try:
            result = self.gemini.generate_content(prompt, use_cache=False)
            response_text = result.get("response", "").lower().strip()

            # 응답에서 topic_id 추출
            for topic_id in self.topics.keys():
                if topic_id.lower() in response_text:
                    return ClassificationResult(
                        topic=topic_id,
                        confidence=0.75,
                        keywords=keywords,
                        confirmation_needed=False,
                        reason="LLM verified"
                    )
        except Exception as e:
            pass

        # LLM 실패 → 점수 최고 선택
        best_topic = max(scores, key=scores.get)
        return ClassificationResult(
            topic=best_topic,
            confidence=max(scores.values()),
            keywords=keywords,
            confirmation_needed=False,
            reason="LLM verification fallback"
        )
