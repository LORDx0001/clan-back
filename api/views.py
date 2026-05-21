import os
import json
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from django.utils import timezone
from .models import ClanConfig, Player, PlayerRole, HeroBackgroundSlide, Announcement, GalleryItem, ScheduleEvent, ClanRule, RecruitmentSubmission

def get_absolute_media_url(request, path_or_url):
    """
    Helper to return absolute URL for local files uploaded,
    otherwise leaves remote HTTP links untouched.
    """
    if not path_or_url:
        return ""
    if path_or_url.startswith("http://") or path_or_url.startswith("https://") or path_or_url.startswith("//"):
        return path_or_url
    return request.build_absolute_uri(path_or_url)


@require_GET
def clan_config_api(request):
    """
    Returns general site configurations, stats, contacts.
    """
    config = ClanConfig.get_solo()
    slides = HeroBackgroundSlide.objects.all()
    slides_data = []
    for s in slides:
        slides_data.append({
            "type": s.slide_type,
            "url": get_absolute_media_url(request, s.file.url if s.file else "")
        })

    data = {
        "clanName": config.clan_name,
        "clanTag": config.clan_tag,
        "clanFounded": config.clan_founded,
        "heroTitle1": config.hero_title_1,
        "heroTitle2": config.hero_title_2,
        "heroDescription": config.hero_description,
        "heroBackgroundType": config.hero_background_type,
        "heroBackgroundFileUrl": get_absolute_media_url(request, config.hero_background_file.url if config.hero_background_file else ""),
        "heroSlides": slides_data,
        "discordLink": config.discord_link,
        "telegramLink": config.telegram_link,
        
        # Stats
        "stats": [
            {
                "title": config.stats_tournaments_title,
                "value": config.stats_tournaments_value,
                "desc": config.stats_tournaments_desc
            },
            {
                "title": config.stats_rank_title,
                "value": config.stats_rank_value,
                "desc": config.stats_rank_desc
            },
            {
                "title": config.stats_members_title,
                "value": config.stats_members_value,
                "desc": config.stats_members_desc
            },
            {
                "title": config.stats_experience_title,
                "value": config.stats_experience_value,
                "desc": config.stats_experience_desc
            }
        ],
        "rulesTermsDesc": config.rules_terms_desc,
        "recruitmentImageUrl": get_absolute_media_url(request, config.recruitment_image.url if config.recruitment_image else "")
    }
    return JsonResponse(data, safe=False, json_dumps_params={'ensure_ascii': False})


@require_GET
def players_list_api(request):
    """
    Returns list of roster players.
    """
    players = Player.objects.all()
    data = []
    for p in players:
        avatar_url = get_absolute_media_url(request, p.get_avatar_url())
        profile_url = get_absolute_media_url(request, p.get_profile_url())
        achievements_list = [line.strip() for line in p.achievements.split('\n') if line.strip()]
        
        player_dict = {
            "id": str(p.id),
            "nickname": p.nickname,
            "role": p.role.name if p.role else "",
            "device": p.device,
            "level": p.level,
            "signatureWeapon": p.signature_weapon,
            "avatar": avatar_url,
            "profileMedia": profile_url,
            "achievements": achievements_list,
            "region": p.region,
            "joinedDate": p.joined_date
        }
        if p.kd is not None:
            player_dict["kd"] = p.kd
        data.append(player_dict)
        
    return JsonResponse(data, safe=False, json_dumps_params={'ensure_ascii': False})


@require_GET
def announcements_list_api(request):
    """
    Returns news and tournament announcements.
    """
    anns = Announcement.objects.all()
    data = []
    for a in anns:
        img_url = get_absolute_media_url(request, a.get_image_url())
        
        ann_dict = {
            "id": str(a.id),
            "title": a.title,
            "type": a.type,
            "date": a.date,
            "content": a.content,
            "author": a.author,
            "imageUrl": img_url,
            "views": a.views
        }
        if a.countdown_date:
            ann_dict["countdownDate"] = a.countdown_date.isoformat()
            
        data.append(ann_dict)
        
    return JsonResponse(data, safe=False, json_dumps_params={'ensure_ascii': False})


@require_GET
def schedule_list_api(request):
    """
    Returns gaming events schedule.
    """
    events = ScheduleEvent.objects.all()
    data = []
    for e in events:
        evt_dict = {
            "id": str(e.id),
            "title": e.title,
            "type": e.type,
            "datetime": e.datetime.isoformat(),
            "teamSize": e.team_size,
            "slotsFilled": e.slots_filled,
            "slotsTotal": e.slots_total
        }
        if e.prize_pool:
            evt_dict["prizePool"] = e.prize_pool
        if e.opponent:
            evt_dict["opponent"] = e.opponent
            
        data.append(evt_dict)
        
    return JsonResponse(data, safe=False, json_dumps_params={'ensure_ascii': False})


@require_GET
def rules_list_api(request):
    """
    Returns swaths of clan laws and regulations.
    """
    rules = ClanRule.objects.all()
    data = []
    for r in rules:
        data.append({
            "id": str(r.id),
            "category": r.category,
            "title": r.title,
            "content": r.content,
            "severity": r.severity
        })
    return JsonResponse(data, safe=False, json_dumps_params={'ensure_ascii': False})


