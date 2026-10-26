import io
from datetime import datetime

import pytest
from PIL import Image

from place_agent.storage import sanitize_label, save_photo, to_jpeg

WHEN = datetime(2026, 10, 20, 12, 30, 45)


@pytest.mark.parametrize(
    "label",
    ["../../evil", "..\\..\\evil", "C:\\Windows\\x", "a/b", "a:b", "／全形斜線", "..", "", "名稱\x00\n換行"],
)
def test_sanitized_label_has_no_path_characters(label):
    safe = sanitize_label(label)
    assert safe
    for bad in ("/", "\\", ":", "..", "\x00", "\n"):
        assert bad not in safe


def test_sanitize_keeps_chinese():
    assert sanitize_label("台北101") == "台北101"


@pytest.mark.parametrize("label", ["../../evil", "..\\..\\evil", "C:\\Windows\\x"])
def test_photo_stays_inside_photos_dir(tmp_path, label):
    photos = tmp_path / "photos"
    photos.mkdir()
    path = save_photo(photos, WHEN, label, b"jpeg")
    assert path.parent == photos
    assert list(tmp_path.iterdir()) == [photos]


def test_filename_format_and_collisions(tmp_path):
    names = [save_photo(tmp_path, WHEN, "阿里山", b"x").name for _ in range(3)]
    assert names == [
        "2026-10-20 12-30-45 阿里山.jpg",
        "2026-10-20 12-30-45 阿里山-2.jpg",
        "2026-10-20 12-30-45 阿里山-3.jpg",
    ]


def test_to_jpeg_converts_png():
    buffer = io.BytesIO()
    Image.new("RGBA", (10, 10), "red").save(buffer, format="PNG")
    assert to_jpeg(buffer.getvalue())[:2] == b"\xff\xd8"  # JPG 檔頭


def test_to_jpeg_rejects_non_image():
    with pytest.raises(ValueError):
        to_jpeg(b"not an image")
