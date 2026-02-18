from typing import Any, Dict

class BrennerSkill:
    """Simple Brenner skill bridge. Safe-by-default: simulated responses unless adapter enabled."""

    def __init__(self):
        try:
            from src.integrations.brenner_adapter.agent_mail import BrennerAdapter
            self.adapter = BrennerAdapter()
        except Exception:
            self.adapter = None

    def execute(self, context: Any, **kwargs) -> Dict:
        text = context if isinstance(context, str) else kwargs.get("text", "")
        if not text:
            return {"error": "no input"}

        if "brenner:deepreason" in text.lower():
            query = text.split("brenner:deepreason", 1)[1].strip()
            if self.adapter:
                return self.adapter.send_query(query, stream=kwargs.get("stream", False))
            return {"reply": f"[Simulated Brenner] Deep reasoning on: {query}"}

        return {"error": "trigger not found"}

    @staticmethod
    def trigger_matches(text: str) -> bool:
        return "brenner:deepreason" in (text or "").lower()
