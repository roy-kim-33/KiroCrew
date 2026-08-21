"""Tests for the fork's magic-byte sniff + transcode guard in prompt_blocks.

Upstream trusts the filename suffix for an inlined image's media type. The fork
does not: channels lie (Discord serves PNG bytes as ``image/webp``), and the
backend validates the BYTES against the declared type — a mismatch is a 400 that
sits at a fixed history index and wedges the session on every later turn. So the
sniff is authoritative, and anything outside the universally-supported set is
transcoded to PNG or left as prose. These pin both halves per format.
"""

from __future__ import annotations

import pytest

from kiro_crew.acp import prompt_blocks as pb

# Smallest byte prefixes that identify each format to the sniffer.
SIGNATURES = {
    "image/png": b"\x89PNG\r\n\x1a\n",
    "image/jpeg": b"\xff\xd8\xff\xe0",
    "image/gif": b"GIF89a",
    "image/webp": b"RIFF\x00\x00\x00\x00WEBP",
    "image/bmp": b"BM\x00\x00\x00\x00",
    "image/avif": b"\x00\x00\x00\x18ftypavif",
    "image/heic": b"\x00\x00\x00\x18ftypheic",
    "image/tiff": b"II*\x00",
    "image/x-icon": b"\x00\x00\x01\x00",
    "image/svg+xml": b'<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"/>',
}


@pytest.mark.parametrize("mime,raw", sorted(SIGNATURES.items()))
def test_every_signature_sniffs_to_its_own_mime(mime: str, raw: bytes) -> None:
    assert pb._sniff_mime_from_bytes(raw) == mime


@pytest.mark.parametrize("raw", [b"", b"not an image at all", b"\x00\x00\x00\x18ftypqt  "])
def test_unrecognized_bytes_sniff_to_none(raw: bytes) -> None:
    """None means "keep the suffix" — the sniffer must not guess."""
    assert pb._sniff_mime_from_bytes(raw) is None


def test_gif_and_webp_are_universally_supported_but_heic_is_not() -> None:
    """The transcode decision is exactly this membership test."""
    assert "image/gif" in pb._UNIVERSALLY_SUPPORTED_MIMES
    assert "image/webp" in pb._UNIVERSALLY_SUPPORTED_MIMES
    for mime in ("image/avif", "image/heic", "image/tiff", "image/x-icon", "image/bmp"):
        assert mime not in pb._UNIVERSALLY_SUPPORTED_MIMES


def test_transcode_returns_png_bytes_for_a_decodable_source() -> None:
    pil = pytest.importorskip("PIL.Image")
    import io

    buf = io.BytesIO()
    pil.new("RGB", (2, 2)).save(buf, format="BMP")
    out = pb._transcode_to_png(buf.getvalue(), "image/bmp")
    assert out is not None
    assert pb._sniff_mime_from_bytes(out) == "image/png"


def test_transcode_fails_closed_on_undecodable_bytes() -> None:
    """None must mean "send the path as text", never "inline it anyway"."""
    assert pb._transcode_to_png(b"<svg/>", "image/svg+xml") is None
    assert pb._transcode_to_png(b"truncated garbage", "image/tiff") is None
