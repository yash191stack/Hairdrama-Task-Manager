from django.urls import path
from . import views, auth_views

urlpatterns = [
    path('profile/', views.get_profile, name='user-profile'),
    path('profile/update/', views.update_profile, name='user-update'),
    path('list/', views.list_users, name='user-list'),
    path('auth/google/', auth_views.google_login_legacy, name='legacy-google-login'),
    path('auth/refresh/', auth_views.refresh_token, name='legacy-auth-refresh'),
]