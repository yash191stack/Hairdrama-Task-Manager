import requests
from .models import User


def verify_google_token(token):
    """
    Google Login component ID token bhejta hai
    is endpoint se verify karte hain
    """
    try:
        # pehle ID token try karo
        response = requests.get(
            f'https://oauth2.googleapis.com/tokeninfo?id_token={token}'
        )
        if response.status_code == 200:
            return response.json()

        # agar ID token nahi to access token try karo
        response = requests.get(
            'https://www.googleapis.com/oauth2/v3/userinfo',
            headers={'Authorization': f'Bearer {token}'}
        )
        if response.status_code == 200:
            return response.json()

        return None

    except Exception as e:
        print(f'Token verification error: {e}')
        return None


def get_or_create_user(google_data):
    email = google_data.get('email')
    google_id = google_data.get('sub')
    name = google_data.get('name', '')
    avatar = google_data.get('picture', '')

    user = User.objects.filter(google_id=google_id).first()
    if user:
        user.avatar = avatar
        user.save(update_fields=['avatar'])
        return user

    user = User.objects.filter(email=email).first()
    if user:
        user.google_id = google_id
        user.avatar = avatar
        user.save(update_fields=['google_id', 'avatar'])
        return user

    user = User.objects.create_user(
        email=email,
        name=name,
        google_id=google_id,
        avatar=avatar
    )
    return user