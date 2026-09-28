import pytest

from shorts_prep import safefs


def test_make_dir_exclusive(tmp_path):
    d = tmp_path / "a" / "b"
    safefs.make_dir_exclusive(d)
    (d / "keep.txt").write_text("keep")
    with pytest.raises(FileExistsError):
        safefs.make_dir_exclusive(d)
    assert (d / "keep.txt").read_text() == "keep"


def test_write_exclusive_never_overwrites(tmp_path):
    f = tmp_path / "x.txt"
    f.write_text("original")
    with pytest.raises(FileExistsError):
        safefs.write_bytes_exclusive(f, b"new")
    assert f.read_text() == "original"


def test_commit_exclusive(tmp_path):
    fd, tmp = safefs.new_temp_file(tmp_path)
    with open(fd, "wb") as fh:
        fh.write(b"data")
    final = tmp_path / "final.bin"
    safefs.commit_exclusive(tmp, final)
    assert final.read_bytes() == b"data"
    assert not tmp.exists()


def test_commit_exclusive_refuses_existing(tmp_path):
    final = tmp_path / "final.bin"
    final.write_bytes(b"original")
    fd, tmp = safefs.new_temp_file(tmp_path)
    with open(fd, "wb") as fh:
        fh.write(b"new")
    with pytest.raises(FileExistsError):
        safefs.commit_exclusive(tmp, final)
    assert final.read_bytes() == b"original"


def test_copy_exclusive(tmp_path):
    src = tmp_path / "src"
    src.write_bytes(b"tpl")
    dst = tmp_path / "dst"
    safefs.copy_file_exclusive(src, dst)
    assert dst.read_bytes() == b"tpl"
    dst.write_bytes(b"edited")
    with pytest.raises(FileExistsError):
        safefs.copy_file_exclusive(src, dst)
    assert dst.read_bytes() == b"edited"
