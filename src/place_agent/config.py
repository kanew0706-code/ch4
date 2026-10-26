"""讀取並檢查 .env 裡的設定。"""

import os
import sys
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

REQUIRED_KEYS = ("DISCORD_TOKEN", "CHANNEL_ID", "CLAUDE_MODEL", "DATA_DIR")


@dataclass(frozen=True)
class Config:
    discord_token: str
    channel_id: int
    claude_model: str
    data_dir: Path

    @property
    def photos_dir(self) -> Path:
        return self.data_dir / "photos"

    @property
    def records_path(self) -> Path:
        return self.data_dir / "records.xlsx"


def load_config() -> Config:
    """讀 .env；缺設定或格式不對就印出原因並結束程式，不用半套設定硬跑。"""
    load_dotenv()
    values = {key: os.getenv(key, "").strip() for key in REQUIRED_KEYS}

    missing = [key for key, value in values.items() if not value]
    if missing:
        sys.exit(f"❌ .env 缺少設定：{', '.join(missing)}")

    placeholders = [key for key, value in values.items() if value.startswith("你的")]
    if placeholders:
        sys.exit(f"❌ .env 裡這些設定還是範本文字，請換成真的值：{', '.join(placeholders)}")

    if not values["CHANNEL_ID"].isdigit():
        sys.exit("❌ CHANNEL_ID 應該全部是數字（在 Discord 對頻道按右鍵 →「複製頻道 ID」）")

    data_dir = Path(values["DATA_DIR"]).expanduser().resolve()
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "photos").mkdir(exist_ok=True)

    return Config(
        discord_token=values["DISCORD_TOKEN"],
        channel_id=int(values["CHANNEL_ID"]),
        claude_model=values["CLAUDE_MODEL"],
        data_dir=data_dir,
    )
