from django.db import models
from django.utils import timezone

class ClanConfig(models.Model):
    """
    Singleton model to manage general clan settings, hero section titles,
    descriptions, support contacts, and stats numbers dynamically from the admin panel.
    """
    clan_name = models.CharField(max_length=100, default="", verbose_name="Название клана")
    clan_tag = models.CharField(max_length=20, default="", verbose_name="Тэг клана")
    clan_founded = models.CharField(max_length=10, default="", verbose_name="Год основания")
    
    # Hero section
    hero_title_1 = models.CharField(max_length=100, default="", verbose_name="Первая строка заголовка")
    hero_title_2 = models.CharField(max_length=100, default="", verbose_name="Вторая строка заголовка")
    hero_description = models.TextField(
        default="",
        verbose_name="Описание на главной"
    )
    hero_background_type = models.CharField(
        max_length=20, 
        choices=[('image', 'Картинка (Фото)'), ('video', 'Видео')],
        default='video',
        verbose_name="Тип фона на главной"
    )
    hero_background_file = models.FileField(
        upload_to="hero_backgrounds/",
        blank=True,
        null=True,
        verbose_name="Файл фона на главной (mp4 / jpg / png)"
    )
    
    # Support contacts
    discord_link = models.CharField(max_length=255, default="", verbose_name="Ссылка Discord")
    telegram_link = models.CharField(max_length=255, default="", verbose_name="Ссылка Telegram @username")
    
    # Stat 1: Tournaments
    stats_tournaments_title = models.CharField(max_length=50, default="", verbose_name="Статистика 1: Заголовок")
    stats_tournaments_value = models.CharField(max_length=50, default="", verbose_name="Статистика 1: Значение")
    stats_tournaments_desc = models.CharField(max_length=100, default="", verbose_name="Статистика 1: Подпись")
    
    # Stat 2: Rank
    stats_rank_title = models.CharField(max_length=50, default="", verbose_name="Статистика 2: Заголовок")
    stats_rank_value = models.CharField(max_length=50, default="", verbose_name="Статистика 2: Значение")
    stats_rank_desc = models.CharField(max_length=100, default="", verbose_name="Статистика 2: Подпись")
    
    # Stat 3: Members
    stats_members_title = models.CharField(max_length=50, default="", verbose_name="Статистика 3: Заголовок")
    stats_members_value = models.CharField(max_length=50, default="", verbose_name="Статистика 3: Значение")
    stats_members_desc = models.CharField(max_length=100, default="", verbose_name="Статистика 3: Подпись")
    
    # Stat 4: Experience
    stats_experience_title = models.CharField(max_length=50, default="", verbose_name="Статистика 4: Заголовок")
    stats_experience_value = models.CharField(max_length=50, default="", verbose_name="Статистика 4: Значение")
    stats_experience_desc = models.CharField(max_length=100, default="", verbose_name="Статистика 4: Подпись")
    
    # Rules recruitment footer text
    rules_terms_desc = models.TextField(
        default="",
        verbose_name="Сноска в правилах рекрутинга"
    )
    recruitment_image = models.ImageField(
        upload_to="recruitment/",
        blank=True,
        null=True,
        verbose_name="Изображение на форме подачи заявки (PUBG фото)"
    )
    rules_image = models.ImageField(
        upload_to="rules/",
        blank=True,
        null=True,
        verbose_name="Изображение над Уставом/Правилами (PUBG фото)"
    )

    class Meta:
        verbose_name = "Общие настройки сайта"
        verbose_name_plural = "Общие настройки сайта"

    def __str__(self):
        return f"Настройки сайта {self.clan_name}"

    @classmethod
    def get_solo(cls):
        obj, created = cls.objects.get_or_create(id=1)
        return obj


