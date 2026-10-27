"""外部API呼び出しの共通処理（429・5xx・通信エラーは待ってから自動リトライ）"""
import json
import os
import time
import urllib.error
import urllib.request

RETRY_CODES = {429, 500, 502, 503, 504}


def http(url, data=None, headers=None, method=None, timeout=300, retries=None):
    """JSON を送って JSON（またはバイト列）を受け取る。一時的なエラーは最大 retries 回リトライ"""
    retries = int(os.environ.get("API_RETRIES", "4")) if retries is None else retries
    body = json.dumps(data).encode() if data is not None else None
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, data=body, method=method or ("POST" if body else "GET"),
                                     headers={"Content-Type": "application/json", **(headers or {})})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read()
            return json.loads(raw) if raw[:1] in (b"{", b"[") else raw
        except urllib.error.HTTPError as e:
            detail = e.read()[:400].decode("utf-8", "replace")
            if e.code not in RETRY_CODES or attempt == retries:
                raise RuntimeError(f"HTTP {e.code}: {detail}") from None
            wait = int(e.headers.get("Retry-After") or 0) or min(20 * 2 ** attempt, 180)
            print(f"   ⏳ HTTP {e.code}（混雑/上限）→ {wait}秒待って再試行 {attempt + 1}/{retries}")
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            if attempt == retries:
                raise
            wait = min(15 * 2 ** attempt, 120)
            print(f"   ⏳ 通信エラー {e} → {wait}秒待って再試行 {attempt + 1}/{retries}")
        time.sleep(wait)
