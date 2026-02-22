import os

from telegram import Bot


async def send_telegram_notification(message: str) -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")

    if not token or not chat_id:
        return

    bot = Bot(token=token)
    await bot.send_message(chat_id=chat_id, text=message)
