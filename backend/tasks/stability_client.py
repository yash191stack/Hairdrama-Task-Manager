import logging
import time
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

API_ROOT = "https://api.stability.ai/v2beta"
IMAGE_BASE = f"{API_ROOT}/stable-image"


class StabilityError(Exception):
    def __init__(self, message, status_code=None, payload=None):
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


def _api_key():
    key = getattr(settings, "STABILITY_API_KEY", "") or ""
    if not key.strip():
        raise StabilityError("STABILITY_API_KEY is not set")
    return key.strip()


def _auth_headers(accept="application/json"):
    return {
        "Authorization": f"Bearer {_api_key()}",
        "Accept": accept,
    }


def _parse_error(resp):
    try:
        body = resp.json()
        name = body.get("name", "")
        errors = body.get("errors", body.get("message", body))
        if name == "payment_required":
            return "Stability API: not enough credits"
        if name == "unauthorized":
            return "Stability API: invalid API key"
        return f"Stability API error: {errors}"
    except Exception:
        return f"Stability API error ({resp.status_code}): {resp.text[:300]}"


def _poll_result(job_id, timeout=180, poll_interval=1.5):
    url = f"{API_ROOT}/results/{job_id}"
    headers = _auth_headers("*/*")
    started = time.time()
    attempts = 0

    while time.time() - started < timeout:
        attempts += 1
        resp = requests.get(url, headers=headers, timeout=60)
        if resp.status_code == 200:
            elapsed = round(time.time() - started, 1)
            logger.info("stability job %s done in %ss (%s polls)", job_id, elapsed, attempts)
            ct = resp.headers.get("Content-Type", "")
            if "image" in ct or resp.content[:4] in (b"\x89PNG", b"\xff\xd8\xff"):
                return resp.content
            try:
                data = resp.json()
                if data.get("status") == "complete" and "result" in data:
                    import base64
                    return base64.b64decode(data["result"])
            except Exception:
                pass
            if len(resp.content) > 1000:
                return resp.content
            raise StabilityError("Stability returned empty result", resp.status_code, resp.text[:200])

        if resp.status_code == 202:
            time.sleep(poll_interval)
            continue

        raise StabilityError(_parse_error(resp), resp.status_code, resp.text[:500])

    raise StabilityError("Stability request timed out waiting for image")


def _post_image(endpoint, files, data=None):
    url = f"{IMAGE_BASE}/{endpoint}"
    resp = requests.post(
        url,
        headers=_auth_headers("image/*"),
        files=files,
        data=data or {},
        timeout=180,
    )
    if resp.status_code == 200:
        return resp.content
    raise StabilityError(_parse_error(resp), resp.status_code, resp.text[:500])


def _post_async(endpoint, files, data=None):
    url = f"{IMAGE_BASE}/{endpoint}"
    resp = requests.post(
        url,
        headers=_auth_headers("application/json"),
        files=files,
        data=data or {},
        timeout=180,
    )
    if resp.status_code != 200:
        raise StabilityError(_parse_error(resp), resp.status_code, resp.text[:500])

    try:
        payload = resp.json()
    except Exception:
        if resp.content[:4] in (b"\x89PNG", b"\xff\xd8\xff"):
            return resp.content
        raise StabilityError("Unexpected response from Stability", resp.status_code)

    job_id = payload.get("id")
    if not job_id:
        raise StabilityError("Stability did not return a job id", payload=payload)

    t0 = time.time()
    logger.info("stability job %s queued (%s)", job_id, endpoint)
    out = _poll_result(job_id)
    logger.info("stability total %.1fs for %s", time.time() - t0, endpoint)
    return out


def remove_background(image_bytes, output_format="png"):
    files = {"image": ("product.png", image_bytes, "image/png")}
    data = {"output_format": output_format}
    return _post_image("edit/remove-background", files, data)


def replace_background_and_relight(
    image_bytes,
    background_prompt,
    foreground_prompt="",
    negative_prompt="",
    preserve_original_subject=0.9,
    light_source_direction="above",
    light_source_strength=0.35,
    seed=0,
    output_format="jpeg",
):
    files = {"subject_image": ("product.jpg", image_bytes, "image/jpeg")}
    data = {
        "background_prompt": background_prompt,
        "foreground_prompt": foreground_prompt,
        "negative_prompt": negative_prompt,
        "preserve_original_subject": str(preserve_original_subject),
        "light_source_direction": light_source_direction,
        "light_source_strength": str(light_source_strength),
        "seed": str(seed),
        "output_format": output_format,
    }
    return _post_async("edit/replace-background-and-relight", files, data)
