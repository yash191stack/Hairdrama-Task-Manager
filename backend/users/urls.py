from django.urls import path
from . import views
from . import auth_views


urlpatterns = [
    path('auth/google/', auth_views.google_login, name='google-login'),
    path('auth/refresh/', auth_views.refresh_token, name='token-refresh'),
    
    path('profile/', views.get_profile, name='user-profile'),
    path('profile/update/', views.update_profile, name='user-update'),
    path('list/', views.list_users, name='user-list'),
]