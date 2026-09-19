"""B 站 UP 主视频抓取/下载工具 — 入口。

用法示例：
  BILI_SESSDATA=xxx python -m src.main 495585242
  BILI_SESSDATA=xxx python -m src.main 495585242 --qn 80 --workers 4 --out ./output
  BILI_SESSDATA=xxx python -m src.main 495585242 --no-download
"""
from __future__ import annotations

import argparse
import os
import re
import sys

from .auth import interactive_login
from .config import (DEFAULT_INTERVAL, DEFAULT_QN, DEFAULT_WORKERS,
                     REPO_URL, VERSION, get_cookie)
from .downloader import download_all
from .spider import get_up_name, get_video_detail, get_video_list
from .storage import save_all
from .utils import BiliSession, find_ffmpeg


def extract_uid(raw: str) -> str:
    m = re.search(r"(\d+)", str(raw))
    if not m:
        print("错误：无法从输入中解析出 UID，请提供纯数字 UID 或主页链接")
        sys.exit(1)
    return m.group(1)


ABOUT_TEXT = f"""Bilibili Spider v{VERSION}
B 站 UP 主视频抓取与下载工具（免安装、零运行时依赖）

功能：
  · 抓取某 UP 主全部投稿的元数据（标题 / 播放 / 点赞 / 投币 / 收藏 / 弹幕 / 时长 / 发布时间）
  · 多线程下载视频并用 ffmpeg 合并为 mp4（默认 1080P，可调）
  · 结果导出 CSV + Excel（零依赖手写 xlsx）
  · 免安装：内置 Python + ffmpeg，扫码登录自动获取 Cookie

用法：
  bilibili-spider <UID或主页链接> [选项]
  bilibili-spider --about      查看本介绍
  bilibili-spider --help       查看全部选项

仓库：{REPO_URL}
"""


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="B 站 UP 主视频抓取与下载工具")
    p.add_argument("uid", nargs="?", default=None,
                   help="UP 主 UID 或主页链接（如 https://space.bilibili.com/495585242），留空则交互输入")
    p.add_argument("--qn", type=int, default=DEFAULT_QN,
                   help=f"目标清晰度（默认 {DEFAULT_QN}=1080P；80=1080P 64=720P 32=480P 16=360P）")
    p.add_argument("--workers", type=int, default=DEFAULT_WORKERS, help="并发下载数（默认 4）")
    p.add_argument("--interval", type=float, default=DEFAULT_INTERVAL, help="请求间隔秒（默认 1.0）")
    p.add_argument("--out", default="./output", help="输出目录（默认 ./output）")
    p.add_argument("--cookie", default="", help="完整 Cookie 串（可选，默认读 BILI_COOKIE/BILI_SESSDATA）")
    p.add_argument("--no-download", action="store_true", help="只采集元数据，不下载视频文件")
    p.add_argument("--about", action="store_true", help="显示项目介绍")
    p.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    if args.about:
        print(ABOUT_TEXT)
        return 0
    uid_input = args.uid
    if not uid_input:
        uid_input = input("请输入 UP 主 UID 或主页链接: ").strip()
    uid = extract_uid(uid_input)
    cookie = args.cookie or get_cookie()
    if not cookie:
        print("未检测到登录 Cookie，尝试扫码登录（Ctrl+C 可跳过，未登录画质会受限）...")
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
    up_name = get_up_name(session, uid)
    print(f"    UP 主：{up_name}")

    print("==> 抓取投稿列表...")
    video_list = get_video_list(session, uid)
    print(f"    共 {len(video_list)} 个视频")
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

    if not args.no_download:
        ffmpeg = find_ffmpeg()
        if not ffmpeg:
            print("警告：未找到 ffmpeg，跳过视频下载（仅保存元数据）。")
        else:
            print(f"==> 开始下载视频（并发 {args.workers}，目标清晰度 qn={args.qn}）...")

            def on_done(bvid, upd, err):
                if err:
                    print(f"    [下载失败] {bvid}: {err}")
                else:
                    print(f"    [已下载] {bvid} -> {os.path.basename(upd['本地文件'])}")

            results = download_all(session, rows, out_dir, args.qn, args.workers,
                                   ffmpeg, on_done=on_done)
            for r in rows:
                res = results.get(r["BV号"], {})
                if res.get("error"):
                    r["本地文件"] = f"失败: {res['error']}"
                elif res.get("本地文件"):
                    r["本地文件"] = res["本地文件"]

    # 清理内部字段
    for r in rows:
        for k in ("_cid", "_duration", "_qn"):
            r.pop(k, None)

    csv_path, xlsx_path = save_all(out_dir, rows)
    print(f"==> 完成！")
    print(f"    数据文件：{csv_path}")
    print(f"    数据文件：{xlsx_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
