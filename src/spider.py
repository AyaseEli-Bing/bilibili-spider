"""B 站数据抓取：UP 主投稿列表 + 视频元数据。"""
from __future__ import annotations

import time
from datetime import datetime

from .utils import BiliSession

API_SPACE_ARC = "https://api.bilibili.com/x/space/wbi/arc/search"
API_VIEW = "https://api.bilibili.com/x/web-interface/view"


def _fmt_ts(ts) -> str:
    try:
        return datetime.fromtimestamp(int(ts)).strftime("%Y-%m-%d %H:%M:%S")
    except (TypeError, ValueError, OSError):
        return ""


def _fmt_duration(sec) -> str:
    try:
        sec = int(sec)
    except (TypeError, ValueError):
        return ""
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def _to_int(value, default: int = 0) -> int:
    """把接口返回的数字字段归一化为 int。

    B 站的粉丝数等字段会在字符串/整数之间波动，直接透传会让下游
    stats._fmt_num 的比较运算抛 TypeError。
    """
    if isinstance(value, bool):
        return default
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return number if number >= 0 else default


def get_up_info(session: BiliSession, uid: str) -> dict:
    """获取 UP 主概览信息（名称、粉丝数）。"""
    data = session.request_json(
        "https://api.bilibili.com/x/web-interface/card", params={"mid": uid}
    )
    if data.get("code") != 0:
        raise RuntimeError(f"UP 主信息接口错误: {data.get('message')}")
    # data 为 null 时 .get("data", {}) 会返回 None，需显式兜底
    card = (data.get("data") or {}).get("card") or {}
    return {
        "name": card.get("name") or str(uid),
        "fans": _to_int(card.get("fans")),
    }


def get_video_list(session: BiliSession, uid: str) -> list[dict]:
    """分页拉取 UP 主全部投稿，返回基础信息列表（含 bvid）。"""
    items: list[dict] = []
    total = None
    pn = 1
    ps = 50
    while True:
        data = session.request_json(
            API_SPACE_ARC,
            params={"mid": uid, "pn": pn, "ps": ps, "order": "pubdate"},
            wbi=True,
        )
        if data.get("code") != 0:
            raise RuntimeError(f"列表接口错误: {data.get('message')}")
        page = data["data"]["page"]
        total = page.get("count")
        vlist = data["data"]["list"]["vlist"]
        if not vlist:
            break
        for v in vlist:
            items.append({
                "bvid": v["bvid"],
                "title": v["title"],
                "created": v.get("created", 0),
                "length": v.get("length", ""),
            })
        if total and len(items) >= total:
            break
        pn += 1
        time.sleep(0.3)  # 分页间额外缓冲
    if total and len(items) < total:
        print(f"警告：声明 {total} 条，实际取到 {len(items)} 条")
    return items


def get_video_detail(session: BiliSession, bvid: str, up_name: str) -> dict:
    """抓取单个视频的完整元数据。"""
    data = session.request_json(API_VIEW, params={"bvid": bvid})
    if data.get("code") != 0:
        raise RuntimeError(f"视频 {bvid} 详情错误: {data.get('message')}")
    d = data["data"]
    stat = d.get("stat", {})
    return {
        "BV号": d["bvid"],
        "标题": d["title"],
        "UP主": d.get("owner", {}).get("name", up_name),
        "发布时间": _fmt_ts(d.get("pubdate")),
        "时长": _fmt_duration(d.get("duration")),
        "播放": stat.get("view", 0),
        "弹幕": stat.get("danmaku", 0),
        "点赞": stat.get("like", 0),
        "投币": stat.get("coin", 0),
        "收藏": stat.get("favorite", 0),
        "分享": stat.get("share", 0),
        "评论": stat.get("reply", 0),
        "视频链接": f"https://www.bilibili.com/video/{d['bvid']}",
        # 内部字段（不写入表格，供统计使用）
        "_duration": d.get("duration", 0),
    }
