"""コマンドライン入口。

    shorts-prep                 最新行から作業フォルダを準備（= shorts-prep run）
    shorts-prep run --dry-run   何も作らずに計画だけ表示
    shorts-prep init-config     設定ファイルのひな形を作成
    shorts-prep setup --client-secret FILE   OAuth クライアント情報をキーチェーンへ登録
    shorts-prep login / logout  Google ログイン / トークン削除
"""

from __future__ import annotations

import argparse
import logging
import sys
from importlib import resources
from logging.handlers import RotatingFileHandler
from pathlib import Path

from . import auth, macos, premiere, safefs
from .config import LOG_DIR, Config, config_path, load_config
from .download import DownloadOptions, download_all
from .errors import PrepError
from .naming import folder_name
from .sheet import Row, fetch_values, pick_last_row

APP_TITLE = "ショート動画準備"
log = logging.getLogger("shorts_prep")


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    _setup_logging()
    try:
        return args.func(args)
    except PrepError as e:
        log.error("%s", e)
        macos.dialog(APP_TITLE, str(e), error=True)
        return 1
    except KeyboardInterrupt:
        return 130
    except Exception as e:  # 想定外のエラーも必ず目に見える形で知らせる
        log.exception("unexpected error")
        macos.dialog(
            APP_TITLE,
            f"予期しないエラーが発生しました:\n{e}\n\nログ: {LOG_DIR / 'shorts_prep.log'}",
            error=True,
        )
        return 1


def _parse_args(argv):
    p = argparse.ArgumentParser(prog="shorts-prep", description=APP_TITLE)
    p.add_argument("--config", help="設定ファイルのパス")
    sub = p.add_subparsers(dest="cmd")

    r = sub.add_parser("run", help="最新行から作業フォルダを準備する")
    r.add_argument("--dry-run", action="store_true", help="何も作成せず計画だけ表示")
    r.add_argument("--no-open", action="store_true", help="完了後に Finder / Premiere を開かない")
    r.set_defaults(func=cmd_run)

    s = sub.add_parser("setup", help="OAuth クライアント情報をキーチェーンに登録してログイン")
    s.add_argument("--client-secret", required=True, type=Path)
    s.set_defaults(func=cmd_setup)

    sub.add_parser("login", help="Google にログイン").set_defaults(func=cmd_login)
    sub.add_parser("logout", help="保存済みトークンを削除").set_defaults(func=cmd_logout)
    sub.add_parser("init-config", help="設定ファイルのひな形を作成").set_defaults(func=cmd_init_config)

    args = p.parse_args(argv)
    if args.cmd is None:
        args = p.parse_args([*(sys.argv[1:] if argv is None else argv), "run"])
    return args


def _setup_logging() -> None:
    log.setLevel(logging.INFO)
    if log.handlers:
        return
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        h = RotatingFileHandler(LOG_DIR / "shorts_prep.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8")
        h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        log.addHandler(h)
    except OSError:
        log.addHandler(logging.StreamHandler())


# ---- commands ---------------------------------------------------------------


def cmd_init_config(args) -> int:
    dst = config_path(args.config)
    dst.parent.mkdir(parents=True, exist_ok=True)
    data = resources.files("shorts_prep").joinpath("config.example.toml").read_bytes()
    try:
        safefs.write_bytes_exclusive(dst, data)
    except FileExistsError:
        print(f"設定ファイルは既にあります（上書きしません）: {dst}")
        return 0
    print(f"設定ファイルを作成しました。spreadsheet_id などを編集してください:\n{dst}")
    return 0


def cmd_setup(args) -> int:
    auth.import_client_secret(args.client_secret.expanduser())
    print("OAuth クライアント情報をキーチェーンに保存しました。")
    print(f"元のファイル {args.client_secret} は削除して構いません。")
    auth.get_credentials(interactive=True)
    print("ログインが完了しました。")
    return 0


