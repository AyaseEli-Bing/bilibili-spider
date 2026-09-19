"""B 站扫码登录：获取 Cookie（供主程序与 get_cookie.py 复用）。"""
from __future__ import annotations

import http.cookiejar
import json
import time
import urllib.parse
import urllib.request

from .utils import DEFAULT_UA

GEN = "https://passport.bilibili.com/x/passport-login/web/qrcode/generate"
POLL = "https://passport.bilibili.com/x/passport-login/web/qrcode/poll"


def _get(url: str, ua: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": ua})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode("utf-8"))


def generate_qr(ua: str = DEFAULT_UA) -> tuple[str, str]:
    data = _get(GEN, ua)
    if data.get("code") != 0:
        raise RuntimeError(f"生成二维码失败: {data.get('message')}")
    return data["data"]["url"], data["data"]["qrcode_key"]


def show_qr(url: str) -> bool:
    """终端显示二维码；无 qrcode 库时返回 False。"""
    try:
        import qrcode
        qr = qrcode.QRCode(border=2)
        qr.add_data(url)
        qr.make(fit=True)
        qr.print_ascii(invert=True)
        return True
    except ImportError:
        return False


def interactive_login(ua: str = DEFAULT_UA, interval: float = 2.0) -> str:
    """交互式扫码登录，返回完整 cookie 串；失败抛异常。

    关键：扫码成功后，poll 响应通过 Set-Cookie 头返回 SESSDATA 等，
    因此必须用带 CookieJar 的 opener 发起 poll 请求，成功后直接从 jar 取。
    """
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

    url, key = generate_qr(ua)
    print("=" * 56)
    print("未检测到登录 Cookie，请用「哔哩哔哩 App」扫码登录：")
    print("=" * 56)
    if not show_qr(url):
        print(f"（无法在终端显示二维码，请用浏览器打开以下链接扫码）:\n{url}\n")

    while True:
        poll_url = POLL + "?" + urllib.parse.urlencode({"qrcode_key": key})
        req = urllib.request.Request(poll_url, headers={
            "User-Agent": ua,
            "Referer": "https://www.bilibili.com/",
        })
        with opener.open(req, timeout=20) as r:
            data = json.loads(r.read().decode("utf-8"))
        inner = data.get("data") or {}
        code = inner.get("code")
        if code == 0:
            break
        if code == 86090:
            print("已扫码，请在手机上确认登录...")
        elif code == 86038:
            print("二维码已过期，重新生成...")
            url, key = generate_qr(ua)
            show_qr(url)
            continue
        elif code not in (86101,):  # 86101 未扫码，静默继续
            print(f"轮询返回 code={code}，继续等待...")
        time.sleep(interval)

    cookie = "; ".join(f"{c.name}={c.value}" for c in jar)
    if not cookie:
        raise RuntimeError("扫码成功但未获取到 Cookie")
    return cookie
