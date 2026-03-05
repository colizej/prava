"""
Shared WebP conversion utility.

Usage in model save():
    from apps.main.image_utils import convert_field_to_webp
    ...
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if convert_field_to_webp(self.image):
            type(self).objects.filter(pk=self.pk).update(image=self.image.name)
"""
import os
from io import BytesIO

from django.core.files.base import ContentFile
from PIL import Image


def convert_field_to_webp(field_file, quality: int = 85) -> bool:
    """
    Convert an ImageField file to WebP in-place.

    - Opens the current file, converts to WebP with Pillow.
    - Saves it under the same path but with .webp extension.
    - Deletes the original file.
    - Updates `field_file.name` on the in-memory field object so the caller
      can persist the new filename with a targeted UPDATE.

    Returns True if conversion happened, False if file is empty, missing,
    already WebP, or Pillow is not available.
    """
    if not field_file or not field_file.name:
        return False
    if field_file.name.lower().endswith('.webp'):
        return False

    try:
        try:
            old_path = field_file.path
        except (ValueError, NotImplementedError):
            return False  # storage without filesystem path (e.g. S3) — skip

        if not os.path.exists(old_path):
            return False

        with Image.open(old_path) as img:
            img.load()
            # Ensure a mode Pillow can encode to WebP
            if img.mode not in ('RGB', 'RGBA'):
                img = img.convert('RGBA' if img.mode == 'LA' or 'A' in img.getbands() else 'RGB')

            buf = BytesIO()
            img.save(buf, 'WEBP', quality=quality, method=4)
            buf.seek(0)
            webp_bytes = buf.read()

        # New filesystem path: same name, .webp extension
        base, _ = os.path.splitext(old_path)
        new_path = base + '.webp'

        with open(new_path, 'wb') as f:
            f.write(webp_bytes)

        # Remove original only if it's a different file
        if old_path != new_path and os.path.exists(old_path):
            os.remove(old_path)

        # Update the in-memory field name so the caller can run .update()
        base_name, _ = os.path.splitext(field_file.name)
        field_file.name = base_name + '.webp'

        return True

    except Exception:
        # Never break a model save — conversion is best-effort
        return False
