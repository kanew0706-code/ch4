"""照片：轉成 JPG、取檔名、存進 DATA_DIR/photos。

防護 3（檔名清洗）在這個檔案的 save_photo() 裡。
"""

import io
import re
import unicodedata
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageOps

LABEL_MAX_CHARS = 30
MAX_DUPLICATES = 99

# 只留下文字、數字、底線、連字號；其他字元（/ \ : . 空白 控制字元…）都會被換掉
_UNSAFE_CHARS = re.compile(r"[^\w-]+")


def to_jpeg(data: bytes) -> bytes:
    """確認收到的真的是圖片，並轉成 JPG。不是圖片就丟 ValueError。"""
    try:
        with Image.open(io.BytesIO(data)) as image:
            image = ImageOps.exif_transpose(image)  # 照手機拍照時的方向轉正
            buffer = io.BytesIO()
            image.convert("RGB").save(buffer, format="JPEG", quality=90)
    except (OSError, Image.DecompressionBombError) as error:
        raise ValueError(f"不是可以讀的圖片：{error}") from None
    return buffer.getvalue()


def sanitize_label(label: str) -> str:
    """把 claude -p 給的名稱清成安全的檔名片段。"""
    text = unicodedata.normalize("NFKC", label)  # 全形的 ／ ＼ ： 先轉成半形，才擋得到
    text = _UNSAFE_CHARS.sub("_", text)
    text = re.sub(r"_+", "_", text).strip("_-")
    return text[:LABEL_MAX_CHARS] or "未命名"


def save_photo(photos_dir: Path, taken_at: datetime, label: str, jpeg: bytes) -> Path:
    """存成「YYYY-MM-DD hh-mm-ss 名稱.jpg」；同一秒撞名就加 -2、-3…，絕不覆蓋舊照片。"""
    stamp = taken_at.strftime("%Y-%m-%d %H-%M-%S")

    # 沒有防護時：claude -p 給的名稱原封不動拿來當檔名
    safe_label = label
    # ==== 防護 3：檔名清洗　開始 ====
    # 名稱來自 claude -p，而 claude -p 看的是別人上傳的照片，所以一律當成不可信。
    # 清掉 / \ .. : 這類會讓路徑跑出 photos 資料夾的字，再確認一次路徑真的在 photos 裡面。
    safe_label = sanitize_label(label)
    if (photos_dir / f"{stamp} {safe_label}.jpg").resolve().parent != photos_dir.resolve():
        raise ValueError(f"檔名會跑出照片資料夾：{label!r}")
    # ==== 防護 3 結束 ====

    for n in range(1, MAX_DUPLICATES + 1):
        suffix = "" if n == 1 else f"-{n}"
        path = photos_dir / f"{stamp} {safe_label}{suffix}.jpg"
        try:
            with open(path, "xb") as file:  # "x"：檔案已經存在就失敗，所以不會覆蓋
                file.write(jpeg)
        except FileExistsError:
            continue
        return path
    raise FileExistsError(f"同一秒的同名照片超過 {MAX_DUPLICATES} 張：{stamp} {safe_label}")
