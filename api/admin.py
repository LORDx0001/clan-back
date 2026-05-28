from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import ClanConfig, Player, PlayerRole, HeroBackgroundSlide, Announcement, GalleryItem, ScheduleEvent, ClanRule, RecruitmentSubmission, PlayerMedia

# Unregister standard User model to register our customized one
admin.site.unregister(User)

class PlayerInline(admin.StackedInline):
    model = Player
    can_delete = False
    verbose_name = "Карточка игрока"
    verbose_name_plural = "Связанная карточка игрока (Профиль)"
    fk_name = 'user'
    extra = 0
    fieldsets = (
        ('Связь с сайтом и Telegram', {
            'fields': ('is_approved', 'telegram_id', 'order')
        }),
        ('Игровые данные профиля', {
            'fields': ('nickname', 'uid', 'clan_role', 'role', 'level', 'kd', 'signature_weapon', 'device', 'region', 'joined_date')
        }),
        ('Медиафайлы профиля', {
            'fields': ('avatar_file', 'profile_file')
        }),
        ('Сведения и Достижения', {
            'fields': ('achievements', 'description')
        }),
    )

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = (PlayerInline,)
    list_display = ('username', 'is_active_badge', 'telegram_id_badge', 'player_approved_badge', 'date_joined')
    list_select_related = ('player_profile',)
    ordering = ('-date_joined',)

    def is_active_badge(self, obj):
        color = '#10b981' if obj.is_active else '#ef4444'
        text = 'Разрешен' if obj.is_active else 'Заблокирован'
        return format_html(
            '<span style="background-color: {}; color: #fff; padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: bold; text-transform: uppercase;">{}</span>',
            color, text
        )
    is_active_badge.short_description = 'Вход на сайт'

    def telegram_id_badge(self, obj):
        p = getattr(obj, 'player_profile', None)
        if p and p.telegram_id:
            return format_html('<code style="font-size: 12px; font-weight: bold;">{}</code>', p.telegram_id)
        return "Не привязан к TG"
    telegram_id_badge.short_description = 'Telegram ID'

    def player_approved_badge(self, obj):
        p = getattr(obj, 'player_profile', None)
        if p:
            color = '#10b981' if p.is_approved else '#f59e0b'
            text = 'Одобрена (Виден)' if p.is_approved else 'На модерации (Скрыт)'
            return format_html(
                '<span style="background-color: {}; color: #fff; padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: bold; text-transform: uppercase;">{}</span>',
                color, text
            )
        return "Нет карточки"
    player_approved_badge.short_description = 'Статус карточки'


@admin.register(PlayerRole)
class PlayerRoleAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

@admin.register(HeroBackgroundSlide)
class HeroBackgroundSlideAdmin(admin.ModelAdmin):
    list_display = ('id', 'slide_type', 'file', 'order')
    list_editable = ('order',)
    list_filter = ('slide_type',)

# We prevent creating additional configs to maintain the singleton nature of ClanConfig
@admin.register(ClanConfig)
class ClanConfigAdmin(admin.ModelAdmin):
    list_display = ('clan_name', 'clan_tag', 'clan_founded', 'discord_link', 'telegram_link')
    
    fieldsets = (
        ('Главная информация о Клане', {
            'fields': ('clan_name', 'clan_tag', 'clan_founded')
        }),
        ('Настройки баннера (Hero)', {
            'fields': ('hero_title_1', 'hero_title_2', 'hero_description', 'hero_background_type', 'hero_background_file')
        }),
        ('Контакты и Соцсети', {
            'fields': ('discord_link', 'telegram_link')
        }),
        ('Статистика 1 (Кубки/Турниры)', {
            'fields': ('stats_tournaments_title', 'stats_tournaments_value', 'stats_tournaments_desc')
        }),
        ('Статистика 2 (Ранг)', {
            'fields': ('stats_rank_title', 'stats_rank_value', 'stats_rank_desc')
        }),
        ('Статистика 3 (Участники)', {
            'fields': ('stats_members_title', 'stats_members_value', 'stats_members_desc')
        }),
        ('Статистика 4 (Праки/Опыт)', {
            'fields': ('stats_experience_title', 'stats_experience_value', 'stats_experience_desc')
        }),
        ('Дополнительно', {
            'fields': ('rules_terms_desc', 'recruitment_image')
        }),
    )

    def has_add_permission(self, request):
        # Allow only 1 row of configuration
        return not ClanConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


