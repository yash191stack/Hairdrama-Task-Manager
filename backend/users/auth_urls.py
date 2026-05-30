from django.urls import path
from . import auth_views

urlpatterns = [
    path('oauth/callback', auth_views.oauth_callback, name='oauth-callback'),
    path('me', auth_views.get_me, name='auth-me'),
    path('logout', auth_views.logout, name='auth-logout'),
    path('refresh', auth_views.refresh_token, name='auth-refresh'),
]
