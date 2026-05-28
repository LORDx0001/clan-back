import os
import time
import requests
import json
import logging
import django
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from api.models import Player

logger = logging.getLogger(__name__)

# ─── States ────────────────────────────────────────────────────────────────────
STATE_NONE            = "NONE"
STATE_REG_USERNAME    = "REG_USERNAME"
STATE_REG_PASSWORD    = "REG_PASSWORD"
STATE_REG_CONFIRM     = "REG_CONFIRM"      # повтор пароля
STATE_RESET_PASSWORD  = "RESET_PASSWORD"
STATE_RESET_CONFIRM   = "RESET_CONFIRM"    # повтор нового пароля


class Command(BaseCommand):
    help = "Telegram-бот: регистрация пользователей и смена пароля"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot_token = None
        self.admin_chat_id = None
        self.user_states = {}   # chat_id → {"state": ..., "data": {...}}

    # ── Entry point ────────────────────────────────────────────────────────────
    def handle(self, *args, **options):
        self.bot_token    = os.environ.get("TELEGRAM_BOT_TOKEN")
        self.admin_chat_id = os.environ.get("TELEGRAM_CHAT_ID")

        if not self.bot_token:
            self.stdout.write(self.style.ERROR("TELEGRAM_BOT_TOKEN не задан!"))
            return

        self.stdout.write(self.style.SUCCESS("Бот запущен."))
        if self.admin_chat_id:
            self.stdout.write(self.style.SUCCESS(f"Группа уведомлений: {self.admin_chat_id}"))

        offset = 0
        while True:
            try:
                url = (
                    f"https://api.telegram.org/bot{self.bot_token}"
                    f"/getUpdates?offset={offset}&timeout=30"
                )
                resp = requests.get(url, timeout=35)
                if resp.status_code == 200:
                    for update in resp.json().get("result", []):
                        offset = update["update_id"] + 1
                        try:
                            self.process_update(update)
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f"Ошибка: {e}"))
                else:
                    time.sleep(5)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Цикл: {e}"))
                time.sleep(5)

    # ── Telegram helpers ───────────────────────────────────────────────────────
    def api(self, method, payload=None):
        url = f"https://api.telegram.org/bot{self.bot_token}/{method}"
        try:
            r = requests.post(url, data=payload, timeout=20)
            return r.json()
        except Exception:
            return {}

    def send(self, chat_id, text, buttons=None):
        """Отправить сообщение с опциональной reply-keyboard."""
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown",
        }
        if buttons is not None:
            kb = {"keyboard": buttons, "resize_keyboard": True, "one_time_keyboard": True}
            payload["reply_markup"] = json.dumps(kb)
        else:
            payload["reply_markup"] = json.dumps({"remove_keyboard": True})
        self.api("sendMessage", payload)

    def cancel_kb(self):
        return [[{"text": "❌ Отмена"}]]

    # ── Main menu ──────────────────────────────────────────────────────────────
    def main_menu(self, chat_id, text=""):
        player = Player.objects.filter(telegram_id=chat_id).first()
        already = player and player.user

        header = text + "\n\n" if text else ""
        body = (
            f"{header}"
            f"👋 Добро пожаловать!\n\n"
            f"Этот бот предназначен для *регистрации* на сайте клана "
            f"и *управления паролем*.\n\n"
            f"Выберите действие:"
        )

        if already:
            buttons = [
                [{"text": "🔑 Сменить пароль"}],
            ]
        else:
            buttons = [
                [{"text": "📝 Зарегистрироваться"}],
            ]

        self.send(chat_id, body, buttons)

    # ── Router ─────────────────────────────────────────────────────────────────
    def process_update(self, update):
        if "message" not in update:
            return
        msg      = update["message"]
        chat_id  = str(msg["chat"]["id"])
        text     = (msg.get("text") or "").strip()
        name     = msg.get("from", {}).get("first_name", "Пользователь")

        # Init state
        if chat_id not in self.user_states:
            self.user_states[chat_id] = {"state": STATE_NONE, "data": {}}

        # Global cancel
        if text in ["❌ Отмена", "/cancel", "отмена", "/menu", "меню"]:
            self.user_states[chat_id] = {"state": STATE_NONE, "data": {}}
            self.main_menu(chat_id, "❌ Действие отменено.")
            return

        state = self.user_states[chat_id]["state"]
        if state == STATE_NONE:
            self.on_menu(chat_id, text, name)
        else:
            self.on_step(chat_id, text, state)

    # ── Menu handler ───────────────────────────────────────────────────────────
    def on_menu(self, chat_id, text, name):
        if text == "/start":
            self.main_menu(chat_id, f"👋 Привет, {name}!")
            return

        if text == "📝 Зарегистрироваться":
            # Already registered?
            player = Player.objects.filter(telegram_id=chat_id).first()
            if player and player.user:
                self.send(chat_id,
                    "⚠️ Вы уже зарегистрированы.\n\n"
                    "Используйте *Сменить пароль*, если забыли пароль.")
                self.main_menu(chat_id)
                return

            self.user_states[chat_id] = {"state": STATE_REG_USERNAME, "data": {}}
            self.send(
                chat_id,
                "📝 *Регистрация — Шаг 1 из 3*\n\n"
                "Придумайте *логин* для входа на сайт.\n"
                "Только латинские буквы и цифры, минимум 3 символа.",
                self.cancel_kb()
            )
            return

        if text == "🔑 Сменить пароль":
            player = Player.objects.filter(telegram_id=chat_id).first()
            if not player or not player.user:
                self.send(chat_id,
                    "⚠️ У вас нет аккаунта на сайте.\n\n"
                    "Сначала пройдите регистрацию через *Зарегистрироваться*.")
                self.main_menu(chat_id)
                return

            self.user_states[chat_id] = {
                "state": STATE_RESET_PASSWORD,
                "data": {"user_id": player.user.id, "username": player.user.username}
            }
            self.send(
                chat_id,
                f"🔑 *Смена пароля*\n\n"
                f"Аккаунт: `{player.user.username}`\n\n"
                f"Введите *новый пароль* (минимум 6 символов):",
                self.cancel_kb()
            )
            return

        self.main_menu(chat_id, "❓ Неизвестная команда.")

    # ── Step handler ───────────────────────────────────────────────────────────
    def on_step(self, chat_id, text, state):
        data = self.user_states[chat_id]["data"]

        # ── REGISTRATION ────────────────────────────────────────────────────────
        if state == STATE_REG_USERNAME:
            if len(text) < 3 or not text.isalnum():
                self.send(chat_id,
                    "⚠️ Логин должен содержать только *латинские буквы и цифры*, "
                    "минимум 3 символа.\n\nПопробуйте ещё раз:",
                    self.cancel_kb())
                return
            if User.objects.filter(username=text).exists():
                self.send(chat_id,
                    "⚠️ Этот логин *уже занят*. Придумайте другой:",
                    self.cancel_kb())
                return

            data["username"] = text
            self.user_states[chat_id]["state"] = STATE_REG_PASSWORD
            self.send(
                chat_id,
                f"✅ Логин: `{text}`\n\n"
                f"📝 *Регистрация — Шаг 2 из 3*\n\n"
                f"Придумайте *пароль* (минимум 6 символов):",
                self.cancel_kb()
            )

        elif state == STATE_REG_PASSWORD:
            if len(text) < 6:
                self.send(chat_id,
                    "⚠️ Пароль слишком короткий. Минимум *6 символов*.\n\nПовторите:",
                    self.cancel_kb())
                return

            data["password"] = text
            self.user_states[chat_id]["state"] = STATE_REG_CONFIRM
            self.send(
                chat_id,
                "📝 *Регистрация — Шаг 3 из 3*\n\n"
                "Повторите пароль для подтверждения:",
                self.cancel_kb()
            )

        elif state == STATE_REG_CONFIRM:
            if text != data["password"]:
                self.send(chat_id,
                    "⚠️ Пароли *не совпадают*!\n\nВведите пароль заново (шаг 2):",
                    self.cancel_kb())
                self.user_states[chat_id]["state"] = STATE_REG_PASSWORD
                return

            # Create user
            username = data["username"]
            password = data["password"]
            try:
                user = User.objects.create_user(
                    username=username,
                    password=password,
                    is_active=False   # ждёт активации администратора
                )
                # Привязываем telegram_id — создаём минимальный Player или ищем существующий
                player = Player.objects.filter(telegram_id=chat_id).first()
                if not player:
                    player = Player.objects.create(
                        nickname=username,
                        telegram_id=chat_id,
                        is_approved=False,
                    )
                player.user = user
                player.save()

                self.user_states[chat_id] = {"state": STATE_NONE, "data": {}}
                self.main_menu(
                    chat_id,
                    "🎉 *Регистрация завершена!*\n\n"
                    f"Ваш логин: `{username}`\n"
                    f"Ваш пароль: ||{password}||\n\n"
                    "⏳ Аккаунт ожидает активации администратором.\n"
                    "После одобрения вы сможете войти на сайт."
                )

                # Уведомление в группу
                if self.admin_chat_id:
                    self.send(
                        self.admin_chat_id,
                        f"🔔 *Новая регистрация на сайте!*\n\n"
                        f"👤 Имя в TG: `{chat_id}`\n"
                        f"🔑 Логин: `{username}`\n\n"
                        f"Перейдите в админ-панель, чтобы:\n"
                        f"• Активировать аккаунт (поставить ✅ *Активный*)\n"
                        f"• Привязать карточку игрока или дать разрешение на создание\n\n"
                        f"👉 [Открыть пользователя в Admin](http://127.0.0.1:8000/admin/auth/user/{user.id}/change/)"
                    )
            except Exception as e:
                self.user_states[chat_id] = {"state": STATE_NONE, "data": {}}
                self.send(chat_id, f"❌ Ошибка регистрации: `{e}`\n\nОбратитесь к администратору.")

        # ── PASSWORD RESET ──────────────────────────────────────────────────────
        elif state == STATE_RESET_PASSWORD:
            if len(text) < 6:
                self.send(chat_id,
                    "⚠️ Пароль слишком короткий. Минимум *6 символов*.\n\nПовторите:",
                    self.cancel_kb())
                return

            data["new_password"] = text
            self.user_states[chat_id]["state"] = STATE_RESET_CONFIRM
            self.send(
                chat_id,
                "🔑 Повторите новый пароль для подтверждения:",
                self.cancel_kb()
            )

        elif state == STATE_RESET_CONFIRM:
            if text != data["new_password"]:
                self.send(chat_id,
                    "⚠️ Пароли *не совпадают*!\n\nВведите новый пароль ещё раз:",
                    self.cancel_kb())
                self.user_states[chat_id]["state"] = STATE_RESET_PASSWORD
                return

            try:
                user = User.objects.get(id=data["user_id"])
                user.set_password(text)
                user.save()

                self.user_states[chat_id] = {"state": STATE_NONE, "data": {}}
                self.main_menu(
                    chat_id,
                    f"✅ *Пароль успешно изменён!*\n\n"
                    f"Логин: `{data['username']}`\n"
                    f"Новый пароль: ||{text}||"
                )

                # Уведомление в группу
                if self.admin_chat_id:
                    self.send(
                        self.admin_chat_id,
                        f"🔔 Пользователь `{data['username']}` сменил пароль на сайте."
                    )
            except Exception as e:
                self.user_states[chat_id] = {"state": STATE_NONE, "data": {}}
                self.send(chat_id, f"❌ Ошибка смены пароля: `{e}`")
