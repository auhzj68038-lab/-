"""既存ファイルを絶対に上書きしないファイル操作。

どの関数も、書き込み先が既に存在する場合は FileExistsError を送出し、
既存のファイル・フォルダには一切手を触れない。
"""

from __future__ import annotations

import errno
import os
import shutil
import tempfile
from pathlib import Path


def make_dir_exclusive(path: Path) -> None:
    """フォルダを新規作成する。既にあれば FileExistsError。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.mkdir()  # exist_ok=False: 既存なら FileExistsError


def write_bytes_exclusive(path: Path, data: bytes) -> None:
    """新規ファイルとして書き込む。既にあれば FileExistsError。"""
    with path.open("xb") as f:
        f.write(data)


def new_temp_file(dir_: Path, suffix: str = ".part") -> tuple[int, Path]:
    """同じフォルダ内に隠し一時ファイルを作る（O_EXCL で作成されるので衝突しない）。"""
    fd, name = tempfile.mkstemp(prefix=".", suffix=suffix, dir=dir_)
    return fd, Path(name)


def commit_exclusive(tmp: Path, final: Path) -> None:
    """一時ファイルを正式な名前にする。final が既にあれば FileExistsError。

    os.rename / os.replace は既存ファイルを黙って上書きするため使わない。
    os.link は宛先が存在すると必ず失敗するので安全。
    ハードリンク非対応のファイルシステム（exFAT 等）では排他オープンでコピーする。
    """
    try:
        os.link(tmp, final)
    except FileExistsError:
        raise
    except OSError as e:
        if e.errno not in (errno.EPERM, errno.ENOTSUP, errno.EOPNOTSUPP, errno.EXDEV):
            raise
        _copy_exclusive(tmp, final)
    tmp.unlink()


def copy_file_exclusive(src: Path, dst: Path) -> None:
    """src を dst にコピーする。dst が既にあれば FileExistsError。"""
    _copy_exclusive(src, dst)
    try:
        shutil.copystat(src, dst)
    except OSError:
        pass


def _copy_exclusive(src: Path, dst: Path) -> None:
    with src.open("rb") as fin:
        fout = dst.open("xb")  # ここで既存チェック。作成できた時点で dst は自分のファイル
        try:
            with fout:
                shutil.copyfileobj(fin, fout, length=1024 * 1024)
        except BaseException:
            dst.unlink(missing_ok=True)
            raise
