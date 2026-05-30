import os
import logging
import requests
from django.conf import settings
from .models import User

logger = logging.getLogger(__name__)


def verify_google_token(token):
    client_id = (getattr(settings, 'GOOGLE_CLIENT_ID', None) or '').strip()
    try:
        response = requests.get(
            f'https://oauth2.googleapis.com/tokeninfo?id_token={token}',
            timeout=10,
        )
        if response.status_code == 200:
            data = response.json()
            aud = data.get('aud') or data.get('azp')
            if client_id and aud and aud != client_id:
                logger.warning('Google aud mismatch: token=%s env=%s', aud, client_id)
                return None
            if not data.get('email'):
                logger.warning('Google token missing email')
                return None
            return data

        response = requests.get(
            'https://www.googleapis.com/oauth2/v3/userinfo',
            headers={'Authorization': f'Bearer {token}'},
            timeout=10,
        )
        if response.status_code == 200:
            return response.json()
        logger.warning('Google verify failed: %s', response.status_code)
        return None
    except Exception as e:
        logger.exception('Google verify error: %s', e)
        return None

def verify_github_code(code):
    try:
        github_client_id = (getattr(settings, 'GITHUB_CLIENT_ID', None) or os.getenv('GITHUB_CLIENT_ID', '')).strip()
        github_client_secret = (getattr(settings, 'GITHUB_CLIENT_SECRET', None) or os.getenv('GITHUB_CLIENT_SECRET', '')).strip()

        if not github_client_id or not github_client_secret:
            logger.error('GitHub OAuth not configured: set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET on Railway')
            return None
        
        client_id = github_client_id
        client_secret = github_client_secret
        
        token_response = requests.post(
            'https://github.com/login/oauth/access_token',
            headers={'Accept': 'application/json'},
            data={
                'client_id': client_id,
                'client_secret': client_secret,
                'code': code
            },
            timeout=10
        )
        
        if token_response.status_code != 200:
            return None
            
        token_data = token_response.json()
        access_token = token_data.get('access_token')
        if not access_token:
            return None
            
        user_response = requests.get(
            'https://api.github.com/user',
            headers={'Authorization': f'token {access_token}'},
            timeout=10
        )
        if user_response.status_code != 200:
            return None
            
        user_data = user_response.json()
        
        if not user_data.get('email'):
            emails_response = requests.get(
                'https://api.github.com/user/emails',
                headers={'Authorization': f'token {access_token}'},
                timeout=10
            )
            if emails_response.status_code == 200:
                for email_info in emails_response.json():
                    if email_info.get('primary') and email_info.get('verified'):
                        user_data['email'] = email_info.get('email')
                        break
                        
        return user_data
    except Exception:
        return None

def get_or_create_oauth_user(provider, profile_data):
    email = profile_data.get('email')
    if not email:
        login = profile_data.get('login', 'github_user')
        email = f"{login}@github.temphub.com"

    google_id = profile_data.get('sub') if provider == 'google' else None
    github_id = str(profile_data.get('id')) if provider == 'github' else None
    name = profile_data.get('name') or profile_data.get('login') or email.split('@')[0]
    avatar = profile_data.get('picture') if provider == 'google' else profile_data.get('avatar_url')

    if google_id:
        user = User.objects.filter(google_id=google_id).first()
        if user:
            user.avatar = avatar
            user.save(update_fields=['avatar'])
            return user

    if github_id:
        user = User.objects.filter(github_id=github_id).first()
        if user:
            user.avatar = avatar
            user.save(update_fields=['avatar'])
            return user

    user = User.objects.filter(email=email).first()
    if user:
        if google_id:
            user.google_id = google_id
        if github_id:
            user.github_id = github_id
        user.avatar = avatar
        user.save(update_fields=['google_id', 'github_id', 'avatar'])
        return user

    is_first = User.objects.count() == 0
    role = 'admin' if is_first else 'user'

    user = User.objects.create_user(
        email=email,
        name=name,
        google_id=google_id,
        github_id=github_id,
        avatar=avatar,
        role=role
    )
    return user