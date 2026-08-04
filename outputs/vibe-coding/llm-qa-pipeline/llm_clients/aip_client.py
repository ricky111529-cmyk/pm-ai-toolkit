"""AIP API 클라이언트."""

import requests
import json
from typing import Dict, Any, Optional
import os

from llm_clients.base_client import BaseLLMClient


class AIPClient(BaseLLMClient):
    """Miricanvas Chat AIP API."""

    def __init__(self):
        super().__init__("aip")
        self.url = "https://<YOUR_API_HOST>/<YOUR_CHAT_ENDPOINT>"
        self.domain = os.getenv("AIP_API_DOMAIN", "staging")
        self.language = os.getenv("AIP_API_LANGUAGE", "ja")
        self.cookie_name = os.getenv("AIP_API_COOKIE_NAME", "<AUTH_COOKIE_NAME>")
        self.cookie_value = os.getenv("AIP_API_COOKIE_VALUE", "")

    def call_aip(
        self, user_input: str, slide_count: str = "auto", session_id: Optional[str] = None
    ) -> str:
        """AIP API 호출."""
        cookies = {self.cookie_name: self.cookie_value}
        headers = {"Content-Type": "application/json"}

        payload = {
            "language": self.language,
            "message": json.dumps({"userInput": user_input, "slideCount": slide_count}),
        }

        if session_id:
            payload["sessionId"] = session_id

        try:
            response = requests.post(
                self.url,
                json=payload,
                headers=headers,
                cookies=cookies,
                timeout=30,
            )
            return response.text
        except Exception as e:
            return json.dumps({"error": str(e)})

    def extract_content(self, response_text: str) -> str:
        """SSE 응답에서 content 추출."""
        content = ""
        for line in response_text.strip().split("\n"):
            try:
                chunk = json.loads(line)
                if chunk.get("type") == "chunk":
                    content += chunk.get("content", "")
            except:
                pass
        return content

    def extract_session_id(self, response_text: str) -> Optional[str]:
        """세션 ID 추출."""
        for line in response_text.strip().split("\n"):
            try:
                chunk = json.loads(line)
                if chunk.get("type") == "complete":
                    return chunk.get("content", "")
            except:
                pass
        return None

    def extract_json(self, response_text: str) -> Optional[str]:
        """JSON 부분 추출."""
        content = self.extract_content(response_text)
        if "--STORYLINE_JSON--" not in content:
            return None

        json_start = content.index("--STORYLINE_JSON--") + len("--STORYLINE_JSON--")
        json_str = content[json_start:].strip()

        try:
            brace_start = json_str.index("{")
            json_str = json_str[brace_start:]

            depth = 0
            for i, ch in enumerate(json_str):
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                if depth == 0:
                    return json_str[: i + 1]
        except:
            pass

        return None

    def generate_content(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """AIP API 호출 및 파싱."""
        # AIP는 프롬프트가 없고, user_input을 받는 방식이라
        # 이 메서드는 사용하지 않음
        return {
            "response": None,
            "input_tokens": 0,
            "output_tokens": 0,
            "cache_hit": False,
            "status": "not_implemented",
        }
