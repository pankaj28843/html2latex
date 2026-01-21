import struct

import pytest

from html2latex.utils.image import get_image_size


def test_get_image_size_png(tmp_path):
    signature = b"\x89PNG\r\n\x1a\n"
    header = signature + b"\x00\x00\x00\rIHDR" + struct.pack(">LL", 10, 20)
    path = tmp_path / "tiny.png"
    path.write_bytes(header + b"extra")
    assert get_image_size(str(path)) == (10, 20)


def test_get_image_size_jpeg(tmp_path):
    # SOI + SOF0 with length 7 (includes 2-byte length field)
    data = b"\xff\xd8" + b"\xff\xc0" + b"\x00\x07" + b"\x08" + b"\x00\x02" + b"\x00\x03"
    path = tmp_path / "tiny.jpg"
    path.write_bytes(data)
    assert get_image_size(str(path)) == (3, 2)


def test_get_image_size_jpeg_missing_marker(tmp_path):
    path = tmp_path / "missing.jpg"
    path.write_bytes(b"\xff\xd8")
    with pytest.raises(ValueError):
        get_image_size(str(path))


def test_get_image_size_jpeg_short_sof(tmp_path):
    data = b"\xff\xd8" + b"\xff\xc0" + b"\x00\x06" + b"\x08" + b"\x00\x02" + b"\x00\x03"
    path = tmp_path / "short-sof.jpg"
    path.write_bytes(data)
    with pytest.raises(ValueError):
        get_image_size(str(path))


def test_get_image_size_jpeg_short_segment(tmp_path):
    # non-SOF marker with invalid length
    data = b"\xff\xd8" + b"\xff\xdb" + b"\x00\x01"
    path = tmp_path / "short-seg.jpg"
    path.write_bytes(data)
    with pytest.raises(ValueError):
        get_image_size(str(path))


def test_get_image_size_jpeg_skip_non_ff_prefix(tmp_path):
    data = (
        b"\xff\xd8"
        + b"\x00"  # non-marker byte to trigger skip
        + b"\xff\xc0"
        + b"\x00\x07"
        + b"\x08"
        + b"\x00\x02"
        + b"\x00\x03"
    )
    path = tmp_path / "skip.jpg"
    path.write_bytes(data)
    assert get_image_size(str(path)) == (3, 2)


def test_get_image_size_jpeg_ff_fill(tmp_path):
    data = b"\xff\xd8" + b"\xff\xff\xc0" + b"\x00\x07" + b"\x08" + b"\x00\x02" + b"\x00\x03"
    path = tmp_path / "fill.jpg"
    path.write_bytes(data)
    assert get_image_size(str(path)) == (3, 2)


def test_get_image_size_invalid(tmp_path):
    path = tmp_path / "invalid.bin"
    path.write_bytes(b"not-an-image")
    with pytest.raises(ValueError):
        get_image_size(str(path))
