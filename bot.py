import os
import telebot
from telebot.types import Message

# === Настройки ===
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 220493509))  # твой ID
bot = telebot.TeleBot(TOKEN)

# === Обработка команды /start ===
@bot.message_handler(commands=['start'])
def start(message: Message):
    bot.send_message(
        message.chat.id,
        "🌙 Привет! Это бот Елены Таро.\n"
        "Задай свой вопрос, и я сделаю для тебя персональный расклад 🕯"
    )

# === Обработка сообщений пользователей ===
@bot.message_handler(func=lambda message: True)
def handle_message(message: Message):
    user_id = message.chat.id
    text = message.text

    # Отправляем тебе (админу) сообщение
    bot.send_message(
        ADMIN_ID,
        f"📩 Новое сообщение от @{message.from_user.username or 'без ника'} (ID {user_id}):\n\n{text}"
    )

    # Подтверждение пользователю
    bot.send_message(
        user_id,
        "✨ Спасибо за сообщение! Я скоро посмотрю твой вопрос и пришлю ответ 🌙"
    )

# === Ты отвечаешь пользователю напрямую ===
@bot.message_handler(commands=['reply'])
def reply_to_user(message: Message):
    if message.chat.id != ADMIN_ID:
        bot.send_message(message.chat.id, "Эта команда только для администратора 🌙")
        return

    try:
        parts = message.text.split(maxsplit=2)
        target_id = int(parts[1])
        reply_text = parts[2]
        bot.send_message(target_id, f"🔮 Ответ от Елены Таро:\n\n{reply_text}")
        bot.send_message(ADMIN_ID, "✅ Ответ отправлен.")
    except Exception:
        bot.send_message(ADMIN_ID, "⚠️ Используй формат:\n/reply <user_id> <текст>")

# === Запуск ===
bot.polling(timeout=60, long_polling_timeout=30)
