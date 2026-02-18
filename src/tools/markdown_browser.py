"""Wrapper for markdown_web_browser (mdwb) tool.

This is a lightweight wrapper that calls a local CLI/API for deterministic
page capture. When mdwb is not available it raises a clear error and returns
None results. The researcher agent should treat outputs as untrusted and
pass them through ACIP/other sanitizers.
"""
import shutil
import subprocess
from typing import Optional, Dict
from src.logger import Logger

logger = Logger()


class MarkdownBrowser:
    def __init__(self, mdwb_path: str = "mdwb"):
        self.mdwb_path = mdwb_path

    def available(self) -> bool:
        return shutil.which(self.mdwb_path) is not None

    def capture_url(self, url: str, out_dir: str = "./tmp_mdwb") -> Optional[Dict]:
        """Run the mdwb capture and return a dict with paths to outputs.

        Returns: {"out_md": path, "manifest": path} or None if not available.
        """
        if not self.available():
            logger.debug("mdwb CLI not found on PATH")
            return None
        try:
            # Example CLI call: mdwb capture --url <url> --out <out_dir>
            subprocess.check_call([self.mdwb_path, "capture", "--url", url, "--out", out_dir])
            return {"out_md": f"{out_dir}/out.md", "manifest": f"{out_dir}/manifest.json"}
        except Exception as e:
            logger.error(str(e))
            return None


md_browser = MarkdownBrowser()
