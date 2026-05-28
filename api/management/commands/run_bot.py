import os
import time
import requests
import json
import logging
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from api.models import Player

logger = logging.getLogger(__name__)

STATE_NONE = "NONE"
STATE_REG_USERNAME = "REG_USERNAME"
STATE_REG_PASSWORD = "REG_PASSWORD"
STATE_RESET_PASSWORD = "RESET_PASSWORD"

class Command(BaseCommand):
    help = "Запускает Telegram бот для регистрации пользователей"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot_token = None
        self.admin_chat_id = None
        self.user_states = {}

    def handle(self, *args, **options):
        self.bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
        self.admin_chat_id = os.environ.get("TELEGRAM_CHAT_ID")

        if not self.bot_token:
            self.stdout.write(self.style.ERROR("Переменная окружения TELEGRAM_BOT_TOKEN не задана!"))
            return

        self.stdout.write(self.style.SUCCESS(f"Запуск Telegram Бота..."))
        if self.admin_chat_id:
            self.stdout.write(self.style.SUCCESS(f"Чат администратора для уведомлений: {self.admin_chat_id}"))

        offset = 0
        while True:
            try:
                url = f"https://api.telegram.org/bot{self.bot_token}/getUpdates?offset={offset}&timeout=30"
                response = requests.get(url, timeout=35)
                if response.status_code == 200:
                    data = response.json()
                    for update in data.get("result", []):
                        offset = update["update_id"] + 1
                        try:
                            self.process_update(update)
                        except Exception as inner_e:
                            self.stdout.write(self.style.ERROR(f"Ошибка обработки: {str(inner_e)}"))
                else:
                    time.sleep(5)
            except Exception as e:
                time.sleep(5)

    def process_update(self, update):
        if "message" not in update:
            return
        
        message = update["message"]
        chat_id = str(message["chat"]["id"])
        text = (message.get("text") or "").strip()
        user_info = message.get("from", {})
        first_name = user_info.get("first_name", "Пользователь")

        if chat_id not in self.user_states:
            self.user_states[chat_id] = {"state": STATE_NONE, "data": {}}

        if text.lower() in ["/cancel", "отмена", "/menu", "меню"]:
            self.user_states[chat_id] = {"state": STATE_NONE, "data": {}}
            self.send_main_menu(chat_id, f"Действие отменено. Возвращаю вас в главное меню.")
            return

        state = self.user_states[chat_id]["state"]

        if state == STATE_NONE:
            self.handle_main_commands(chat_id, text, first_name)
        else:
            self.handle_state_wizards(chat_id, text)

    def send_telegram(self, method, payload=None):
        url = f"https://api.telegram.org/bot{self.bot_token}/{method}"
        try:
            res = requests.post(url, data=payload, timeout=20)
            return res.json()
        except:
            return {}

    def send_message(self, chat_id, text, reply_markup=None):
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        if reply_markup:
            payload["reply_markup"] = json.dumps(reply_markup)
        return self.send_telegram("sendMessage", payload)

    def send_main_menu(self, chat_id, welcome_text):
        full_text = f"{welcome_text}\n\nЭтот бот используется для регистрации и сброса пароля на нашем сайте.\n\nВыберите действие:"
        
        buttons = [
            [{"text": "🔑 Регистрация на сайте"}],
            [{"text": "🔑 Сброс/Смена пароля"}]
        ]

        reply_markup = {
            "keyboard": buttons,
            "resize_keyboard": True,
            "one_time_keyboard": False
        }
        self.send_message(chat_id, full_text, reply_markup)

    def handle_main_commands(self, chat_id, text, first_name):
        if text == "/start":
            self.send_main_menu(chat_id, f"👋 Привет, {first_name}!")
            return

        elif text == "🔑 Регистрация на сайте":
            # We look for a User where a Player is linked to this telegram_id? 
            # Or better yet, we just check if any User's player_profile has this tg id.
            # Wait, if registration is only through bot, user might NOT have a Player linked yet!
            # Let's save chat_id to the user itself? Django User doesn't have telegram_id natively.
            # But we can store it in player_profile. 
            # If user wants to register, we let them create an account. Later admin links it.
            # Or we create a Player profile under the hood just to store the telegram_id.
            
            player = Player.objects.filter(telegram_id=chat_id).first()
            if player and player.user:
                self.send_message(chat_id, "⚠️ Вы уже зарегистрированы на сайте. Используйте '🔑 Сброс/Смена пароля'.")
                return
                
            self.user_states[chat_id] = {
                "state": STATE_REG_USERNAME,
                "data": {}
            }
            reply_markup = {"keyboard": [[{"text": "отмена"}]], "resize_keyboard": True}
            self.send_message(chat_id, "🔐 *Регистрация на сайте*\n\nШаг 1: Придумайте *Логин* (только английские буквы и цифры):", reply_markup)

        elif text == "🔑 Сброс/Смена пароля":
            player = Player.objects.filter(telegram_id=chat_id).first()
            if not player or not player.user:
                self.send_message(chat_id, "⚠️ Вы еще не зарегистрированы или ваш аккаунт не привязан. Выберите '🔑 Регистрация на сайте' или обратитесь к администратору.")
                return
                
            self.user_states[chat_id] = {
                "state": STATE_RESET_PASSWORD,
                "data": {"user_id": player.user.id}
            }
            reply_markup = {"keyboard": [[{"text": "отмена"}]], "resize_keyboard": True}
            self.send_message(chat_id, f"🔐 *Смена пароля для логина:* `{player.user.username}`\n\nВведите *Новый пароль* (минимум 6 символов):", reply_markup)

        else:
            self.send_main_menu(chat_id, "❓ Неизвестная команда.")

    def handle_state_wizards(self, chat_id, text):
        state = self.user_states[chat_id]["state"]

        if state == STATE_REG_USERNAME:
            if not text or len(text) < 3 or not text.isalnum():
                self.send_message(chat_id, "⚠️ Логин должен содержать только буквы и цифры (минимум 3 символа). Введите логин:")
                return
            if User.objects.filter(username=text).exists():
                self.send_message(chat_id, "⚠️ Этот логин уже занят! Придумайте другой:")
                return
                
            self.user_states[chat_id]["data"]["username"] = text
            self.user_states[chat_id]["state"] = STATE_REG_PASSWORD
            self.send_message(chat_id, "Шаг 2: Придумайте *Пароль* (минимум 6 символов):")

        elif state == STATE_REG_PASSWORD:
            if not text or len(text) < 6:
                self.send_message(chat_id, "⚠️ Пароль слишком короткий. Введите пароль (минимум 6 символов):")
                return
                
            username = self.user_states[chat_id]["data"]["username"]
            password = text
            
            try:
                user = User.objects.create_user(username=username, password=password, is_active=False)
                
                # Check if we have an existing player to link. Otherwise create a minimal one to save telegram_id.
                player = Player.objects.filter(telegram_id=chat_id).first()
                if not player:
                    player = Player.objects.create(
                        nickname=username,
                        telegram_id=chat_id,
                        is_approved=False
                    )
                player.user = user
                player.save()
                
                self.user_states[chat_id] = {"state": STATE_NONE, "data": {}}
                self.send_main_menu(
                    chat_id,
                    f"🎉 *Регистрация успешна!*\n\n"
                    f"Ваш логин: `{username}`\n"
                    f"Ваш пароль: ||{password}|| (нажмите чтобы скопировать)\n\n"
                    f"⏳ Ваш аккаунт ожидает активации администратором. После одобрения вы сможете войти на сайт!"
                )
                
                if self.admin_chat_id:
                    admin_msg = (
                        f"🔐 *Новая регистрация на сайте!*\n\n"
                        f"👤 TG ID: {chat_id}\n"
                        f"🔑 Логин: `{username}`\n\n"
                        f"👉 *[НАЖМИТЕ СЮДА ДЛЯ АКТИВАЦИИ](http://127.0.0.1:8000/admin/auth/user/{user.id}/change/)* (поставьте галочку 'Активный')"
                    )
                    self.send_message(self.admin_chat_id, admin_msg)
            except Exception as e:
                self.send_message(chat_id, f"❌ Ошибка регистрации: {e}")

        elif state == STATE_RESET_PASSWORD:
            if not text or len(text) < 6:
                self.send_message(chat_id, "⚠️ Пароль слишком короткий. Введите пароль (минимум 6 символов):")
                return
                
            user_id = self.user_states[chat_id]["data"]["user_id"]
            user = User.objects.get(id=user_id)
            user.set_password(text)
            user.save()
            
            self.user_states[chat_id] = {"state": STATE_NONE, "data": {}}
            self.send_main_menu(chat_id, f"✅ Пароль успешно изменен!\n\nВаш логин: `{user.username}`\nВаш новый пароль: ||{text}||")
