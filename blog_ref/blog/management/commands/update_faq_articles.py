"""
Management command to re-save all articles with FAQ to apply hiding logic.
"""

from django.core.management.base import BaseCommand
from blog.models import Article
import re


class Command(BaseCommand):
    help = 'Re-save articles with FAQ to hide FAQ blocks in content_html'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without actually updating',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - no changes will be made'))

        # Find all articles with FAQ in markdown
        all_articles = Article.objects.all()
        total = all_articles.count()

        self.stdout.write(f'Scanning {total} articles for FAQ...')

        faq_articles = []

        for article in all_articles:
            # Check for FAQ section marker: ### FAQ, ### Foire aux Questions, ### Les questions fréquentes, etc.
            if article.content_markdown and re.search(r'###\s*(?:FAQ|Foire aux [Qq]uestions|Les questions [Ff]réquentes|Questions [Ff]réquentes)', article.content_markdown, re.IGNORECASE):
                faq_articles.append(article)

        self.stdout.write(f'Found {len(faq_articles)} articles with FAQ in Markdown')

        if not faq_articles:
            self.stdout.write(self.style.SUCCESS('No articles with FAQ found'))
            return

        updated = 0
        skipped = 0

        for i, article in enumerate(faq_articles, 1):
            # Progress indicator
            progress = f'[{i}/{len(faq_articles)}]'

            # Check if FAQ section heading is still visible in HTML
            # OR if FAQ_SECTION_MARKER is missing (needed for banner positioning)
            needs_update = True
            if article.content_html:
                # Check for FAQ heading in HTML - if present, needs update
                if re.search(r'<h3[^>]*>(?:FAQ|Foire aux [Qq]uestions|Les questions [Ff]réquentes|Questions [Ff]réquentes)[^<]*</h3>', article.content_html, re.IGNORECASE):
                    needs_update = True  # FAQ heading visible, must update
                elif 'FAQ_SECTION_MARKER' not in article.content_html and 'FAQ_HIDDEN' in article.content_html:
                    needs_update = True  # FAQ hidden but marker missing, needs update
                elif 'FAQ_HIDDEN' in article.content_html and 'FAQ_SECTION_MARKER' in article.content_html:
                    needs_update = False  # Already hidden with marker
                else:
                    needs_update = True  # No FAQ content, but has FAQ in markdown

            if needs_update:
                if dry_run:
                    self.stdout.write(f'  {progress} WOULD UPDATE: {article.title[:50]} ({article.slug})')
                else:
                    self.stdout.write(f'  {progress} Updating: {article.title[:50]} ({article.slug})')
                    article.save()  # This will trigger FAQ hiding
                updated += 1
            else:
                self.stdout.write(f'  {progress} Skipped: {article.title[:50]} (already hidden)')
                skipped += 1

        if dry_run:
            self.stdout.write(self.style.WARNING(f'\n✨ DRY RUN: Would update {updated} articles, skip {skipped}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'\n✨ Updated {updated} articles, skipped {skipped}'))
