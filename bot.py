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


def _send_format_hint(bot: telebot.TeleBot, admin_id: int):
    bot.send_message(
        admin_id,
        "Формат команды:\n/reply <user_id> <текст ответа>"
    )


class ConfiguredBot:
    def __init__(self, config: BotConfig):
        self.config = config
        self.bot = telebot.TeleBot(config.token)
        self._register_handlers()

    def _register_handlers(self):
        bot = self.bot
        config = self.config

        @bot.message_handler(commands=['start'])
        def start(message: Message):
            bot.send_message(message.chat.id, config.greeting_text)

        @bot.message_handler(
            func=lambda m: m.from_user and m.from_user.id != config.admin_id,
            content_types=['text'],
        )
        def handle_client_message(message: Message):
            user_id = message.chat.id
            text = message.text or ""
            first_name = message.from_user.first_name or "(без имени)"
            username = message.from_user.username or "нет ника"

            admin_text = (
                f"📩 Новое сообщение ({config.label}):\n"
                f"Имя: {first_name}\n"
                f"Ник: @{username}\n"
                f"ID: {user_id}\n\n"
                f"{text}"
            )

            bot.send_message(config.admin_id, admin_text)

            bot.send_message(user_id, config.auto_reply_text)

        @bot.message_handler(commands=['reply'])
        def reply_to_user(message: Message):
            if message.chat.id != config.admin_id:
                bot.send_message(message.chat.id, "Эта команда только для Елены 🌙")
                return

            user_id, reply_text = _parse_reply_command(message.text)
            if user_id is None:
                _send_format_hint(bot, config.admin_id)
                return

            try:
                bot.send_message(user_id, reply_text)
                bot.send_message(config.admin_id, "✅ Ответ отправлен.")
            except Exception as e:
                bot.send_message(config.admin_id, f"⚠️ Ошибка: {e}")

        @bot.message_handler(content_types=['photo'])
        def reply_with_photo(message: Message):
            if message.chat.id != config.admin_id:
                return

            caption = message.caption or ""
            if not caption.startswith('/reply'):
                _send_format_hint(bot, config.admin_id)
                return

            user_id, reply_text = _parse_reply_command(caption)
            if user_id is None:
                _send_format_hint(bot, config.admin_id)
                return

            try:
                photo_sizes = message.photo or []
                if not photo_sizes:
                    bot.send_message(config.admin_id, "⚠️ Не удалось получить фото из сообщения.")
                    return

                file_id = photo_sizes[-1].file_id
                bot.send_photo(user_id, file_id, caption=reply_text)
                bot.send_message(config.admin_id, "✅ Ответ с фото отправлен.")
            except Exception as e:
                bot.send_message(config.admin_id, f"⚠️ Ошибка: {e}")

    def run(self):
        self.bot.infinity_polling(timeout=60, long_polling_timeout=30)



def _create_bots():
    configs = []

    if MAIN_BOT_TOKEN:
        configs.append(
            BotConfig(
                token=MAIN_BOT_TOKEN,
                admin_id=ADMIN_ID,
                greeting_text=(
                    "✨ Привет! Меня зовут Елена, я таролог с 14-летним опытом.\n\n"
                    "Очень рада, что ты обратилась/лся ко мне. Я работаю с Таро не как с "
                    "«страшными предсказаниями», а как с честным разговором с твоим подсознанием — "
                    "карты показывают направления, возможные развилки и то, на что важно обратить внимание.\n\n"
                    "Расскажи, пожалуйста, что сейчас для тебя самое важное:\n"
                    "• какая ситуация беспокоит\n"
                    "• про какие отношения, деньги, самореализацию, здоровье или переезд хочешь спросить\n"
                    "• какие страхи или сомнения особенно чувствуються\n\n"
                    "Пиши свободно, столько, сколько тебе комфортно. 🙏 Всё, что ты напишешь, останется "
                    "между нами.\n\n"
                    "По твоему запросу я предложу несколько вариантов раскладов с конкретными вопросами, "
                    "ты выберешь тот, который больше откликается — и мы сделаем расклад именно под тебя 🌙\n\n"
                    "Можешь начать прямо сейчас: опиши свою ситуацию или напиши, о чём хочется узнать в первую очередь."
                ),
                auto_reply_text=(
                    "🌙 Я получила твой запрос.\n"
                    "Совсем скоро посмотрю ситуацию по картам и предложу тебе варианты раскладов. "
                    "Если захочешь что-то добавить или уточнить — не стесняйся, пиши, что чувствуешь"
                ),
                label="Helena Taro"
            )
        )

    if SUPPORT_BOT_TOKEN:
        configs.append(
            BotConfig(
                token=SUPPORT_BOT_TOKEN,
                admin_id=ADMIN_ID,
                greeting_text=(
                    "✨ Привет! Ты написал(а) в поддержку Helena Taro.\n"
                    "Расскажи, пожалуйста, с каким вопросом или сложностью столкнулся — я постараюсь "
                    "помочь как можно скорее."
                ),
                auto_reply_text=(
                    "🌙 Спасибо за сообщение! Я всё увидела и скоро отвечу."
                    " Если захочешь что-то добавить — просто напиши здесь."
                ),
                label="Поддержка"
            )
        )

    return [ConfiguredBot(config) for config in configs]


def _run_bots(bots):
    if not bots:
        raise RuntimeError("Не настроено ни одного бота. Проверь переменные окружения с токенами.")

    threads = []

    for configured in bots:
        thread = threading.Thread(
            target=configured.run,
        )
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()


if __name__ == "__main__":
    _run_bots(_create_bots())
