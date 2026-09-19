"""配置读取：Cookie 等敏感信息从环境变量读取，避免硬编码泄露。"""
from __future__ import annotations

import os

VERSION = "1.4.0"
REPO_URL = "https://github.com/AyaseEli-Bing/bilibili-spider"

DEFAULT_INTERVAL = 1.0


def get_cookie() -> str:
    """读取 Cookie：优先 BILI_COOKIE（完整串），其次 BILI_SESSDATA（自动拼 SESSDATA=）。"""
    full = os.environ.get("BILI_COOKIE", "").strip()
    if full:
        return full
    sessdata = os.environ.get("BILI_SESSDATA", "").strip()
    if sessdata:
        return f"SESSDATA={sessdata}"
    return ""
