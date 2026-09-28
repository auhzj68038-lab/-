"""Premiere Pro テンプレートの検出と複製。"""

from __future__ import annotations

from pathlib import Path

from . import safefs
from .config import Config
from .errors import PrepError


def find_template(cfg: Config) -> Path:
    if cfg.template is not None:
        t = cfg.template
        if not t.is_file():
            raise PrepError(f"Premiere テンプレートが見つかりません:\n{t}")
        if t.suffix.lower() != ".prproj":
            raise PrepError(f"テンプレートは .prproj ファイルを指定してください:\n{t}")
        return t

    root = cfg.output_root
    if not root.is_dir():
        raise PrepError(f"作業フォルダが見つかりません:\n{root}")
    found = sorted(p for p in root.iterdir() if p.is_file() and p.suffix.lower() == ".prproj")
    if not found:
        raise PrepError(
            f"Premiere テンプレート（.prproj）が見つかりません。\n"
            f"次のフォルダに1つ置いてください:\n{root}"
        )
    if len(found) > 1:
        names = "\n".join(f"・{p.name}" for p in found)
        raise PrepError(
            "テンプレート候補が複数あります。どれを使うか設定ファイルの "
            f"[paths] template に指定してください:\n{names}"
        )
    return found[0]


def copy_template(template: Path, dest_dir: Path, name: str) -> Path:
    dst = dest_dir / f"{name}.prproj"
    try:
        safefs.copy_file_exclusive(template, dst)
    except FileExistsError as e:
        raise PrepError(f"同名のプロジェクトが既にあるため複製しませんでした:\n{dst}") from e
    return dst
