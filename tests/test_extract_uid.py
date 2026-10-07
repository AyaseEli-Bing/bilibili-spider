"""Offline regressions for UID extraction from user-supplied input.

`extract_uid` used to take the first run of digits anywhere in the string, so
a video link resolved to UID "1" and the tool silently scraped the wrong
channel. It also called `sys.exit`, which made it untestable.

These cases are table-driven per the issue; none of them touch the network.
"""
import pytest

from src.main import extract_uid


@pytest.mark.parametrize(
    "raw",
    [
        "123456",
        "  123456  ",
        "https://space.bilibili.com/123456",
        "http://space.bilibili.com/123456",
        "https://space.bilibili.com/123456/",
        "https://space.bilibili.com/123456?spm_id_from=333.1",
        "https://space.bilibili.com/123456#video",
    ],
    ids=["digits", "digits-padded", "space-https", "space-http", "space-trailing-slash",
         "space-with-query", "space-with-fragment"],
)
def test_accepts_plain_uid_and_space_profile_links(raw):
    assert extract_uid(raw) == "123456"


@pytest.mark.parametrize(
    "raw",
    [
        "https://www.bilibili.com/video/BV1xx411c7M0",
        "https://www.bilibili.com/video/av170001",
        "https://m.bilibili.com/2026-10-05/123456",
        "abc",
        "",
        "https://space.bilibili.com/",
        "bilibili.com/123456",
    ],
    ids=["video-bv", "video-av", "mobile-timestamp", "letters", "empty",
         "space-without-uid", "missing-scheme"],
)
def test_rejects_anything_that_is_not_a_uid_or_space_link(raw):
    with pytest.raises(ValueError):
        extract_uid(raw)


def test_error_message_points_at_the_supported_formats():
    """The message must say what to pass and what not to pass."""
    with pytest.raises(ValueError) as excinfo:
        extract_uid("https://www.bilibili.com/video/BV1xx411c7M0")
    message = str(excinfo.value)
    assert "UID" in message
    assert "space.bilibili.com" in message
    assert "视频" in message


def test_does_not_call_sys_exit():
    """Regression guard: the function must raise, not terminate the process."""
    import inspect

    import src.main as main_module

    source = inspect.getsource(main_module.extract_uid)
    assert "sys.exit" not in source