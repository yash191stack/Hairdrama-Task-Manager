import requests
from .models import User


def verify_google_token(token):
    
    try:
        response = requests.get(
            'https://www.googleapis.com/oauth2/v3/userinfo',
            headers={'Authorization': f'Bearer {token}'}
        )

        if response.status_code != 200:
            return None

        return response.json()

    except Exception:
        return None


def get_or_create_user(google_data):
    
    email = google_data.get('email')
    google_id = google_data.get('sub')  # Google ka unique user id
    name = google_data.get('name', '')
    avatar = google_data.get('picture', '')

    # first find with google id
    user = User.objects.filter(google_id=google_id).first()

    if user:
        user.avatar = avatar
        user.save(update_fields=['avatar'])
        return user

    # google_id se nahi mila to find   with email
    user = User.objects.filter(email=email).first()

    if user:
        # email se mila ? then link with google_id
        user.google_id = google_id
        user.avatar = avatar
        user.save(update_fields=['google_id', 'avatar'])
        return user

    # bilkul naya user hai ? Then create
    user = User.objects.create_user(
        email=email,
        name=name,
        google_id=google_id,
        avatar=avatar
    )
    return user