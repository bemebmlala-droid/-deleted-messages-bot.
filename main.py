
import os
import asyncio
import sqlite3

from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message, BusinessMessagesDeleted, BusinessConnection
from aiogram.filters import CommandStart

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN не задан")

bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()

db = sqlite3.connect("messages.db")
db.execute("""
CREATE TABLE IF NOT EXISTS messages (
    chat_id INTEGER,
    message_id INTEGER,
    business_connection_id TEXT,
    text TEXT
)
""")
db.commit()


@router.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "Привет! Подключи меня к Telegram Business "
        "и предоставь необходимые разрешения."
    )


@router.business_message()
async def save_message(message: Message):
    db.execute(
        "INSERT INTO messages VALUES (?, ?, ?, ?)",
        (
            message.chat.id,
            message.message_id,
            message.business_connection_id,
            message.text or message.caption or "[Медиа]"
        )
    )
    db.commit()


@router.deleted_business_messages()
async def deleted_messages(event: BusinessMessagesDeleted):
    for message_id in event.message_ids:
        result = db.execute(
            """
            SELECT text FROM messages
            WHERE chat_id = ? AND message_id = ?
            AND business_connection_id = ?
            """,
            (
                event.chat.id,
                message_id,
                event.business_connection_id
            )
        ).fetchone()

        if result:
            await bot.send_message(
                event.chat.id,
                f"Удалённое сообщение:\n{result[0]}"
            )


async def main():
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