@require_GET
def gallery_list_api(request):
    """
    Returns media screenshots, videos, and award cups.
    """
    items = GalleryItem.objects.all()
    data = []
    for item in items:
        file_url = get_absolute_media_url(request, item.get_file_url())
        thumb_url = get_absolute_media_url(request, item.get_thumbnail_url())
        
        data.append({
            "id": str(item.id),
            "type": item.type,
            "title": item.title,
            "category": item.category,
            "fileUrl": file_url,
            "thumbnail": thumb_url,
            "description": item.description or "",
            "taggedPlayers": [{"id": str(p.id), "nickname": p.nickname} for p in item.tagged_players.all()],
            "views": item.views,
            "likes": item.likes,
            "date": item.date,
            "author": item.author
        })
    return JsonResponse(data, safe=False, json_dumps_params={'ensure_ascii': False})


@csrf_exempt
@require_POST
def submit_recruitment_api(request):
    """
    Submits a recruit form, automatically grades, records in DB, returns grade status.
    Supports both JSON payloads and multipart/form-data with 3-4 stats photos.
    Sends full stats and files directly to Telegram Bot as a beautiful grouped media group.
    """
    try:
        # Check if content type is multipart/form-data
        if request.content_type and request.content_type.startswith('multipart/form-data'):
            nickname = request.POST.get('nickname', '').strip()
            game_id = str(request.POST.get('gameId', '')).strip()
            role = request.POST.get('role', 'Assaulter')
            device = request.POST.get('device', '').strip()
            age = int(request.POST.get('age', 18))
            play_time = int(request.POST.get('playTime', 4))
            discord_telegram = request.POST.get('discordTelegram', '').strip()
            about = request.POST.get('about', '').strip()
        else:
            data = json.loads(request.body)
            nickname = data.get('nickname', '').strip()
            game_id = str(data.get('gameId', '')).strip()
            role = data.get('role', 'Assaulter')
            device = data.get('device', '').strip()
            age = int(data.get('age', 18))
            play_time = int(data.get('playTime', 4))
            discord_telegram = data.get('discordTelegram', '').strip()
            about = data.get('about', '').strip()
            
        if not nickname or not game_id or not discord_telegram:
            return JsonResponse({"error": "Никнейм, PUBG ID и Контакт обязательны для заполнения!"}, status=400)
            
        # Automatic Gaming Profile Scoring Algorithm
        if play_time >= 6 and age >= 16:
            assessment_grade = 'excellent'
        elif age < 15:
            assessment_grade = 'unqualified'
        else:
            assessment_grade = 'accepted_with_test'
            
        # Get uploaded stat photos
        stat_photo_1 = request.FILES.get('stat_photo_1')
        stat_photo_2 = request.FILES.get('stat_photo_2')
        stat_photo_3 = request.FILES.get('stat_photo_3')
        stat_photo_4 = request.FILES.get('stat_photo_4')
            
        # Save to database
        submission = RecruitmentSubmission.objects.create(
            nickname=nickname,
            game_id=game_id,
            role=role,
            device=device,
            age=age,
            play_time=play_time,
            discord_telegram=discord_telegram,
            about=about,
            assessment_grade=assessment_grade,
            stat_photo_1=stat_photo_1,
            stat_photo_2=stat_photo_2,
            stat_photo_3=stat_photo_3,
            stat_photo_4=stat_photo_4
        )
        
        # Telegram notification
        bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        chat_id = os.environ.get('TELEGRAM_CHAT_ID')
        if bot_token and chat_id:
            try:
                # 1. Send text message
                msg = (
                    f"🔥 *Новая заявка в клан!*\n\n"
                    f"👤 *Никнейм:* {nickname}\n"
                    f"🆔 *PUBG ID:* {game_id}\n"
                    f"🎯 *Роль:* {role}\n"
                    f"📱 *Устройство:* {device}\n"
                    f"🎂 *Возраст:* {age}\n"
                    f"⏱ *Часов в день:* {play_time}\n"
                    f"💬 *Связь:* {discord_telegram}\n"
                    f"📊 *Статус скоринга:* {assessment_grade}\n"
                    f"📝 *О себе:* {about}"
                )
                requests.post(
                    f"https://api.telegram.org/bot{bot_token}/sendMessage",
                    data={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"},
                    timeout=5
                )

                # 2. Collect files and send as a Media Group (Album)
                media_files = {}
                media_group = []
                photos_list = [stat_photo_1, stat_photo_2, stat_photo_3, stat_photo_4]
                file_index = 0
                for photo in photos_list:
                    if photo:
                        photo.seek(0)
                        file_key = f"photo_{file_index}"
                        media_files[file_key] = (photo.name, photo.read(), photo.content_type)
                        media_group.append({
                            "type": "photo",
                            "media": f"attach://{file_key}"
                        })
                        file_index += 1

                if media_group:
                    requests.post(
                        f"https://api.telegram.org/bot{bot_token}/sendMediaGroup",
                        data={
                            "chat_id": chat_id,
                            "media": json.dumps(media_group)
                        },
                        files=media_files,
                        timeout=10
                    )
            except Exception as tg_err:
                print(f"Telegram notification error: {tg_err}")
        
        return JsonResponse({
            "success": True,
            "id": submission.id,
            "nickname": submission.nickname,
            "assessmentGrade": submission.assessment_grade,
            "createdAt": submission.created_at.isoformat()
        }, status=201)
        
    except (ValueError, TypeError, json.JSONDecodeError) as e:
        return JsonResponse({"error": f"Некорректный формат данных: {str(e)}"}, status=400)
