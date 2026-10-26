"""啟動入口：uv run python -m place_agent"""

import logging
import shutil
import sys

import discord

from .bot import FoodBot
from .config import load_config


def main() -> None:
    cfg = load_config()
    if shutil.which("claude") is None:
        sys.exit("❌ 找不到 claude 指令：請確認 Claude Code 已安裝，並且在終端機打 claude --version 有反應")

    discord.utils.setup_logging(level=logging.INFO)
    bot = FoodBot(cfg)
    try:
        bot.run(cfg.discord_token, log_handler=None)
    except discord.LoginFailure:
        sys.exit("❌ DISCORD_TOKEN 不正確：到 Developer Portal → Bot →「Reset Token」產生新的，填回 .env")
    except discord.PrivilegedIntentsRequired:
        sys.exit("❌ 還沒打開 Message Content Intent：到 Developer Portal → Bot → Privileged Gateway Intents 打開它")


if __name__ == "__main__":
    main()
