import json
from typing import List

from jinja2 import Environment, BaseLoader

from src.llm import LLM
from src.services.utils import retry_wrapper, validate_responses
from src.browser.search import BingSearch
from src.tools.markdown_browser import md_browser
from src.security.acip_integration import acip

PROMPT = open("src/agents/researcher/prompt.jinja2").read().strip()


class Researcher:
    def __init__(self, base_model: str):
        self.bing_search = BingSearch()
        self.llm = LLM(model_id=base_model)

    def render(self, step_by_step_plan: str, contextual_keywords: str) -> str:
        env = Environment(loader=BaseLoader())
        template = env.from_string(PROMPT)
        return template.render(
            step_by_step_plan=step_by_step_plan,
            contextual_keywords=contextual_keywords
        )

    @validate_responses
    def validate_response(self, response: str) -> dict | bool:

        if "queries" not in response and "ask_user" not in response:
            return False
        else:
            return {
                "queries": response["queries"],
                "ask_user": response["ask_user"]
            }
        
    def _capture_url_safe(self, url: str) -> str:
        """Capture a URL with mdwb if available; return markdown text or empty string."""
        result = md_browser.capture_url(url, out_dir="./tmp_mdwb")
        if result and result.get("out_md"):
            try:
                with open(result["out_md"], "r", encoding="utf-8") as f:
                    raw_md = f.read()
                # Run ACIP on externally-sourced markdown before using it
                check = acip.check_prompt(raw_md[:2000])
                return raw_md if check["allowed"] else ""
            except Exception:
                pass
        return ""

    @retry_wrapper
    def execute(self, step_by_step_plan: str, contextual_keywords: List[str], project_name: str) -> dict | bool:
        contextual_keywords_str = ", ".join(map(lambda k: k.capitalize(), contextual_keywords))
        prompt = self.render(step_by_step_plan, contextual_keywords_str)
        
        response = self.llm.inference(prompt, project_name)
        
        valid_response = self.validate_response(response)

        return valid_response
