NEGATIVE = (
    "cartoon, illustration, anime, low quality, blurry, deformed jewelry, "
    "wrong product, duplicate necklace, extra clasps, watermark, text, logo, "
    "oversaturated, plastic look, bad anatomy, distorted hands"
)


def task_seed(task_id):
    return abs(hash(str(task_id))) % 4294967294


def product_label(task_title, user_prompt):
    bits = []
    if task_title:
        bits.append(task_title.strip())
    if user_prompt:
        bits.append(user_prompt.strip())
    base = ", ".join(bits) if bits else "jewelry product"
    return f"{base}, exact same product as reference photo, unchanged shape and details"


def build(image_type, angle, theme, user_prompt, task_title):
    fg = product_label(task_title, user_prompt)
    custom = (user_prompt or "").strip()
    theme_txt = (theme or "").strip()

    if image_type == "white_background":
        bg = (
            "pure solid white background hex FFFFFF, professional ecommerce studio, "
            "soft diffused softbox lighting, clean product photography, DSLR, "
            "no props, no shadows on backdrop"
        )
        if custom:
            bg = f"{bg}, {custom}"
        return {
            "background_prompt": bg,
            "foreground_prompt": fg,
            "negative_prompt": NEGATIVE,
            "preserve_original_subject": 0.92,
        }

    if image_type == "theme":
        scene = theme_txt or custom or "luxury marble surface with soft daylight"
        bg = (
            f"photorealistic product photography, {scene}, "
            "natural placement on surface, shallow depth of field, "
            "professional commercial lighting, 85mm lens look"
        )
        return {
            "background_prompt": bg,
            "foreground_prompt": fg,
            "negative_prompt": NEGATIVE,
            "preserve_original_subject": 0.9,
        }

    if image_type == "creative":
        scene = custom or theme_txt or "golden hour coastal lifestyle scene"
        bg = (
            f"photorealistic artistic lifestyle photograph, {scene}, "
            "cinematic natural light, not cartoon, magazine quality, DSLR"
        )
        return {
            "background_prompt": bg,
            "foreground_prompt": fg,
            "negative_prompt": NEGATIVE + ", cartoon, illustration",
            "preserve_original_subject": 0.88,
        }

    if image_type == "model":
        angle_l = (angle or "front").lower()
        if "side" in angle_l:
            view = "45 degree side profile portrait, neck and shoulders visible"
        elif "close" in angle_l:
            view = "tight close-up macro of neck and collarbone, shallow depth of field"
        else:
            view = "front facing portrait, neck and collarbone visible"

        extra = custom or theme_txt or ""
        bg = (
            f"photorealistic fashion model wearing the exact jewelry product, {view}, "
            "natural skin tones, studio beauty lighting, professional fashion photography, "
            "realistic human model, high detail"
        )
        if extra:
            bg = f"{bg}, {extra}"

        preserve = 0.82 if "close" in angle_l else 0.78
        return {
            "background_prompt": bg,
            "foreground_prompt": fg,
            "negative_prompt": NEGATIVE + ", mannequin, doll, fake skin",
            "preserve_original_subject": preserve,
        }

    raise ValueError(f"unknown image_type: {image_type}")
