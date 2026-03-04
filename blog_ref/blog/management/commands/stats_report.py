"""
Django management command to track and report statistics changes for articles and plays.

Usage:
    python manage.py stats_report           # Show changes since last run
    python manage.py stats_report --full    # Show full statistics table
    python manage.py stats_report --reset   # Reset statistics baseline
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Count
from blog.models import Article
from profiles.models import Play
from library.models import ClassicPlay
from creators.models import Project
from interactive.models import Quiz, QuizResult
import json
import os
from pathlib import Path
from datetime import datetime
from decimal import Decimal


class Command(BaseCommand):
    help = 'Track and report statistics changes for articles and plays'

    def add_arguments(self, parser):
        parser.add_argument(
            '--full',
            action='store_true',
            help='Show full statistics table instead of just changes',
        )
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset statistics baseline (save current state)',
        )
        parser.add_argument(
            '--top',
            type=int,
            default=20,
            help='Number of items to show (default: 20)',
        )

    def handle(self, *args, **options):
        # Path to stats file
        stats_file = Path('output/stats_history.json')
        stats_file.parent.mkdir(exist_ok=True)

        # Load previous stats
        previous_stats = self.load_previous_stats(stats_file)

        # Collect current stats
        current_stats = self.collect_current_stats()

        if options['reset']:
            self.save_stats(stats_file, current_stats)
            self.stdout.write(self.style.SUCCESS(
                f"\n✅ Статистика сохранена как базовая линия:\n"
                f"   📝 {len(current_stats['articles'])} статей\n"
                f"   🎭 {len(current_stats['plays'])} пьес (каталог)\n"
                f"   📚 {len(current_stats['library_plays'])} пьес (библиотека)\n"
                f"   🎬 {len(current_stats['projects'])} проектов\n"
                f"   🎯 {len(current_stats['quizzes'])} квизов"
            ))
            return

        if options['full']:
            self.show_full_stats(current_stats, options['top'])
        else:
            # Compare and show changes
            if previous_stats:
                self.show_changes(previous_stats, current_stats, options['top'])
            else:
                self.stdout.write(self.style.WARNING(
                    "\n⚠️  Нет предыдущих данных для сравнения. Запустите с --reset для создания базовой линии."
                ))
                self.show_full_stats(current_stats, options['top'])

        # Save current stats for next comparison
        self.save_stats(stats_file, current_stats)

    def collect_current_stats(self):
        """Collect current statistics from database."""
        stats = {
            'timestamp': datetime.now().isoformat(),
            'articles': {},
            'plays': {},
            'library_plays': {},
            'projects': {},
            'quizzes': {},
        }

        # Collect article stats
        for article in Article.objects.filter(status='published').select_related('profile_author'):
            stats['articles'][article.slug] = {
                'title': article.title,
                'author': article.profile_author.display_name if article.profile_author else 'Anonymous',
                'views': article.views,
                'likes': article.likes,
                'published_at': article.published_at.isoformat() if article.published_at else None,
            }

        # Collect play stats (catalog)
        for play in Play.objects.filter(status='published').prefetch_related('authors'):
            # Get first author
            first_author = play.authors.first()
            author_name = first_author.display_name if first_author else 'Anonymous'

            stats['plays'][play.slug] = {
                'title': play.title,
                'author': author_name,
                'views': play.views,
                'downloads': play.downloads,
                'likes': play.likes,
                'published_at': play.published_at.isoformat() if play.published_at else None,
            }

        # Collect library play stats (classic plays)
        for play in ClassicPlay.objects.filter(status='published').select_related('author'):
            stats['library_plays'][play.slug] = {
                'title': play.title,
                'author': play.author.name if play.author else 'Anonymous',
                'views': play.views_count,
                'likes': play.likes_count,
                'bookmarks': play.bookmarks_count,
                'published_at': play.published_at.isoformat() if play.published_at else None,
            }

        # Collect project stats
        for project in Project.objects.filter(is_active=True, is_archived=False).select_related('creator'):
            # Count active members (excluding creator)
            members_count = project.members.filter(status='active').exclude(profile=project.creator).count()

            # Count comments
            comments_count = project.comments.count()

            stats['projects'][project.slug] = {
                'name': project.name,
                'creator': project.creator.display_name if project.creator else 'Anonymous',
                'type': project.get_project_type_display(),
                'members': members_count,
                'comments': comments_count,
                'is_public': project.is_public,
                'created_at': project.created_at.isoformat(),
            }

        # Collect quiz stats
        for quiz in Quiz.objects.filter(is_published=True):
            # Count total attempts
            attempts_count = QuizResult.objects.filter(quiz=quiz).count()

            # Count unique users
            unique_users = QuizResult.objects.filter(quiz=quiz).values('user').distinct().count()

            # Calculate average score
            results = QuizResult.objects.filter(quiz=quiz).values_list('percentage', flat=True)
            avg_score = sum(results) / len(results) if results else 0

            stats['quizzes'][quiz.slug] = {
                'title': quiz.title,
                'attempts': attempts_count,
                'unique_users': unique_users,
                'avg_score': round(avg_score, 1),
                'created_at': quiz.created_at.isoformat(),
            }

        return stats

    def load_previous_stats(self, stats_file):
        """Load previous statistics from file."""
        if not stats_file.exists():
            return None

        try:
            with open(stats_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None

    def save_stats(self, stats_file, stats):
        """Save current statistics to file."""
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)

    def show_changes(self, previous, current, top_n):
        """Show changes between previous and current statistics."""
        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS('📊 СТАТИСТИКА ИЗМЕНЕНИЙ'))
        self.stdout.write(self.style.SUCCESS('='*80))

        # Parse previous timestamp
        prev_time = datetime.fromisoformat(previous['timestamp'])
        curr_time = datetime.fromisoformat(current['timestamp'])
        time_diff = curr_time - prev_time

        self.stdout.write(f"\n⏱  Период: {self.format_time_diff(time_diff)}")
        self.stdout.write(f"   С: {prev_time.strftime('%d.%m.%Y %H:%M')}")
        self.stdout.write(f"   По: {curr_time.strftime('%d.%m.%Y %H:%M')}")

        # Article changes
        article_changes = self.calculate_changes(
            previous.get('articles', {}),
            current.get('articles', {})
        )

        if article_changes:
            self.stdout.write(self.style.SUCCESS('\n\n📝 СТАТЬИ:'))
            self.stdout.write('─' * 80)

            # Sort by total activity (views + likes changes)
            sorted_articles = sorted(
                article_changes,
                key=lambda x: abs(x['views_change']) + abs(x['likes_change']),
                reverse=True
            )[:top_n]

            if sorted_articles:
                for item in sorted_articles:
                    self.print_item_change(item, item_type='article')
            else:
                self.stdout.write('  Нет изменений')

        # Play changes
        play_changes = self.calculate_changes(
            previous.get('plays', {}),
            current.get('plays', {}),
            include_downloads=True
        )

        if play_changes:
            self.stdout.write(self.style.SUCCESS('\n\n🎭 ПЬЕСЫ:'))
            self.stdout.write('─' * 80)

            # Sort by total activity (views + downloads + likes changes)
            sorted_plays = sorted(
                play_changes,
                key=lambda x: abs(x['views_change']) + abs(x.get('downloads_change', 0)) + abs(x['likes_change']),
                reverse=True
            )[:top_n]

            if sorted_plays:
                for item in sorted_plays:
                    self.print_item_change(item, item_type='play')
            else:
                self.stdout.write('  Нет изменений')

        # Library play changes (classic plays)
        library_changes = self.calculate_library_changes(
            previous.get('library_plays', {}),
            current.get('library_plays', {})
        )

        if library_changes:
            self.stdout.write(self.style.SUCCESS('\n\n📚 БИБЛИОТЕКА (классические пьесы):'))
            self.stdout.write('─' * 80)

            # Sort by total activity
            sorted_library = sorted(
                library_changes,
                key=lambda x: abs(x['views_change']) + abs(x['likes_change']) + abs(x.get('bookmarks_change', 0)),
                reverse=True
            )[:top_n]

            if sorted_library:
                for item in sorted_library:
                    self.print_item_change(item, item_type='library_play')
            else:
                self.stdout.write('  Нет изменений')

        # Project changes
        project_changes = self.calculate_project_changes(
            previous.get('projects', {}),
            current.get('projects', {})
        )

        if project_changes:
            self.stdout.write(self.style.SUCCESS('\n\n🎬 ПРОЕКТЫ:'))
            self.stdout.write('─' * 80)

            # Sort by total activity
            sorted_projects = sorted(
                project_changes,
                key=lambda x: abs(x.get('members_change', 0)) + abs(x.get('comments_change', 0)),
                reverse=True
            )[:top_n]

            if sorted_projects:
                for item in sorted_projects:
                    self.print_project_change(item)
            else:
                self.stdout.write('  Нет изменений')

        # Quiz changes
        quiz_changes = self.calculate_quiz_changes(
            previous.get('quizzes', {}),
            current.get('quizzes', {})
        )

        if quiz_changes:
            self.stdout.write(self.style.SUCCESS('\n\n🎯 КВИЗЫ:'))
            self.stdout.write('─' * 80)

            # Sort by attempts change
            sorted_quizzes = sorted(
                quiz_changes,
                key=lambda x: abs(x.get('attempts_change', 0)),
                reverse=True
            )[:top_n]

            if sorted_quizzes:
                for item in sorted_quizzes:
                    self.print_quiz_change(item)
            else:
                self.stdout.write('  Нет изменений')

        # Summary
        self.show_summary(article_changes, play_changes, library_changes, project_changes, quiz_changes)

    def calculate_changes(self, previous, current, include_downloads=False):
        """Calculate changes between two stat dictionaries."""
        changes = []

        for slug, curr_data in current.items():
            prev_data = previous.get(slug, {})

            views_change = curr_data.get('views', 0) - prev_data.get('views', 0)
            likes_change = curr_data.get('likes', 0) - prev_data.get('likes', 0)

            change_item = {
                'slug': slug,
                'title': curr_data.get('title', 'Unknown'),
                'author': curr_data.get('author', 'Anonymous'),
                'views_change': views_change,
                'likes_change': likes_change,
                'current_views': curr_data.get('views', 0),
                'current_likes': curr_data.get('likes', 0),
                'is_new': slug not in previous,
            }

            if include_downloads:
                downloads_change = curr_data.get('downloads', 0) - prev_data.get('downloads', 0)
                change_item['downloads_change'] = downloads_change
                change_item['current_downloads'] = curr_data.get('downloads', 0)

            # Only include if there are changes or it's new
            if (views_change != 0 or likes_change != 0 or
                (include_downloads and downloads_change != 0) or
                change_item['is_new']):
                changes.append(change_item)

        return changes

    def calculate_library_changes(self, previous, current):
        """Calculate changes for library plays (includes bookmarks)."""
        changes = []

        for slug, curr_data in current.items():
            prev_data = previous.get(slug, {})

            views_change = curr_data.get('views', 0) - prev_data.get('views', 0)
            likes_change = curr_data.get('likes', 0) - prev_data.get('likes', 0)
            bookmarks_change = curr_data.get('bookmarks', 0) - prev_data.get('bookmarks', 0)

            change_item = {
                'slug': slug,
                'title': curr_data.get('title', 'Unknown'),
                'author': curr_data.get('author', 'Anonymous'),
                'views_change': views_change,
                'likes_change': likes_change,
                'bookmarks_change': bookmarks_change,
                'current_views': curr_data.get('views', 0),
                'current_likes': curr_data.get('likes', 0),
                'current_bookmarks': curr_data.get('bookmarks', 0),
                'is_new': slug not in previous,
            }

            # Only include if there are changes or it's new
            if (views_change != 0 or likes_change != 0 or bookmarks_change != 0 or
                change_item['is_new']):
                changes.append(change_item)

        return changes

    def calculate_project_changes(self, previous, current):
        """Calculate changes for projects (members and comments)."""
        changes = []

        for slug, curr_data in current.items():
            prev_data = previous.get(slug, {})

            members_change = curr_data.get('members', 0) - prev_data.get('members', 0)
            comments_change = curr_data.get('comments', 0) - prev_data.get('comments', 0)

            change_item = {
                'slug': slug,
                'name': curr_data.get('name', 'Unknown'),
                'creator': curr_data.get('creator', 'Anonymous'),
                'type': curr_data.get('type', 'Autre'),
                'members_change': members_change,
                'comments_change': comments_change,
                'current_members': curr_data.get('members', 0),
                'current_comments': curr_data.get('comments', 0),
                'is_public': curr_data.get('is_public', False),
                'is_new': slug not in previous,
            }

            # Only include if there are changes or it's new
            if (members_change != 0 or comments_change != 0 or change_item['is_new']):
                changes.append(change_item)

        return changes

    def calculate_quiz_changes(self, previous, current):
        """Calculate changes for quizzes (attempts and users)."""
        changes = []

        for slug, curr_data in current.items():
            prev_data = previous.get(slug, {})

            attempts_change = curr_data.get('attempts', 0) - prev_data.get('attempts', 0)
            users_change = curr_data.get('unique_users', 0) - prev_data.get('unique_users', 0)

            change_item = {
                'slug': slug,
                'title': curr_data.get('title', 'Unknown'),
                'attempts_change': attempts_change,
                'users_change': users_change,
                'current_attempts': curr_data.get('attempts', 0),
                'current_users': curr_data.get('unique_users', 0),
                'current_avg_score': curr_data.get('avg_score', 0),
                'prev_avg_score': prev_data.get('avg_score', 0),
                'is_new': slug not in previous,
            }

            # Only include if there are changes or it's new
            if (attempts_change != 0 or users_change != 0 or change_item['is_new']):
                changes.append(change_item)

        return changes

    def print_item_change(self, item, item_type='article'):
        """Print a single item change with formatting."""
        # Icon and title
        if item_type == 'article':
            icon = '📝'
        elif item_type == 'library_play':
            icon = '📚'
        else:  # play
            icon = '🎭'

        if item['is_new']:
            self.stdout.write(self.style.SUCCESS(f"\n  {icon} {item['title']} ⭐ НОВОЕ"))
        else:
            self.stdout.write(f"\n  {icon} {item['title']}")

        # Author
        self.stdout.write(self.style.HTTP_INFO(f"     Автор: {item['author']}"))

        # Changes with current values
        changes = []

        # Views
        if item['views_change'] > 0:
            changes.append(self.style.SUCCESS(f"👁 {item['current_views']} (+{item['views_change']})"))
        elif item['views_change'] < 0:
            changes.append(self.style.ERROR(f"👁 {item['current_views']} ({item['views_change']})"))
        else:
            changes.append(f"👁 {item['current_views']}")

        # Downloads (for catalog plays)
        if 'downloads_change' in item:
            if item['downloads_change'] > 0:
                changes.append(self.style.SUCCESS(f"⬇️ {item['current_downloads']} (+{item['downloads_change']})"))
            elif item['downloads_change'] < 0:
                changes.append(self.style.ERROR(f"⬇️ {item['current_downloads']} ({item['downloads_change']})"))
            else:
                changes.append(f"⬇️ {item['current_downloads']}")

        # Bookmarks (for library plays)
        if 'bookmarks_change' in item:
            if item['bookmarks_change'] > 0:
                changes.append(self.style.SUCCESS(f"🔖 {item['current_bookmarks']} (+{item['bookmarks_change']})"))
            elif item['bookmarks_change'] < 0:
                changes.append(self.style.ERROR(f"🔖 {item['current_bookmarks']} ({item['bookmarks_change']})"))
            else:
                changes.append(f"🔖 {item['current_bookmarks']}")

        # Likes
        if item['likes_change'] > 0:
            changes.append(self.style.SUCCESS(f"❤️ {item['current_likes']} (+{item['likes_change']})"))
        elif item['likes_change'] < 0:
            changes.append(self.style.ERROR(f"❤️ {item['current_likes']} ({item['likes_change']})"))
        else:
            changes.append(f"❤️ {item['current_likes']}")

        self.stdout.write(f"     {' | '.join(changes)}")

        # Warning for anomalies (likes > views)
        if item['current_likes'] > item['current_views']:
            ratio = item['current_likes'] / max(item['current_views'], 1)
            if ratio > 3:  # Very suspicious: 3x more likes than views
                self.stdout.write(self.style.WARNING(
                    f"     ⚠️  АНОМАЛИЯ: {item['current_likes']} лайков > {item['current_views']} просмотров (×{ratio:.1f})"
                ))
            elif ratio > 1.5:  # Moderately suspicious
                self.stdout.write(self.style.HTTP_INFO(
                    f"     ℹ️  Лайков больше просмотров: {item['current_likes']} > {item['current_views']}"
                ))

    def print_project_change(self, item):
        """Print a single project change with formatting."""
        icon = '🎬'

        if item['is_new']:
            self.stdout.write(self.style.SUCCESS(f"\n  {icon} {item['name']} ⭐ НОВОЕ"))
        else:
            self.stdout.write(f"\n  {icon} {item['name']}")

        # Creator and type
        self.stdout.write(self.style.HTTP_INFO(f"     Создатель: {item['creator']} | Тип: {item['type']}"))

        # Changes with current values
        changes = []

        # Members
        if item['members_change'] > 0:
            changes.append(self.style.SUCCESS(f"👥 {item['current_members']} (+{item['members_change']})"))
        elif item['members_change'] < 0:
            changes.append(self.style.ERROR(f"👥 {item['current_members']} ({item['members_change']})"))
        else:
            changes.append(f"👥 {item['current_members']}")

        # Comments
        if item['comments_change'] > 0:
            changes.append(self.style.SUCCESS(f"💬 {item['current_comments']} (+{item['comments_change']})"))
        elif item['comments_change'] < 0:
            changes.append(self.style.ERROR(f"💬 {item['current_comments']} ({item['comments_change']})"))
        else:
            changes.append(f"💬 {item['current_comments']}")

        # Public status
        if item['is_public']:
            changes.append("🌐 публичный")

        self.stdout.write(f"     {' | '.join(changes)}")

    def print_quiz_change(self, item):
        """Print a single quiz change with formatting."""
        icon = '🎯'

        if item['is_new']:
            self.stdout.write(self.style.SUCCESS(f"\n  {icon} {item['title']} ⭐ НОВОЕ"))
        else:
            self.stdout.write(f"\n  {icon} {item['title']}")

        # Changes with current values
        changes = []

        # Attempts
        if item['attempts_change'] > 0:
            changes.append(self.style.SUCCESS(f"🎮 {item['current_attempts']} попыток (+{item['attempts_change']})"))
        elif item['attempts_change'] < 0:
            changes.append(self.style.ERROR(f"🎮 {item['current_attempts']} попыток ({item['attempts_change']})"))
        else:
            changes.append(f"🎮 {item['current_attempts']} попыток")

        # Unique users
        if item['users_change'] > 0:
            changes.append(self.style.SUCCESS(f"👤 {item['current_users']} польз. (+{item['users_change']})"))
        elif item['users_change'] < 0:
            changes.append(self.style.ERROR(f"👤 {item['current_users']} польз. ({item['users_change']})"))
        else:
            changes.append(f"👤 {item['current_users']} польз.")

        # Average score
        avg_score = item['current_avg_score']
        prev_avg_score = item['prev_avg_score']
        score_change = avg_score - prev_avg_score

        if score_change > 0.5:
            changes.append(self.style.SUCCESS(f"📊 {avg_score:.1f}% (+{score_change:.1f}%)"))
        elif score_change < -0.5:
            changes.append(self.style.ERROR(f"📊 {avg_score:.1f}% ({score_change:.1f}%)"))
        else:
            changes.append(f"📊 {avg_score:.1f}%")

        self.stdout.write(f"     {' | '.join(changes)}")

    def show_summary(self, article_changes, play_changes, library_changes, project_changes, quiz_changes):
        """Show summary statistics."""
        self.stdout.write(self.style.SUCCESS('\n\n📈 ИТОГО:'))
        self.stdout.write('─' * 80)

        # Calculate changes
        total_article_views_change = sum(item['views_change'] for item in article_changes)
        total_article_likes_change = sum(item['likes_change'] for item in article_changes)
        new_articles = sum(1 for item in article_changes if item['is_new'])

        # Calculate current totals
        total_article_views_current = sum(item['current_views'] for item in article_changes)
        total_article_likes_current = sum(item['current_likes'] for item in article_changes)

        self.stdout.write(f"\n  📝 Статьи (изменения с прошлого запуска):")
        self.stdout.write(f"     Новых: {new_articles}")
        self.stdout.write(f"     Просмотров: {self.format_change(total_article_views_change)}")
        self.stdout.write(f"     Лайков: {self.format_change(total_article_likes_change)}")
        if article_changes:
            self.stdout.write(self.style.HTTP_INFO(
                f"     💡 Текущие итоги: {total_article_views_current} просмотров, {total_article_likes_current} лайков"
            ))

        # Play summary
        total_play_views_change = sum(item['views_change'] for item in play_changes)
        total_play_downloads_change = sum(item.get('downloads_change', 0) for item in play_changes)
        total_play_likes_change = sum(item['likes_change'] for item in play_changes)
        new_plays = sum(1 for item in play_changes if item['is_new'])

        # Calculate current totals
        total_play_views_current = sum(item['current_views'] for item in play_changes)
        total_play_downloads_current = sum(item.get('current_downloads', 0) for item in play_changes)
        total_play_likes_current = sum(item['current_likes'] for item in play_changes)

        self.stdout.write(f"\n  🎭 Пьесы (изменения с прошлого запуска):")
        self.stdout.write(f"     Новых: {new_plays}")
        self.stdout.write(f"     Просмотров: {self.format_change(total_play_views_change)}")
        self.stdout.write(f"     Скачиваний: {self.format_change(total_play_downloads_change)}")
        self.stdout.write(f"     Лайков: {self.format_change(total_play_likes_change)}")
        if play_changes:
            self.stdout.write(self.style.HTTP_INFO(
                f"     💡 Текущие итоги: {total_play_views_current} просмотров, {total_play_downloads_current} скачиваний, {total_play_likes_current} лайков"
            ))

        # Library play summary
        total_library_views_change = sum(item['views_change'] for item in library_changes)
        total_library_likes_change = sum(item['likes_change'] for item in library_changes)
        total_library_bookmarks_change = sum(item.get('bookmarks_change', 0) for item in library_changes)
        new_library = sum(1 for item in library_changes if item['is_new'])

        # Calculate current totals
        total_library_views_current = sum(item['current_views'] for item in library_changes)
        total_library_likes_current = sum(item['current_likes'] for item in library_changes)
        total_library_bookmarks_current = sum(item.get('current_bookmarks', 0) for item in library_changes)

        self.stdout.write(f"\n  📚 Библиотека (изменения с прошлого запуска):")
        self.stdout.write(f"     Новых: {new_library}")
        self.stdout.write(f"     Просмотров: {self.format_change(total_library_views_change)}")
        self.stdout.write(f"     Лайков: {self.format_change(total_library_likes_change)}")
        self.stdout.write(f"     Закладок: {self.format_change(total_library_bookmarks_change)}")
        if library_changes:
            self.stdout.write(self.style.HTTP_INFO(
                f"     💡 Текущие итоги: {total_library_views_current} просмотров, {total_library_likes_current} лайков, {total_library_bookmarks_current} закладок"
            ))

        # Project summary
        total_members_change = sum(item.get('members_change', 0) for item in project_changes)
        total_comments_change = sum(item.get('comments_change', 0) for item in project_changes)
        new_projects = sum(1 for item in project_changes if item['is_new'])
        public_projects = sum(1 for item in project_changes if item.get('is_public', False))

        # Calculate current totals
        total_members_current = sum(item.get('current_members', 0) for item in project_changes)
        total_comments_current = sum(item.get('current_comments', 0) for item in project_changes)

        self.stdout.write(f"\n  🎬 Проекты (изменения с прошлого запуска):")
        self.stdout.write(f"     Новых: {new_projects}")
        self.stdout.write(f"     Участников: {self.format_change(total_members_change)}")
        self.stdout.write(f"     Комментариев: {self.format_change(total_comments_change)}")
        if project_changes:
            self.stdout.write(self.style.HTTP_INFO(
                f"     💡 Текущие итоги: {total_members_current} участников, {total_comments_current} комментариев, {public_projects} публичных"
            ))

        # Quiz summary
        total_attempts_change = sum(item.get('attempts_change', 0) for item in quiz_changes)
        total_users_change = sum(item.get('users_change', 0) for item in quiz_changes)
        new_quizzes = sum(1 for item in quiz_changes if item['is_new'])

        # Calculate current totals
        total_attempts_current = sum(item.get('current_attempts', 0) for item in quiz_changes)
        total_users_current = sum(item.get('current_users', 0) for item in quiz_changes)

        self.stdout.write(f"\n  🎯 Квизы (изменения с прошлого запуска):")
        self.stdout.write(f"     Новых: {new_quizzes}")
        self.stdout.write(f"     Попыток: {self.format_change(total_attempts_change)}")
        self.stdout.write(f"     Пользователей: {self.format_change(total_users_change)}")
        if quiz_changes:
            self.stdout.write(self.style.HTTP_INFO(
                f"     💡 Текущие итоги: {total_attempts_current} попыток, {total_users_current} пользователей"
            ))

        # Total
        total_views = total_article_views_change + total_play_views_change + total_library_views_change
        total_downloads = total_play_downloads_change
        total_likes = total_article_likes_change + total_play_likes_change + total_library_likes_change

        self.stdout.write(self.style.SUCCESS(f"\n  🌟 Всего (изменения):"))
        self.stdout.write(f"     Просмотров: {self.format_change(total_views)}")
        self.stdout.write(f"     Скачиваний: {self.format_change(total_downloads)}")
        self.stdout.write(f"     Лайков: {self.format_change(total_likes)}")
        self.stdout.write(f"     Закладок: {self.format_change(total_library_bookmarks_change)}")

        self.stdout.write('\n' + '='*80 + '\n')

    def show_full_stats(self, current, top_n):
        """Show full current statistics table."""
        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS('📊 ПОЛНАЯ СТАТИСТИКА'))
        self.stdout.write(self.style.SUCCESS('='*80))

        curr_time = datetime.fromisoformat(current['timestamp'])
        self.stdout.write(f"\n⏱  Время: {curr_time.strftime('%d.%m.%Y %H:%M')}")

        # Articles
        articles = list(current.get('articles', {}).values())
        if articles:
            self.stdout.write(self.style.SUCCESS('\n\n📝 СТАТЬИ (топ по просмотрам):'))
            self.stdout.write('─' * 80)

            sorted_articles = sorted(articles, key=lambda x: x.get('views', 0), reverse=True)[:top_n]

            for i, article in enumerate(sorted_articles, 1):
                self.stdout.write(f"\n  {i}. {article['title']}")
                self.stdout.write(self.style.HTTP_INFO(f"     Автор: {article['author']}"))
                self.stdout.write(f"     👁 {article.get('views', 0)} | ❤️ {article.get('likes', 0)}")

        # Plays
        plays = list(current.get('plays', {}).values())
        if plays:
            self.stdout.write(self.style.SUCCESS('\n\n🎭 ПЬЕСЫ (топ по просмотрам):'))
            self.stdout.write('─' * 80)

            sorted_plays = sorted(plays, key=lambda x: x.get('views', 0), reverse=True)[:top_n]

            for i, play in enumerate(sorted_plays, 1):
                self.stdout.write(f"\n  {i}. {play['title']}")
                self.stdout.write(self.style.HTTP_INFO(f"     Автор: {play['author']}"))
                self.stdout.write(f"     👁 {play.get('views', 0)} | ⬇️ {play.get('downloads', 0)} | ❤️ {play.get('likes', 0)}")

        # Library plays
        library_plays = list(current.get('library_plays', {}).values())
        if library_plays:
            self.stdout.write(self.style.SUCCESS('\n\n📚 БИБЛИОТЕКА (топ по просмотрам):'))
            self.stdout.write('─' * 80)

            sorted_library = sorted(library_plays, key=lambda x: x.get('views', 0), reverse=True)[:top_n]

            for i, play in enumerate(sorted_library, 1):
                self.stdout.write(f"\n  {i}. {play['title']}")
                self.stdout.write(self.style.HTTP_INFO(f"     Автор: {play['author']}"))
                self.stdout.write(f"     👁 {play.get('views', 0)} | ❤️ {play.get('likes', 0)} | 🔖 {play.get('bookmarks', 0)}")

        # Projects
        projects = list(current.get('projects', {}).values())
        if projects:
            self.stdout.write(self.style.SUCCESS('\n\n🎬 ПРОЕКТЫ (топ по участникам):'))
            self.stdout.write('─' * 80)

            sorted_projects = sorted(projects, key=lambda x: x.get('members', 0), reverse=True)[:top_n]

            for i, project in enumerate(sorted_projects, 1):
                visibility = "🌐" if project.get('is_public', False) else "🔒"
                self.stdout.write(f"\n  {i}. {project['name']} {visibility}")
                self.stdout.write(self.style.HTTP_INFO(f"     Создатель: {project['creator']} | Тип: {project.get('type', 'Autre')}"))
                self.stdout.write(f"     👥 {project.get('members', 0)} участников | 💬 {project.get('comments', 0)} комментариев")

        # Quizzes
        quizzes = list(current.get('quizzes', {}).values())
        if quizzes:
            self.stdout.write(self.style.SUCCESS('\n\n🎯 КВИЗЫ (топ по попыткам):'))
            self.stdout.write('─' * 80)

            sorted_quizzes = sorted(quizzes, key=lambda x: x.get('attempts', 0), reverse=True)[:top_n]

            for i, quiz in enumerate(sorted_quizzes, 1):
                self.stdout.write(f"\n  {i}. {quiz['title']}")
                self.stdout.write(f"     🎮 {quiz.get('attempts', 0)} попыток | 👤 {quiz.get('unique_users', 0)} польз. | 📊 {quiz.get('avg_score', 0):.1f}% средний балл")

        # Totals
        total_article_views = sum(a.get('views', 0) for a in articles)
        total_article_likes = sum(a.get('likes', 0) for a in articles)
        total_play_views = sum(p.get('views', 0) for p in plays)
        total_play_downloads = sum(p.get('downloads', 0) for p in plays)
        total_play_likes = sum(p.get('likes', 0) for p in plays)
        total_library_views = sum(p.get('views', 0) for p in library_plays)
        total_library_likes = sum(p.get('likes', 0) for p in library_plays)
        total_library_bookmarks = sum(p.get('bookmarks', 0) for p in library_plays)
        total_members = sum(p.get('members', 0) for p in projects)
        total_comments = sum(p.get('comments', 0) for p in projects)
        total_quiz_attempts = sum(q.get('attempts', 0) for q in quizzes)
        total_quiz_users = sum(q.get('unique_users', 0) for q in quizzes)

        self.stdout.write(self.style.SUCCESS('\n\n📈 ИТОГО:'))
        self.stdout.write('─' * 80)
        self.stdout.write(f"\n  📝 Статьи: {len(articles)} шт. | {total_article_views} просмотров | {total_article_likes} лайков")
        self.stdout.write(f"  🎭 Пьесы (каталог): {len(plays)} шт. | {total_play_views} просмотров | {total_play_downloads} скачиваний | {total_play_likes} лайков")
        self.stdout.write(f"  📚 Библиотека: {len(library_plays)} шт. | {total_library_views} просмотров | {total_library_likes} лайков | {total_library_bookmarks} закладок")
        self.stdout.write(f"  🎬 Проекты: {len(projects)} шт. | {total_members} участников | {total_comments} комментариев")
        self.stdout.write(f"  🎯 Квизы: {len(quizzes)} шт. | {total_quiz_attempts} попыток | {total_quiz_users} пользователей")
        self.stdout.write(f"\n  🌟 Всего: {total_article_views + total_play_views + total_library_views} просмотров | {total_play_downloads} скачиваний | {total_article_likes + total_play_likes + total_library_likes} лайков")

        self.stdout.write('\n' + '='*80 + '\n')

    def format_change(self, value):
        """Format change value with color."""
        if value > 0:
            return self.style.SUCCESS(f"+{value}")
        elif value < 0:
            return self.style.ERROR(f"{value}")
        else:
            return f"{value}"

    def format_time_diff(self, td):
        """Format timedelta in human-readable format."""
        seconds = int(td.total_seconds())

        if seconds < 60:
            return f"{seconds} сек"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{minutes} мин"
        elif seconds < 86400:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours} ч {minutes} мин"
        else:
            days = seconds // 86400
            hours = (seconds % 86400) // 3600
            return f"{days} дн {hours} ч"
