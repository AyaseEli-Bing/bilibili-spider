"""Offline regressions for the video detail entry point."""
import pytest

from src.spider import get_video_detail


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.calls = 0

    def request_json(self, url, *, params):
        assert url == "https://api.bilibili.com/x/web-interface/view"
        assert params == {"bvid": "BV1"}
        self.calls += 1
        return self.response


def test_raises_on_non_object_api_response():
    for response in (None, [], "invalid"):
        session = FakeSession(response)
        with pytest.raises(RuntimeError, match="视频 BV1 详情错误: 接口返回异常"):
            get_video_detail(session, "BV1", "up")
        assert session.calls == 1


def test_error_message_includes_api_code():
    session = FakeSession({"code": -404, "message": "啥都木有", "data": {}})
    with pytest.raises(RuntimeError) as excinfo:
        get_video_detail(session, "BV1", "up")
    message = str(excinfo.value)
    assert "视频 BV1 详情错误: 啥都木有" in message
    assert "code=-404" in message
    assert session.calls == 1


def test_reads_successful_response():
    session = FakeSession({
        "code": 0,
        "data": {
            "bvid": "BV1",
            "title": "测试标题",
            "pubdate": 1704067200,
            "duration": 65,
            "owner": {"name": "测试UP主"},
            "stat": {
                "view": 100,
                "danmaku": 1,
                "like": 2,
                "coin": 3,
                "favorite": 4,
                "share": 5,
                "reply": 6,
            },
        },
    })
    detail = get_video_detail(session, "BV1", "测试UP主")
    assert detail["BV号"] == "BV1"
    assert detail["标题"] == "测试标题"
    assert detail["UP主"] == "测试UP主"
    assert detail["播放"] == 100
    assert session.calls == 1
