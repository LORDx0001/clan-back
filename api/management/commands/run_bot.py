import os
import time
import requests
import json
import logging
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.utils import timezone
from api.models import Player, PlayerRole, GalleryItem

logger = logging.getLogger(__name__)

# Constants for states
STATE_NONE = "NONE"

# Roster Steps
STATE_ROSTER_NICKNAME = "ROSTER_NICKNAME"
STATE_ROSTER_UID = "ROSTER_UID"
STATE_ROSTER_ROLE = "ROSTER_ROLE"
STATE_ROSTER_DEVICE = "ROSTER_DEVICE"
STATE_ROSTER_LEVEL = "ROSTER_LEVEL"
STATE_ROSTER_KD = "ROSTER_KD"
STATE_ROSTER_WEAPON = "ROSTER_WEAPON"
STATE_ROSTER_AVATAR = "ROSTER_AVATAR"
STATE_ROSTER_ACHIEVEMENTS = "ROSTER_ACHIEVEMENTS"
STATE_ROSTER_REGION = "ROSTER_REGION"
STATE_ROSTER_DESCRIPTION = "ROSTER_DESCRIPTION"

# Highlight Steps
STATE_HL_TITLE = "HL_TITLE"
STATE_HL_CATEGORY = "HL_CATEGORY"
STATE_HL_MEDIA = "HL_MEDIA"

# Set of optional states that are skipped during both registration and editing
OPTIONAL_STATES = {
    STATE_ROSTER_UID,
    STATE_ROSTER_DEVICE,
    STATE_ROSTER_KD,
    STATE_ROSTER_AVATAR,
    STATE_ROSTER_DESCRIPTION
}

