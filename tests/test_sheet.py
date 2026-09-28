import pytest

from shorts_prep.errors import PrepError
from shorts_prep.sheet import pick_last_row


def test_last_row_skips_trailing_empty(cfg_factory):
    values = [
        ["日付", "タイトル", "素材URL"],
        ["2026/9/27", "古い", "https://a.example/1.jpg"],
        ["2026/9/28", "新しい", "https://a.example/2.jpg\nhttps://a.example/3.mp4, http://bad.example/x"],
        ["", "", ""],
        [],
    ]
    row = pick_last_row(values, cfg_factory())
    assert row.row_number == 3
    assert row.title == "新しい"
    assert row.asset_urls == ("https://a.example/2.jpg", "https://a.example/3.mp4")
    assert row.invalid_urls == ("http://bad.example/x",)


def test_multiple_asset_columns_and_dedupe(cfg_factory):
    cfg = cfg_factory(columns={"assets": ["素材1", "素材2"]})
    values = [
        ["日付", "タイトル", "素材1", "素材2"],
        ["", "t", "https://x.example/a.png", "https://x.example/a.png https://x.example/b.png"],
    ]
    row = pick_last_row(values, cfg)
    assert row.asset_urls == ("https://x.example/a.png", "https://x.example/b.png")


def test_missing_column_message(cfg_factory):
    with pytest.raises(PrepError, match="素材URL"):
        pick_last_row([["日付", "タイトル"], ["x", "y"]], cfg_factory())


def test_empty_title(cfg_factory):
    with pytest.raises(PrepError, match="タイトル"):
        pick_last_row([["日付", "タイトル", "素材URL"], ["2026/1/1", "", "https://a/b"]], cfg_factory())


def test_optional_script(cfg_factory):
    cfg = cfg_factory(columns={"script": "台本"})
    row = pick_last_row([["日付", "タイトル", "素材URL", "台本"], ["", "t", "", "こんにちは"]], cfg)
    assert row.script == "こんにちは"
    # 台本列が無くてもエラーにしない
    row = pick_last_row([["日付", "タイトル", "素材URL"], ["", "t", ""]], cfg)
    assert row.script == ""
