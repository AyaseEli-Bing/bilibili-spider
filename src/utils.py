"""通用工具：wbi 签名、urllib 请求封装、限速、下载、ffmpeg 定位。纯标准库。"""
from __future__ import annotations

import hashlib
import http.cookiejar
import json
import os
import shutil
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
REFERER = "https://www.bilibili.com"

# wbi 签名乱序表（B 站官方固定值）
_MIXIN_KEY_ENC_TAB = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49,
    33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16, 24, 55, 40,
    61, 26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11,
    36, 20, 34, 44, 52,
]


def get_mixin_key(orig: str) -> str:
    return "".join(orig[i] for i in _MIXIN_KEY_ENC_TAB)[:32]


def enc_wbi(params: dict, img_key: str, sub_key: str) -> dict:
    """对请求参数做 wbi 签名，返回带 wts/w_rid 的新参数 dict。"""
    mixin_key = get_mixin_key(img_key + sub_key)
    params = dict(params)
    params["wts"] = round(time.time())
    # 按 key 排序
    params = dict(sorted(params.items()))
    # 过滤 value 中的 !'()* 字符
    cleaned = {
        k: "".join(ch for ch in str(v) if ch not in "!'()*")
        for k, v in params.items()
    }
    query = urllib.parse.urlencode(cleaned)
    params["w_rid"] = hashlib.md5((query + mixin_key).encode()).hexdigest()
    return params


class RateLimiter:
    """线程安全的全局限速器：保证相邻两次请求之间至少间隔 interval 秒。"""

    def __init__(self, interval: float = 1.0):
        self.interval = interval
        self._lock = threading.Lock()
        self._last = 0.0

    def wait(self):
        with self._lock:
            now = time.time()
            wait = self._last + self.interval - now
            if wait > 0:
                time.sleep(wait)
            self._last = time.time()


class BiliSession:
    """B 站请求会话：携带 Cookie/UA/Referer，支持 wbi 签名、重试、限速。"""

    def __init__(self, cookie: str = "", ua: str = DEFAULT_UA, interval: float = 1.0):
        self.cookie = cookie
        self.ua = ua
        self.limiter = RateLimiter(interval)
        self._img_key: str | None = None
        self._sub_key: str | None = None

    # ---- 基础请求 ----
    def _headers(self, referer: str = REFERER) -> dict:
        # 注意：不要加 Accept: application/json，会触发 B 站风控（-352）
        h = {
            "User-Agent": self.ua,
            "Referer": referer,
        }
        if self.cookie:
            h["Cookie"] = self.cookie
        return h

    def request_json(self, url: str, params: dict | None = None,
                     wbi: bool = False, referer: str = REFERER,
                     retries: int = 3, timeout: int = 20) -> dict:
        """GET 请求并解析 JSON，失败自动重试。"""
        self._ensure_buvid3()
        if params:
            if wbi:
                self._ensure_wbi_keys()
                params = enc_wbi(params, self._img_key, self._sub_key)
            url = url + "?" + urllib.parse.urlencode(params)

        last_err: Exception | None = None
        for attempt in range(retries):
            self.limiter.wait()
            try:
                req = urllib.request.Request(url, headers=self._headers(referer))
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except (urllib.error.URLError, urllib.error.HTTPError,
                    TimeoutError, json.JSONDecodeError) as e:
                last_err = e
                time.sleep(1.5 * (attempt + 1))
        raise RuntimeError(f"请求失败（已重试 {retries} 次）: {url} -> {last_err}")

    def download(self, url: str, dest: str, referer: str = REFERER,
                 retries: int = 3, timeout: int = 60,
                 chunk: int = 1024 * 1024) -> None:
        """流式下载二进制文件到 dest。"""
        self._ensure_buvid3()
        last_err: Exception | None = None
        for attempt in range(retries):
            try:
                req = urllib.request.Request(url, headers=self._headers(referer))
                with urllib.request.urlopen(req, timeout=timeout) as resp, \
                        open(dest, "wb") as f:
                    while True:
                        buf = resp.read(chunk)
                        if not buf:
                            break
                        f.write(buf)
                return
            except (urllib.error.URLError, urllib.error.HTTPError,
                    TimeoutError, OSError) as e:
                last_err = e
                time.sleep(1.5 * (attempt + 1))
        raise RuntimeError(f"下载失败: {url} -> {last_err}")

    # ---- 设备指纹 ----
    def _ensure_buvid3(self):
        """若 Cookie 缺 buvid3，访问首页自动补齐（未登录也能过风控）。"""
        if "buvid3" in self.cookie:
            return
        cj = http.cookiejar.CookieJar()
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
        try:
            req = urllib.request.Request("https://www.bilibili.com/",
                                         headers={"User-Agent": self.ua})
            opener.open(req, timeout=10)
        except Exception:
            return
        for c in cj:
            if c.name in ("buvid3", "buvid4", "b_nut", "_uuid"):
                self.cookie += f"; {c.name}={c.value}"
        self.cookie = self.cookie.strip().lstrip(";").strip()

    # ---- wbi ----
    def _ensure_wbi_keys(self):
        if self._img_key and self._sub_key:
            return
        data = self.request_json("https://api.bilibili.com/x/web-interface/nav")
        wbi_img = data["data"]["wbi_img"]
        self._img_key = wbi_img["img_url"].rsplit("/", 1)[1].split(".")[0]
        self._sub_key = wbi_img["sub_url"].rsplit("/", 1)[1].split(".")[0]


def find_ffmpeg() -> str | None:
    """定位 ffmpeg：优先打包内置（PyInstaller），回退系统 PATH。"""
    if getattr(sys, "frozen", False):
        base = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
        for name in ("ffmpeg", "ffmpeg.exe"):
            for cand in (os.path.join(base, "bin", name), os.path.join(base, name)):
                if os.path.exists(cand):
                    return cand
    return shutil.which("ffmpeg")
