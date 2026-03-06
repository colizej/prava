import os
import tempfile
from io import BytesIO
from unittest.mock import MagicMock, patch

from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
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


# ─── Security: honeypot & rate limiting on contact form ───────────────────────

VALID_CONTACT_DATA = {
    'name': 'Alice',
    'email': 'alice@example.com',
    'subject': 'Hello',
    'message': 'This is a test message.',
}


class ContactHoneypotTests(TestCase):
    """Bots that fill the hidden 'hp' field are silently discarded."""

    def setUp(self):
        cache.clear()

    def test_honeypot_filled_redirects_silently(self):
        """POST with 'hp' set → fake-success redirect, no ContactMessage saved."""
        from apps.main.models import ContactMessage
        data = {**VALID_CONTACT_DATA, 'hp': 'gotcha'}
        response = self.client.post(reverse('main:contact'), data,
                                    REMOTE_ADDR='10.1.1.1')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ContactMessage.objects.count(), 0)

    def test_honeypot_empty_allows_message(self):
        """POST without 'hp' proceeds and saves the message."""
        from apps.main.models import ContactMessage
        data = {**VALID_CONTACT_DATA, 'hp': ''}
        response = self.client.post(reverse('main:contact'), data,
                                    REMOTE_ADDR='10.1.1.2')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ContactMessage.objects.count(), 1)

    def test_honeypot_absent_allows_message(self):
        """POST without 'hp' key at all proceeds normally."""
        from apps.main.models import ContactMessage
        response = self.client.post(reverse('main:contact'), VALID_CONTACT_DATA,
                                    REMOTE_ADDR='10.1.1.3')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ContactMessage.objects.count(), 1)


class ContactRateLimitTests(TestCase):
    """After 3 successful messages from the same IP, next is blocked."""

    def setUp(self):
        cache.clear()

    def _post(self, ip='10.2.2.1'):
        return self.client.post(
            reverse('main:contact'),
            VALID_CONTACT_DATA,
            REMOTE_ADDR=ip,
        )

    def test_blocked_after_three_messages(self):
        """3 successful POSTs exhaust the quota; 4th is redirected with error."""
        for _ in range(3):
            self._post()
        response = self._post()
        self.assertEqual(response.status_code, 302)
        self.assertIn('Trop de messages', response.wsgi_request._messages._queued_messages[0].message
                      if hasattr(response.wsgi_request, '_messages') else '')
        from apps.main.models import ContactMessage
        # Only 3 messages saved, not 4
        self.assertEqual(ContactMessage.objects.count(), 3)

    def test_not_blocked_on_third_message(self):
        """Exactly 3 messages are allowed (the 3rd itself succeeds)."""
        from apps.main.models import ContactMessage
        for _ in range(3):
            self._post(ip='10.2.2.2')
        self.assertEqual(ContactMessage.objects.count(), 3)

    def test_different_ips_are_independent(self):
        """Rate limit is per-IP; exhausting one IP does not block another."""
        from apps.main.models import ContactMessage
        for _ in range(3):
            self._post(ip='10.2.2.3')
        # Different IP should still be allowed
        self._post(ip='10.2.2.4')
        self.assertEqual(ContactMessage.objects.count(), 4)
