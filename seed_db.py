import os
import django
import requests
from django.utils import timezone
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clan_backend.settings')
django.setup()

from api.models import ClanConfig, Player, PlayerRole, HeroBackgroundSlide, Announcement, GalleryItem, ScheduleEvent, ClanRule, RecruitmentSubmission

print("Starting database seeding for Interstellar...")

MEDIA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'media')
os.makedirs(MEDIA_DIR, exist_ok=True)

def download_file(url, relative_path):
    local_path = os.path.join(MEDIA_DIR, relative_path)
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    try:
        print(f"Downloading {url} -> {relative_path}...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30, stream=True)
        response.raise_for_status()
        with open(local_path, 'wb') as out_file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    out_file.write(chunk)
        print("Success!")
        return relative_path
    except Exception as e:
        print(f"Failed to download {url}: {e}")
        return None

# 1. Download PUBG & Cyber Gaming assets into local media directory using requests
bg_file = download_file(
    "https://www.w3schools.com/html/mov_bbb.mp4",
    "hero_backgrounds/background.mp4"
)
av_reaper = download_file(
    "https://images.unsplash.com/photo-1542751371-adc38448a05e?w=800&auto=format&fit=crop&q=80",
    "avatars/reaper.jpg"
)
av_apex = download_file(
    "https://images.unsplash.com/photo-1538481199705-c710c4e965fc?w=800&auto=format&fit=crop&q=80",
    "avatars/apex.jpg"
)
av_vortex = download_file(
    "https://images.unsplash.com/photo-1511512578047-dfb367046420?w=800&auto=format&fit=crop&q=80",
    "avatars/vortex.jpg"
)
ann_recruit = download_file(
    "https://images.unsplash.com/photo-1607604276583-eef5d076aa5f?w=800&auto=format&fit=crop&q=80",
    "announcements/recruitment.jpg"
)
ann_victory = download_file(
    "https://images.unsplash.com/photo-1560253023-3ec5d502959f?w=800&auto=format&fit=crop&q=80",
    "announcements/victory.jpg"
)
gal_vid = download_file(
    "https://www.w3schools.com/html/movie.mp4",
    "gallery/highlight.mp4"
)
gal_ss1 = download_file(
    "https://images.unsplash.com/photo-1542751371-adc38448a05e?w=800&auto=format&fit=crop&q=80",
    "gallery/miramar.jpg"
)
gal_ss2 = download_file(
    "https://images.unsplash.com/photo-1553481187-be93c21490a9?w=800&auto=format&fit=crop&q=80",
    "gallery/erangel.jpg"
)
gal_trophy = download_file(
    "https://images.unsplash.com/photo-1578269174936-2709b5a5e06e?w=800&auto=format&fit=crop&q=80",
    "gallery/trophy.jpg"
)

# Clear existing database records
Player.objects.all().delete()
PlayerRole.objects.all().delete()
HeroBackgroundSlide.objects.all().delete()
Announcement.objects.all().delete()
GalleryItem.objects.all().delete()
ScheduleEvent.objects.all().delete()
ClanRule.objects.all().delete()
RecruitmentSubmission.objects.all().delete()
ClanConfig.objects.all().delete()

# Seed dynamic roles
role_mgmt = PlayerRole.objects.create(name="Руководство / Менеджмент")
role_attack = PlayerRole.objects.create(name="А-Сквад (Атака)")
role_tactics = PlayerRole.objects.create(name="Тактики (Снайперы/Скауты)")

# Seed background slides for hero section
if bg_file:
    HeroBackgroundSlide.objects.create(slide_type="video", file=bg_file, order=1)
if av_apex:
    HeroBackgroundSlide.objects.create(slide_type="image", file=av_apex, order=2)
if av_vortex:
    HeroBackgroundSlide.objects.create(slide_type="image", file=av_vortex, order=3)

# 2. Populate ClanConfig
config = ClanConfig.get_solo()
config.clan_name = "Interstellar"
config.clan_tag = "Inter"
config.clan_founded = "2026"
config.hero_title_1 = "МЫ — ВЕРШИНА"
config.hero_title_2 = "ИНТЕРСТЕЛЛАР"
config.hero_description = "Профессиональная мобильная киберспортивная команда PUBG Mobile. Стремимся к победам и доминированию в СНГ регионе."
config.discord_link = "https://discord.gg/interstellar"
config.telegram_link = "https://t.me/interstellar_pubg"
config.hero_background_type = "video"
if bg_file:
    config.hero_background_file = bg_file

config.stats_tournaments_title = "ТУРНИРЫ"
config.stats_tournaments_value = "34+ ПОБЕД"
config.stats_tournaments_desc = "Золото в СНГ киберлигах"

config.stats_rank_title = "РЕЙТИНГ"
config.stats_rank_value = "TOP-10"
config.stats_rank_desc = "Официальный CIS Cup"

config.stats_members_title = "СОСТАВ"
config.stats_members_value = "15+ PRO"
config.stats_members_desc = "Дисциплинированные игроки"

config.stats_experience_title = "ПРАКИ"
config.stats_experience_value = "20+ ЕЖЕНЕДЕЛЬНО"
config.stats_experience_desc = "Постоянная подготовка"
config.save()

# 3. Populate Players with local downloaded file assets
p1 = Player.objects.create(
    nickname="Inter・REAPER",
    role=role_mgmt,
    device="iPad Pro M2",
    level=82,
    kd=6.5,
    signature_weapon="M416",
    avatar_file=av_reaper if av_reaper else None,
    profile_file=bg_file if bg_file else None,  # Video profile demonstration!
    achievements="Капитан сквада\nMVP CIS Cup\nТоп-3 Снайпер",
    region="CIS",
    joined_date="Май 2026"
)

p2 = Player.objects.create(
    nickname="Inter・APEX",
    role=role_tactics,
    device="iPhone 15 Pro Max",
    level=78,
    kd=5.8,
    signature_weapon="AWM",
    avatar_file=av_apex if av_apex else None,
    profile_file=av_apex if av_apex else None,
    achievements="Основной снайпер\nЛучший AIM сезона",
    region="CIS",
    joined_date="Май 2026"
)

p3 = Player.objects.create(
    nickname="Inter・VORTEX",
    role=role_attack,
    device="ROG Phone 8",
    level=76,
    kd=6.2,
    signature_weapon="AKM",
    avatar_file=av_vortex if av_vortex else None,
    profile_file=av_vortex if av_vortex else None,
    achievements="Штурмовик основы\n500+ матчей",
    region="CIS",
    joined_date="Май 2026"
)

# 4. Populate Announcements with local uploaded files
Announcement.objects.create(
    title="Набор в резервный состав открыт",
    type="news",
    content="Мы рады сообщить об открытии набора в наш резервный сквад. Подайте заявку на сайте, пройдите отбор и заберите свой шанс играть под флагом Interstellar!",
    author="Admin",
    image_file=ann_recruit if ann_recruit else None
)

Announcement.objects.create(
    title="Победа на турнире CIS ELITE",
    type="tournament",
    content="Команда Interstellar забрала золото на турнире CIS ELITE с призовым фондом в $5,000! Спасибо всем болельщикам за безумную поддержку в чатах!",
    author="Management",
    image_file=ann_victory if ann_victory else None
)

# 5. Populate ScheduleEvents
now = timezone.now()
ScheduleEvent.objects.create(
    title="Clan War vs Elite Squad",
    type="scrim",
    datetime=now + timedelta(days=1),
    team_size="Squad 4x4",
    slots_filled=4,
    slots_total=4,
    opponent="Elite Squad"
)

ScheduleEvent.objects.create(
    title="Разбор тактик: Эрангель",
    type="training",
    datetime=now + timedelta(days=2),
    team_size="Весь Клан",
    slots_filled=12,
    slots_total=15
)

# 6. Populate ClanRules
ClanRule.objects.create(
    category="Общие правила",
    title="Уважение и Дисциплина",
    content="Оскорбление тиммейтов, токсичное поведение на праках и в дискорде строго запрещены. Наказание - мгновенное исключение из организации.",
    severity="high"
)

ClanRule.objects.create(
    category="Тренировки",
    title="Посещение праков",
    content="Обязательное присутствие на запланированных тренировочных матчах. Предупреждать об отсутствии минимум за 2 часа.",
    severity="medium"
)

ClanRule.objects.create(
    category="Состав",
    title="Смена игрового никнейма",
    content="Все участники обязаны сменить игровой никнейм на ник с префиксом Inter・ в течение 7 дней с момента принятия.",
    severity="high"
)

# 7. Populate GalleryItems with descriptions and tagged players
if gal_vid:
    gi1 = GalleryItem.objects.create(
        title="Безумный сквадвайп 1v4 на Эрангеле",
        category="Матчи / Хайлайты",
        file_upload=gal_vid,
        thumbnail_upload=av_reaper if av_reaper else None,
        description="Клатч-момент нашего капитана REAPER на турнире CIS Cup, спасший раунд.",
        views=1420,
        likes=385
    )
    gi1.tagged_players.add(p1)

if gal_ss1:
    gi2 = GalleryItem.objects.create(
        title="Снайперская дуэль в Мирамаре",
        category="Скриншоты",
        file_upload=gal_ss1,
        thumbnail_upload=gal_ss1,
        description="Точный выстрел с AWM на расстоянии 450 метров.",
        views=620,
        likes=110
    )
    gi2.tagged_players.add(p2)

if gal_ss2:
    gi3 = GalleryItem.objects.create(
        title="Победный ужин (Winner Winner Chicken Dinner)",
        category="Скриншоты",
        file_upload=gal_ss2,
        thumbnail_upload=gal_ss2,
        description="Квалификационная игра, принесшая нам первое место.",
        views=850,
        likes=192
    )
    gi3.tagged_players.add(p1, p2, p3)

if gal_trophy:
    gi4 = GalleryItem.objects.create(
        title="Кубок чемпионов CIS Mobile Cup 2026",
        category="Награды / Трофеи",
        file_upload=gal_trophy,
        thumbnail_upload=gal_trophy,
        description="Наш главный трофей в этом сезоне!",
        views=3100,
        likes=940
    )

print("Seeding completed successfully!")
