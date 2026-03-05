"""
management command: python manage.py convert_images_to_webp

Converts all existing JPG/PNG images in media/ to WebP (except signs/).
Updates DB field values to reflect the new filenames.

Models covered:
  - Question.image           (media/questions/)
  - BlogPost.featured_image  (media/blog/)
  - ArticleImage.image       (media/reglementation/)
  - UserProfile.avatar       (media/avatars/)

Safe to run multiple times — already-WebP files are skipped.
"""
from django.core.management.base import BaseCommand

from apps.main.image_utils import convert_field_to_webp


class Command(BaseCommand):
    help = 'Convert existing media images to WebP (skips signs/ folder).'

    def handle(self, *args, **options):
        total_converted = 0
        total_saved = 0

        total_converted += self._convert_model(
            'Question', 'examens', 'image',
        )
        total_converted += self._convert_model(
            'BlogPost', 'blog', 'featured_image',
        )
        total_converted += self._convert_model(
            'ArticleImage', 'reglementation', 'image',
        )
        total_converted += self._convert_model(
            'UserProfile', 'accounts', 'avatar',
        )

        self.stdout.write(self.style.SUCCESS(
            f'\n✓ Done — {total_converted} image(s) converted to WebP.'
        ))

    def _convert_model(self, model_name, app_label, field_name):
        from django.apps import apps
        Model = apps.get_model(app_label, model_name)

        qs = Model.objects.exclude(**{f'{field_name}': ''}).exclude(
            **{f'{field_name}': None}
        )
        count = 0
        for obj in qs.iterator():
            field = getattr(obj, field_name)
            if not field or not field.name:
                continue
            if field.name.lower().endswith('.webp'):
                continue

            old_name = field.name
            converted = convert_field_to_webp(field)
            if converted:
                # field.name is now updated to .webp — persist to DB
                Model.objects.filter(pk=obj.pk).update(**{field_name: field.name})
                count += 1
                self.stdout.write(
                    f'  [{model_name}#{obj.pk}] {old_name} → {field.name}'
                )

        label = f'{model_name}.{field_name}'
        self.stdout.write(f'  {label}: {count} converted')
        return count
