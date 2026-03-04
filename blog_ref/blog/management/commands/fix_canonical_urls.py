"""
Django management command to fix canonical URLs.

Replaces localhost/127.0.0.1 with production domain in canonical_url field.

Usage:
    python manage.py fix_canonical_urls
    python manage.py fix_canonical_urls --dry-run
"""
from django.core.management.base import BaseCommand
from django.db.models import Q
from blog.models import Article


class Command(BaseCommand):
    help = 'Fix canonical URLs: replace localhost with production domain'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without actually changing it',
        )
        parser.add_argument(
            '--domain',
            type=str,
            default='https://piecedetheatre.be',
            help='Production domain to use (default: https://piecedetheatre.be)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        production_domain = options['domain'].rstrip('/')

        self.stdout.write('=' * 70)
        self.stdout.write('FIX CANONICAL URLs - localhost → production')
        self.stdout.write('=' * 70)
        self.stdout.write('')

        # Find articles with localhost
        articles = Article.objects.filter(
            Q(canonical_url__contains='localhost') |
            Q(canonical_url__contains='127.0.0.1')
        )

        total = articles.count()

        if total == 0:
            self.stdout.write(self.style.SUCCESS('✅ Aucun article avec localhost trouvé!'))
            return

        self.stdout.write(f'📊 {total} articles avec localhost trouvés')
        self.stdout.write('')

        if dry_run:
            self.stdout.write(self.style.WARNING('⚠️  MODE DRY-RUN: Aucune modification ne sera effectuée'))
            self.stdout.write('')

        # Show sample
        self.stdout.write('Exemple de corrections:')
        for article in articles[:3]:
            old_url = article.canonical_url
            new_url = old_url.replace('http://localhost:8000', production_domain)
            new_url = new_url.replace('http://127.0.0.1:8000', production_domain)
            new_url = new_url.replace('https://localhost:8000', production_domain)

            self.stdout.write(f'  • {article.slug}')
            self.stdout.write(f'    AVANT: {old_url}')
            self.stdout.write(f'    APRÈS: {new_url}')
            self.stdout.write('')

        if dry_run:
            self.stdout.write(self.style.SUCCESS(f'✅ Dry-run terminé. {total} articles seraient modifiés.'))
            return

        # Confirm
        if not options.get('skip_confirmation'):
            self.stdout.write(self.style.WARNING(f'⚠️  Cela va modifier {total} articles!'))
            response = input('Continuer? (oui/non): ').strip().lower()
            if response not in ['oui', 'o', 'yes', 'y']:
                self.stdout.write(self.style.ERROR('❌ Opération annulée'))
                return

        self.stdout.write('')
        self.stdout.write('🔧 Mise à jour en cours...')
        self.stdout.write('')

        success_count = 0
        error_count = 0

        for idx, article in enumerate(articles, 1):
            try:
                old_url = article.canonical_url
                new_url = old_url.replace('http://localhost:8000', production_domain)
                new_url = new_url.replace('http://127.0.0.1:8000', production_domain)
                new_url = new_url.replace('https://localhost:8000', production_domain)

                if new_url != old_url:
                    article.canonical_url = new_url
                    article.save(update_fields=['canonical_url'])
                    success_count += 1

                    # Show progress
                    if idx <= 5 or idx % 50 == 0 or idx == total:
                        self.stdout.write(f'  ✅ [{idx}/{total}] {article.slug}')

            except Exception as e:
                error_count += 1
                self.stdout.write(self.style.ERROR(f'  ❌ [{idx}/{total}] {article.slug}: {str(e)}'))

        self.stdout.write('')
        self.stdout.write('=' * 70)
        self.stdout.write(self.style.SUCCESS(f'✅ Succès: {success_count}'))
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f'❌ Erreurs: {error_count}'))
        self.stdout.write(f'📊 Total: {total}')
        self.stdout.write('=' * 70)
