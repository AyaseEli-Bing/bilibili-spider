"""Offline regressions for the UP overview entry point.

Covers the failure modes of `get_up_info` that the report stage depends on:
a non-zero API code must not be reported as a zero-fan overview, and the
returned `fans` must always be an `int` so `_fmt_num` can compare it.
"""
import pytest

from src.spider import get_up_info

UID = "495585242"


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.calls = 0

    def request_json(self, url, *, params):
        assert url == "https://api.bilibili.com/x/web-interface/card"
        assert params == {"mid": UID}
        self.calls += 1
        return self.response


def test_reads_name_and_fans_from_a_successful_response():
    session = FakeSession({
        "code": 0,
        "data": {"card": {"name": "测试UP主", "fans": 123456}},
    })
    assert get_up_info(session, UID) == {"name": "测试UP主", "fans": 123456}
    assert session.calls == 1


@pytest.mark.parametrize(
    ("fans", "expected"),
    [
        ("123456", 123456),
        (123456, 123456),
        (None, 0),
        ("", 0),
        ("暂无", 0),
        (-1, 0),
    ],
    ids=["numeric-string", "int", "null", "empty-string",
         "non-numeric-string", "negative"],
)
def test_normalizes_fan_count_to_int(fans, expected):
    session = FakeSession({
        "code": 0,
        "data": {"card": {"name": "测试UP主", "fans": fans}},
    })
    info = get_up_info(session, UID)
    assert info["fans"] == expected
    assert isinstance(info["fans"], int)


def test_falls_back_to_uid_when_card_omits_the_name():
    session = FakeSession({"code": 0, "data": {"card": {"fans": 1}}})
    assert get_up_info(session, UID)["name"] == UID


@pytest.mark.parametrize(
    ("code", "message"),
    [(-101, "账号未登录"), (-403, "访问权限不足"), (-352, "风控校验失败")],
    ids=["not-logged-in", "forbidden", "risk-control"],
)
def test_raises_instead_of_reporting_zero_fans_on_api_error(code, message):
    """A failed overview must not look like an UP主 with zero followers."""
    session = FakeSession({"code": code, "message": message, "data": {}})
    with pytest.raises(RuntimeError, match=f"UP 主信息接口错误: {message}"):
        get_up_info(session, UID)
    assert session.calls == 1


def test_raises_when_data_is_null():
    """`data` present but null: previously an AttributeError from `.get`."""
    session = FakeSession({"code": -101, "message": "账号未登录", "data": None})
    with pytest.raises(RuntimeError, match="UP 主信息接口错误: 账号未登录"):
        get_up_info(session, UID)
    assert session.calls == 1


def test_normalized_fans_survives_the_report_stage():
    """The regression from the issue: a string fan count broke `_fmt_num`."""
    from src.stats import format_report

    session = FakeSession({
        "code": 0,
        "data": {"card": {"name": "测试UP主", "fans": "123456"}},
    })
    info = get_up_info(session, UID)
    report = format_report(info["name"], info["fans"], 1, [{
        "BV号": "BV1", "播放": 100, "点赞": 1, "投币": 1, "收藏": 1,
        "弹幕": 1, "评论": 1, "分享": 1, "_duration": 60,
        "发布时间": "2024-01-01 10:00:00",
    }])
    assert "粉丝数：12.35 万" in report
    assert "测试UP主" in report