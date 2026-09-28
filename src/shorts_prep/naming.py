"""フォルダ名・ファイル名の生成。"""

from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime

# macOS / Finder / Premiere で問題になる文字
_FORBIDDEN = re.compile(r'[/\\:*?"<>|\x00-\x1f\x7f]')
_SPACES = re.compile(r"\s+")
# macOS のファイル名上限は 255 バイト。余裕を持たせる
_MAX_BYTES = 180

_DATE_FORMATS = (
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%Y.%m.%d",
    "%Y年%m月%d日",
    "%Y%m%d",
)


def sanitize_component(text: str, fallback: str = "無題", max_bytes: int = _MAX_BYTES) -> str:
    """1つのファイル名/フォルダ名として安全な文字列にする。"""
    s = unicodedata.normalize("NFC", text or "")
    s = _SPACES.sub(" ", s)  # 改行・タブは空白1つに
    s = _FORBIDDEN.sub("_", s).strip()
    s = s.strip(".").strip()  # 先頭ドット（隠しファイル化）や末尾ドットを避ける
    if not s:
        s = fallback
    return truncate_bytes(s, max_bytes)


def truncate_bytes(s: str, max_bytes: int) -> str:
    encoded = s.encode("utf-8")
    if len(encoded) <= max_bytes:
        return s
    return encoded[:max_bytes].decode("utf-8", errors="ignore").rstrip()


def normalize_date(text: str, today: date | None = None) -> str:
    """セルの日付を YYYY-MM-DD にする。空なら今日の日付、解釈できなければ原文を安全化して使う。"""
    raw = unicodedata.normalize("NFKC", (text or "").strip())
    if not raw:
        return (today or date.today()).isoformat()
    head = raw.split()[0]  # "2026/09/28 10:00" のような時刻付きに対応
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(head, fmt).date().isoformat()
        except ValueError:
            continue
    return sanitize_component(raw, fallback=(today or date.today()).isoformat(), max_bytes=40)


def folder_name(date_cell: str, title: str, today: date | None = None) -> str:
    d = normalize_date(date_cell, today)
    t = sanitize_component(title)
    return truncate_bytes(f"{d}_{t}", _MAX_BYTES)
