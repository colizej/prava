"""
Django management command to audit and optionally fix statistics anomalies.

Usage:
    python manage.py stats_audit              # Show anomalies
    python manage.py stats_audit --fix        # Fix anomalies by recounting
    python manage.py stats_audit --threshold 1.5  # Custom threshold
"""

from django.core.management.base import BaseCommand
from blog.models import Article, ArticleLike
from profiles.models import Play
from django.db.models import Count


class Command(BaseCommand):
    help = 'Audit statistics for anomalies (likes > views) and optionally fix them'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Fix anomalies by recounting likes from ArticleLike model',
        )
        parser.add_argument(
            '--threshold',
            type=float,
            default=1.5,
            help='Ratio threshold for anomaly detection (default: 1.5)',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Maximum number of items to check (default: 100)',
        )

    def handle(self, *args, **options):
        threshold = options['threshold']
        limit = options['limit']
        fix_mode = options['fix']

        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS('📊 АУДИТ СТАТИСТИКИ'))
        self.stdout.write(self.style.SUCCESS('='*80))

        if fix_mode:
            self.stdout.write(self.style.WARNING('\n⚠️  РЕЖИМ ИСПРАВЛЕНИЯ ВКЛЮЧЕН'))

        self.stdout.write(f"\n🔍 Порог аномалии: ×{threshold} (лайков/просмотров)")
        self.stdout.write(f"📋 Лимит проверки: {limit} элементов\n")

        # Check articles
        article_anomalies = self.check_articles(threshold, limit, fix_mode)

        # Check plays
        play_anomalies = self.check_plays(threshold, limit, fix_mode)

        # Summary
        self.show_summary(article_anomalies, play_anomalies, fix_mode)

    def check_articles(self, threshold, limit, fix_mode):
        """Check articles for statistical anomalies."""
        self.stdout.write(self.style.SUCCESS('\n📝 ПРОВЕРКА СТАТЕЙ:'))
        self.stdout.write('─' * 80)

        anomalies = []
        articles = Article.objects.filter(status='published').order_by('-likes')[:limit]

        for article in articles:
            if article.views == 0 and article.likes > 0:
                ratio = float('inf')
                anomaly_level = 'CRITICAL'
            elif article.likes > article.views * threshold:
                ratio = article.likes / max(article.views, 1)
                if ratio > 10:
                    anomaly_level = 'CRITICAL'
                elif ratio > 5:
                    anomaly_level = 'HIGH'
                elif ratio > 3:
                    anomaly_level = 'MEDIUM'
                else:
                    anomaly_level = 'LOW'
            else:
                continue

            # Count actual likes from database
            actual_likes = ArticleLike.objects.filter(article=article).count()

            anomaly = {
                'article': article,
                'views': article.views,
                'likes': article.likes,
                'actual_likes': actual_likes,
                'ratio': ratio,
                'level': anomaly_level,
                'discrepancy': article.likes - actual_likes,
            }
            anomalies.append(anomaly)

            # Print anomaly
            level_color = {
                'CRITICAL': self.style.ERROR,
                'HIGH': self.style.WARNING,
                'MEDIUM': self.style.HTTP_INFO,
                'LOW': self.style.HTTP_INFO,
            }[anomaly_level]

            self.stdout.write(f"\n  📝 {article.title[:60]}...")
            self.stdout.write(level_color(f"     🚨 [{anomaly_level}] Ratio: ×{ratio:.1f}"))
            self.stdout.write(f"     Просмотров: {article.views}")
            self.stdout.write(f"     Лайков (поле): {article.likes}")
            self.stdout.write(f"     Лайков (БД): {actual_likes}")

            if anomaly['discrepancy'] != 0:
                self.stdout.write(self.style.WARNING(
                    f"     ⚠️  Расхождение: {anomaly['discrepancy']}"
                ))

            # Fix if requested
            if fix_mode:
                article.likes = actual_likes
                article.save(update_fields=['likes'])
                self.stdout.write(self.style.SUCCESS(
                    f"     ✅ Исправлено: лайков теперь {actual_likes}"
                ))

        if not anomalies:
            self.stdout.write(self.style.SUCCESS('\n  ✅ Аномалий не обнаружено'))

        return anomalies

    def check_plays(self, threshold, limit, fix_mode):
        """Check plays for statistical anomalies."""
        self.stdout.write(self.style.SUCCESS('\n\n🎭 ПРОВЕРКА ПЬЕС:'))
        self.stdout.write('─' * 80)

        anomalies = []
        plays = Play.objects.filter(status='published').order_by('-likes')[:limit]

        for play in plays:
            if play.views == 0 and play.likes > 0:
                ratio = float('inf')
                anomaly_level = 'CRITICAL'
            elif play.likes > play.views * threshold:
                ratio = play.likes / max(play.views, 1)
                if ratio > 10:
                    anomaly_level = 'CRITICAL'
                elif ratio > 5:
                    anomaly_level = 'HIGH'
                elif ratio > 3:
                    anomaly_level = 'MEDIUM'
                else:
                    anomaly_level = 'LOW'
            else:
                continue

            # Note: Play doesn't have a separate Like model yet
            # So we can't verify actual likes count

            anomaly = {
                'play': play,
                'views': play.views,
                'downloads': play.downloads,
                'likes': play.likes,
                'ratio': ratio,
                'level': anomaly_level,
            }
            anomalies.append(anomaly)

            # Print anomaly
            level_color = {
                'CRITICAL': self.style.ERROR,
                'HIGH': self.style.WARNING,
                'MEDIUM': self.style.HTTP_INFO,
                'LOW': self.style.HTTP_INFO,
            }[anomaly_level]

            self.stdout.write(f"\n  🎭 {play.title[:60]}...")
            self.stdout.write(level_color(f"     🚨 [{anomaly_level}] Ratio: ×{ratio:.1f}"))
            self.stdout.write(f"     Просмотров: {play.views}")
            self.stdout.write(f"     Скачиваний: {play.downloads}")
            self.stdout.write(f"     Лайков: {play.likes}")

            if fix_mode:
                self.stdout.write(self.style.WARNING(
                    "     ⚠️  Автоисправление для пьес пока не реализовано"
                ))

        if not anomalies:
            self.stdout.write(self.style.SUCCESS('\n  ✅ Аномалий не обнаружено'))

        return anomalies

    def show_summary(self, article_anomalies, play_anomalies, fix_mode):
        """Show summary of anomalies found."""
        self.stdout.write(self.style.SUCCESS('\n\n📊 ИТОГО:'))
        self.stdout.write('─' * 80)

        total_anomalies = len(article_anomalies) + len(play_anomalies)

        if total_anomalies == 0:
            self.stdout.write(self.style.SUCCESS('\n  ✅ Все статистики в норме!'))
        else:
            self.stdout.write(f"\n  🚨 Найдено аномалий: {total_anomalies}")

            if article_anomalies:
                critical = sum(1 for a in article_anomalies if a['level'] == 'CRITICAL')
                high = sum(1 for a in article_anomalies if a['level'] == 'HIGH')
                medium = sum(1 for a in article_anomalies if a['level'] == 'MEDIUM')
                low = sum(1 for a in article_anomalies if a['level'] == 'LOW')

                self.stdout.write(f"\n  📝 Статьи:")
                if critical:
                    self.stdout.write(self.style.ERROR(f"     🔴 Критичных: {critical}"))
                if high:
                    self.stdout.write(self.style.WARNING(f"     🟠 Высоких: {high}"))
                if medium + low:
                    self.stdout.write(f"     🟡 Средних/низких: {medium + low}")

            if play_anomalies:
                critical = sum(1 for a in play_anomalies if a['level'] == 'CRITICAL')
                high = sum(1 for a in play_anomalies if a['level'] == 'HIGH')
                medium = sum(1 for a in play_anomalies if a['level'] == 'MEDIUM')
                low = sum(1 for a in play_anomalies if a['level'] == 'LOW')

                self.stdout.write(f"\n  🎭 Пьесы:")
                if critical:
                    self.stdout.write(self.style.ERROR(f"     🔴 Критичных: {critical}"))
                if high:
                    self.stdout.write(self.style.WARNING(f"     🟠 Высоких: {high}"))
                if medium + low:
                    self.stdout.write(f"     🟡 Средних/низких: {medium + low}")

            if fix_mode:
                fixed_count = sum(1 for a in article_anomalies if a['discrepancy'] != 0)
                if fixed_count:
                    self.stdout.write(self.style.SUCCESS(f"\n  ✅ Исправлено статей: {fixed_count}"))

        self.stdout.write('\n\n' + '='*80)

        if not fix_mode and total_anomalies > 0:
            self.stdout.write(self.style.WARNING(
                '\n💡 Для исправления запустите: python manage.py stats_audit --fix\n'
            ))
