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
    path('roles/', views.roles_list_api, name='roles_list_api'),
    path('auth/login/', views.login_api, name='login_api'),
    path('auth/register/', views.register_api, name='register_api'),
    path('auth/logout/', views.logout_api, name='logout_api'),
    path('auth/me/', views.me_api, name='me_api'),
    path('auth/update-profile/', views.update_profile_api, name='update_profile_api'),
]
