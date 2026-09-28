"""設定ファイル（TOML）の読み込み。秘密情報はここに置かない。"""

from __future__ import annotations

import os
import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from .errors import PrepError

APP_SUPPORT_DIR = Path("~/Library/Application Support/shorts_prep").expanduser()
DEFAULT_CONFIG_PATH = APP_SUPPORT_DIR / "config.toml"
LOG_DIR = Path("~/Library/Logs/shorts_prep").expanduser()


@dataclass(frozen=True)
class Config:
    spreadsheet_id: str
    sheet_name: str
    col_date: str
    col_title: str
    col_assets: tuple[str, ...]
    col_script: str
    output_root: Path
    template: Path | None
    max_size_bytes: int
    timeout_sec: float
    retries: int
    allowed_content_types: tuple[str, ...] = field(default_factory=tuple)
    open_folder: bool = True
    open_premiere: bool = True


def config_path(override: str | None = None) -> Path:
    if override:
        return Path(override).expanduser()
    env = os.environ.get("SHORTS_PREP_CONFIG")
    if env:
        return Path(env).expanduser()
    return DEFAULT_CONFIG_PATH


def load_config(path: Path) -> Config:
    if not path.is_file():
        raise PrepError(
            f"設定ファイルが見つかりません:\n{path}\n\n"
            "`shorts-prep init-config` で作成してから編集してください。"
        )
    with path.open("rb") as f:
        try:
            raw = tomllib.load(f)
        except tomllib.TOMLDecodeError as e:
            raise PrepError(f"設定ファイルの書式が正しくありません:\n{path}\n{e}") from e
    return parse_config(raw)


_SHEET_URL = re.compile(r"/spreadsheets/d/([A-Za-z0-9_-]+)")


def extract_spreadsheet_id(text: str) -> str:
    """スプレッドシートのURLをそのまま貼られてもIDを取り出す。"""
    text = text.strip()
    m = _SHEET_URL.search(text)
    return m.group(1) if m else text


def parse_config(raw: dict) -> Config:
    sheet = raw.get("sheet", {})
    cols = raw.get("columns", {})
    paths = raw.get("paths", {})
    dl = raw.get("download", {})
    after = raw.get("after", {})

    spreadsheet_id = extract_spreadsheet_id(str(sheet.get("spreadsheet_id", "")))
    if not spreadsheet_id or "ここに" in spreadsheet_id:
        raise PrepError("設定ファイルの [sheet] spreadsheet_id を設定してください。")

    assets = cols.get("assets", ["素材URL"])
    if isinstance(assets, str):
        assets = [assets]

    template = str(paths.get("template", "")).strip()

    return Config(
        spreadsheet_id=spreadsheet_id,
        sheet_name=str(sheet.get("sheet_name", "シート1")),
        col_date=str(cols.get("date", "日付")),
        col_title=str(cols.get("title", "タイトル")),
        col_assets=tuple(str(a) for a in assets),
        col_script=str(cols.get("script", "")).strip(),
        output_root=Path(
            paths.get("output_root", "~/Desktop/プレミア/ショート動画自動作成")
        ).expanduser(),
        template=Path(template).expanduser() if template else None,
        max_size_bytes=int(dl.get("max_size_mb", 2048)) * 1024 * 1024,
        timeout_sec=float(dl.get("timeout_sec", 60)),
        retries=max(0, int(dl.get("retries", 3))),
        allowed_content_types=tuple(
            dl.get(
                "allowed_content_types",
                ["image/", "video/", "audio/", "application/octet-stream"],
            )
        ),
        open_folder=bool(after.get("open_folder", True)),
        open_premiere=bool(after.get("open_premiere", True)),
    )
