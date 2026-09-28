"""素材のダウンロード。既存ファイルは上書きしない。"""

from __future__ import annotations

import logging
import mimetypes
import os
import time
from dataclasses import dataclass
from email.message import Message
from pathlib import Path, PurePosixPath
from typing import Callable
from urllib.parse import unquote, urlsplit

import httpx

from . import safefs
from .naming import sanitize_component

log = logging.getLogger(__name__)

_RETRY_STATUS = {408, 425, 429, 500, 502, 503, 504}
_USER_AGENT = "shorts-prep/0.1"


class DownloadError(Exception):
    pass


class _Retryable(DownloadError):
    pass


@dataclass(frozen=True)
class DownloadOptions:
    max_size_bytes: int
    timeout_sec: float
    retries: int
    allowed_content_types: tuple[str, ...]


@dataclass(frozen=True)
class DownloadResult:
    url: str
    path: Path | None
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.path is not None


def redact(url: str) -> str:
    """ログ用。署名付きURLのクエリ（トークン等）を隠す。"""
    p = urlsplit(url)
    return f"{p.scheme}://{p.hostname}{p.path}" + ("?…" if p.query else "")


def _require_https(request: httpx.Request) -> None:
    # リダイレクト先も含めて毎回チェックされる
    if request.url.scheme != "https":
        raise DownloadError(f"https 以外への接続は拒否しました: {request.url.scheme}://{request.url.host}")


def make_client(opts: DownloadOptions, transport: httpx.BaseTransport | None = None) -> httpx.Client:
    return httpx.Client(
        follow_redirects=True,
        max_redirects=10,
        timeout=httpx.Timeout(opts.timeout_sec),
        headers={"User-Agent": _USER_AGENT},
        event_hooks={"request": [_require_https]},
        transport=transport,
    )


def download_all(
    urls: list[str] | tuple[str, ...],
    dest_dir: Path,
    opts: DownloadOptions,
    client: httpx.Client | None = None,
    sleep: Callable[[float], None] = time.sleep,
) -> list[DownloadResult]:
    own = client is None
    client = client or make_client(opts)
    results = []
    try:
        width = max(2, len(str(len(urls))))
        for i, url in enumerate(urls, start=1):
            prefix = f"{i:0{width}d}_"
            try:
                path = _download_with_retry(client, url, dest_dir, prefix, opts, sleep)
                log.info("downloaded %s -> %s", redact(url), path.name)
                results.append(DownloadResult(url, path))
            except (DownloadError, httpx.HTTPError, OSError) as e:
                log.warning("failed %s: %s", redact(url), e)
                results.append(DownloadResult(url, None, str(e)))
    finally:
        if own:
            client.close()
    return results


def _download_with_retry(client, url, dest_dir, prefix, opts, sleep) -> Path:
    attempt = 0
    while True:
        try:
            return _download_once(client, url, dest_dir, prefix, opts)
        except (_Retryable, httpx.TransportError) as e:
            if attempt >= opts.retries:
                raise DownloadError(f"{opts.retries + 1}回試しましたが失敗しました: {e}") from e
            wait = 2**attempt
            log.info("retry %s in %ss (%s)", redact(url), wait, e)
            sleep(wait)
            attempt += 1


def _download_once(client: httpx.Client, url: str, dest_dir: Path, prefix: str, opts: DownloadOptions) -> Path:
    with client.stream("GET", url) as resp:
        if resp.status_code in _RETRY_STATUS:
            raise _Retryable(f"HTTP {resp.status_code}")
        if resp.status_code != 200:
            raise DownloadError(f"HTTP {resp.status_code}")

        ctype = resp.headers.get("content-type", "application/octet-stream").split(";")[0].strip().lower()
        if not any(ctype.startswith(p) for p in opts.allowed_content_types):
            raise DownloadError(f"素材ではなさそうなファイルです（Content-Type: {ctype}）")

        length = resp.headers.get("content-length")
        if length and length.isdigit() and int(length) > opts.max_size_bytes:
            raise DownloadError(f"サイズ上限を超えています（{int(length) // (1024 * 1024)}MB）")

        name = prefix + _filename(resp, ctype)
        final = dest_dir / name
        if final.exists():
            raise DownloadError(f"同名のファイルが既にあるためスキップしました: {name}")

        fd, tmp = safefs.new_temp_file(dest_dir)
        try:
            written = 0
            with os.fdopen(fd, "wb") as f:
                for chunk in resp.iter_bytes(1024 * 1024):
                    written += len(chunk)
                    if written > opts.max_size_bytes:
                        raise DownloadError("サイズ上限を超えたため中断しました")
                    f.write(chunk)
            if written == 0:
                raise DownloadError("中身が空でした")
            try:
                safefs.commit_exclusive(tmp, final)
            except FileExistsError as e:
                raise DownloadError(f"同名のファイルが既にあるためスキップしました: {name}") from e
        except httpx.TransportError as e:
            raise _Retryable(str(e)) from e
        finally:
            tmp.unlink(missing_ok=True)
        return final


def _filename(resp: httpx.Response, ctype: str) -> str:
    name = ""
    cd = resp.headers.get("content-disposition")
    if cd:
        msg = Message()
        msg["content-disposition"] = cd
        name = msg.get_filename() or ""
    if not name:
        name = unquote(PurePosixPath(resp.url.path).name)
    name = sanitize_component(PurePosixPath(name).name, fallback="asset", max_bytes=150)
    if not PurePosixPath(name).suffix:
        ext = mimetypes.guess_extension(ctype) if ctype != "application/octet-stream" else None
        if ext:
            name += ext
    return name
