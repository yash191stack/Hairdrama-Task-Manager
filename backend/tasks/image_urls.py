import os
import re
from django.conf import settings

PRODUCTION_BACKEND = 'https://hairdrama-task-manager-production.up.railway.app'


def generation_filename(url):
    if not url:
        return None
    if '/media/generations/' in url:
        return url.split('/media/generations/')[-1].split('?')[0]
    match = re.search(r'gen_[^/?#]+\.jpg', url)
    if match:
        return match.group(0)
    tail = url.rstrip('/').split('/')[-1]
    return tail if tail.endswith('.jpg') else None


def resolve_backend_url():
    url = (getattr(settings, 'BACKEND_URL', '') or '').strip().rstrip('/')
    if url and url.startswith('http') and 'localhost' not in url:
        return url
    if not settings.DEBUG:
        return PRODUCTION_BACKEND
    return url or 'http://localhost:8000'


def resolve_generation_url(stored_url, request=None, generation_id=None):
    if stored_url and 'supabase.co/storage/v1/object/public/' in stored_url:
        return stored_url

    filename = generation_filename(stored_url)
    if not filename:
        return stored_url or ''

    frontend = (getattr(settings, 'FRONTEND_URL', '') or '').strip().rstrip('/')
    if frontend and not settings.DEBUG:
        return f'{frontend}/generations/{filename}'

    if generation_id and request:
        return request.build_absolute_uri(f'/api/generations/{generation_id}/file/')

    backend = resolve_backend_url()
    return f'{backend}/media/generations/{filename}'
