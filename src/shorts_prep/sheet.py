"""スプレッドシートの読み込みと最終行の解釈。"""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlsplit

from .config import Config
from .errors import PrepError

_URL_SPLIT = re.compile(r"[\s,、]+")


@dataclass(frozen=True)
class Row:
    row_number: int  # シート上の行番号（1始まり）
    date: str
    title: str
    asset_urls: tuple[str, ...]
    invalid_urls: tuple[str, ...]
    script: str


def fetch_values(service, spreadsheet_id: str, sheet_name: str) -> list[list[str]]:
    """シート全体の値を表示形式（日付も見た目通りの文字列）で取得する。"""
    quoted = "'" + sheet_name.replace("'", "''") + "'"
    try:
        resp = (
            service.spreadsheets()
            .values()
            .get(
                spreadsheetId=spreadsheet_id,
                range=quoted,
                valueRenderOption="FORMATTED_VALUE",
                majorDimension="ROWS",
            )
            .execute()
        )
    except Exception as e:  # googleapiclient.errors.HttpError など
        raise PrepError(
            "スプレッドシートを読み込めませんでした。\n"
            "・spreadsheet_id とシート名が正しいか\n"
            "・ログインしたアカウントにシートの閲覧権限があるか\n"
            f"を確認してください。\n\n詳細: {e}"
        ) from e
    return resp.get("values", [])


def pick_last_row(values: list[list[str]], cfg: Config) -> Row:
    if not values:
        raise PrepError(f"シート「{cfg.sheet_name}」が空です。")
    header = [str(h).strip() for h in values[0]]

    def col_index(name: str, required: bool) -> int | None:
        if name in header:
            return header.index(name)
        if required:
            raise PrepError(
                f"見出し行に列「{name}」が見つかりません。\n"
                f"見つかった列: {', '.join(h for h in header if h) or '(なし)'}\n"
                "設定ファイルの [columns] を確認してください。"
            )
        return None

    i_date = col_index(cfg.col_date, required=True)
    i_title = col_index(cfg.col_title, required=True)
    i_assets = [col_index(c, required=True) for c in cfg.col_assets]
    i_script = col_index(cfg.col_script, required=False) if cfg.col_script else None

    last_idx = None
    for idx in range(len(values) - 1, 0, -1):
        if any(str(c).strip() for c in values[idx]):
            last_idx = idx
            break
    if last_idx is None:
        raise PrepError(f"シート「{cfg.sheet_name}」にデータ行がありません（見出し行のみ）。")

    row = values[last_idx]

    def cell(i: int | None) -> str:
        if i is None or i >= len(row):
            return ""
        return str(row[i]).strip()

    title = cell(i_title)
    if not title:
        raise PrepError(f"最終行（{last_idx + 1}行目）の「{cfg.col_title}」が空です。")

    valid: list[str] = []
    invalid: list[str] = []
    for i in i_assets:
        for token in split_urls(cell(i)):
            (valid if is_allowed_url(token) else invalid).append(token)

    return Row(
        row_number=last_idx + 1,
        date=cell(i_date),
        title=title,
        asset_urls=tuple(dict.fromkeys(valid)),  # 重複除去（順序維持）
        invalid_urls=tuple(invalid),
        script=cell(i_script),
    )


def split_urls(text: str) -> list[str]:
    return [t for t in _URL_SPLIT.split(text or "") if t]


def is_allowed_url(url: str) -> bool:
    try:
        parts = urlsplit(url)
    except ValueError:
        return False
    return parts.scheme == "https" and bool(parts.hostname)
