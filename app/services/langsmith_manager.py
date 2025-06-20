import os
from typing import Dict, Any


class TracingManager:
    """Handles basic LangSmith tracing"""

    def __init__(self, project_name: str = "youtube-agent"):
        self.project_name = project_name

    def get_config(self, user_id: str = "default") -> Dict[str, Any]:
        """Get LangSmith config for basic tracing"""
        if not self._is_enabled():
            return {}

        return {
            "project_name": self.project_name,
            "metadata": {"user_id": user_id},
            "tags": ["chat"]
        }

    def _is_enabled(self) -> bool:
        """Check if LangSmith is enabled"""
        return (os.environ.get("LANGCHAIN_TRACING_V2") == "true" and
                os.environ.get("LANGSMITH_API_KEY"))

