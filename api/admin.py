from django.contrib import admin
from django.utils.html import format_html
from .models import ClanConfig, Player, PlayerRole, HeroBackgroundSlide, Announcement, GalleryItem, ScheduleEvent, ClanRule, RecruitmentSubmission

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


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ('nickname_preview', 'role', 'level', 'signature_weapon', 'region', 'joined_date')
    list_filter = ('role', 'region')
    search_fields = ('nickname', 'device', 'signature_weapon', 'achievements')
    list_editable = ('level',)
    
    fieldsets = (
        ('Игровой профиль', {
            'fields': ('nickname', 'role', 'level', 'kd', 'signature_weapon')
        }),
        ('Аватар и Медиа профиля', {
            'fields': ('avatar_file', 'profile_file')
        }),
        ('Остальные сведения', {
            'fields': ('achievements', 'region', 'joined_date')
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
    list_display = ('title', 'type', 'category', 'date', 'author')
    list_filter = ('type', 'category', 'date')
    search_fields = ('title', 'category', 'author')
    list_editable = ('category',)
    filter_horizontal = ('tagged_players',)
    
    fieldsets = (
        ('Основное', {
            'fields': ('title', 'category', 'description', 'tagged_players')
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
        return format_html(html)
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
