"""Offline regressions for the public video-list pagination entry point."""
from unittest.mock import patch

import pytest

from src.spider import get_video_list


class FakeSession:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def request_json(self, url, *, params, wbi):
        assert url == "https://api.bilibili.com/x/space/wbi/arc/search"
        assert params == {
            "mid": "fixture-up", "pn": len(self.calls) + 1,
            "ps": 50, "order": "pubdate",
        }
        assert wbi is True
        assert len(self.calls) < len(self.responses), "Unexpected extra list request"
        self.calls.append(dict(params))
        return self.responses[len(self.calls) - 1]


def page(total, start, size):
    return {
        "code": 0,
        "data": {
            "page": {"count": total},
            "list": {"vlist": [
                {"bvid": f"BV{number}", "title": f"video {number}",
                 "created": number, "length": "00:01"}
                for number in range(start, start + size)
            ]},
        },
    }


def test_collects_all_records_from_short_pages(capsys):
    session = FakeSession([
        page(100, 0, 30), page(100, 30, 30),
        page(100, 60, 30), page(100, 90, 10),
    ])
    with patch("src.spider.time.sleep", return_value=None):
        items = get_video_list(session, "fixture-up")

    assert len(items) == 100
    assert [item["bvid"] for item in items] == [f"BV{i}" for i in range(100)]
    assert items[0] == {
        "bvid": "BV0", "title": "video 0", "created": 0, "length": "00:01",
    }
    assert items[-1]["bvid"] == "BV99"
    assert len(session.calls) == 4
    assert "警告：声明" not in capsys.readouterr().out


@pytest.mark.parametrize(
    ("sizes", "expected_count"),
    [([30, 30, 0], 60), ([0], 0)],
    ids=["early-empty-page", "first-page-empty"],
)
def test_warns_once_when_declared_records_are_missing(sizes, expected_count, capsys):
    responses = []
    start = 0
    for size in sizes:
        responses.append(page(100, start, size))
        start += size
    session = FakeSession(responses)
    with patch("src.spider.time.sleep", return_value=None):
        items = get_video_list(session, "fixture-up")

    assert len(items) == expected_count
    warnings = [line for line in capsys.readouterr().out.splitlines()
                if line.startswith("警告：声明")]
    assert warnings == [f"警告：声明 100 条，实际取到 {expected_count} 条"]
    assert len(session.calls) == len(sizes)


@pytest.mark.parametrize(
    ("total", "sizes", "expected_count"),
    [(0, [0], 0), (100, [50, 50], 100), (60, [30, 30], 60),
     (None, [30, 30, 0], 60), (0, [30, 30, 0], 60)],
    ids=["empty-list", "full-pages", "exact-short-pages",
         "missing-count", "zero-count-with-records"],
)
def test_stops_at_known_total_or_empty_page_without_warning(
    total, sizes, expected_count, capsys,
):
    responses = []
    start = 0
    for size in sizes:
        response = page(total, start, size)
        if total is None:
            del response["data"]["page"]["count"]
            response["data"]["page"]["total"] = 1
        responses.append(response)
        start += size
    session = FakeSession(responses)
    with patch("src.spider.time.sleep", return_value=None):
        items = get_video_list(session, "fixture-up")

    assert len(items) == expected_count
    assert [item["bvid"] for item in items] == [f"BV{i}" for i in range(expected_count)]
    assert len(session.calls) == len(sizes)
    assert "警告：声明" not in capsys.readouterr().out


def test_accepts_overdelivery_and_duplicate_records_without_warning(capsys):
    session = FakeSession([page(55, 0, 30), page(55, 0, 30)])
    with patch("src.spider.time.sleep", return_value=None):
        items = get_video_list(session, "fixture-up")

    assert len(items) == 60
    assert [item["bvid"] for item in items] == [f"BV{i}" for i in range(30)] * 2
    assert len(session.calls) == 2
    assert "警告：声明" not in capsys.readouterr().out


@pytest.mark.parametrize("after_first_page", [False, True], ids=["first", "later"])
def test_propagates_existing_api_error(after_first_page, capsys):
    responses = [page(100, 0, 30)] if after_first_page else []
    responses.append({"code": -352, "message": "synthetic API failure"})
    session = FakeSession(responses)
    with patch("src.spider.time.sleep", return_value=None), pytest.raises(
        RuntimeError, match="列表接口错误: synthetic API failure",
    ):
        get_video_list(session, "fixture-up")

    assert len(session.calls) == len(responses)
    assert "警告：声明" not in capsys.readouterr().out
