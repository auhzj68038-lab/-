import httpx

from shorts_prep.download import DownloadOptions, download_all, make_client

OPTS = DownloadOptions(
    max_size_bytes=100,
    timeout_sec=5,
    retries=2,
    allowed_content_types=("image/", "video/", "application/octet-stream"),
)


def _client(handler):
    return make_client(OPTS, transport=httpx.MockTransport(handler))


def _run(tmp_path, urls, handler, sleeps=None):
    with _client(handler) as c:
        return download_all(urls, tmp_path, OPTS, client=c, sleep=(sleeps.append if sleeps is not None else lambda s: None))


def test_success_and_names(tmp_path):
    def handler(req):
        if req.url.path == "/pics/cat.jpg":
            return httpx.Response(200, headers={"content-type": "image/jpeg"}, content=b"jpg")
        return httpx.Response(
            200,
            headers={"content-type": "video/mp4", "content-disposition": "attachment; filename*=UTF-8''%E7%8C%AB.mp4"},
            content=b"mp4",
        )

    res = _run(tmp_path, ["https://h.example/pics/cat.jpg", "https://h.example/dl?id=1"], handler)
    assert [r.path.name for r in res] == ["01_cat.jpg", "02_猫.mp4"]
    assert (tmp_path / "01_cat.jpg").read_bytes() == b"jpg"
    assert not list(tmp_path.glob(".*.part"))


def test_extension_from_content_type(tmp_path):
    res = _run(tmp_path, ["https://h.example/file"], lambda r: httpx.Response(200, headers={"content-type": "image/png"}, content=b"x"))
    assert res[0].path.name == "01_file.png"


def test_rejects_html(tmp_path):
    res = _run(tmp_path, ["https://h.example/page"], lambda r: httpx.Response(200, headers={"content-type": "text/html"}, content=b"<html>"))
    assert not res[0].ok and "Content-Type" in res[0].error
    assert list(tmp_path.iterdir()) == []


def test_size_limit_streaming(tmp_path):
    res = _run(tmp_path, ["https://h.example/big.mp4"], lambda r: httpx.Response(200, headers={"content-type": "video/mp4"}, content=b"x" * 101))
    assert not res[0].ok
    assert list(tmp_path.iterdir()) == []


def test_retry_then_success(tmp_path):
    calls = []

    def handler(req):
        calls.append(1)
        if len(calls) < 3:
            return httpx.Response(503)
        return httpx.Response(200, headers={"content-type": "image/jpeg"}, content=b"ok")

    sleeps = []
    res = _run(tmp_path, ["https://h.example/a.jpg"], handler, sleeps)
    assert res[0].ok
    assert sleeps == [1, 2]


def test_no_retry_on_404(tmp_path):
    calls = []

    def handler(req):
        calls.append(1)
        return httpx.Response(404)

    res = _run(tmp_path, ["https://h.example/a.jpg"], handler)
    assert not res[0].ok and len(calls) == 1


def test_redirect_to_http_blocked(tmp_path):
    def handler(req):
        if req.url.scheme == "https":
            return httpx.Response(302, headers={"location": "http://evil.example/a.jpg"})
        return httpx.Response(200, headers={"content-type": "image/jpeg"}, content=b"x")

    res = _run(tmp_path, ["https://h.example/a.jpg"], handler)
    assert not res[0].ok and "https" in res[0].error


def test_does_not_overwrite_existing(tmp_path):
    (tmp_path / "01_a.jpg").write_bytes(b"original")
    res = _run(tmp_path, ["https://h.example/a.jpg"], lambda r: httpx.Response(200, headers={"content-type": "image/jpeg"}, content=b"new"))
    assert not res[0].ok
    assert (tmp_path / "01_a.jpg").read_bytes() == b"original"
