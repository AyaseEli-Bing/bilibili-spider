"""视频下载：DASH 音视频流获取、多线程下载、ffmpeg 合并。"""
from __future__ import annotations

import os
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

from .utils import BiliSession

API_PLAYURL = "https://api.bilibili.com/x/player/playurl"

# 清晰度表（qn -> 说明），供降级选择参考
QN_ORDER = [127, 126, 125, 120, 116, 112, 80, 74, 64, 32, 16]


def _safe_name(s: str, limit: int = 60) -> str:
    s = re.sub(r'[\\/:*?"<>|\r\n\t]+', "_", s).strip()
    s = re.sub(r"\s+", " ", s)
    return s[:limit].strip() or "video"


def _pick_best(videos: list[dict], qn: int) -> dict | None:
    """在不超过目标 qn 的前提下选最高清晰度；没有则选最低清晰度降级。"""
    if not videos:
        return None
    eligible = [v for v in videos if v.get("quality", 0) <= qn]
    pool = eligible or videos
    pool = sorted(pool, key=lambda v: v.get("quality", 0), reverse=True)
    return pool[0]


def _stream_url(item: dict) -> str:
    return item.get("baseUrl") or item.get("base_url") or item.get("backupUrl") or item.get("backup_url")


def get_play_urls(session: BiliSession, bvid: str, cid: int, qn: int) -> tuple[str, str, int]:
    """返回 (视频流URL, 音频流URL, 实际清晰度 qn)。"""
    data = session.request_json(
        API_PLAYURL,
        params={"bvid": bvid, "cid": cid, "qn": qn, "fnval": 16, "fourk": 1},
    )
    if data.get("code") != 0:
        raise RuntimeError(f"取流失败 {bvid}: code={data.get('code')} {data.get('message')}")
    dash = data.get("data", {}).get("dash") or {}
    videos = dash.get("video") or []
    audios = dash.get("audio") or []
    v = _pick_best(videos, qn)
    a = audios[0] if audios else None
    if v is None or a is None:
        raise RuntimeError(f"未获取到音视频流 {bvid}")
    return _stream_url(v), _stream_url(a), v.get("quality", qn)


def merge(ffmpeg: str, video_path: str, audio_path: str, out_path: str) -> None:
    cmd = [ffmpeg, "-y", "-i", video_path, "-i", audio_path,
           "-c", "copy", "-movflags", "+faststart", out_path]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg 合并失败: {proc.stderr[-300:]}")


def download_one(session: BiliSession, bvid: str, cid: int, title: str,
                 out_dir: str, qn: int, ffmpeg: str) -> dict:
    """下载单个视频并合并，返回元数据更新（本地文件路径 + 实际清晰度）。"""
    video_url, audio_url, actual_qn = get_play_urls(session, bvid, cid, qn)
    safe = _safe_name(title)
    name = f"{bvid}_{safe}"
    video_tmp = os.path.join(out_dir, f"{name}.v.m4s")
    audio_tmp = os.path.join(out_dir, f"{name}.a.m4s")
    final = os.path.join(out_dir, f"{name}.mp4")
    try:
        session.download(video_url, video_tmp)
        session.download(audio_url, audio_tmp)
        merge(ffmpeg, video_tmp, audio_tmp, final)
    finally:
        for p in (video_tmp, audio_tmp):
            if os.path.exists(p):
                os.remove(p)
    return {"本地文件": final, "_qn": actual_qn}


def download_all(session: BiliSession, items: list[dict], out_dir: str,
                 qn: int, workers: int, ffmpeg: str,
                 on_done=None) -> dict[str, dict]:
    """多线程下载全部视频。items 为含 bvid/_cid/标题 的字典列表。

    返回 {bvid: 更新后的字段}；失败的视频记录错误信息。
    """
    results: dict[str, dict] = {}

    def task(it: dict) -> tuple[str, dict, str | None]:
        try:
            upd = download_one(session, it["bvid"], it["_cid"], it["标题"], out_dir, qn, ffmpeg)
            return it["bvid"], upd, None
        except Exception as e:  # noqa: BLE001
            return it["bvid"], {}, str(e)

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(task, it): it for it in items}
        for fut in as_completed(futs):
            bvid, upd, err = fut.result()
            if err:
                results[bvid] = {"error": err}
            else:
                results[bvid] = upd
            if on_done:
                on_done(bvid, upd, err)
    return results
