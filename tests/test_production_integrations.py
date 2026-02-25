import os

from src.integrations.brenner_adapter.agent_mail import BrennerAdapter, BrennerNotConfiguredError
from src.integrations.ms_client import MSClient
from src.tools.markdown_browser import MarkdownBrowser, MDWBConfig, CaptureStatus


def test_brenner_requires_configuration_when_not_simulated(monkeypatch):
    monkeypatch.delenv("BRENNER_HTTP_URL", raising=False)
    monkeypatch.delenv("BRENNER_HTTP_TOKEN", raising=False)
    monkeypatch.setenv("BRENNER_SIMULATE", "false")

    adapter = BrennerAdapter(simulate=False)
    try:
        adapter.send_query("deep reasoning")
        assert False, "Expected BrennerNotConfiguredError"
    except BrennerNotConfiguredError:
        assert True


def test_markdown_browser_disabled_status():
    browser = MarkdownBrowser(config=MDWBConfig(mdwb_path="definitely-not-a-real-mdwb"))
    result = browser.capture_url("https://example.com")
    assert result.status == CaptureStatus.DISABLED


def test_ms_client_returns_empty_without_binary():
    client = MSClient()
    client.config.ms_path = "definitely-not-a-real-ms"
    client._available = None
    assert client.search_skills("planner") == []
    assert client.fetch_skill("id") == {}
