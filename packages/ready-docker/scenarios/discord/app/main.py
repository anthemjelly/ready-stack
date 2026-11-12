"""Discord 翻譯 bot 場景（ready-docker Layer 3 示範）。

指令：
    !translate <文字>   → 自動偵測語言並翻成英文

設計重點：
    * 只做業務邏輯；時區、appuser、healthcheck、entrypoint 由 core / python 層處理。
    * DISCORD_BOT_TOKEN 缺失時印出清楚錯誤並「正常結束」，不會無限 crash loop
      （搭配 compose.yml 的 restart: on-failure:5）。
    * 日誌用標準庫 logging，經 PYTHONUNBUFFERED=1 即時輸出到 docker logs。

啟動：
    DISCORD_BOT_TOKEN=... python -m app.main
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys

import discord
from deep_translator import GoogleTranslator
from discord.ext import commands
from dotenv import load_dotenv

LOGGER = logging.getLogger("ready_docker.discord")

PREFIX = "!"
TARGET_LANG = "en"


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stdout,
    )


def load_token() -> str:
    """讀取 token；容器內沒有 .env 時 load_dotenv() 會安全地忽略。"""
    load_dotenv()
    return os.getenv("DISCORD_BOT_TOKEN", "").strip()


def translate_to_english(text: str) -> str:
    """把任意語言文字翻成英文（給指令與測試重用）。"""
    translated = GoogleTranslator(source="auto", target=TARGET_LANG).translate(text)
    if not translated:
        raise ValueError("翻譯服務回傳空結果")
    return translated


intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents)


@bot.event
async def on_ready() -> None:
    LOGGER.info("已登入為 %s (id=%s)", bot.user, getattr(bot.user, "id", "?"))
    LOGGER.info("bot 已就緒：輸入 %stranslate <文字> 即會翻成英文", PREFIX)


@bot.command(name="translate", help="把訊息翻成英文")
async def translate(ctx: commands.Context, *, text: str = "") -> None:
    cleaned = text.strip()
    if not cleaned:
        await ctx.reply(f"用法：`{PREFIX}translate <要翻譯的文字>`")
        return
    try:
        # 翻譯是同步阻塞 I/O，放去 thread 避免卡住 Discord event loop。
        translated = await asyncio.to_thread(translate_to_english, cleaned)
    except Exception:  # 翻譯服務出錯只需回報用戶，不應令 bot 崩潰
        LOGGER.exception("翻譯失敗：%r", cleaned)
        await ctx.reply("❌ 翻譯失敗，請稍後再試（詳情已記錄在容器日誌）。")
        return
    await ctx.reply(f"🔄 翻譯結果：\n{translated}")


def main() -> int:
    _configure_logging()
    token = load_token()
    if not token:
        LOGGER.error("缺少環境變數 DISCORD_BOT_TOKEN，bot 不會啟動（這不是 crash）。")
        LOGGER.error("請複製 .env.example 為 .env 並填入 token 後重試：")
        LOGGER.error("  cp .env.example .env && docker compose --profile discord up -d")
        LOGGER.error("或以 docker run --env-file .env ready-stack/discord:dev 啟動。")
        # 回傳 0：設定未完成屬預期狀態，配合 restart: on-failure:5 就不會無限重啟。
        return 0
    try:
        bot.run(token)
    except discord.LoginFailure:
        LOGGER.error(
            "DISCORD_BOT_TOKEN 無效（LoginFailure），請到 Discord Developer Portal 重新取得 token。"
        )
        return 0
    except KeyboardInterrupt:
        LOGGER.info("收到中斷訊號，結束 bot。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
