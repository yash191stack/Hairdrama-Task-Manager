import os
import logging
import uuid
import requests
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
from django.conf import settings

from .models import GeneratedImage, Job
from . import prompts
from .stability_client import StabilityError, replace_background_and_relight

logger = logging.getLogger(__name__)

executor = ThreadPoolExecutor(max_workers=2)

OUTPUT_SIZE = (1024, 1024)


def trigger_bg_generation(job_id, image_type, prompt="", angle="none", theme=""):
    executor.submit(_run_generation, job_id, image_type, prompt, angle, theme)


def _fetch_product_bytes(url):
    resp = requests.get(
        url,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.content


def _prepare_subject(image_bytes):
    img = Image.open(BytesIO(image_bytes))
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")
    img.thumbnail((1536, 1536), Image.Resampling.LANCZOS)
    buf = BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=95)
    return buf.getvalue()


def _normalize_output(raw_bytes):
    img = Image.open(BytesIO(raw_bytes))
    if img.mode != "RGB":
        img = img.convert("RGB")
    img = img.resize(OUTPUT_SIZE, Image.Resampling.LANCZOS)
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=92)
    return buf.getvalue()


def _save_generation(task, jpeg_bytes, image_type, prompt, angle, theme, meta):
    filename = f"gen_{task.id}_{uuid.uuid4().hex[:8]}.jpg"
    media_root = getattr(settings, "MEDIA_ROOT", os.path.join(settings.BASE_DIR, "media"))
    gen_dir = os.path.join(media_root, "generations")
    os.makedirs(gen_dir, exist_ok=True)
    filepath = os.path.join(gen_dir, filename)
    with open(filepath, "wb") as f:
        f.write(jpeg_bytes)

    backend_url = getattr(settings, "BACKEND_URL", "http://localhost:8000")
    saved_url = f"{backend_url}/media/generations/{filename}"

    GeneratedImage.objects.create(
        task=task,
        image_type=image_type,
        image_url=saved_url,
        prompt_used=prompt or meta.get("background_prompt", ""),
        angle=angle or "none",
        metadata=meta,
    )
    return saved_url


def _run_generation(job_id, image_type, prompt, angle, theme):
    try:
        job = Job.objects.get(pk=job_id)
    except Job.DoesNotExist:
        return

    job.status = "running"
    job.save(update_fields=["status", "updated_at"])

    try:
        task = job.task
        if not task.product_image_url:
            raise StabilityError("Task has no product image")

        raw = _fetch_product_bytes(task.product_image_url)
        subject = _prepare_subject(raw)
        seed = prompts.task_seed(task.id)
        spec = prompts.build(image_type, angle, theme, prompt, task.title)

        result_bytes = replace_background_and_relight(
            subject,
            background_prompt=spec["background_prompt"],
            foreground_prompt=spec["foreground_prompt"],
            negative_prompt=spec["negative_prompt"],
            preserve_original_subject=spec["preserve_original_subject"],
            seed=seed,
        )
        result_bytes = _normalize_output(result_bytes)
        endpoint = "edit/replace-background-and-relight"
        credits = 8

        meta = {
            "provider": "stability",
            "endpoint": endpoint,
            "estimated_credits": credits,
            "seed": seed,
            "theme": theme,
            "background_prompt": spec.get("background_prompt", ""),
            "foreground_prompt": spec.get("foreground_prompt", ""),
            "preserve_original_subject": spec.get("preserve_original_subject"),
        }

        saved_url = _save_generation(
            task, result_bytes, image_type, prompt, angle, theme, meta
        )

        job.status = "completed"
        job.image_url = saved_url
        job.error = ""
        job.save(update_fields=["status", "image_url", "error", "updated_at"])

    except StabilityError as e:
        logger.error("generation failed job=%s: %s", job_id, e)
        job.status = "failed"
        job.error = str(e)
        job.save(update_fields=["status", "error", "updated_at"])
    except Exception as e:
        logger.exception("generation failed job=%s", job_id)
        job.status = "failed"
        job.error = str(e) or "Generation failed"
        job.save(update_fields=["status", "error", "updated_at"])
