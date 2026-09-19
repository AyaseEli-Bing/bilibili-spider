"""B 站 UP 主数据量检测工具 — 入口。

用法示例：
  BILI_SESSDATA=xxx python -m src.main 495585242
  BILI_SESSDATA=xxx python -m src.main 495585242 --limit 20 --out ./output
"""
from __future__ import annotations

import argparse
import os
import re
import sys

from .auth import interactive_login
from .config import DEFAULT_INTERVAL, REPO_URL, VERSION, get_cookie
from .spider import get_up_info, get_video_detail, get_video_list
from .stats import format_report
from .storage import save_all
from .utils import BiliSession


def extract_uid(raw: str) -> str:
    m = re.search(r"(\d+)", str(raw))
    if not m:
        print("错误：无法从输入中解析出 UID，请提供纯数字 UID 或主页链接")
        sys.exit(1)
    return m.group(1)


ABOUT_TEXT = f"""Bilibili Spider v{VERSION}
B 站 UP 主数据量检测工具（免安装、零运行时依赖）

功能：
  · 检测某 UP 主投稿数据量（抓取前概览：粉丝数 / 投稿总数）
  · 抓取每条视频元数据（标题 / 播放 / 点赞 / 投币 / 收藏 / 弹幕 / 时长 / 发布时间）
  · 汇总统计：总播放 / 总点赞 / 总时长 / 平均播放 等
  · 维度分析：时长分布、发布时间分布
  · 结果导出 CSV + Excel（零依赖手写 xlsx）

用法：
  bilibili-spider <UID或主页链接> [选项]
  bilibili-spider --about      查看本介绍
  bilibili-spider --help       查看全部选项

仓库：{REPO_URL}
"""


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="B 站 UP 主数据量检测工具")
    p.add_argument("uid", nargs="?", default=None,
                   help="UP 主 UID 或主页链接（如 https://space.bilibili.com/495585242），留空则交互输入")
    p.add_argument("--interval", type=float, default=DEFAULT_INTERVAL, help="请求间隔秒（默认 1.0）")
    p.add_argument("--out", default="./output", help="输出目录（默认 ./output）")
    p.add_argument("--cookie", default="", help="完整 Cookie 串（可选，默认读 BILI_COOKIE/BILI_SESSDATA）")
    p.add_argument("--limit", type=int, default=0, help="只检测最新 N 个视频（默认 0 = 全部）")
    p.add_argument("--about", action="store_true", help="显示项目介绍")
    p.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    if args.about:
        print(ABOUT_TEXT)
        return 0

    uid_input = args.uid
    interactive_mode = not uid_input
    if interactive_mode:
        uid_input = input("请输入 UP 主 UID 或主页链接: ").strip()
    uid = extract_uid(uid_input)

    # 数量：命令行 --limit 优先；交互模式下未指定则询问
    limit = args.limit
    if not limit and interactive_mode:
        raw = input("请输入要检测的数量（留空或 0 = 全部）: ").strip()
        try:
            limit = int(raw) if raw else 0
        except ValueError:
            limit = 0

    cookie = args.cookie or get_cookie()
    if not cookie:
        print("未检测到登录 Cookie，尝试扫码登录（Ctrl+C 可跳过，未登录可能受限）...")
        try:
            cookie = interactive_login(interval=args.interval)
            print("登录成功！")
        except KeyboardInterrupt:
            print("\n已跳过登录，以未登录状态继续。")
            cookie = ""
        except Exception as e:  # noqa: BLE001
            print(f"扫码登录失败: {e}，以未登录状态继续。")
            cookie = ""

    session = BiliSession(cookie=cookie, interval=args.interval)
    out_dir = os.path.abspath(args.out)
    os.makedirs(out_dir, exist_ok=True)

    print(f"==> 获取 UP 主 {uid} 信息...")
    up = get_up_info(session, uid)
    up_name = up["name"]
    up_fans = up["fans"]
    print(f"    UP 主：{up_name}")

    print("==> 抓取投稿列表...")
    video_list = get_video_list(session, uid)
    total_available = len(video_list)
    if limit and limit > 0:
        video_list = video_list[:limit]
    print(f"    投稿总数 {total_available} 个，本次检测 {len(video_list)} 个")
    if not video_list:
        print("没有获取到视频，退出。")
        return 0

    rows: list[dict] = []
    total = len(video_list)
    for i, v in enumerate(video_list, 1):
        try:
            rows.append(get_video_detail(session, v["bvid"], up_name))
            print(f"    [{i}/{total}] {rows[-1]['标题'][:40]}")
        except Exception as e:  # noqa: BLE001
            print(f"    [{i}/{total}] {v['bvid']} 详情获取失败: {e}")

    if not rows:
        print("没有采集到有效数据，退出。")
        return 0

    # 输出数据量检测报告
    print()
    print(format_report(up_name, up_fans, total_available, rows))

    # 清理内部字段后导出
    for r in rows:
        for k in ("_duration",):
            r.pop(k, None)

    csv_path, xlsx_path = save_all(out_dir, rows)
    print(f"==> 完成！")
    print(f"    数据文件：{csv_path}")
    print(f"    数据文件：{xlsx_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
