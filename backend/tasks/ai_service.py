import os
import time
import uuid
import requests
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw, ImageFilter, ImageOps
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from .models import Task, GeneratedImage, Job

def extract_product_with_floodfill(img):
    img = img.convert("RGBA")
    w, h = img.size
    corners = [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]
    for cx, cy in corners:
        pixel = img.getpixel((cx, cy))
        if pixel[3] > 0:
            ImageDraw.floodfill(img, (cx, cy), (0, 0, 0, 0), thresh=30)
    return img

executor = ThreadPoolExecutor(max_workers=3)

def trigger_bg_generation(job_id, image_type, prompt='', angle='none', theme=''):
    executor.submit(_process_bg_generation, job_id, image_type, prompt, angle, theme)

def _process_bg_generation(job_id, image_type, prompt, angle, theme):
    try:
        job = Job.objects.get(pk=job_id)
    except Job.DoesNotExist:
        return

    job.status = 'running'
    job.save()

    try:
        task = job.task
        time.sleep(1.5)

        product_url = task.product_image_url
        if not product_url:
            product_url = "https://images.unsplash.com/photo-1599643478518-a784e5dc4c8f?w=500&auto=format&fit=crop"

        try:
            response = requests.get(product_url, timeout=10)
            product_img = Image.open(BytesIO(response.content)).convert("RGBA")
            product_img = extract_product_with_floodfill(product_img)
        except Exception:
            product_img = Image.new("RGBA", (400, 400), (255, 215, 0, 255))
            draw = ImageDraw.Draw(product_img)
            draw.ellipse([100, 100, 300, 300], fill=(220, 220, 220, 255), outline=(255, 255, 255, 255), width=8)

        # 1. Base Backdrop Generation
        bg_width, bg_height = 800, 800
        backdrop = Image.new("RGBA", (bg_width, bg_height))
        draw = ImageDraw.Draw(backdrop)

        if image_type == 'white_background':
            draw.rectangle([0, 0, bg_width, bg_height], fill=(255, 255, 255, 255))
            
        elif image_type == 'theme':
            t_name = (theme or prompt or "marble").lower()
            if 'velvet' in t_name or 'luxury' in t_name:
                for y in range(bg_height):
                    r = int(120 - (y / bg_height) * 80)
                    draw.line([(0, y), (bg_width, y)], fill=(r, 10, 30, 255))
                draw.ellipse([150, 600, 650, 750], fill=(40, 0, 10, 120))
            else:  # Marble Surface
                for y in range(bg_height):
                    c = int(220 + (y / bg_height) * 25)
                    draw.line([(0, y), (bg_width, y)], fill=(c, c, c, 255))
                # Marble veins
                draw.line([(100, 0), (300, 800)], fill=(180, 180, 180, 255), width=2)
                draw.line([(500, 0), (400, 800)], fill=(190, 190, 190, 255), width=3)
                draw.ellipse([200, 580, 600, 680], fill=(160, 160, 160, 100))

        elif image_type == 'creative':
            p_name = (prompt or "").lower()
            if 'sunset' in p_name or 'beach' in p_name:
                for y in range(bg_height):
                    r = int(255 - (y / bg_height) * 100)
                    g = int(120 + (y / bg_height) * 40)
                    b = int(50 + (y / bg_height) * 150)
                    draw.line([(0, y), (bg_width, y)], fill=(r, g, b, 255))
                draw.ellipse([400, 300, 550, 450], fill=(255, 240, 200, 255)) # Sun
                draw.rectangle([0, 500, bg_width, bg_height], fill=(40, 70, 120, 255)) # Sea
            else:  # Artistic Interior
                for y in range(bg_height):
                    c = int(240 - (y / bg_height) * 60)
                    draw.line([(0, y), (bg_width, y)], fill=(c, c - 10, c - 20, 255))
                # Geometric shapes
                draw.rectangle([100, 300, 300, 800], fill=(210, 180, 160, 255))
                draw.ellipse([450, 200, 650, 400], fill=(190, 210, 200, 255))
                draw.ellipse([200, 550, 600, 650], fill=(120, 110, 100, 80))

        elif image_type == 'model':
            # Soft studio gradient backdrop
            for y in range(bg_height):
                c = int(40 + (y / bg_height) * 40)
                draw.line([(0, y), (bg_width, y)], fill=(c, c - 5, c + 10, 255))
            
            # Draw model neck and silhouette representing wearing context
            model_color = (220, 190, 170, 255)
            # Neck silhouette
            draw.polygon([(300, 800), (320, 450), (480, 450), (500, 800)], fill=model_color)
            # Face jawline (bottom half)
            draw.ellipse([280, 180, 520, 480], fill=model_color)
            # Soft shadow under necklace position
            draw.ellipse([340, 480, 460, 520], fill=(10, 10, 10, 80))

        # 2. Extract Product and Composite
        # Downscale product keeping aspect ratio
        prod_w, prod_h = product_img.size
        max_size = 350 if image_type == 'model' else 450
        ratio = min(max_size / prod_w, max_size / prod_h)
        new_size = (int(prod_w * ratio), int(prod_h * ratio))
        product_resized = product_img.resize(new_size, Image.Resampling.LANCZOS)

        # Composite coordinates
        px = (bg_width - new_size[0]) // 2
        py = 460 - (new_size[1] // 2) if image_type == 'model' else (bg_height - new_size[1]) // 2

        # Combine
        backdrop.paste(product_resized, (px, py), product_resized)

        # 3. Save File
        img_buffer = BytesIO()
        backdrop.convert("RGB").save(img_buffer, format="JPEG", quality=90)
        img_buffer.seek(0)

        filename = f"gen_{task.id}_{uuid.uuid4().hex[:8]}.jpg"
        
        # Dual storage strategy: attempt Supabase or standard Local storage
        supabase_url = getattr(settings, 'SUPABASE_URL', '')
        supabase_key = getattr(settings, 'SUPABASE_ANON_KEY', '')

        saved_url = None

        if supabase_url and supabase_key:
            try:
                # Mock storage or real Supabase API push
                headers = {
                    "Authorization": f"Bearer {supabase_key}",
                    "Content-Type": "image/jpeg"
                }
                bucket = "generations"
                upload_url = f"{supabase_url}/storage/v1/object/{bucket}/{filename}"
                upload_res = requests.post(upload_url, data=img_buffer.getvalue(), headers=headers, timeout=15)
                if upload_res.status_code == 200:
                    saved_url = f"{supabase_url}/storage/v1/object/public/{bucket}/{filename}"
            except Exception:
                pass

        if not saved_url:
            # Fallback to local Django storage
            filepath = os.path.join('generations', filename)
            stored_path = default_storage.save(filepath, ContentFile(img_buffer.getvalue()))
            saved_url = f"{settings.BACKEND_URL}/media/{stored_path}"

        # Create Generation Image record
        gen_img = GeneratedImage.objects.create(
            task=task,
            image_type=image_type,
            image_url=saved_url,
            prompt_used=prompt or f"Consistent Pearl {image_type} photograph",
            angle=angle or 'none',
            metadata={
                'theme': theme,
                'composite': 'Pillow composition v1',
                'dimensions': '800x800'
            }
        )

        job.status = 'completed'
        job.image_url = saved_url
        job.save()

    except Exception as e:
        job.status = 'failed'
        job.error = str(e)
        job.save()
