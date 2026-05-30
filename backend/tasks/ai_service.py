import os
import logging
import uuid
import time
import requests
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageFilter
from django.conf import settings

from .models import GeneratedImage, Job
from . import prompts
from .stability_client import (
    StabilityError,
    remove_background,
    replace_background_and_relight,
)

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
    img.thumbnail((1280, 1280), Image.Resampling.LANCZOS)
    buf = BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=92)
    return buf.getvalue()


def _cache_dir():
    media_root = getattr(settings, "MEDIA_ROOT", os.path.join(settings.BASE_DIR, "media"))
    path = os.path.join(media_root, "cache")
    os.makedirs(path, exist_ok=True)
    return path


def _get_cutout(task_id, subject_jpeg):
    path = os.path.join(_cache_dir(), f"{task_id}_cutout.png")
    if os.path.isfile(path):
        with open(path, "rb") as f:
            return f.read()
    cutout = remove_background(subject_jpeg, output_format="png")
    with open(path, "wb") as f:
        f.write(cutout)
    return cutout


def _white_catalog_jpeg(cutout_png):
    cutout = Image.open(BytesIO(cutout_png)).convert("RGBA")
    canvas = Image.new("RGB", OUTPUT_SIZE, (255, 255, 255))

    max_w = int(OUTPUT_SIZE[0] * 0.72)
    max_h = int(OUTPUT_SIZE[1] * 0.72)
    cutout.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)

    shadow = Image.new("RGBA", cutout.size, (0, 0, 0, 0))
    alpha = cutout.split()[3]
    shadow.paste((0, 0, 0, 70), mask=alpha)
    shadow = shadow.filter(ImageFilter.GaussianBlur(10))

    x = (OUTPUT_SIZE[0] - cutout.width) // 2
    y = (OUTPUT_SIZE[1] - cutout.height) // 2 + 20

    canvas.paste(shadow, (x + 6, y + 10), shadow)
    canvas.paste(cutout, (x, y), cutout)

    buf = BytesIO()
    canvas.save(buf, format="JPEG", quality=93)
    return buf.getvalue()


def _normalize_output(raw_bytes):
    img = Image.open(BytesIO(raw_bytes))
    if img.mode != "RGB":
        img = img.convert("RGB")
    if img.size != OUTPUT_SIZE:
        img = img.resize(OUTPUT_SIZE, Image.Resampling.LANCZOS)
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=92)
    return buf.getvalue()


def _save_generation(task, jpeg_bytes, image_type, prompt, angle, theme, meta):
    filename = f"gen_{task.id}_{uuid.uuid4().hex[:8]}.jpg"
    gen_dir = os.path.join(
        getattr(settings, "MEDIA_ROOT", os.path.join(settings.BASE_DIR, "media")),
        "generations",
    )
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

    t_start = time.time()
    try:
        task = job.task
        if not task.product_image_url:
            raise StabilityError("Task has no product image")

        raw = _fetch_product_bytes(task.product_image_url)
        subject = _prepare_subject(raw)
        desc = task.description or ""
        seed = prompts.task_seed(task.id, image_type, angle)
        spec = prompts.build(image_type, angle, theme, prompt, task.title, desc)

        t_api = time.time()

        if spec.get("mode") == "cutout_white":
            cutout = _get_cutout(str(task.id), subject)
            result_bytes = _white_catalog_jpeg(cutout)
            endpoint = "edit/remove-background + catalog white"
            credits = 5
        else:
            result_bytes = replace_background_and_relight(
                subject,
                background_prompt=spec["background_prompt"],
                foreground_prompt=spec["foreground_prompt"],
                negative_prompt=spec["negative_prompt"],
                preserve_original_subject=spec["preserve_original_subject"],
                light_source_strength=spec.get("light_source_strength", 0.28),
                seed=seed,
            )
            result_bytes = _normalize_output(result_bytes)
            endpoint = "edit/replace-background-and-relight"
            credits = 8

        api_sec = round(time.time() - t_api, 1)
        total_sec = round(time.time() - t_start, 1)
        meta = {
            "provider": "stability",
            "endpoint": endpoint,
            "estimated_credits": credits,
            "seed": seed,
            "theme": theme,
            "background_prompt": spec.get("background_prompt", ""),
            "foreground_prompt": spec.get("foreground_prompt", ""),
            "preserve_original_subject": spec.get("preserve_original_subject"),
            "duration_api_sec": api_sec,
            "duration_total_sec": total_sec,
        }
        logger.info("job %s finished in %ss (stability %ss)", job_id, total_sec, api_sec)

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
