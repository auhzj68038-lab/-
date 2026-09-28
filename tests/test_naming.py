import unicodedata
from datetime import date

from shorts_prep.naming import folder_name, normalize_date, sanitize_component


def test_normalize_date_formats():
    assert normalize_date("2026/9/28") == "2026-09-28"
    assert normalize_date("2026-09-28") == "2026-09-28"
    assert normalize_date("2026年9月28日") == "2026-09-28"
    assert normalize_date("２０２６／０９／２８") == "2026-09-28"  # 全角
    assert normalize_date("2026/09/28 10:00:00") == "2026-09-28"


def test_normalize_date_empty_uses_today():
    assert normalize_date("", today=date(2026, 1, 2)) == "2026-01-02"


def test_sanitize_forbidden_and_hidden():
    assert sanitize_component("a/b:c?") == "a_b_c_"
    assert sanitize_component("..hidden") == "hidden"
    assert sanitize_component("   ") == "無題"
    assert sanitize_component("改行\nあり") == "改行 あり"


def test_sanitize_nfc():
    nfd = unicodedata.normalize("NFD", "ガイド")
    assert sanitize_component(nfd) == unicodedata.normalize("NFC", "ガイド")


def test_truncate_keeps_valid_utf8():
    s = sanitize_component("あ" * 200)
    assert len(s.encode()) <= 180
    s.encode("utf-8")


def test_folder_name():
    assert folder_name("2026/9/28", "猫の動画 #1") == "2026-09-28_猫の動画 #1"
