"""Discord bot：收照片、加 ⏳、排隊，一次處理一張，最後回覆結果。"""

import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path

import discord

from . import analyzer, ledger, storage
from .analyzer import Analysis, AnalysisError
from .config import Config

log = logging.getLogger(__name__)

MAX_PHOTO_BYTES = 10 * 1024 * 1024
MAX_QUEUE = 20
EXCEL_RETRY_SECONDS = 5
EXCEL_MAX_TRIES = 12
IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp")

WAITING, DONE, FAILED = "⏳", "✅", "❌"
MSG_ANALYSIS_FAILED = "❌ 分析失敗，請再傳一次。"
MSG_FAILED = "❌ 處理失敗，請再傳一次。"


@dataclass(frozen=True)
class Job:
    message: discord.Message
    attachment: discord.Attachment


class FoodBot(discord.Client):
    def __init__(self, cfg: Config):
        intents = discord.Intents.default()
        intents.message_content = True  # 沒有這個，收到的訊息裡文字和附件都是空的
        super().__init__(
            intents=intents,
            allowed_mentions=discord.AllowedMentions.none(),  # 回覆時不 @ 任何人
        )
        self.cfg = cfg
        self.queue: asyncio.Queue[Job] = asyncio.Queue(maxsize=MAX_QUEUE)
        self.pending: dict[int, int] = {}  # 訊息編號 → 這則訊息還有幾張照片沒處理完

    async def setup_hook(self) -> None:
        # 只有一個工人在處理排隊區，所以同一時間只會有一個 claude -p 在跑
        self.worker = asyncio.create_task(self._work())

    async def on_ready(self) -> None:
        channel = self.get_channel(self.cfg.channel_id)
        if channel is None:
            log.warning("找不到 CHANNEL_ID=%s 這個頻道：確認 ID 正確、bot 已經加入那個伺服器並看得到該頻道", self.cfg.channel_id)
        else:
            log.info("✅ 已上線：%s，正在監聽 #%s", self.user, channel)
        log.info("照片和紀錄存在：%s（按 Ctrl+C 結束）", self.cfg.data_dir)

    async def on_message(self, message: discord.Message) -> None:
        if message.channel.id != self.cfg.channel_id or message.author.bot:
            return
        images = [a for a in message.attachments if _is_image(a)]
        if not images:
            return

        await _react(message, WAITING)
        for attachment in images:
            if attachment.size > MAX_PHOTO_BYTES:
                await _reply(message, f"⚠️ {attachment.filename} 太大了（上限 10 MB），請壓小一點再傳。")
                continue
            try:
                self.queue.put_nowait(Job(message, attachment))
            except asyncio.QueueFull:
                await _reply(message, "⚠️ 目前排隊的照片太多，請稍後再傳。")
                continue
            self.pending[message.id] = self.pending.get(message.id, 0) + 1

        if message.id not in self.pending:  # 一張都沒排進去
            await _unreact(message, WAITING, self.user)

    async def _work(self) -> None:
        while True:
            job = await self.queue.get()
            try:
                await self._process(job)
            except Exception:  # 任何意外都只算這一張失敗，工人繼續處理下一張
                log.exception("處理照片時發生預期外的錯誤")
                await _reply(job.message, MSG_FAILED)
                await _react(job.message, FAILED)
            finally:
                self.queue.task_done()
                await self._finish(job.message)

    async def _process(self, job: Job) -> None:
        message = job.message
        taken_at = message.created_at.astimezone().replace(tzinfo=None)  # 你電腦的本地時間
        log.info("處理 %s 傳的 %s（排隊中還有 %d 張）", message.author.display_name, job.attachment.filename, self.queue.qsize())

        try:
            jpeg = await asyncio.to_thread(storage.to_jpeg, await job.attachment.read())
        except (discord.HTTPException, ValueError) as error:
            log.warning("讀不到照片：%s", error)
            await _reply(message, "❌ 這個檔案讀不到，或不是圖片，請改傳 JPG 或 PNG。")
            await _react(message, FAILED)
            return

        try:
            result = await analyzer.analyze(jpeg, message.content, self.cfg)
        except AnalysisError as error:
            log.warning("分析失敗：%s", error)
            await _reply(message, MSG_ANALYSIS_FAILED)
            await _react(message, FAILED)
            return

        photo = await asyncio.to_thread(
            storage.save_photo, self.cfg.photos_dir, taken_at, photo_label(result), jpeg
        )

        record = ledger.Record(
            taken_at=taken_at,
            uploader=message.author.display_name,
            place_name=place_name(result),
            scenery="、".join(result.scenery) if result.is_place else result.name,
            intro=result.intro,
            photo_path=str(photo),
        )
        if not await self._append_with_retry(record):
            photo.unlink(missing_ok=True)  # 沒記到 Excel 就不留照片，維持「有照片就一定有紀錄」
            await _reply(message, MSG_FAILED)
            await _react(message, FAILED)
            return

        log.info("完成：%s → %s", record.place_name, photo.name)
        await _reply(message, format_reply(result))
        await _react(message, DONE)

    async def _append_with_retry(self, record: ledger.Record) -> bool:
        """Excel 被打開時寫不進去：印警告、等一下再試。試到上限還不行就回傳 False。"""
        path = self.cfg.records_path
        for attempt in range(1, EXCEL_MAX_TRIES + 1):
            try:
                await asyncio.to_thread(ledger.append_record, path, record)
                return True
            except PermissionError:
                log.warning(
                    "⚠️ %s 可能正被 Excel 打開，寫不進去。請關掉它，%d 秒後重試（第 %d/%d 次）",
                    path.name, EXCEL_RETRY_SECONDS, attempt, EXCEL_MAX_TRIES,
                )
                await asyncio.sleep(EXCEL_RETRY_SECONDS)
        log.error("❌ 重試 %d 次仍然寫不進 %s，這張照片當作失敗", EXCEL_MAX_TRIES, path.name)
        return False

    async def _finish(self, message: discord.Message) -> None:
        """這則訊息的照片全部處理完，就把 ⏳ 拿掉。"""
        left = self.pending.get(message.id, 1) - 1
        if left > 0:
            self.pending[message.id] = left
            return
        self.pending.pop(message.id, None)
        await _unreact(message, WAITING, self.user)


