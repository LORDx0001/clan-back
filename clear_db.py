import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clan_backend.settings')
django.setup()


from api.models import ClanConfig, Player, Announcement, GalleryItem, ScheduleEvent, ClanRule, RecruitmentSubmission

print("Clearing database...")
Player.objects.all().delete()
Announcement.objects.all().delete()
GalleryItem.objects.all().delete()
ScheduleEvent.objects.all().delete()
ClanRule.objects.all().delete()
RecruitmentSubmission.objects.all().delete()

# Reset ClanConfig singleton to a clean slate
ClanConfig.objects.all().delete()
ClanConfig.get_solo()  # creates a fresh blank record with default values

print("Database cleared successfully!")
