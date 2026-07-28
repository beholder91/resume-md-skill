import hashlib

import pytest

import resume_md.fonts as fonts


def test_font_download_is_checksum_verified(tmp_path, monkeypatch):
    payload = b"fixture-font"
    monkeypatch.setenv("RESUMEMD_FONT_CACHE", str(tmp_path))
    monkeypatch.setitem(
        fonts._FONT_FILES,
        "fixture",
        {
            "filename": "fixture.ttf",
            "url": "https://example.invalid/fixture.ttf",
            "sha256": hashlib.sha256(payload).hexdigest(),
            "family": "Fixture",
        },
    )

    def downloader(_url, destination):
        destination.write_bytes(payload)

    path = fonts.ensure_font("fixture", downloader)
    assert path.read_bytes() == payload


def test_font_download_rejects_wrong_checksum(tmp_path, monkeypatch):
    monkeypatch.setenv("RESUMEMD_FONT_CACHE", str(tmp_path))
    monkeypatch.setitem(
        fonts._FONT_FILES,
        "fixture",
        {
            "filename": "fixture.ttf",
            "url": "https://example.invalid/fixture.ttf",
            "sha256": "0" * 64,
            "family": "Fixture",
        },
    )

    with pytest.raises(RuntimeError, match="字体校验失败"):
        fonts.ensure_font(
            "fixture",
            lambda _url, destination: destination.write_bytes(b"wrong"),
        )
    assert not (tmp_path / "fixture.ttf").exists()

