"""冒烟测试：验证 xlsx_writer / storage / wbi 签名等核心逻辑（不联网）。"""
from __future__ import annotations

import hashlib
import os
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils import enc_wbi, get_mixin_key  # noqa: E402
from src.xlsx_writer import write_xlsx  # noqa: E402
from src.storage import save_all  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_smoke")
os.makedirs(OUT, exist_ok=True)


def test_wbi():
    img_key = "7cd084941338484aae1ad9425b84077c"
    sub_key = "4932caff0ff746eab6f01bf08b70ac45"
    mixin = get_mixin_key(img_key + sub_key)
    assert len(mixin) == 32, f"mixinKey 长度应为 32，实际 {len(mixin)}"
    # mixinKey 是 img+sub 拼接后按乱序表取前 32 位，简单校验其为 img+sub 的子序列
    joined = img_key + sub_key
    assert all(c in joined for c in mixin), "mixinKey 字符应来自 img_key+sub_key"
    params = enc_wbi({"mid": "495585242", "pn": 1, "ps": 50}, img_key, sub_key)
    assert "wts" in params and "w_rid" in params, "wbi 签名应含 wts 与 w_rid"
    assert len(params["w_rid"]) == 32, "w_rid 应为 32 位 MD5"
    print("  [wbi] OK -> mixinKey/w_rid 生成正确")


def test_xlsx():
    path = os.path.join(OUT, "test.xlsx")
    headers = ["编号", "标题", "播放量", "备注"]
    rows = [
        [1, "测试 & <视频> \"标题\"", 12345, None],
        [2, "第二行", 678.5, True],
        [3, "含中文与 emoji 😀", 0, "ok"],
    ]
    write_xlsx(path, headers, rows)
    assert os.path.exists(path), "xlsx 未生成"
    with zipfile.ZipFile(path) as z:
        names = set(z.namelist())
        for required in ("[Content_Types].xml", "_rels/.rels",
                         "xl/workbook.xml", "xl/worksheets/sheet1.xml",
                         "xl/styles.xml", "xl/_rels/workbook.xml.rels"):
            assert required in names, f"缺少 {required}"
        sheet = z.read("xl/worksheets/sheet1.xml").decode("utf-8")
    assert "测试 &amp; &lt;视频&gt;" in sheet, "XML 转义失败"
    assert "inlineStr" in sheet, "文本单元格应使用 inlineStr"
    print(f"  [xlsx] OK -> {path} 结构完整，{os.path.getsize(path)} bytes")


def test_storage():
    rows = [
        {"BV号": "BV1xx", "标题": "标题A", "播放": 100, "本地文件": ""},
        {"BV号": "BV2yy", "标题": "标题B", "播放": 200, "本地文件": "/tmp/a.mp4"},
    ]
    csv_path, xlsx_path = save_all(OUT, rows)
    assert os.path.exists(csv_path) and os.path.exists(xlsx_path)
    with open(csv_path, encoding="utf-8-sig") as f:
        content = f.read()
    assert "BV号" in content and "标题A" in content, "CSV 内容异常"
    print(f"  [storage] OK -> CSV {os.path.getsize(csv_path)}B / xlsx {os.path.getsize(xlsx_path)}B")


if __name__ == "__main__":
    print("运行冒烟测试...")
    test_wbi()
    test_xlsx()
    test_storage()
    print("=== 全部通过 ===")
