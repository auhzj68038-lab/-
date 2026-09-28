import httpx
import pytest

from shorts_prep import cli, premiere
from shorts_prep.errors import PrepError
from shorts_prep.sheet import Row


def test_find_template_autodetect(cfg_factory):
    cfg = cfg_factory()
    cfg.output_root.mkdir()
    with pytest.raises(PrepError, match="見つかりません"):
        premiere.find_template(cfg)
    (cfg.output_root / "テンプレ.prproj").write_bytes(b"t")
    assert premiere.find_template(cfg).name == "テンプレ.prproj"
    (cfg.output_root / "別.prproj").write_bytes(b"t")
    with pytest.raises(PrepError, match="複数"):
        premiere.find_template(cfg)


@pytest.fixture
def setup_run(cfg_factory, monkeypatch, tmp_path):
    cfg = cfg_factory()
    cfg.output_root.mkdir()
    (cfg.output_root / "テンプレ.prproj").write_bytes(b"template")
    row = Row(3, "2026/9/28", "テスト動画", ("https://h.example/a.jpg",), (), "台本です")

    monkeypatch.setattr(cli, "load_config", lambda p: cfg)
    monkeypatch.setattr(cli, "_read_last_row", lambda c: row)
    monkeypatch.setattr(cli.macos, "IS_MAC", False)

    def fake_download_all(urls, dest, opts):
        from shorts_prep.download import download_all, make_client

        t = httpx.MockTransport(lambda r: httpx.Response(200, headers={"content-type": "image/jpeg"}, content=b"img"))
        with make_client(opts, transport=t) as c:
            return download_all(urls, dest, opts, client=c)

    monkeypatch.setattr(cli, "download_all", fake_download_all)
    return cfg


def test_run_end_to_end(setup_run):
    cfg = setup_run
    assert cli.main(["run", "--no-open"]) == 0
    folder = cfg.output_root / "2026-09-28_テスト動画"
    assert (folder / "2026-09-28_テスト動画.prproj").read_bytes() == b"template"
    assert (folder / "assets" / "01_a.jpg").read_bytes() == b"img"
    assert (folder / "script.txt").read_text(encoding="utf-8") == "台本です\n"


def test_run_aborts_if_folder_exists(setup_run):
    cfg = setup_run
    folder = cfg.output_root / "2026-09-28_テスト動画"
    folder.mkdir()
    (folder / "編集中.prproj").write_bytes(b"precious")
    assert cli.main(["run", "--no-open"]) == 1
    assert sorted(p.name for p in folder.iterdir()) == ["編集中.prproj"]
    assert (folder / "編集中.prproj").read_bytes() == b"precious"


def test_dry_run_creates_nothing(setup_run, capsys):
    cfg = setup_run
    assert cli.main(["run", "--dry-run"]) == 0
    assert not (cfg.output_root / "2026-09-28_テスト動画").exists()
    assert "ドライラン" in capsys.readouterr().out


def test_extract_spreadsheet_id():
    from shorts_prep.config import extract_spreadsheet_id

    assert extract_spreadsheet_id("https://docs.google.com/spreadsheets/d/1AbC_d-9/edit#gid=0") == "1AbC_d-9"
    assert extract_spreadsheet_id(" 1AbC ") == "1AbC"


def test_wizard_writes_config(tmp_path, monkeypatch):
    import tomllib

    cfg_path = tmp_path / "cfg" / "config.toml"
    root = tmp_path / "root"
    answers = iter(['https://docs.google.com/spreadsheets/d/XYZ123/edit', 'ネタ"帳'])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))
    monkeypatch.setattr(cli.auth, "has_client_secret", lambda: True)
    monkeypatch.setattr(cli.auth, "get_credentials", lambda interactive=True: None)
    monkeypatch.setattr(cli.macos, "IS_MAC", False)
    monkeypatch.setattr(cli, "cmd_run", lambda a: 0)
    # 出力先をテスト用フォルダに向け、テンプレを置いておく
    real_load = cli.load_config

    def load(p):
        text = p.read_text(encoding="utf-8").replace("~/Desktop/プレミア/ショート動画自動作成", str(root))
        p.write_text(text, encoding="utf-8")
        return real_load(p)

    monkeypatch.setattr(cli, "load_config", load)
    root.mkdir()
    (root / "t.prproj").write_bytes(b"t")

    assert cli.main(["--config", str(cfg_path), "wizard"]) == 0
    raw = tomllib.loads(cfg_path.read_text(encoding="utf-8"))
    assert raw["sheet"]["spreadsheet_id"] == "XYZ123"
    assert raw["sheet"]["sheet_name"] == 'ネタ"帳'
