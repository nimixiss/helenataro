import os
import threading
from dataclasses import dataclass
from typing import Optional, Tuple

import telebot
from telebot.types import Message


@dataclass
class BotConfig:
    token: str
    admin_id: int
    greeting_text: str
    auto_reply_text: str
    label: str


def _parse_reply_command(raw_text: Optional[str]) -> Tuple[Optional[int], Optional[str]]:
    if not raw_text:
        return None, None

    parts = raw_text.split(maxsplit=2)
    if len(parts) < 3:
        return None, None

    try:
        user_id = int(parts[1])
    except ValueError:
        return None, None

    reply_text = parts[2].strip()
    if not reply_text:
        return None, None

    return user_id, reply_text


class ManagedBot:
    SUPPORTED_CONTENT_TYPES = [
        "text",
        "audio",
        "document",
        "photo",
        "sticker",
        "video",
        "video_note",
        "voice",
        "location",
        "contact",
    ]

    def __init__(self, config: BotConfig):
        self.config = config
        self.bot = telebot.TeleBot(config.token, parse_mode="HTML")
        self._register_admin_handlers()
        self._register_user_handlers()

    def start(self) -> None:
        print(f"Запуск бота '{self.config.label}'")
        self.bot.infinity_polling(timeout=60, long_polling_timeout=30)

    # === Admin helpers ===
    def _send_format_hint(self) -> None:
        self.bot.send_message(
            self.config.admin_id,
            "Формат команды:\n/reply <user_id> <текст ответа>",
        )

    def _forward_with_metadata(self, message: Message) -> None:
        user = message.from_user
        username = f"@{user.username}" if user.username else "—"
        full_name_parts = [user.first_name or "", user.last_name or ""]
        full_name = " ".join(part for part in full_name_parts if part).strip() or "—"
        info_message = (
            f"💌 <b>{self.config.label}</b>\n"
            f"ID: <code>{user.id}</code>\n"
            f"Имя: {full_name}\n"
            f"Username: {username}\n"
            f"Профиль: <a href='tg://user?id={user.id}'>ссылка</a>"
        )
        self.bot.send_message(
            self.config.admin_id,
            info_message,
            disable_web_page_preview=True,
        )
        self.bot.forward_message(self.config.admin_id, message.chat.id, message.message_id)

    def _register_admin_handlers(self) -> None:
        @self.bot.message_handler(commands=['reply'])
        def reply_to_user(message: Message) -> None:
            if message.chat.id != self.config.admin_id:
                self.bot.send_message(
                    message.chat.id,
                    "Эта команда доступна только администратору.",
                )
                return

            user_id, reply_text = _parse_reply_command(message.text)
            if user_id is None or reply_text is None:
                self._send_format_hint()
                return

            try:
                self.bot.send_message(user_id, reply_text)
                self.bot.send_message(self.config.admin_id, "✅ Ответ отправлен.")
            except Exception as exc:  # noqa: BLE001
                self.bot.send_message(
                    self.config.admin_id,
                    f"⚠️ Ошибка: {exc}",
                )

        @self.bot.message_handler(content_types=['photo'])
        def reply_with_photo(message: Message) -> None:
            if message.chat.id != self.config.admin_id:
                return

            caption = message.caption or ""
            if not caption.startswith('/reply'):
                self._send_format_hint()
                return

            user_id, reply_text = _parse_reply_command(caption)
            if user_id is None or reply_text is None:
                self._send_format_hint()
                return

            try:
                file_id = message.photo[-1].file_id
                self.bot.send_photo(user_id, file_id, caption=reply_text)
                self.bot.send_message(self.config.admin_id, "✅ Ответ с фото отправлен.")
            except Exception as exc:  # noqa: BLE001
                self.bot.send_message(
                    self.config.admin_id,
                    f"⚠️ Ошибка: {exc}",
                )

    def _register_user_handlers(self) -> None:
        @self.bot.message_handler(commands=['start'])
        def start_dialog(message: Message) -> None:
            if message.chat.id == self.config.admin_id:
                self._send_format_hint()
                return

            if self.config.greeting_text:
                self.bot.send_message(message.chat.id, self.config.greeting_text)

        @self.bot.message_handler(content_types=self.SUPPORTED_CONTENT_TYPES)
        def handle_any_message(message: Message) -> None:
            if message.chat.id == self.config.admin_id:
                return

            if message.content_type == 'text' and message.text and message.text.startswith('/start'):
                return

            self._forward_with_metadata(message)

            if self.config.auto_reply_text:
                self.bot.send_message(message.chat.id, self.config.auto_reply_text)


def _build_configs() -> list[BotConfig]:
    admin_id = int(os.getenv("ADMIN_ID", 220493509))

    main_token = os.getenv("BOT_TOKEN")
    support_token = os.getenv("SUPPORT_BOT_TOKEN")

    configs: list[BotConfig] = []

    if main_token:
        configs.append(
            BotConfig(
                token=main_token,
                admin_id=admin_id,
                greeting_text=os.getenv(
                    "MAIN_GREETING_TEXT",
                    "Привет! Я Елена. Расскажи, что тебя волнует ✨",
                ),
                auto_reply_text=os.getenv(
                    "MAIN_AUTO_REPLY_TEXT",
                    "Спасибо за сообщение! Я свяжусь с тобой как можно скорее 💌",
                ),
                label=os.getenv("MAIN_BOT_LABEL", "Helena Taro"),
            )
        )

    if support_token:
        configs.append(
            BotConfig(
                token=support_token,
                admin_id=admin_id,
                greeting_text=os.getenv(
                    "SUPPORT_GREETING_TEXT",
                    "Привет! Это чат поддержки. Напиши свой вопрос, и мы ответим в ближайшее время.",
                ),
                auto_reply_text=os.getenv(
                    "SUPPORT_AUTO_REPLY_TEXT",
                    "Спасибо! Мы получили твоё сообщение и скоро свяжемся.",
                ),
                label=os.getenv("SUPPORT_BOT_LABEL", "Support"),
            )
        )

    if not configs:
        raise RuntimeError(
            "Не найдено ни одного токена. Проверь переменные окружения BOT_TOKEN и SUPPORT_BOT_TOKEN.",
        )

    return configs


def main() -> None:
    configs = _build_configs()
    bots = [ManagedBot(config) for config in configs]

    threads: list[threading.Thread] = []
    for managed_bot in bots:
        thread = threading.Thread(target=managed_bot.start, daemon=True)
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()


if __name__ == "__main__":
    main()
