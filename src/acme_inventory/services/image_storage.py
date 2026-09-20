from pathlib import Path
from uuid import uuid4

from flask import current_app, url_for
from PIL import Image, UnidentifiedImageError

ALLOWED_IMAGE_FORMATS = {"PNG": "png", "JPEG": "jpg", "GIF": "gif", "WEBP": "webp"}


def store_image(file, folder):
    if folder not in {"profiles", "items"}:
        raise ValueError("Invalid image folder.")
    try:
        image = Image.open(file.stream)
        extension = ALLOWED_IMAGE_FORMATS.get(image.format)
        image.verify()
        if not extension:
            raise ValueError("Use a PNG, JPEG, GIF, or WebP image.")
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise ValueError("Upload a valid image.") from None
    finally:
        file.stream.seek(0)
    directory = Path(current_app.config["UPLOAD_DIR"]) / folder
    directory.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid4().hex}.{extension}"
    file.save(directory / filename)
    return url_for("media.upload", filename=f"{folder}/{filename}")
