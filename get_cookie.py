#!/usr/bin/env python3
"""B 站 Cookie 获取工具：扫码登录，自动提取 SESSDATA 等 Cookie。

用法：
    python3 get_cookie.py                 # 终端扫码，打印 Cookie
    python3 get_cookie.py --save .env     # 同时把 Cookie 写入文件
"""
from __future__ import annotations

import argparse
import sys

from src.auth import interactive_login


def main() -> int:
    ap = argparse.ArgumentParser(description="B 站扫码登录获取 Cookie")
    ap.add_argument("--save", help="把 Cookie 写入指定文件（如 .env）")
    ap.add_argument("--interval", type=float, default=2.0, help="轮询间隔秒（默认 2）")
    args = ap.parse_args()

    cookie = interactive_login(interval=args.interval)

    print("\n" + "=" * 56)
    print("登录成功！Cookie 如下：")
    print("=" * 56)
    print(f"\n{cookie}\n")
    print("可直接在终端执行：")
    print(f'export BILI_COOKIE="{cookie}"')
    print()

    if args.save:
        with open(args.save, "w", encoding="utf-8") as f:
            f.write(cookie)
        print(f"已保存到 {args.save}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
