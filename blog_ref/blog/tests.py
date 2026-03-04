"""
Tests for blog app - comments spam protection
"""

from django.test import TestCase, Client
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
import time

from blog.models import Article, ArticleComment, Category
from profiles.models import Profile

User = get_user_model()


class CommentSpamProtectionTest(TestCase):
    """Test spam protection in blog comments"""

    def setUp(self):
        self.client = Client()
        cache.clear()

        # Create a test user and profile (profile created automatically via signal)
        self.user = User.objects.create_user(
            username='testuser@test.com',
            email='testuser@test.com',
            password='testpass123'
        )
        # Get the auto-created profile
        self.profile = self.user.profile

        # Create a category
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )

        # Create a published article
        self.article = Article.objects.create(
            title='Test Article',
            slug='test-article',
            description='Test description',
            content_markdown='Test content',
            profile_author=self.profile,
            category=self.category,
            status='published',
            published_at=timezone.now()
        )

    def tearDown(self):
        cache.clear()

    def test_comment_honeypot_empty_allows_submission(self):
        """Comments with empty honeypot should be accepted"""
        # Simulate normal submission with time delay
        form_time = int((time.time() - 3) * 1000)  # 3 seconds ago

        data = {
            'author_name': 'Real User',
            'author_email': 'real@user.com',
            'comment': 'This is a genuine comment from a real person.',
            'website': '',  # Empty honeypot = human
            'form_rendered_time': form_time
        }

        response = self.client.post(
            reverse('blog:add_comment', args=[self.article.slug]),
            data,
            REMOTE_ADDR='192.168.1.1'
        )

        # Should redirect or show success
        # Comment should be created (pending moderation)
        self.assertTrue(
            ArticleComment.objects.filter(
                article=self.article,
                author_email='real@user.com'
            ).exists()
        )

    def test_comment_honeypot_filled_rejects_bot(self):
        """Comments with filled honeypot should be rejected (bot)"""
        form_time = int((time.time() - 3) * 1000)

        data = {
            'author_name': 'Bot User',
            'author_email': 'bot@spam.com',
            'comment': 'This is a spam comment',
            'website': 'http://spam-site.com',  # Filled honeypot = bot
            'form_rendered_time': form_time
        }

        response = self.client.post(
            reverse('blog:add_comment', args=[self.article.slug]),
            data,
            REMOTE_ADDR='192.168.1.100'
        )

        # Comment should NOT be created
        self.assertFalse(
            ArticleComment.objects.filter(
                author_email='bot@spam.com'
            ).exists()
        )

    def test_comment_time_trap_instant_submission_rejected(self):
        """Comments submitted instantly (< 2 seconds) should be rejected"""
        # Instant submission (0.5 seconds ago)
        form_time = int((time.time() - 0.5) * 1000)

        data = {
            'author_name': 'Bot User',
            'author_email': 'fastbot@spam.com',
            'comment': 'This is a bot comment submitted instantly',
            'website': '',
            'form_rendered_time': form_time
        }

        response = self.client.post(
            reverse('blog:add_comment', args=[self.article.slug]),
            data,
            REMOTE_ADDR='192.168.1.101'
        )

        # Should show error or reject
        self.assertFalse(
            ArticleComment.objects.filter(
                author_email='fastbot@spam.com'
            ).exists()
        )

    def test_comment_time_trap_normal_submission_accepted(self):
        """Comments submitted after 2+ seconds should be accepted"""
        # Normal submission (5 seconds ago)
        form_time = int((time.time() - 5) * 1000)

        data = {
            'author_name': 'Normal User',
            'author_email': 'normal@user.com',
            'comment': 'This is a normal comment with proper timing',
            'website': '',
            'form_rendered_time': form_time
        }

        response = self.client.post(
            reverse('blog:add_comment', args=[self.article.slug]),
            data,
            REMOTE_ADDR='192.168.1.2'
        )

        # Comment should be created
        self.assertTrue(
            ArticleComment.objects.filter(
                author_email='normal@user.com'
            ).exists()
        )

    def test_comment_time_trap_expired_form_rejected(self):
        """Comments from expired forms (> 1 hour) should be rejected"""
        # Form rendered 2 hours ago
        form_time = int((time.time() - 7200) * 1000)

        data = {
            'author_name': 'Old User',
            'author_email': 'old@form.com',
            'comment': 'This is from an expired form',
            'website': '',
            'form_rendered_time': form_time
        }

        response = self.client.post(
            reverse('blog:add_comment', args=[self.article.slug]),
            data,
            REMOTE_ADDR='192.168.1.3'
        )

        # Should be rejected
        self.assertFalse(
            ArticleComment.objects.filter(
                author_email='old@form.com'
            ).exists()
        )

    def test_comment_rate_limiting(self):
        """Should block after 3 comments from same IP within 10 minutes (across different articles)"""
        form_time = int((time.time() - 5) * 1000)

        # Create 2 more articles for testing rate limiting across articles
        article2 = Article.objects.create(
            title='Test Article 2',
            slug='test-article-2',
            description='Test description 2',
            content_markdown='Test content 2',
            category=self.category,
            profile_author=self.profile,
            status='published',
            published_at=timezone.now()
        )
        article3 = Article.objects.create(
            title='Test Article 3',
            slug='test-article-3',
            description='Test description 3',
            content_markdown='Test content 3',
            category=self.category,
            profile_author=self.profile,
            status='published',
            published_at=timezone.now()
        )

        # First 3 comments to DIFFERENT articles should work (global limit is 3)
        articles = [self.article, article2, article3]
        for i, article in enumerate(articles):
            data = {
                'author_name': f'User {i}',
                'author_email': f'user{i}@test.com',
                'comment': f'Comment number {i}',
                'website': '',
                'form_rendered_time': form_time
            }

            response = self.client.post(
                reverse('blog:add_comment', args=[article.slug]),
                data,
                REMOTE_ADDR='192.168.1.200'
            )

        # 4th comment (to any article) should be rate limited globally
        data = {
            'author_name': 'User 4',
            'author_email': 'user4@test.com',
            'comment': 'This should be blocked by global rate limit',
            'website': '',
            'form_rendered_time': form_time
        }

        response = self.client.post(
            reverse('blog:add_comment', args=[self.article.slug]),
            data,
            REMOTE_ADDR='192.168.1.200'
        )

        # Should show rate limit message
        self.assertIn(response.status_code, [200, 302])

        # Check that only 3 comments were created (global limit)
        comment_count = ArticleComment.objects.filter(
            ip_address='192.168.1.200'
        ).count()
        self.assertEqual(comment_count, 3)

    def test_comment_spam_pattern_detection(self):
        """Should reject comments with spam patterns"""
        form_time = int((time.time() - 5) * 1000)

        # Test multiple URLs - now checks ANY 2+ URLs, not just consecutive ones
        data = {
            'author_name': 'Spammer',
            'author_email': 'spam@test.com',
            'comment': 'Check out http://site1.com and http://site2.com for great deals!',
            'website': '',
            'form_rendered_time': form_time
        }

        response = self.client.post(
            reverse('blog:add_comment', args=[self.article.slug]),
            data,
            REMOTE_ADDR='192.168.1.50'
        )

        # Should be rejected due to 2+ URLs
        self.assertFalse(
            ArticleComment.objects.filter(
                author_email='spam@test.com'
            ).exists(),
            "Comment with multiple URLs should be rejected"
        )

    def test_per_article_rate_limiting(self):
        """Should block second comment to same article within 10 minutes from same IP"""
        form_time = int((time.time() - 5) * 1000)

        # First comment to article should work
        data1 = {
            'author_name': 'User One',
            'author_email': 'user1@test.com',
            'comment': 'First comment to this article',
            'website': '',
            'form_rendered_time': form_time
        }

        response1 = self.client.post(
            reverse('blog:add_comment', args=[self.article.slug]),
            data1,
            REMOTE_ADDR='192.168.1.100'
        )

        # Verify first comment was created
        self.assertTrue(
            ArticleComment.objects.filter(
                author_email='user1@test.com'
            ).exists()
        )

        # Second comment to SAME article from SAME IP should be blocked
        data2 = {
            'author_name': 'User One',
            'author_email': 'user1@test.com',
            'comment': 'Second comment to same article - should be blocked',
            'website': '',
            'form_rendered_time': form_time
        }

        response2 = self.client.post(
            reverse('blog:add_comment', args=[self.article.slug]),
            data2,
            REMOTE_ADDR='192.168.1.100'
        )

        # Should show per-article rate limit message
        self.assertIn(response2.status_code, [200, 302])

        # Should still only have 1 comment from this IP to this article
        comment_count = ArticleComment.objects.filter(
            article=self.article,
            ip_address='192.168.1.100'
        ).count()
        self.assertEqual(comment_count, 1, "Should only allow 1 comment per article per IP per 10 minutes")

    def test_authenticated_user_auto_approved(self):
        """Authenticated users should have comments auto-approved"""
        self.client.login(username='testuser@test.com', password='testpass123')

        form_time = int((time.time() - 3) * 1000)

        data = {
            'comment': 'This is a comment from an authenticated user',
            'website': '',
            'form_rendered_time': form_time
        }

        response = self.client.post(
            reverse('blog:add_comment', args=[self.article.slug]),
            data
        )

        # Comment should be created and approved
        comment = ArticleComment.objects.filter(
            article=self.article,
            author_profile=self.profile
        ).first()

        self.assertIsNotNone(comment)
        self.assertEqual(comment.status, 'approved')

    def test_duplicate_comment_detection(self):
        """Should reject duplicate comments within 1 hour"""
        form_time = int((time.time() - 3) * 1000)

        data = {
            'author_name': 'User',
            'author_email': 'user@test.com',
            'comment': 'Exact duplicate comment',
            'website': '',
            'form_rendered_time': form_time
        }

        # First submission
        response1 = self.client.post(
            reverse('blog:add_comment', args=[self.article.slug]),
            data,
            REMOTE_ADDR='192.168.1.10'
        )

        # Second submission (duplicate)
        response2 = self.client.post(
            reverse('blog:add_comment', args=[self.article.slug]),
            data,
            REMOTE_ADDR='192.168.1.10'
        )

        # Only one comment should exist
        comment_count = ArticleComment.objects.filter(
            comment='Exact duplicate comment'
        ).count()
        self.assertEqual(comment_count, 1)


if __name__ == '__main__':
    import unittest
    unittest.main()