class PlayerMediaInline(admin.TabularInline):
    model = PlayerMedia
    extra = 2
    verbose_name = "Медиафайл игрока"
    verbose_name_plural = "Дополнительные фотографии и видео игрока"


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ('order', 'nickname_preview', 'user', 'is_approved', 'clan_role', 'role', 'level', 'signature_weapon', 'region', 'joined_date')
    list_display_links = ('nickname_preview',)
    list_filter = ('is_approved', 'clan_role', 'role', 'region')
    search_fields = ('nickname', 'device', 'signature_weapon', 'achievements')
    list_editable = ('order', 'level', 'is_approved')
    inlines = [PlayerMediaInline]
    
    fieldsets = (
        ('Игровой профиль', {
            'fields': ('user', 'order', 'nickname', 'uid', 'clan_role', 'role', 'level', 'kd', 'signature_weapon', 'device', 'telegram_id', 'is_approved')
        }),
        ('Фото профиля (Аватар)', {
            'fields': ('avatar_file',)
        }),
        ('Остальные сведения', {
            'fields': ('achievements', 'region', 'joined_date', 'description')
        }),
    )

    def nickname_preview(self, obj):
        avatar_url = obj.get_avatar_url()
        if not avatar_url:
            return obj.nickname
        return format_html(
            '<div style="display: flex; align-items: center; gap: 8px;">'
            '<img src="{}" style="width: 32px; height: 32px; border-radius: 50%; object-fit: cover;" />'
            '<strong>{}</strong>'
            '</div>',
            avatar_url, obj.nickname
        )
    nickname_preview.short_description = 'Игрок'


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'date', 'author')
    list_filter = ('type', 'date')
    search_fields = ('title', 'content', 'author')
    
    fieldsets = (
        ('Контент', {
            'fields': ('title', 'type', 'content', 'author')
        }),
        ('Медиафайл (Фото или Видео)', {
            'fields': ('image_file',)
        }),
    )


@admin.register(GalleryItem)
class GalleryItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_approved', 'type', 'category', 'date', 'author')
    list_filter = ('is_approved', 'type', 'category', 'date')
    search_fields = ('title', 'category', 'author')
    list_editable = ('category', 'is_approved')
    filter_horizontal = ('tagged_players',)
    
    fieldsets = (
        ('Основное', {
            'fields': ('title', 'category', 'description', 'tagged_players', 'telegram_id', 'is_approved')
        }),
        ('Медиафайлы (Видео / Картинки)', {
            'fields': ('file_upload', 'thumbnail_upload')
        }),
    )


@admin.register(ScheduleEvent)
class ScheduleEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'datetime', 'team_size', 'prize_pool', 'slots_display', 'opponent')
    list_filter = ('type', 'datetime')
    search_fields = ('title', 'opponent')
    list_editable = ('team_size', 'prize_pool')

    def slots_display(self, obj):
        return f"{obj.slots_filled} / {obj.slots_total}"
    slots_display.short_description = 'Слоты (Участники)'


@admin.register(ClanRule)
class ClanRuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'severity_badge')
    list_filter = ('category', 'severity')
    search_fields = ('title', 'content', 'category')
    list_editable = ('category',)

    def severity_badge(self, obj):
        colors = {
            'high': '#ff4d4d',
            'medium': '#ff9900',
            'low': '#33cc33'
        }
        labels = {
            'high': 'Критическое (Исключение)',
            'medium': 'Важно (Выговор)',
            'low': 'Тактическое (Предупреждение)'
        }
        return format_html(
            '<span style="background-color: {}; color: #fff; padding: 3px 8px; border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            colors.get(obj.severity, '#999'), labels.get(obj.severity, obj.severity)
        )
    severity_badge.short_description = 'Наказание / Серьезность'


@admin.register(RecruitmentSubmission)
class RecruitmentSubmissionAdmin(admin.ModelAdmin):
    list_display = ('nickname', 'role', 'device', 'age', 'play_time', 'discord_telegram', 'grade_badge', 'created_at')
    list_filter = ('assessment_grade', 'role', 'created_at')
    search_fields = ('nickname', 'game_id', 'discord_telegram', 'about')
    readonly_fields = ('nickname', 'game_id', 'role', 'device', 'age', 'play_time', 'discord_telegram', 'about', 'assessment_grade', 'created_at', 'stat_photos_preview')

    fieldsets = (
        ('Анкета кандидата', {
            'fields': ('nickname', 'game_id', 'role', 'device', 'age', 'play_time', 'discord_telegram', 'about', 'assessment_grade', 'created_at')
        }),
        ('Фотографии статистики (3-4 шт)', {
            'fields': ('stat_photos_preview',)
        }),
    )

    def stat_photos_preview(self, obj):
        html = '<div style="display: flex; gap: 15px; flex-wrap: wrap;">'
        photos = [obj.stat_photo_1, obj.stat_photo_2, obj.stat_photo_3, obj.stat_photo_4]
        found = False
        for i, photo in enumerate(photos, 1):
            if photo:
                found = True
                html += f'<div style="text-align: center;"><a href="{photo.url}" target="_blank"><img src="{photo.url}" style="max-width: 220px; max-height: 220px; border: 1px solid #ddd; border-radius: 4px; display: block; margin-bottom: 5px;" /></a><span style="font-size: 11px; color: #666;">Скриншот #{i}</span></div>'
        if not found:
            return "Скриншоты статистики не прикреплены"
        html += '</div>'
        return mark_safe(html)
    stat_photos_preview.short_description = 'Скриншоты статистики'

    def grade_badge(self, obj):
        colors = {
            'excellent': '#a855f7',       # purple
            'accepted_with_test': '#eab308', # orange/yellow
            'unqualified': '#ef4444'        # red
        }
        return format_html(
            '<span style="background-color: {}; color: #fff; padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: bold; text-transform: uppercase;">{}</span>',
            colors.get(obj.assessment_grade, '#999'), obj.get_assessment_grade_display()
        )
    grade_badge.short_description = 'Статус заявки'

    def has_add_permission(self, request):
        return False  # submissions come only from frontend API