def cmd_login(args) -> int:
    auth.get_credentials(interactive=True)
    print("ログインが完了しました。")
    return 0


def cmd_logout(args) -> int:
    auth.logout()
    print("保存済みのトークンを削除しました。")
    return 0


def cmd_run(args) -> int:
    cfg = load_config(config_path(args.config))

    # 何かを作る前に、失敗しうる確認を全部済ませる
    template = premiere.find_template(cfg)
    row = _read_last_row(cfg)
    name = folder_name(row.date, row.title)
    folder = cfg.output_root / name

    if folder.exists():
        raise PrepError(
            "同じ名前のフォルダが既にあるため中止しました（何も変更していません）。\n\n"
            f"{folder}\n\n"
            "作り直す場合は、このフォルダを移動または名前変更してから再実行してください。"
        )

    if args.dry_run:
        _print_plan(cfg, row, folder, template)
        return 0

    try:
        safefs.make_dir_exclusive(folder)
    except FileExistsError as e:
        raise PrepError(f"同じ名前のフォルダが既にあるため中止しました:\n{folder}") from e
    log.info("created %s (row %d)", folder, row.row_number)

    assets_dir = folder / "assets"
    safefs.make_dir_exclusive(assets_dir)

    if row.script:
        safefs.write_bytes_exclusive(folder / "script.txt", (row.script + "\n").encode("utf-8"))

    results = download_all(row.asset_urls, assets_dir, _dl_opts(cfg))
    project = premiere.copy_template(template, folder, name)

    ok = sum(r.ok for r in results)
    failed = [r for r in results if not r.ok]
    if failed or row.invalid_urls:
        lines = [f"フォルダは作成しましたが、一部の素材を取得できませんでした（成功 {ok}/{len(results)}）。", ""]
        for r in failed:
            lines.append(f"・{_short(r.url)}\n    → {r.error}")
        for u in row.invalid_urls:
            lines.append(f"・{_short(u)}\n    → https のURLではないためスキップ")
        lines += ["", str(folder)]
        macos.dialog(APP_TITLE, "\n".join(lines), error=True)
    else:
        macos.notify(APP_TITLE, f"準備完了: {name}（素材 {ok} 件）")

    if not args.no_open:
        if cfg.open_folder:
            macos.open_path(folder)
        if cfg.open_premiere:
            macos.open_path(project)
    return 0 if not failed else 2


# ---- helpers ----------------------------------------------------------------


def _read_last_row(cfg: Config) -> Row:
    from googleapiclient.discovery import build

    creds = auth.get_credentials(interactive=True)
    service = build("sheets", "v4", credentials=creds, cache_discovery=False)
    return pick_last_row(fetch_values(service, cfg.spreadsheet_id, cfg.sheet_name), cfg)


def _dl_opts(cfg: Config) -> DownloadOptions:
    return DownloadOptions(
        max_size_bytes=cfg.max_size_bytes,
        timeout_sec=cfg.timeout_sec,
        retries=cfg.retries,
        allowed_content_types=cfg.allowed_content_types,
    )


def _short(url: str, n: int = 80) -> str:
    return url if len(url) <= n else url[: n - 1] + "…"


def _print_plan(cfg: Config, row: Row, folder: Path, template: Path) -> None:
    print("【ドライラン】以下を作成する予定です（まだ何も作っていません）")
    print(f"  読み込む行 : {cfg.sheet_name} の {row.row_number} 行目")
    print(f"  フォルダ   : {folder}")
    print(f"  テンプレ   : {template.name} → {folder.name}.prproj")
    if row.script:
        print("  台本       : script.txt")
    print(f"  素材       : {len(row.asset_urls)} 件 → {folder / 'assets'}")
    for u in row.asset_urls:
        print(f"    - {_short(u)}")
    for u in row.invalid_urls:
        print(f"    × {_short(u)}（https ではないためスキップ）")


if __name__ == "__main__":
    sys.exit(main())
