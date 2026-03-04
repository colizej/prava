# Generated migration for migrating scheduled status to published

from django.db import migrations


def migrate_scheduled_to_published(apps, schema_editor):
    """
    Migrate all Article objects with status='scheduled' to status='published'.
    This is a data migration to clean up after removing 'scheduled' from STATUS_CHOICES.
    """
    Article = apps.get_model('blog', 'Article')

    # Find all articles with 'scheduled' status (if any exist)
    scheduled_articles = Article.objects.filter(status='scheduled')
    count = scheduled_articles.count()

    if count > 0:
        # Update them to 'published'
        scheduled_articles.update(status='published')
        print(f"✓ Migrated {count} scheduled article(s) to published status")
    else:
        print("✓ No scheduled articles found - nothing to migrate")


def reverse_migration(apps, schema_editor):
    """
    Reverse migration - not really needed but included for completeness.
    We can't reliably determine which articles should be 'scheduled' again.
    """
    print("⚠️ Reverse migration: Cannot restore 'scheduled' status automatically")
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0019_remove_scheduled_status'),
    ]

    operations = [
        migrations.RunPython(migrate_scheduled_to_published, reverse_migration),
    ]
