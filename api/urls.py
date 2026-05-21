from django.urls import path
from . import views

urlpatterns = [
    path('config/', views.clan_config_api, name='clan_config_api'),
    path('players/', views.players_list_api, name='players_list_api'),
    path('announcements/', views.announcements_list_api, name='announcements_list_api'),
    path('schedule/', views.schedule_list_api, name='schedule_list_api'),
    path('rules/', views.rules_list_api, name='rules_list_api'),
    path('gallery/', views.gallery_list_api, name='gallery_list_api'),
    path('recruitment/submit/', views.submit_recruitment_api, name='submit_recruitment_api'),
]
