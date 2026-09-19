"""数据量统计与维度分析：汇总统计 + 时长/发布时间分布。"""
from __future__ import annotations

from collections import Counter


def _sec_to_str(sec: int) -> str:
    sec = int(sec)
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h} 小时 {m} 分 {s} 秒"
    return f"{m} 分 {s} 秒"


def _fmt_num(n: int) -> str:
    """大数字格式化：123456 -> 12.35万。"""
    if n >= 100_000_000:
        return f"{n / 100_000_000:.2f} 亿"
    if n >= 10_000:
        return f"{n / 10_000:.2f} 万"
    return str(n)


def summarize(rows: list[dict]) -> dict[str, str]:
    """汇总统计，返回「指标 -> 文本」的字典。"""
    n = len(rows)
    if n == 0:
        return {}
    plays = sum(int(r.get("播放", 0)) for r in rows)
    likes = sum(int(r.get("点赞", 0)) for r in rows)
    coins = sum(int(r.get("投币", 0)) for r in rows)
    favs = sum(int(r.get("收藏", 0)) for r in rows)
    danmaku = sum(int(r.get("弹幕", 0)) for r in rows)
    replies = sum(int(r.get("评论", 0)) for r in rows)
    shares = sum(int(r.get("分享", 0)) for r in rows)
    duration = sum(int(r.get("_duration", 0)) for r in rows)
    return {
        "视频总数": str(n),
        "总播放量": _fmt_num(plays),
        "平均播放": _fmt_num(plays // n),
        "总点赞": _fmt_num(likes),
        "总投币": _fmt_num(coins),
        "总收藏": _fmt_num(favs),
        "总弹幕": _fmt_num(danmaku),
        "总评论": _fmt_num(replies),
        "总分享": _fmt_num(shares),
        "总时长": _sec_to_str(duration),
        "平均时长": _sec_to_str(duration // n),
    }


def duration_distribution(rows: list[dict]) -> list[tuple[str, int]]:
    """时长分布（按分钟分桶）。"""
    buckets = {"1 分钟以内": 0, "1 - 5 分钟": 0, "5 - 10 分钟": 0,
               "10 - 30 分钟": 0, "30 分钟以上": 0}
    for r in rows:
        d = int(r.get("_duration", 0))
        if d < 60:
            buckets["1 分钟以内"] += 1
        elif d < 300:
            buckets["1 - 5 分钟"] += 1
        elif d < 600:
            buckets["5 - 10 分钟"] += 1
        elif d < 1800:
            buckets["10 - 30 分钟"] += 1
        else:
            buckets["30 分钟以上"] += 1
    return [(name, cnt) for name, cnt in buckets.items() if cnt > 0]


def year_distribution(rows: list[dict]) -> list[tuple[str, int]]:
    """发布时间分布（按年份）。"""
    counter: Counter[str] = Counter()
    for r in rows:
        year = str(r.get("发布时间", ""))[:4]
        if year:
            counter[year] += 1
    return sorted(counter.items())


def format_report(up_name: str, up_fans: int, total_available: int,
                  rows: list[dict]) -> str:
    """生成完整的数据量检测报告文本。"""
    lines: list[str] = []
    bar = "=" * 56

    # 1. 抓取前概览
    lines.append(bar)
    lines.append(f"UP 主概览：{up_name}")
    lines.append(bar)
    lines.append(f"  粉丝数：{_fmt_num(up_fans)}")
    lines.append(f"  投稿总数：{total_available}")
    lines.append("")

    # 2. 汇总统计
    summary = summarize(rows)
    if summary:
        lines.append(bar)
        lines.append(f"汇总统计（本次检测 {len(rows)} 条）")
        lines.append(bar)
        for k, v in summary.items():
            lines.append(f"  {k}：{v}")
        lines.append("")

    # 3. 维度分布
    dur = duration_distribution(rows)
    if dur:
        lines.append(bar)
        lines.append("时长分布")
        lines.append(bar)
        for name, cnt in dur:
            pct = f"{cnt / len(rows) * 100:.1f}%" if rows else "0%"
            lines.append(f"  {name}：{cnt} 个（{pct}）")
        lines.append("")

    year = year_distribution(rows)
    if year:
        lines.append(bar)
        lines.append("发布时间分布（按年份）")
        lines.append(bar)
        for y, cnt in year:
            lines.append(f"  {y} 年：{cnt} 个")
        lines.append("")

    return "\n".join(lines)