class PlayerRole(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название роли (например: Капитан, Атакующий, Снайпер)")

    class Meta:
        verbose_name = "Роль игрока"
        verbose_name_plural = "Роли игроков"

    def __str__(self):
        return self.name


class HeroBackgroundSlide(models.Model):
    SLIDE_TYPE_CHOICES = [
        ('image', 'Фото (Картинка)'),
        ('video', 'Видео (без звука)'),
    ]
    slide_type = models.CharField(max_length=20, choices=SLIDE_TYPE_CHOICES, default='image', verbose_name="Тип слайда")
    file = models.FileField(upload_to="hero_carousel/", verbose_name="Файл слайда (mp4 / jpg / png / webp)")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок сортировки")

    class Meta:
        verbose_name = "Слайд фона на главной"
        verbose_name_plural = "Карусель фона на главной"
        ordering = ['order', 'id']

    def __str__(self):
        return f"Слайд #{self.id} ({self.get_slide_type_display()})"


class Player(models.Model):
    nickname = models.CharField(max_length=100, verbose_name="Никнейм игрока")
    role = models.ForeignKey(PlayerRole, on_delete=models.CASCADE, verbose_name="Роль игрока", related_name="players", null=True, blank=True)
    device = models.CharField(max_length=150, blank=True, default="", verbose_name="Игровое устройство (необязательно)")
    level = models.PositiveIntegerField(default=1, verbose_name="Уровень аккаунта")
    kd = models.FloatField(blank=True, null=True, verbose_name="K/D Ratio (необязательно)")
    signature_weapon = models.CharField(max_length=150, default="", verbose_name="Любимое оружие")
    
    avatar_file = models.ImageField(upload_to="avatars/", blank=True, null=True, verbose_name="Аватарка игрока (Файл фото)")
    profile_file = models.FileField(upload_to="player_profiles/", blank=True, null=True, verbose_name="Полноэкранное медиа профиля (Файл фото или видео)")
    
    achievements = models.TextField(
        verbose_name="Достижения", 
        help_text="Введите каждое достижение с новой строки"
    )
    region = models.CharField(max_length=150, default="", verbose_name="Регион")
    joined_date = models.CharField(max_length=100, verbose_name="Когда присоединился")
    description = models.TextField(blank=True, default="", verbose_name="Описание игрока (необязательно)")

    class Meta:
        verbose_name = "Игрок (Ростер)"
        verbose_name_plural = "Состав (Ростер)"
        ordering = ['id']

    def __str__(self):
        return f"{self.nickname} ({self.role.name if self.role else 'Без роли'})"

    def get_avatar_url(self):
        if self.avatar_file:
            return self.avatar_file.url
        return ""

    def get_profile_url(self):
        if self.profile_file:
            return self.profile_file.url
        return ""


class PlayerMedia(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="media_gallery", verbose_name="Игрок")
    file = models.FileField(upload_to="player_media/", verbose_name="Файл медиа (Фото или Видео)")

    class Meta:
        verbose_name = "Медиафайл игрока"
        verbose_name_plural = "Дополнительные медиафайлы игрока"

    def __str__(self):
        return f"Медиа для {self.player.nickname} (#{self.id})"


class Announcement(models.Model):
    title = models.CharField(max_length=255, verbose_name="Заголовок объявления")
    type = models.CharField(max_length=100, default='news', verbose_name="Тип объявления", help_text="Например: tournament, training, scrim, news")
    date = models.CharField(max_length=100, default=timezone.now, verbose_name="Дата публикации")
    content = models.TextField(verbose_name="Содержимое (текст)")
    countdown_date = models.DateTimeField(
        blank=True, null=True, 
        verbose_name="Время окончания (для таймера обратного отсчета)",
        help_text="Если указано, на сайте будет тикать таймер"
    )
    author = models.CharField(max_length=100, verbose_name="Автор публикации")
    image_file = models.FileField(upload_to="announcements/", blank=True, null=True, verbose_name="Медиафайл (Фото или Видео)")
    views = models.PositiveIntegerField(default=0, verbose_name="Количество просмотров")

    class Meta:
        verbose_name = "Новость и объявление"
        verbose_name_plural = "Новости и объявления"
        ordering = ['-id']

    def __str__(self):
        return self.title

    def get_image_url(self):
        if self.image_file:
            return self.image_file.url
        return ""


class GalleryItem(models.Model):
    TYPE_CHOICES = [
        ('video', 'Видео-хайлайт'),
        ('screenshot', 'Скриншот матча'),
        ('trophy', 'Кубок / Награда'),
    ]
    type = models.CharField(max_length=100, choices=TYPE_CHOICES, default='screenshot', verbose_name="Тип медиа")
    title = models.CharField(max_length=255, verbose_name="Название")
    category = models.CharField(max_length=100, default="", verbose_name="Категория")
    
    file_upload = models.FileField(upload_to="gallery/", blank=True, null=True, verbose_name="Загрузить медиафайл напрямую")
    thumbnail_upload = models.ImageField(upload_to="gallery/thumbs/", blank=True, null=True, verbose_name="Загрузить файл обложки")
    description = models.TextField(blank=True, null=True, verbose_name="Описание хайлайта (необязательное)")
    tagged_players = models.ManyToManyField('Player', blank=True, related_name="gallery_items", verbose_name="Отмеченные участники клана")
    views = models.PositiveIntegerField(default=0, verbose_name="Просмотры")
    likes = models.PositiveIntegerField(default=0, verbose_name="Лайки")
    date = models.CharField(max_length=100, blank=True, default="", verbose_name="Дата добавления")
    author = models.CharField(max_length=100, blank=True, default="Администрация", verbose_name="Кто загрузил")

    class Meta:
        verbose_name = "Элемент галереи"
        verbose_name_plural = "Галерея медиа"
        ordering = ['-id']

    def __str__(self):
        return f"{self.type}: {self.title}"

    def get_file_url(self):
        if self.file_upload:
            return self.file_upload.url
        return ""

    def get_thumbnail_url(self):
        if self.thumbnail_upload:
            return self.thumbnail_upload.url
        return ""

    def save(self, *args, **kwargs):
        if not self.date:
            self.date = timezone.now().strftime("%d.%m.%Y")
        if self.file_upload:
            name = self.file_upload.name.lower()
            if name.endswith(('.mp4', '.mov', '.avi', '.webm')):
                self.type = 'video'
            elif name.endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                self.type = 'screenshot'
        super().save(*args, **kwargs)


class ScheduleEvent(models.Model):
    title = models.CharField(max_length=255, verbose_name="Название события")
    type = models.CharField(max_length=100, default='scrim', verbose_name="Тип события", help_text="Например: scrim, training, tournament, meeting и т.д.")
    datetime = models.DateTimeField(verbose_name="Дата и время проведения (UTC)")
    team_size = models.CharField(max_length=100, default="", verbose_name="Тип игры / Формат сбора")
    prize_pool = models.CharField(max_length=150, blank=True, null=True, verbose_name="Призовой фонд (необязательно)")
    slots_filled = models.PositiveIntegerField(default=0, verbose_name="Заполнено слотов / участников")
    slots_total = models.PositiveIntegerField(default=16, verbose_name="Всего слотов / участников")
    opponent = models.CharField(max_length=200, blank=True, null=True, verbose_name="Противник (необязательно)")

    class Meta:
        verbose_name = "Событие расписания"
        verbose_name_plural = "Расписание событий"
        ordering = ['datetime']

    def __str__(self):
        return f"[{self.type}] {self.title}"


class ClanRule(models.Model):
    SEVERITY_CHOICES = [
        ('low', 'Низкая (Предупреждение)'),
        ('medium', 'Средняя (Выговор)'),
        ('high', 'Высокая (Исключение)'),
    ]
    category = models.CharField(max_length=100, default="", verbose_name="Раздел / Категория")
    title = models.CharField(max_length=255, verbose_name="Название правила")
    content = models.TextField(verbose_name="Содержание правила")
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='medium', verbose_name="Важность нарушения")

    class Meta:
        verbose_name = "Правило клана"
        verbose_name_plural = "Свод правил клана"
        ordering = ['id']

    def __str__(self):
        return self.title


