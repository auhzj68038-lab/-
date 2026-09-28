from pathlib import Path

import pytest

from shorts_prep.config import parse_config


@pytest.fixture
def cfg_factory(tmp_path: Path):
    def make(**over):
        raw = {
            "sheet": {"spreadsheet_id": "abc", "sheet_name": "シート1"},
            "columns": {"date": "日付", "title": "タイトル", "assets": ["素材URL"], "script": ""},
            "paths": {"output_root": str(tmp_path / "root"), "template": ""},
            "download": {"max_size_mb": 1, "timeout_sec": 5, "retries": 2},
        }
        for section, values in over.items():
            raw.setdefault(section, {}).update(values)
        return parse_config(raw)

    return make
