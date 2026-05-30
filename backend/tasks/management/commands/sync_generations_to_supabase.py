import os
from django.conf import settings
from django.core.management.base import BaseCommand
from tasks.models import GeneratedImage
from tasks.storage_service import upload_generation, ensure_bucket, public_url


def filename_from_url(url):
    if not url:
        return None
    if '/media/generations/' in url:
        return url.split('/media/generations/')[-1].split('?')[0]
    return url.rstrip('/').split('/')[-1].split('?')[0]


class Command(BaseCommand):
    help = 'Upload local generation files to Supabase Storage and fix image_url in DB'

    def handle(self, *args, **options):
        ensure_bucket()
        gen_dir = os.path.join(settings.MEDIA_ROOT, 'generations')
        updated = 0
        missing = 0

        for gen in GeneratedImage.objects.all().iterator():
            fname = filename_from_url(gen.image_url)
            if not fname:
                missing += 1
                continue

            if gen.image_url and 'supabase.co' in gen.image_url:
                continue

            filepath = os.path.join(gen_dir, fname)
            if not os.path.isfile(filepath):
                self.stdout.write(self.style.WARNING(f'Missing file: {fname}'))
                missing += 1
                continue

            with open(filepath, 'rb') as f:
                data = f.read()

            url = upload_generation(fname, data)
            if not url:
                self.stdout.write(self.style.ERROR(f'Upload failed: {fname}'))
                continue

            gen.image_url = url
            gen.save(update_fields=['image_url'])
            updated += 1
            self.stdout.write(self.style.SUCCESS(f'Uploaded {fname}'))

        self.stdout.write(self.style.SUCCESS(f'Done: {updated} uploaded, {missing} missing/skipped'))