class RecruitmentSubmission(models.Model):
    nickname = models.CharField(max_length=100, verbose_name="Никнейм")
    game_id = models.CharField(max_length=100, verbose_name="PUBG ID")
    role = models.CharField(max_length=100, verbose_name="Игровая роль")
    device = models.CharField(max_length=150, verbose_name="Игровое устройство")
    age = models.PositiveIntegerField(verbose_name="Возраст")
    play_time = models.PositiveIntegerField(verbose_name="Часов в игре в день")
    discord_telegram = models.CharField(max_length=200, verbose_name="Discord / Telegram")
    about = models.TextField(blank=True, null=True, verbose_name="О себе / Опыт")
    assessment_grade = models.CharField(
        max_length=50, 
        choices=[
            ('unqualified', 'Резерв (Отказ)'),
            ('accepted_with_test', 'Допущен к дуэли (1v1 тест)'),
            ('excellent', 'Высокий приоритет (PRO)')
        ],
        verbose_name="Автоматический статус отбора"
    )
    stat_photo_1 = models.ImageField(upload_to="recruits_stats/", blank=True, null=True, verbose_name="Фото статистики 1")
    stat_photo_2 = models.ImageField(upload_to="recruits_stats/", blank=True, null=True, verbose_name="Фото статистики 2")
    stat_photo_3 = models.ImageField(upload_to="recruits_stats/", blank=True, null=True, verbose_name="Фото статистики 3")
    stat_photo_4 = models.ImageField(upload_to="recruits_stats/", blank=True, null=True, verbose_name="Фото статистики 4")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Время отправки")

    class Meta:
        verbose_name = "Заявка на вступление"
        verbose_name_plural = "Заявки на вступление (Рекруты)"
        ordering = ['-created_at']

    def __str__(self):
        return f"Заявка #{self.id}: {self.nickname} ({self.assessment_grade})"
