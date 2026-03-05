import os
import tempfile
from io import BytesIO
from unittest.mock import MagicMock, patch

from django.test import TestCase
from PIL import Image


# ─── convert_field_to_webp ───────────────────────────────────────────────────

class ConvertFieldToWebpTests(TestCase):

    def _make_jpg(self, tmpdir, filename='test.jpg'):
        """Create a real JPEG image on disk and return its path."""
        path = os.path.join(tmpdir, filename)
        img = Image.new('RGB', (100, 100), color=(200, 100, 50))
        img.save(path, 'JPEG')
        return path

    def _make_png(self, tmpdir, filename='test.png'):
        path = os.path.join(tmpdir, filename)
        img = Image.new('RGBA', (80, 80), color=(10, 20, 30, 255))
        img.save(path, 'PNG')
        return path

    def _mock_field(self, path):
        """Return a mock ImageField with .name and .path matching `path`."""
        field = MagicMock()
        field.name = os.path.relpath(path)
        field.path = path
        return field

    def test_returns_false_for_none_field(self):
        from apps.main.image_utils import convert_field_to_webp
        self.assertFalse(convert_field_to_webp(None))

    def test_returns_false_for_empty_name(self):
        from apps.main.image_utils import convert_field_to_webp
        field = MagicMock()
        field.name = ''
        self.assertFalse(convert_field_to_webp(field))

    def test_returns_false_if_already_webp(self):
        from apps.main.image_utils import convert_field_to_webp
        field = MagicMock()
        field.name = 'some/image.webp'
        self.assertFalse(convert_field_to_webp(field))

    def test_returns_false_if_file_missing(self):
        from apps.main.image_utils import convert_field_to_webp
        field = MagicMock()
        field.name = 'ghost.jpg'
        field.path = '/tmp/does_not_exist_xyz.jpg'
        self.assertFalse(convert_field_to_webp(field))

    def test_converts_jpg_to_webp(self):
        from apps.main.image_utils import convert_field_to_webp
        with tempfile.TemporaryDirectory() as tmpdir:
            jpg_path = self._make_jpg(tmpdir)
            field = self._mock_field(jpg_path)
            result = convert_field_to_webp(field)
            self.assertTrue(result)
            # Original JPG removed
            self.assertFalse(os.path.exists(jpg_path))
            # WebP created
            webp_path = os.path.splitext(jpg_path)[0] + '.webp'
            self.assertTrue(os.path.exists(webp_path))
            # field.name updated
            self.assertTrue(field.name.endswith('.webp'))

    def test_converts_png_to_webp(self):
        from apps.main.image_utils import convert_field_to_webp
        with tempfile.TemporaryDirectory() as tmpdir:
            png_path = self._make_png(tmpdir)
            field = self._mock_field(png_path)
            result = convert_field_to_webp(field)
            self.assertTrue(result)
            webp_path = os.path.splitext(png_path)[0] + '.webp'
            self.assertTrue(os.path.exists(webp_path))

    def test_webp_output_is_valid_image(self):
        from apps.main.image_utils import convert_field_to_webp
        with tempfile.TemporaryDirectory() as tmpdir:
            jpg_path = self._make_jpg(tmpdir)
            field = self._mock_field(jpg_path)
            convert_field_to_webp(field)
            webp_path = os.path.splitext(jpg_path)[0] + '.webp'
            with Image.open(webp_path) as img:
                self.assertEqual(img.format, 'WEBP')
