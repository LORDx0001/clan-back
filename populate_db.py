import os
import django
from datetime import datetime, timedelta
from django.utils import timezone

# Configure Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clan_backend.settings')
django.setup()

from api.models import ClanConfig, Player, Announcement, GalleryItem, ScheduleEvent, ClanRule

def populate():
    print("Populating initial gaming data...")

    # 1. Clan Config (Site Settings)
    config = ClanConfig.get_solo()
    config.clan_name = "Interstellar"
    config.clan_tag = "Inter"
    config.clan_founded = "2024"
    config.hero_title_1 = "КОСМИЧЕСКИЙ"
    config.hero_title_2 = "ПРОРЫВ 2026"
    config.hero_description = "Киберспортивная организация Interstellar в PUBG Mobile. Только лучшая координация, тренированный кибер-состав и безоговорочная победа в зоне."
    config.discord_link = "discord.gg/interstellar-pubg"
    config.telegram_link = "@inter_manager_pubg"
    config.stats_tournaments_title = "ТУРНИРЫ"
    config.stats_tournaments_value = "34+ ПОБЕД"
    config.stats_tournaments_desc = "Топ-1 места в турнирах"
    config.stats_rank_title = "СТАТУС В СНГ"
    config.stats_rank_value = "TOP-10 RANK"
    config.stats_rank_desc = "Официальные лидерборды"
    config.stats_members_title = "АКТИВНОСТЬ"
    config.stats_members_value = "30+ АКТИВНЫХ"
    config.stats_members_desc = "Про-состав и резервисты"
    config.stats_experience_title = "ИГРОВОЙ ОПЫТ"
    config.stats_experience_value = "20+ ПРАКОВ"
    config.stats_experience_desc = "Разборы тактик еженедельно"
    config.rules_terms_desc = "Все участники клана обязаны сменить игровой никнейм на ник с префиксом Inter・ в течение 7 дней после успешного тестирования. Карту смены ника клан предоставляет лучшим кандидатам!"
    config.save()
    print("- Clan config updated.")

    # 2. Players (Roster)
    Player.objects.all().delete()
    players_data = [
        {
            "nickname": "Inter・PHANTOM",
            "role": "Leader",
            "device": "iPad Pro 12.9 M2",
            "level": 78,
            "signature_weapon": "M416 + M16A4",
            "avatar": "https://images.unsplash.com/photo-1542751371-adc38448a05e?w=800&auto=format&fit=crop&q=80",
            "achievements": "TOP-1 MVP PMPL Season 1\nPMCO Finalist\n1000+ Chicken Dinners",
            "region": "CIS / Almaty",
            "joined_date": "Февраль 2024"
        },
        {
            "nickname": "Inter・BEAST",
            "role": "Assaulter",
            "device": "iPhone 15 Pro Max",
            "level": 74,
            "signature_weapon": "M762 + Groza",
            "avatar": "https://images.unsplash.com/photo-1538481199705-c710c4e965fc?w=800&auto=format&fit=crop&q=80",
            "achievements": "Best Entry Fragger 2024\nPMPL MVP Weekly\n70% Headshot Rate",
            "region": "CIS / Tashkent",
            "joined_date": "Март 2024"
        },
        {
            "nickname": "Inter・WYVERN",
            "role": "Sniper",
            "device": "iPad Mini 6",
            "level": 72,
            "signature_weapon": "AWM + M416",
            "avatar": "https://images.unsplash.com/photo-1511512578047-dfb367046420?w=800&auto=format&fit=crop&q=80",
            "achievements": "God of Sniper CIS Cup\nLongest Headshot 534m\nSolo vs Squad Champion",
            "region": "CIS / Moscow",
            "joined_date": "Май 2024"
        },
        {
            "nickname": "Inter・CYPHER",
            "role": "Scout",
            "device": "ROG Phone 8 Pro",
            "level": 71,
            "signature_weapon": "UMP45 + AKM",
            "avatar": "https://images.unsplash.com/photo-1552820728-8b83bb6b773f?w=800&auto=format&fit=crop&q=80",
            "achievements": "In-Game Leader Assistant\nGolden Helmet Master\nTactical Brain of Interstellar",
            "region": "CIS / Baku",
            "joined_date": "Июль 2024"
        },
        {
            "nickname": "Inter・AURORA",
            "role": "Support",
            "device": "iPhone 14 Pro",
            "level": 70,
            "signature_weapon": "DP-28 + DBS",
            "avatar": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=800&auto=format&fit=crop&q=80",
            "achievements": "CIS Girls Cup Winner\nBest Medic CIS Pro League\nSaviour Master",
            "region": "CIS / Astana",
            "joined_date": "Сентябрь 2024"
        },
        {
            "nickname": "Inter・KAIZEN",
            "role": "Manager",
            "device": "MacBook Pro M3",
            "level": 65,
            "signature_weapon": "M416",
            "avatar": "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=800&auto=format&fit=crop&q=80",
            "achievements": "Top Manager League 2024\nContract Expert\nTeam Coordinator",
            "region": "CIS / Tbilisi",
            "joined_date": "Январь 2024"
        }
    ]
    for p in players_data:
        Player.objects.create(**p)
    print(f"- Created {len(players_data)} players.")

    # 3. Announcements
    Announcement.objects.all().delete()
    ann_data = [
        {
            "title": "ВЫХОД В ФИНАЛ CIS CHAMPIONSHIP 2026!",
            "type": "tournament",
            "date": "20.05.2026",
            "content": "Поздравляем основной состав Interstellar с блестящим выходом в Гранд-Финал СНГ Лиги. Наши парни заняли 2 место в таблице полуфинала с общим количеством киллов - 142. Финал состоится уже через несколько дней, готовьтесь поддержать команду!",
            "countdown_date": timezone.now() + timedelta(days=4),
            "author": "Inter・KAIZEN (Менеджер)",
            "image_url": "https://images.unsplash.com/photo-1542751371-adc38448a05e?w=800&auto=format&fit=crop&q=80",
            "views": 342
        },
        {
            "title": "Большие праки на 10,000 рублей против Top Esports CIS",
            "type": "scrim",
            "date": "18.05.2026",
            "content": "Сегодня пройдет закрытая серия тренировочных матчей (Scrims) против топовых коллективов СНГ региона. В призовом фонде 10,000 рублей для команды, набравшей максимальное количество очков за 5 карт. Будет жарко. Стрим на канале лидера!",
            "countdown_date": timezone.now() + timedelta(hours=8),
            "author": "Inter・PHANTOM (Капитан)",
            "image_url": "https://images.unsplash.com/photo-1538481199705-c710c4e965fc?w=800&auto=format&fit=crop&q=80",
            "views": 189
        },
        {
            "title": "Запуск набора в Академию Interstellar ACADEMY",
            "type": "news",
            "date": "15.05.2026",
            "content": "Мы официально открываем двери для молодых талантов! Если вы дисциплинированы и мечтаете попасть на профессиональную сцену — подавайте заявку во вкладке 'Рекрутинг'. Кандидаты с лучшими результатами будут приглашены на тестовые дуэли.",
            "author": "Inter・KAIZEN (Менеджер)",
            "image_url": "https://images.unsplash.com/photo-1511512578047-dfb367046420?w=800&auto=format&fit=crop&q=80",
            "views": 521
        }
    ]
    for a in ann_data:
        Announcement.objects.create(**a)
    print(f"- Created {len(ann_data)} announcements.")

    # 4. Schedule
    ScheduleEvent.objects.all().delete()
    sch_data = [
        {
            "title": "CIS Clan Pro League - Гранд-Финал",
            "type": "tournament",
            "datetime": timezone.now() + timedelta(days=4, hours=4),
            "team_size": "Турнир: 4 vs 4 Squad",
            "prize_pool": "50,000 KZT",
            "slots_filled": 16,
            "slots_total": 16,
            "opponent": "Top CIS Clans (PRO)"
        },
        {
            "title": "Вечерние квалификационные праки",
            "type": "scrim",
            "datetime": timezone.now() + timedelta(days=1, hours=6),
            "team_size": "Кланвар: 4x4 Squad",
            "prize_pool": "",
            "slots_filled": 12,
            "slots_total": 18,
            "opponent": "CIS Community Custom"
        },
        {
            "title": "Регулярная тренировка: Тактика Erangel + Miramar",
            "type": "training",
            "datetime": timezone.now() + timedelta(hours=2),
            "team_size": "Tactical Squad Training",
            "slots_filled": 4,
            "slots_total": 4,
            "opponent": ""
        },
        {
            "title": "Внутриклановое собрание и разбор ошибок",
            "type": "meeting",
            "datetime": timezone.now() + timedelta(days=2, hours=10),
            "team_size": "Discord meeting",
            "slots_filled": 15,
            "slots_total": 30,
            "opponent": ""
        }
    ]
    for s in sch_data:
        ScheduleEvent.objects.create(**s)
    print(f"- Created {len(sch_data)} schedule events.")

    # 5. Rules
    ClanRule.objects.all().delete()
    rules_data = [
        {
            "category": "Поведение в игре",
            "title": "Абсолютная дисциплина во время связи",
            "content": "Во время официальных игр, турниров и праков в Discord должен быть идеальный звуковой климат. Говорит только тот, у кого есть тактическая информация, капитан отдает приказы беспрекословно. Запрещен флуд, посторонние звуки и обсуждение неигровых тем.",
            "severity": "high"
        },
        {
            "category": "Поведение в игре",
            "title": "Запрет токсичности и оскорблений",
            "content": "Мы уважаем своих тиммейтов и соперников. Любое проявление токсичности, обвинений, оскорбления родственников или национальности влечет за собой немедленный вылет из клана без права вето.",
            "severity": "high"
        },
        {
            "category": "Критерии активности",
            "title": "Обязательное участие в тренировках",
            "content": "Игроки А-состава обязаны посещать не менее 80% запланированных тренировок в неделю. Если вы не можете присутствовать, вы обязаны предупредить менеджера/капитана минимум за 2 часа до начала игры.",
            "severity": "medium"
        },
        {
            "category": "Техническое оснащение",
            "title": "Стабильное соединение и устройство",
            "content": "Каждый профессиональный игрок основы должен иметь игровой девайс, выдающий стабильные 60-90 FPS в замесах, и пинг не выше 50-70 мс. Просадки FPS вредят общему результату команды.",
            "severity": "low"
        }
    ]
    for r in rules_data:
        ClanRule.objects.create(**r)
    print(f"- Created {len(rules_data)} clan rules.")

    # 6. Gallery
    GalleryItem.objects.all().delete()
    gallery_data = [
        {
            "type": "trophy",
            "title": "Кубок CIS Summer Open 2024",
            "category": "Победы в кубках",
            "file_url": "https://images.unsplash.com/photo-1578269174936-2709b5a5e06e?w=800&auto=format&fit=crop&q=80",
            "thumbnail": "https://images.unsplash.com/photo-1578269174936-2709b5a5e06e?w=300&auto=format&fit=crop&q=80",
            "views": 412,
            "likes": 128,
            "date": "12.08.2024",
            "author": "Inter・KAIZEN"
        },
        {
            "type": "screenshot",
            "title": "Очередной стрик из 15 побед подряд в рейтинге Squad",
            "category": "Матчи",
            "file_url": "https://images.unsplash.com/photo-1542751371-adc38448a05e?w=800&auto=format&fit=crop&q=80",
            "thumbnail": "https://images.unsplash.com/photo-1542751371-adc38448a05e?w=300&auto=format&fit=crop&q=80",
            "views": 312,
            "likes": 98,
            "date": "25.04.2025",
            "author": "Inter・BEAST"
        },
        {
            "type": "video",
            "title": "Шокирующий сквад-вайп за 8 секунд от Inter・PHANTOM",
            "category": "Хайлайты",
            "file_url": "https://www.w3schools.com/html/mov_bbb.mp4",
            "thumbnail": "https://images.unsplash.com/photo-1560253023-3ec5d502959f?w=800&auto=format&fit=crop&q=80",
            "views": 1245,
            "likes": 432,
            "date": "14.05.2026",
            "author": "Inter・PHANTOM"
        },
        {
            "type": "screenshot",
            "title": "Тренировка сквада на карте Miramar - Тактический клатч",
            "category": "Матчи",
            "file_url": "https://images.unsplash.com/photo-1580234810907-b40315b76418?w=800&auto=format&fit=crop&q=80",
            "thumbnail": "https://images.unsplash.com/photo-1580234810907-b40315b76418?w=300&auto=format&fit=crop&q=80",
            "views": 198,
            "likes": 45,
            "date": "19.05.2026",
            "author": "Inter・CYPHER"
        }
    ]
    for g in gallery_data:
        GalleryItem.objects.create(**g)
    print(f"- Created {len(gallery_data)} gallery items.")
    print("Database populate successful!")

if __name__ == '__main__':
    populate()
