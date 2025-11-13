import os
import threading
from dataclasses import dataclass

import telebot
from telebot.types import Message


@dataclass
class BotConfig:
    token: str
    admin_id: int
    greeting_text: str
    auto_reply_text: str
    label: str


# === Настройки ===
ADMIN_ID = int(os.getenv("ADMIN_ID", 220493509))  # твой id

MAIN_BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPPORT_BOT_TOKEN = os.getenv("SUPPORT_BOT_TOKEN")


def _parse_reply_command(raw_text: str):
    parts = raw_text.split(maxsplit=2)
    if len(parts) < 3:
        return None, None

    try:
        return int(parts[1]), parts[2]
    except ValueError:
        return None, None

    # автоответ клиенту
    bot.send_message(
        admin_id,
        "Формат команды:\n/reply <user_id> <текст ответа>"
    )


# === Твоя команда для ответа клиенту ===
def _parse_reply_command(raw_text: str):
    parts = raw_text.split(maxsplit=2)
    if len(parts) < 3:
        return None, None

    try:
        return int(parts[1]), parts[2]
    except ValueError:
        return None, None


def _send_format_hint():
    bot.send_message(
        ADMIN_ID,
        "Формат команды:\n/reply <user_id> <текст ответа>"
    )


@bot.message_handler(commands=['reply'])
def reply_to_user(message: Message):
    # только ты можешь использовать /reply
    if message.chat.id != ADMIN_ID:
        bot.send_message(message.chat.id, "Эта команда только для Елены 🌙")
        return

    user_id, reply_text = _parse_reply_command(message.text)
    if user_id is None:
        _send_format_hint()
        return

    try:
        bot.send_message(user_id, reply_text)
        bot.send_message(ADMIN_ID, "✅ Ответ отправлен.")
    except Exception as e:
        bot.send_message(ADMIN_ID, f"⚠️ Ошибка: {e}")


@bot.message_handler(content_types=['photo'])
def reply_with_photo(message: Message):
    if message.chat.id != ADMIN_ID:
        return

    caption = message.caption or ""
    if not caption.startswith('/reply'):
        _send_format_hint()
        return

    user_id, reply_text = _parse_reply_command(caption)
    if user_id is None:
        _send_format_hint()
        return

    try:
        file_id = message.photo[-1].file_id
        bot.send_photo(user_id, file_id, caption=reply_text)
        bot.send_message(ADMIN_ID, "✅ Ответ с фото отправлен.")
    except Exception as e:
        bot.send_message(ADMIN_ID, f"⚠️ Ошибка: {e}")


# === Запуск бота ===
bot.polling(timeout=60, long_polling_timeout=30)