def place_name(result: Analysis) -> str:
    """Excel「地方名稱」欄和回覆標題用的名稱。"""
    if not result.is_place:
        return "不是地方"
    if not result.identified:
        return f"無法確定（{result.name}）"
    return result.name


def photo_label(result: Analysis) -> str:
    """照片檔名裡的名稱（之後還會經過防護 3 清洗）。"""
    if not result.is_place:
        return f"不是地方-{result.short_name}"
    if not result.identified:
        return f"無法確定-{result.short_name}"
    return result.short_name


def format_reply(result: Analysis) -> str:
    if not result.is_place:
        return f"🚫 你傳的不是地方，是「{result.name}」。"
    scenery = "、".join(result.scenery) or "（看不出來）"
    return (
        f"📍 {place_name(result)}\n"
        f"景物：{scenery}\n"
        f"特色：{result.intro or '（沒有介紹）'}"
    )


def _is_image(attachment: discord.Attachment) -> bool:
    if attachment.content_type:
        return attachment.content_type.startswith("image/")
    return Path(attachment.filename).suffix.lower() in IMAGE_EXTENSIONS


async def _reply(message: discord.Message, text: str) -> None:
    """用「回覆該則訊息」的方式回在頻道裡；原訊息被刪掉的話就直接發在頻道。"""
    try:
        await message.reply(text, mention_author=False)
    except discord.HTTPException:
        try:
            await message.channel.send(text)
        except discord.HTTPException as error:
            log.warning("回覆失敗：%s", error)


async def _react(message: discord.Message, emoji: str) -> None:
    try:
        await message.add_reaction(emoji)
    except discord.HTTPException as error:
        log.warning("加反應 %s 失敗（bot 可能沒有「新增反應」權限）：%s", emoji, error)


async def _unreact(message: discord.Message, emoji: str, me: discord.ClientUser | None) -> None:
    if me is None:
        return
    try:
        await message.remove_reaction(emoji, me)
    except discord.HTTPException:
        pass