class Command(BaseCommand):
    help = "Запускает Telegram бот для приема анкет в состав и хайлайтов"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot_token = None
        self.admin_chat_id = None
        self.user_states = {}  # chat_id -> {"state": STATE, "data": {}, "is_edit": False, "role_map": {}}

    def handle(self, *args, **options):
        self.bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
        self.admin_chat_id = os.environ.get("TELEGRAM_CHAT_ID")

        if not self.bot_token:
            self.stdout.write(self.style.ERROR("Переменная окружения TELEGRAM_BOT_TOKEN не задана!"))
            return

        self.stdout.write(self.style.SUCCESS(f"Запуск Telegram Бота..."))
        if self.admin_chat_id:
            self.stdout.write(self.style.SUCCESS(f"Чат администратора для уведомлений: {self.admin_chat_id}"))
        else:
            self.stdout.write(self.style.WARNING("Переменная TELEGRAM_CHAT_ID не задана. Уведомления не будут приходить в админ-чат."))

        offset = 0
        while True:
            try:
                url = f"https://api.telegram.org/bot{self.bot_token}/getUpdates?offset={offset}&timeout=30"
                response = requests.get(url, timeout=35)
                if response.status_code == 200:
                    data = response.json()
                    for update in data.get("result", []):
                        offset = update["update_id"] + 1
                        self.process_update(update)
                else:
                    self.stdout.write(self.style.ERROR(f"Ошибка получения обновлений: {response.text}"))
                    time.sleep(5)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Критическая ошибка в цикле бота: {str(e)}"))
                time.sleep(5)

    def process_update(self, update):
        if "message" not in update:
            return
        
        message = update["message"]
        chat_id = str(message["chat"]["id"])
        text = message.get("text", "").strip()
        user_info = message.get("from", {})
        first_name = user_info.get("first_name", "Игрок")

        # Initialize user state if not exists
        if chat_id not in self.user_states:
            self.user_states[chat_id] = {"state": STATE_NONE, "data": {}, "is_edit": False}

        # Check for global cancel / exit command
        if text.lower() in ["/cancel", "отмена", "/menu", "меню"]:
            self.user_states[chat_id] = {"state": STATE_NONE, "data": {}, "is_edit": False}
            self.send_main_menu(chat_id, f"Действие отменено. Возвращаю вас в главное меню.")
            return

        state = self.user_states[chat_id]["state"]

        # If state is NONE, handle main commands
        if state == STATE_NONE:
            self.handle_main_commands(chat_id, text, first_name)
        else:
            self.handle_state_wizards(chat_id, message, state)

    def send_telegram(self, method, payload=None, files=None):
        url = f"https://api.telegram.org/bot{self.bot_token}/{method}"
        try:
            res = requests.post(url, data=payload, files=files, timeout=20)
            return res.json()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Ошибка запроса Telegram API {method}: {e}"))
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

    def get_step_keyboard(self, chat_id, next_state):
        is_edit = self.user_states[chat_id]["is_edit"]
        is_optional = next_state in OPTIONAL_STATES
        
        if is_edit or is_optional:
            buttons = [
                [{"text": "Пропустить ⏭️"}],
                [{"text": "отмена"}]
            ]
        else:
            buttons = [
                [{"text": "отмена"}]
            ]
            
        return {
            "keyboard": buttons,
            "resize_keyboard": True,
            "one_time_keyboard": True
        }

    def send_main_menu(self, chat_id, welcome_text):
        player = Player.objects.filter(telegram_id=chat_id).first()

        buttons = []
        if player:
            status_text = "✅ Одобрен и опубликован на сайте" if player.is_approved else "⏳ На модерации (появится после одобрения)"
            full_text = (
                f"{welcome_text}\n\n"
                f"👤 *Твой игровой профиль:* {player.nickname}\n"
                f"📊 *Статус на сайте:* {status_text}\n\n"
                f"Выбери следующее действие:"
            )
            buttons = [
                [{"text": "📝 Изменить анкету состава"}],
                [{"text": "🎥 Добавить хайлайт"}],
                [{"text": "❌ Удалить мой профиль"}],
                [{"text": "ℹ️ Помощь и Описание"}]
            ]
        else:
            full_text = (
                f"{welcome_text}\n\n"
                f"Этот бот поможет тебе подать заявку в состав клана и опубликовать свои игровые хайлайты на нашем сайте.\n\n"
                f"Выбери действие на клавиатуре:"
            )
            buttons = [
                [{"text": "📝 Подать заявку в состав"}],
                [{"text": "ℹ️ Помощь и Описание"}]
            ]

        reply_markup = {
            "keyboard": buttons,
            "resize_keyboard": True,
            "one_time_keyboard": False
        }
        self.send_message(chat_id, full_text, reply_markup)

    def handle_main_commands(self, chat_id, text, first_name):
        player = Player.objects.filter(telegram_id=chat_id).first()

        if text == "/start":
            self.send_main_menu(chat_id, f"👋 Привет, {first_name}! Добро пожаловать в бот клана!")
            return

        elif text in ["📝 Подать заявку в состав", "📝 Изменить анкету состава"]:
            is_edit = player is not None
            self.user_states[chat_id] = {
                "state": STATE_ROSTER_NICKNAME,
                "data": {},
                "is_edit": is_edit
            }
            
            skip_info = "\n\n💡 _Вы можете нажать кнопку 'Пропустить ⏭️' на любом шаге, чтобы оставить старое значение._" if is_edit else ""
            cancel_info = "\n\n❌ _Для отмены отправьте слово 'отмена'._"
            
            prompt = "Шаг 1: Введите ваш *Игровой Никнейм* (который будет на сайте):"
            if is_edit:
                prompt = f"Текущий никнейм: *{player.nickname}*\n\nВведите новый никнейм:"
            
            reply_markup = {
                "keyboard": [[{"text": "Пропустить ⏭️"}], [{"text": "отмена"}]] if is_edit else [[{"text": "отмена"}]],
                "resize_keyboard": True,
                "one_time_keyboard": True
            }
            self.send_message(chat_id, f"🚀 Начинаем заполнение анкеты в состав!{skip_info}{cancel_info}\n\n{prompt}", reply_markup)

        elif text == "🎥 Добавить хайлайт":
            if not player:
                self.send_message(chat_id, "⚠️ Вы не можете добавить хайлайт, так как у вас нет профиля в составе! Сначала заполните анкету в состав.")
                return
            
            if not player.is_approved:
                self.send_message(chat_id, "⏳ Ваш профиль еще находится на модерации. Вы сможете добавлять хайлайты сразу после того, как администратор одобрит ваш профиль состава в админ-панели!")
                return

            self.user_states[chat_id] = {
                "state": STATE_HL_TITLE,
                "data": {},
                "is_edit": False
            }
            self.send_message(chat_id, "🎥 *Добавление Хайлайта*\n\nОтправьте слово 'отмена' для выхода.\n\nШаг 1: Введите *Название* для хайлайта (например: _Соло минус сквад на праке_ или _Безумный зажим с AWM_):")

        elif text == "❌ Удалить мой профиль":
            if not player:
                self.send_message(chat_id, "⚠️ У вас нет активного профиля для удаления.")
                return
            
            # Delete highlights by player
            highlights = GalleryItem.objects.filter(telegram_id=chat_id)
            hl_count = highlights.count()
            highlights.delete()
            player.delete()
            
            self.send_main_menu(chat_id, f"🗑 Ваш профиль игрока и {hl_count} хайлайтов были полностью удалены из базы данных и сайта.")

        elif text in ["ℹ️ Помощь и Описание", "/help"]:
            help_text = (
                f"ℹ️ *Информация о Боте*\n\n"
                f"Этот бот интегрирован с официальным сайтом клана PUBG Mobile!\n\n"
                f"🔥 *Возможности:*\n"
                f"1. *Анкета состава:* отправьте свои игровые данные (никнейм, UID, роль, уровень, K/D, аватарку, девайс, достижения, регион). После одобрения администратором ваш красивый профиль появится на странице состава клана!\n"
                f"2. *Редактирование:* вы всегда можете изменить любые параметры своей анкеты в этом боте в реальном времени.\n"
                f"3. *Хайлайты:* делитесь своими лучшими моментами (видео или скриншоты). Они также проходят модерацию и выводятся в медиа-галерее сайта!\n\n"
                f"📝 *Команды:*\n"
                f"• `меню` или `/menu` — Вернуться в главное меню\n"
                f"• `отмена` или `/cancel` — Прервать заполнение анкеты"
            )
            self.send_message(chat_id, help_text)

        else:
            self.send_main_menu(chat_id, "❓ Неизвестная команда. Пожалуйста, воспользуйтесь кнопками на клавиатуре:")

    def handle_state_wizards(self, chat_id, message, state):
        text = message.get("text", "").strip()
        player = Player.objects.filter(telegram_id=chat_id).first()
        is_edit = self.user_states[chat_id]["is_edit"]
        is_skip = text.lower() in ["/skip", "пропустить", "пропустить ⏭️"] and (is_edit or state in OPTIONAL_STATES)

        # ----------------------------------------------------------------------
        # ROSTER PROFILE FLOW
        # ----------------------------------------------------------------------
        if state == STATE_ROSTER_NICKNAME:
            if not is_skip:
                if not text:
                    self.send_message(chat_id, "⚠️ Никнейм должен быть текстовым сообщением! Введите никнейм:")
                    return
                self.user_states[chat_id]["data"]["nickname"] = text
            else:
                self.user_states[chat_id]["data"]["nickname"] = player.nickname

            self.user_states[chat_id]["state"] = STATE_ROSTER_UID
            prompt = "Шаг 2: Введите ваш *PUBG ID (UID)* (необязательно, только цифры, например: 5123456789):"
            if is_edit:
                prompt = f"Текущий PUBG ID: *{player.uid}*\n\nВведите новый PUBG ID:"
            self.send_message(chat_id, prompt, self.get_step_keyboard(chat_id, STATE_ROSTER_UID))

        elif state == STATE_ROSTER_UID:
            if not is_skip:
                if not text:
                    self.send_message(chat_id, "⚠️ PUBG ID должен быть текстовым сообщением! Введите PUBG ID:")
                    return
                self.user_states[chat_id]["data"]["uid"] = text
            else:
                self.user_states[chat_id]["data"]["uid"] = player.uid if is_edit else ""

            # Query roles to show inline buttons
            roles = PlayerRole.objects.all()
            self.user_states[chat_id]["state"] = STATE_ROSTER_ROLE
            self.user_states[chat_id]["role_map"] = {str(r.id): r.name for r in roles}

            buttons = []
            for r in roles:
                buttons.append([{"text": r.name}])
            
            if is_edit:
                buttons.append([{"text": "Пропустить ⏭️"}])
            buttons.append([{"text": "отмена"}])

            reply_markup = {
                "keyboard": buttons,
                "resize_keyboard": True,
                "one_time_keyboard": True
            }

            prompt = "Шаг 3: Выберите вашу *Игровую Роль* в команде (или введите вручную):"
            if is_edit:
                current_role = player.role.name if player.role else "Без роли"
                prompt = f"Текущая роль: *{current_role}*\n\nВыберите или введите новую игровую роль:"
            
            self.send_message(chat_id, prompt, reply_markup)

        elif state == STATE_ROSTER_ROLE:
            if not is_skip:
                if not text:
                    self.send_message(chat_id, "⚠️ Выберите или введите игровую роль!")
                    return
                # Check if role exists or create a new one dynamically
                db_role = PlayerRole.objects.filter(name__iexact=text).first()
                if not db_role:
                    db_role = PlayerRole.objects.create(name=text)
                self.user_states[chat_id]["data"]["role_id"] = db_role.id
            else:
                self.user_states[chat_id]["data"]["role_id"] = player.role.id if (player and player.role) else None

            self.user_states[chat_id]["state"] = STATE_ROSTER_DEVICE
            prompt = "Шаг 4: Введите ваше *Игровое Устройство* (необязательно, например: iPad Pro M2, iPhone 15 Pro):"
            if is_edit:
                prompt = f"Текущее устройство: *{player.device}*\n\nВведите новое устройство:"
            self.send_message(chat_id, prompt, self.get_step_keyboard(chat_id, STATE_ROSTER_DEVICE))

        elif state == STATE_ROSTER_DEVICE:
            if not is_skip:
                if not text:
                    self.send_message(chat_id, "⚠️ Устройство должно быть текстом! Введите модель устройства:")
                    return
                self.user_states[chat_id]["data"]["device"] = text
            else:
                self.user_states[chat_id]["data"]["device"] = player.device if is_edit else ""

            self.user_states[chat_id]["state"] = STATE_ROSTER_LEVEL
            prompt = "Шаг 5: Укажите *Уровень Аккаунта* (например: 75):"
            if is_edit:
                prompt = f"Текущий уровень: *{player.level}*\n\nВведите новый уровень:"
            self.send_message(chat_id, prompt, self.get_step_keyboard(chat_id, STATE_ROSTER_LEVEL))

        elif state == STATE_ROSTER_LEVEL:
            if not is_skip:
                try:
                    lvl = int(text)
                    if lvl <= 0:
                        raise ValueError()
                    self.user_states[chat_id]["data"]["level"] = lvl
                except ValueError:
                    self.send_message(chat_id, "⚠️ Уровень аккаунта должен быть положительным числом! Введите уровень:")
                    return
            else:
                self.user_states[chat_id]["data"]["level"] = player.level

            self.user_states[chat_id]["state"] = STATE_ROSTER_KD
            prompt = "Шаг 6: Укажите ваш текущий *K/D Ratio* (необязательно, например: 4.85 или 5.2):"
            if is_edit:
                prompt = f"Текущий K/D: *{player.kd}*\n\nВведите новый K/D:"
            self.send_message(chat_id, prompt, self.get_step_keyboard(chat_id, STATE_ROSTER_KD))

        elif state == STATE_ROSTER_KD:
            if not is_skip:
                try:
                    # Convert comma to dot
                    kd_str = text.replace(",", ".")
                    kd_val = float(kd_str)
                    if kd_val < 0:
                        raise ValueError()
                    self.user_states[chat_id]["data"]["kd"] = kd_val
                except ValueError:
                    self.send_message(chat_id, "⚠️ K/D должен быть положительным числом! Укажите K/D (например: 5.1):")
                    return
            else:
                self.user_states[chat_id]["data"]["kd"] = player.kd if is_edit else None

            self.user_states[chat_id]["state"] = STATE_ROSTER_WEAPON
            prompt = "Шаг 7: Укажите ваше *Коронное/Любимое Оружие* (например: M416 + DP-28, AWM):"
            if is_edit:
                prompt = f"Коронное оружие: *{player.signature_weapon}*\n\nУкажите новое любимое оружие:"
            self.send_message(chat_id, prompt, self.get_step_keyboard(chat_id, STATE_ROSTER_WEAPON))

        elif state == STATE_ROSTER_WEAPON:
            if not is_skip:
                if not text:
                    self.send_message(chat_id, "⚠️ Оружие должно быть текстовым сообщением! Укажите оружие:")
                    return
                self.user_states[chat_id]["data"]["signature_weapon"] = text
            else:
                self.user_states[chat_id]["data"]["signature_weapon"] = player.signature_weapon

            self.user_states[chat_id]["state"] = STATE_ROSTER_AVATAR
            prompt = "Шаг 8: 📸 Отправьте вашу *Аватарку* (картинку / фото, необязательно, отправьте фото или нажмите пропустить):"
            if is_edit:
                prompt = f"📸 У вас уже загружена аватарка. Отправьте новое фото, чтобы заменить ее, или пропустите:"
            self.send_message(chat_id, prompt, self.get_step_keyboard(chat_id, STATE_ROSTER_AVATAR))

        elif state == STATE_ROSTER_AVATAR:
            photo = message.get("photo")
            if not is_skip:
                if not photo:
                    self.send_message(chat_id, "⚠️ Вы должны прислать фото/картинку! Пожалуйста, отправьте аватарку как фото:")
                    return
                # Get largest size photo
                file_id = photo[-1]["file_id"]
                self.user_states[chat_id]["data"]["avatar_file_id"] = file_id
            else:
                self.user_states[chat_id]["data"]["avatar_file_id"] = None

            self.user_states[chat_id]["state"] = STATE_ROSTER_ACHIEVEMENTS
            prompt = "Шаг 9: 🏆 Введите ваши *Достижения* (каждое достижение с новой строки, например:\n_Top-1 PMCO 2024_\n_Top-4 PMSL Stage 1_\n_MVP Clan War_):"
            if is_edit:
                current_ach = player.achievements if player else ""
                prompt = f"Текущие достижения:\n{current_ach}\n\nВведите новый список достижений:"
            self.send_message(chat_id, prompt, self.get_step_keyboard(chat_id, STATE_ROSTER_ACHIEVEMENTS))

        elif state == STATE_ROSTER_ACHIEVEMENTS:
            if not is_skip:
                if not text:
                    self.send_message(chat_id, "⚠️ Достижения должны быть текстом! Введите достижения:")
                    return
                self.user_states[chat_id]["data"]["achievements"] = text
            else:
                self.user_states[chat_id]["data"]["achievements"] = player.achievements

            self.user_states[chat_id]["state"] = STATE_ROSTER_REGION
            prompt = "Шаг 10: Укажите ваш *Регион/Страну* (например: Россия, Казахстан, Узбекистан):"
            if is_edit:
                prompt = f"Текущий регион: *{player.region}*\n\nВведите новый регион:"
            self.send_message(chat_id, prompt, self.get_step_keyboard(chat_id, STATE_ROSTER_REGION))

        elif state == STATE_ROSTER_REGION:
            if not is_skip:
                if not text:
                    self.send_message(chat_id, "⚠️ Регион должен быть текстовым сообщением! Укажите регион:")
                    return
                self.user_states[chat_id]["data"]["region"] = text
            else:
                self.user_states[chat_id]["data"]["region"] = player.region

            self.user_states[chat_id]["state"] = STATE_ROSTER_DESCRIPTION
            prompt = "Шаг 11: 📝 Добавьте *Описание/Биографию* о себе (необязательно, нажмите пропустить):"
            if is_edit:
                prompt = f"Текущая биография: *{player.description}*\n\nВведите новое описание профиля:"
            self.send_message(chat_id, prompt, self.get_step_keyboard(chat_id, STATE_ROSTER_DESCRIPTION))

        elif state == STATE_ROSTER_DESCRIPTION:
            if not is_skip:
                self.user_states[chat_id]["data"]["description"] = text if text else ""
            else:
                self.user_states[chat_id]["data"]["description"] = player.description if is_edit else ""

            # Complete registration/update
            self.save_player_profile(chat_id)


        # ----------------------------------------------------------------------
        # HIGHLIGHT UPLOAD FLOW
        # ----------------------------------------------------------------------
        elif state == STATE_HL_TITLE:
            if not text:
                self.send_message(chat_id, "⚠️ Название хайлайта должно быть текстовым сообщением! Введите название:")
                return
            self.user_states[chat_id]["data"]["title"] = text
            self.user_states[chat_id]["state"] = STATE_HL_CATEGORY
            
            # Categorization quick buttons
            buttons = [
                [{"text": "Клатчи"}],
                [{"text": "Снайпинг"}],
                [{"text": "Турниры"}],
                [{"text": "Фрагмуви"}],
                [{"text": "отмена"}]
            ]
            reply_markup = {
                "keyboard": buttons,
                "resize_keyboard": True,
                "one_time_keyboard": True
            }
            self.send_message(chat_id, "Шаг 2: Выберите или введите *Категорию* хайлайта (например: _Клатчи, Снайпинг, Праки, Турниры_):", reply_markup)

        elif state == STATE_HL_CATEGORY:
            if not text:
                self.send_message(chat_id, "⚠️ Категория хайлайта должна быть текстом! Введите категорию:")
                return
            self.user_states[chat_id]["data"]["category"] = text
            self.user_states[chat_id]["state"] = STATE_HL_MEDIA

            # Remove keyboard helper for upload
            reply_markup = {
                "keyboard": [[{"text": "отмена"}]],
                "resize_keyboard": True
            }
            self.send_message(chat_id, "Шаг 3: 🎥 Отправьте *Медиафайл* вашего хайлайта. Это может быть красивое игровое видео или скриншот матча (как сжатый файл, так и обычное видео/фото):", reply_markup)

        elif state == STATE_HL_MEDIA:
            # Check for photo, video, document
            photo = message.get("photo")
            video = message.get("video")
            document = message.get("document")

            file_id = None
            file_name = "media_highlight"
            content_type = ""

            if photo:
                file_id = photo[-1]["file_id"]
                file_name = f"highlight_{chat_id}_{int(time.time())}.jpg"
                content_type = "image/jpeg"
            elif video:
                file_id = video["file_id"]
                file_name = f"highlight_{chat_id}_{int(time.time())}.mp4"
                content_type = "video/mp4"
            elif document:
                # Can be image/video sent as document
                file_id = document["file_id"]
                file_name = document.get("file_name", f"highlight_{chat_id}_{int(time.time())}")
                content_type = document.get("mime_type", "")

            if not file_id:
                self.send_message(chat_id, "⚠️ Вы должны прислать Видео или Фото! Пожалуйста, отправьте медиафайл:")
                return

            self.send_message(chat_id, "📥 Загружаю ваш файл и сохраняю хайлайт... Пожалуйста, подождите, это может занять несколько секунд.")
            self.save_highlight_media(chat_id, file_id, file_name, content_type)

    def save_player_profile(self, chat_id):
        data = self.user_states[chat_id]["data"]
        is_edit = self.user_states[chat_id]["is_edit"]
        
        self.send_message(chat_id, "⏳ Сохранение профиля... Пожалуйста, подождите.")

        try:
            player = Player.objects.filter(telegram_id=chat_id).first()
            
            if is_edit and player:
                player.nickname = data["nickname"]
                player.uid = data["uid"]
                if data["role_id"]:
                    player.role_id = data["role_id"]
                player.device = data["device"]
                player.level = data["level"]
                player.kd = data["kd"]
                player.signature_weapon = data["signature_weapon"]
                player.achievements = data["achievements"]
                player.region = data["region"]
                player.description = data["description"]
                # Profile edited through the bot moves back to moderation (unapproved)
                player.is_approved = False
                player.save()
                verb = "обновлена"
            else:
                role_obj = None
                if data.get("role_id"):
                    role_obj = PlayerRole.objects.get(id=data["role_id"])

                player = Player.objects.create(
                    nickname=data["nickname"],
                    uid=data["uid"],
                    role=role_obj,
                    device=data["device"],
                    level=data["level"],
                    kd=data["kd"],
                    signature_weapon=data["signature_weapon"],
                    achievements=data["achievements"],
                    region=data["region"],
                    description=data["description"],
                    telegram_id=chat_id,
                    is_approved=False,  # Unapproved by default for bot submissions
                    joined_date=timezone.now().strftime("%B %Y")
                )
                verb = "создана"

            # Download and save avatar if uploaded
            avatar_file_id = data.get("avatar_file_id")
            if avatar_file_id:
                # getFile
                file_info = self.send_telegram("getFile", {"file_id": avatar_file_id})
                if file_info.get("ok"):
                    file_path = file_info["result"]["file_path"]
                    download_url = f"https://api.telegram.org/file/bot{self.bot_token}/{file_path}"
                    file_res = requests.get(download_url, timeout=30)
                    if file_res.status_code == 200:
                        file_ext = file_path.split(".")[-1]
                        player.avatar_file.save(f"avatar_{chat_id}.{file_ext}", ContentFile(file_res.content))
                        player.save()

            # Clean state
            self.user_states[chat_id] = {"state": STATE_NONE, "data": {}, "is_edit": False}

            # Send success to user
            self.send_main_menu(
                chat_id, 
                f"🎉 Ваша анкета была успешно {verb}!\n\n"
                f"⏳ Статус: *На модерации администрации*.\n\n"
                f"Мы отправили ее на проверку. Как только администратор примет ее в админ-панели, твой профиль с шикарными характеристиками мгновенно появится в таблице состава на сайте!"
            )

            # Notify Admin Chat if configured
            if self.admin_chat_id:
                admin_msg = (
                    f"🔔 *Уведомление для модератора:*\n\n"
                    f"👤 Игрок *{player.nickname}* {verb} анкету состава через Telegram-бот!\n"
                    f"🆔 PUBG ID: `{player.uid}`\n"
                    f"🎯 Роль: {player.role.name if player.role else 'Без роли'}\n"
                    f"📱 Девайс: {player.device}\n"
                    f"🔥 K/D Ratio: {player.kd} | Уровень: {player.level}\n\n"
                    f"👉 *[НАЖМИТЕ СЮДА ЧТОБЫ ОТКРЫТЬ АДМИН-ПАНЕЛЬ И ОДОБРИТЬ](http://127.0.0.1:8000/admin/api/player/{player.id}/change/)*"
                )
                self.send_message(self.admin_chat_id, admin_msg)

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Ошибка сохранения анкеты: {e}"))
            self.send_main_menu(chat_id, f"❌ Произошла техническая ошибка при сохранении анкеты: {str(e)}. Пожалуйста, попробуйте еще раз.")

    def save_highlight_media(self, chat_id, file_id, file_name, content_type):
        data = self.user_states[chat_id]["data"]

        try:
            player = Player.objects.filter(telegram_id=chat_id).first()
            if not player:
                self.send_main_menu(chat_id, "⚠️ Ошибка: ваш профиль не найден.")
                return

            # getFile from Telegram
            file_info = self.send_telegram("getFile", {"file_id": file_id})
            if not file_info.get("ok"):
                self.send_main_menu(chat_id, "❌ Не удалось получить файл от серверов Telegram. Пожалуйста, попробуйте еще раз.")
                return

            file_path = file_info["result"]["file_path"]
            download_url = f"https://api.telegram.org/file/bot{self.bot_token}/{file_path}"
            file_res = requests.get(download_url, timeout=60)
            if file_res.status_code != 200:
                self.send_main_menu(chat_id, "❌ Не удалось скачать файл. Пожалуйста, попробуйте еще раз.")
                return

            # Create GalleryItem (Highlight)
            hl = GalleryItem.objects.create(
                title=data["title"],
                category=data["category"],
                telegram_id=chat_id,
                is_approved=False,  # Unapproved by default for bot highlights
                author=player.nickname,
                date=timezone.now().strftime("%d.%m.%Y")
            )

            # Save the file
            hl.file_upload.save(file_name, ContentFile(file_res.content))
            hl.tagged_players.add(player)
            hl.save()

            # Clean user state
            self.user_states[chat_id] = {"state": STATE_NONE, "data": {}, "is_edit": False}

            self.send_main_menu(
                chat_id,
                f"🎉 *Хайлайт успешно добавлен!*\n\n"
                f"📺 Название: *{hl.title}*\n"
                f"📂 Категория: *{hl.category}*\n"
                f"⏳ Статус: *На модерации администрации*.\n\n"
                f"Администрация проверит ваш хайлайт в ближайшее время. После одобрения он появится в медиа-галерее сайта!"
            )

            # Notify Admin Chat
            if self.admin_chat_id:
                admin_msg = (
                    f"🎬 *Новый хайлайт на проверку!*\n\n"
                    f"👤 Автор: *{player.nickname}*\n"
                    f"📺 Заголовок: *{hl.title}*\n"
                    f"📂 Категория: {hl.category}\n\n"
                    f"👉 *[НАЖМИТЕ СЮДА ЧТОБЫ ОТКРЫТЬ АДМИН-ПАНЕЛЬ И ОДОБРИТЬ ХАЙЛАЙТ](http://127.0.0.1:8000/admin/api/galleryitem/{hl.id}/change/)*"
                )
                self.send_message(self.admin_chat_id, admin_msg)

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Ошибка сохранения хайлайта: {e}"))
            self.send_main_menu(chat_id, f"❌ Произошла техническая ошибка при сохранении хайлайта: {str(e)}. Пожалуйста, попробуйте еще раз.")
