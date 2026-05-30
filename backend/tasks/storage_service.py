import logging
import os
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

BUCKET = os.getenv('SUPABASE_STORAGE_BUCKET', 'generations')


def _supabase_configured():
    return bool(getattr(settings, 'SUPABASE_URL', None) and getattr(settings, 'SUPABASE_SECRET_KEY', None))


def public_url(filename):
    base = settings.SUPABASE_URL.rstrip('/')
    return f"{base}/storage/v1/object/public/{BUCKET}/{filename}"


def upload_generation(filename, data, content_type='image/jpeg'):
    if not _supabase_configured():
        return None

    base = settings.SUPABASE_URL.rstrip('/')
    key = settings.SUPABASE_SECRET_KEY
    url = f"{base}/storage/v1/object/{BUCKET}/{filename}"

    resp = requests.post(
        url,
        headers={
            'Authorization': f'Bearer {key}',
            'Content-Type': content_type,
            'x-upsert': 'true',
        },
        data=data,
        timeout=120,
    )

    if resp.status_code not in (200, 201):
        logger.error('Supabase upload failed %s: %s', resp.status_code, resp.text[:300])
        return None

    return public_url(filename)


def ensure_bucket():
    if not _supabase_configured():
        return False

    base = settings.SUPABASE_URL.rstrip('/')
    key = settings.SUPABASE_SECRET_KEY
    resp = requests.post(
        f"{base}/storage/v1/bucket",
        headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'},
        json={'id': BUCKET, 'name': BUCKET, 'public': True},
        timeout=30,
    )
    if resp.status_code in (200, 201, 409):
        return True
    logger.warning('Could not ensure bucket: %s %s', resp.status_code, resp.text[:200])
    return False
