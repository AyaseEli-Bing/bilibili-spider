from src.stats import duration_distribution, summarize


def test_normalizes_invalid_and_negative_stat_values():
    rows = [
        {"播放": "100", "点赞": None, "投币": -2, "_duration": "60"},
        {"播放": "invalid", "点赞": True, "投币": 3, "_duration": -1},
    ]

    summary = summarize(rows)

    assert summary["总播放量"] == "100"
    assert summary["总点赞"] == "0"
    assert summary["总投币"] == "3"
    assert summary["总时长"] == "1 分 0 秒"
    assert summary["平均时长"] == "0 分 30 秒"
    assert duration_distribution(rows) == [("1 分钟以内", 1), ("1 - 5 分钟", 1)]
