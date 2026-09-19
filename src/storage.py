"""结果落盘：CSV（utf-8-sig）与 Excel（xlsx_writer）。"""
from __future__ import annotations

import csv
import os

from .xlsx_writer import write_xlsx

HEADERS = [
    "BV号", "标题", "UP主", "发布时间", "时长", "播放", "弹幕", "点赞",
    "投币", "收藏", "分享", "评论", "视频链接", "本地文件",
]


def write_csv(path: str, rows: list[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=HEADERS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in HEADERS})


def write_excel(path: str, rows: list[dict]) -> None:
    data = [[r.get(k, "") for k in HEADERS] for r in rows]
    write_xlsx(path, HEADERS, data)


def save_all(out_dir: str, rows: list[dict]) -> tuple[str, str]:
    os.makedirs(out_dir, exist_ok=True)
    csv_path = os.path.join(out_dir, "视频列表.csv")
    xlsx_path = os.path.join(out_dir, "视频列表.xlsx")
    write_csv(csv_path, rows)
    write_excel(xlsx_path, rows)
    return csv_path, xlsx_path
