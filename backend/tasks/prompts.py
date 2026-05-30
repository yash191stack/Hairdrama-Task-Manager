NEGATIVE_BASE = (
    "cartoon, illustration, anime, low quality, blurry, deformed jewelry, "
    "different necklace, altered chain, changed clasp, extra pearls, missing pendant, "
    "duplicate product, watermark, text, logo, plastic, CGI, 3d render"
)

MODEL_NEGATIVE = (
    "fabric swatch, textile flat lay, velvet cloth only, no human, no face, headless model, "
    "jewelry on table, product on stand without person, mannequin without face, "
    "hands only, abstract fashion, clothing rack, empty background, duplicate necklace, "
    "wrong jewelry design, regenerated pendant"
)


def task_seed(task_id, image_type, angle):
    raw = f"{task_id}:{image_type}:{angle or 'none'}"
    return abs(hash(raw)) % 4294967294


def product_label(task_title, task_description, user_prompt):
    parts = []
    if task_title:
        parts.append(task_title.strip())
    if task_description:
        parts.append(task_description.strip()[:200])
    if user_prompt:
        parts.append(user_prompt.strip())
    label = ", ".join(parts) if parts else "fine jewelry necklace"
    return (
        f"{label}. CRITICAL: preserve the EXACT same jewelry from the reference — "
        "identical chain links, clasp, pendant shape, pearl count, metal color and reflections. "
        "Do not redesign or simplify the product."
    )


def build(image_type, angle, theme, user_prompt, task_title, task_description=""):
    fg = product_label(task_title, task_description, user_prompt)
    custom = (user_prompt or "").strip()
    theme_txt = (theme or "").strip()

    if image_type == "white_background":
        return {
            "mode": "cutout_white",
            "foreground_prompt": fg,
            "negative_prompt": NEGATIVE_BASE,
        }

    if image_type == "theme":
        scene = theme_txt or custom or "premium white marble countertop, luxury boutique"
        bg = (
            f"Professional DSLR product photograph. Scene: {scene}. "
            "The jewelry sits naturally on the surface. Soft commercial lighting, "
            "realistic shadows, shallow depth of field, 85mm lens, high-end catalog."
        )
        return {
            "mode": "relight",
            "background_prompt": bg,
            "foreground_prompt": fg,
            "negative_prompt": NEGATIVE_BASE,
            "preserve_original_subject": 0.97,
            "light_source_strength": 0.25,
        }

    if image_type == "creative":
        scene = custom or theme_txt or "golden hour coastal cliff, lifestyle magazine"
        bg = (
            f"Photorealistic artistic lifestyle photograph. Scene: {scene}. "
            "Cinematic natural light, editorial quality, NOT cartoon, real environment."
        )
        return {
            "mode": "relight",
            "background_prompt": bg,
            "foreground_prompt": fg,
            "negative_prompt": NEGATIVE_BASE + ", cartoon, illustration",
            "preserve_original_subject": 0.96,
            "light_source_strength": 0.28,
        }

    if image_type == "model":
        angle_l = (angle or "front").lower()
        if "side" in angle_l:
            view = (
                "45-degree side profile portrait of a real woman, full face partially visible, "
                "elegant neck and shoulder, wearing the necklace"
            )
        elif "close" in angle_l:
            view = (
                "tight beauty close-up of a real woman's neck, jawline and collarbone, "
                "face edge visible, wearing the necklace, macro DSLR"
            )
        else:
            view = (
                "front-facing portrait of a real woman, clear visible face, eyes and smile, "
                "neck and collarbones, wearing the necklace on her neck"
            )

        extra = custom or theme_txt
        bg = (
            f"High-end fashion photography. {view}. "
            "Natural skin tones, professional studio beauty lighting, photorealistic, "
            "vogue editorial, real human model, NOT fabric, NOT flat lay product shot."
        )
        if extra:
            bg = f"{bg} {extra}"

        return {
            "mode": "relight",
            "background_prompt": bg,
            "foreground_prompt": (
                f"{fg} The necklace is worn correctly on the model's neck, "
                "same product as reference, not a different design."
            ),
            "negative_prompt": NEGATIVE_BASE + ", " + MODEL_NEGATIVE,
            "preserve_original_subject": 0.91,
            "light_source_strength": 0.22,
        }

    raise ValueError(f"unknown image_type: {image_type}")
