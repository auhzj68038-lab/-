"""macOS の通知・ダイアログ・ファイルを開く処理。macOS 以外では標準出力に出すだけ。"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

IS_MAC = sys.platform == "darwin"

# 文字列は argv 経由で渡し、AppleScript のコードに埋め込まない（インジェクション対策）
_DIALOG = """
on run argv
    set t to item 1 of argv
    set m to item 2 of argv
    set k to item 3 of argv
    if k is "error" then
        display dialog m with title t buttons {"OK"} default button 1 with icon stop
    else
        display dialog m with title t buttons {"OK"} default button 1 with icon note
    end if
end run
"""

_NOTIFY = """
on run argv
    display notification (item 2 of argv) with title (item 1 of argv)
end run
"""


def dialog(title: str, message: str, error: bool = False) -> None:
    print(f"[{title}] {message}", file=sys.stderr if error else sys.stdout)
    if IS_MAC:
        subprocess.run(
            ["osascript", "-e", _DIALOG, title, message, "error" if error else "info"],
            check=False,
            capture_output=True,
        )


def notify(title: str, message: str) -> None:
    print(f"[{title}] {message}")
    if IS_MAC:
        subprocess.run(["osascript", "-e", _NOTIFY, title, message], check=False, capture_output=True)


def open_path(path: Path) -> None:
    if IS_MAC:
        subprocess.run(["open", str(path)], check=False)
