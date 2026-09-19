#!/usr/bin/env python3
"""B 站 Cookie 获取工具：扫码登录，自动提取 SESSDATA 等 Cookie。

用法：
    python3 get_cookie.py                 # 终端扫码，打印 Cookie
    python3 get_cookie.py --save .env     # 同时把 Cookie 写入文件

二维码显示依赖 qrcode 库（pip install qrcode，纯 Python 无编译依赖）；
未安装时降级为打印登录链接。
"""
from __future__ import annotations

import argparse
import http.cookiejar
import json
import sys
import time
import urllib.parse
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

GEN = "https://passport.bilibili.com/x/passport-login/web/qrcode/generate"
POLL = "https://passport.bilibili.com/x/passport-login/web/qrcode/poll"


def _get(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode("utf-8"))


def generate_qr() -> tuple[str, str]:
    data = _get(GEN)
    if data.get("code") != 0:
        raise RuntimeError(f"生成二维码失败: {data.get('message')}")
    return data["data"]["url"], data["data"]["qrcode_key"]


def show_qr(url: str) -> None:
    """终端显示二维码；无 qrcode 库时降级为打印链接。"""
    try:
        import qrcode
        qr = qrcode.QRCode(border=2)
        qr.add_data(url)
        qr.make(fit=True)
        qr.print_ascii(invert=True)
    except ImportError:
        print("（未安装 qrcode 库，无法在终端画二维码）")
        print(f"请用浏览器打开以下链接后扫码，或用其他工具把链接生成二维码：\n{url}\n")


def poll(key: str) -> tuple[int, dict]:
    url = POLL + "?" + urllib.parse.urlencode({"qrcode_key": key})
    data = _get(url)
    return data.get("code"), data.get("data") or {}


def fetch_cookie(sync_url: str) -> dict:
    """访问登录同步 URL，用 cookiejar 收集 SESSDATA 等。"""
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    req = urllib.request.Request(sync_url, headers={"User-Agent": UA})
    try:
        opener.open(req, timeout=20)
    except Exception:
        pass
    return {c.name: c.value for c in jar}


def main() -> int:
    ap = argparse.ArgumentParser(description="B 站扫码登录获取 Cookie")
    ap.add_argument("--save", help="把 Cookie 写入指定文件（如 .env）")
    ap.add_argument("--interval", type=float, default=2.0, help="轮询间隔秒（默认 2）")
    args = ap.parse_args()

    url, key = generate_qr()
    print("=" * 60)
    print("请用「哔哩哔哩 App」扫码登录（有效期约 3 分钟）：")
    print("=" * 60)
    show_qr(url)

    while True:
        code, data = poll(key)
        if code == 0:
            break
        if code == 86090:
            print("已扫码，请在手机上确认登录...")
        elif code == 86038:
            print("二维码已过期，重新生成...")
            url, key = generate_qr()
            show_qr(url)
            continue
        elif code not in (86101,):  # 86101 未扫码，静默继续
            print(f"轮询返回 code={code}，继续等待...")
        time.sleep(args.interval)

    cookies = fetch_cookie(data.get("url") or "")
    if not cookies:
        print("\n[!] 未获取到 Cookie，请重试。")
        return 1

    print("\n" + "=" * 60)
    print("登录成功！Cookie 如下：")
    print("=" * 60)
    sessdata = cookies.get("SESSDATA", "")
    if sessdata:
        print(f"\nSESSDATA（单独）:\n{sessdata}\n")
    full = "; ".join(f"{k}={v}" for k, v in cookies.items())
    print(f"完整 Cookie:\n{full}\n")
    print("可直接在终端执行：")
    print(f'export BILI_COOKIE="{full}"')
    print()

    if args.save:
        with open(args.save, "w", encoding="utf-8") as f:
            f.write(full)
        print(f"已保存到 {args.save}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
