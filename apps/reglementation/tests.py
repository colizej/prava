from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import CodeArticle, RuleCategory


# ─── Helpers ──────────────────────────────────────────────────────────────────

def make_user(username='reguser', password='testpass123', **kwargs):
    return User.objects.create_user(username=username, password=password, **kwargs)


def make_premium_user(username='premreg'):
    user = make_user(username)
    user.profile.is_premium = True
    user.profile.premium_until = None
    user.profile.save(update_fields=['is_premium', 'premium_until'])
    return user


def make_category(name='Test Code', slug='test-code', law_id='1975'):
    return RuleCategory.objects.create(
        name=name, slug=slug, law_id=law_id, is_active=True
    )


def make_article(category, number='Art. 1', title='Titre', slug='art-1',
                 is_free=True, order=1):
    return CodeArticle.objects.create(
        article_number=number,
        category=category,
        title=title,
        slug=slug,
        content='Contenu de test.',
        is_free=is_free,
        order=order,
    )


# ─── article_detail access control ───────────────────────────────────────────

class ArticleDetailAccessTests(TestCase):

    def setUp(self):
        self.cat = make_category()
        self.free_article = make_article(self.cat, 'Art. 1', 'Libre', 'art-libre', is_free=True, order=1)
        self.paid_article = make_article(self.cat, 'Art. 2', 'Payant', 'art-payant', is_free=False, order=2)

    def test_free_article_accessible_anonymous(self):
        url = reverse('reglementation:article', kwargs={'slug': self.free_article.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_paid_article_anonymous_redirects_to_login(self):
        url = reverse('reglementation:article', kwargs={'slug': self.paid_article.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response['Location'])

    def test_paid_article_non_premium_redirects_to_pricing(self):
        user = make_user('noprem')
        self.client.force_login(user)
        url = reverse('reglementation:article', kwargs={'slug': self.paid_article.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/pricing/', response['Location'])

    def test_paid_article_premium_user_gets_200(self):
        user = make_premium_user('prem2')
        self.client.force_login(user)
        url = reverse('reglementation:article', kwargs={'slug': self.paid_article.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_nonexistent_article_gives_404(self):
        url = reverse('reglementation:article', kwargs={'slug': 'this-does-not-exist'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


# ─── category_detail: free-only filter for non-premium ───────────────────────

class CategoryDetailFilterTests(TestCase):

    def setUp(self):
        self.cat = make_category('Cat Filter', 'cat-filter')
        self.free_a = make_article(self.cat, 'Art. 3', 'Libre2', 'art-libre2', is_free=True, order=1)
        self.paid_a = make_article(self.cat, 'Art. 4', 'Payant2', 'art-payant2', is_free=False, order=2)

    def test_anonymous_sees_only_free_articles(self):
        url = reverse('reglementation:category', kwargs={'slug': self.cat.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        articles = list(response.context['articles'])
        slugs = [a.slug for a in articles]
        self.assertIn(self.free_a.slug, slugs)
        self.assertNotIn(self.paid_a.slug, slugs)

    def test_non_premium_sees_only_free_articles(self):
        user = make_user('noprem2')
        self.client.force_login(user)
        url = reverse('reglementation:category', kwargs={'slug': self.cat.slug})
        response = self.client.get(url)
        articles = list(response.context['articles'])
        slugs = [a.slug for a in articles]
        self.assertIn(self.free_a.slug, slugs)
        self.assertNotIn(self.paid_a.slug, slugs)

    def test_premium_sees_all_articles(self):
        user = make_premium_user('prem3')
        self.client.force_login(user)
        url = reverse('reglementation:category', kwargs={'slug': self.cat.slug})
        response = self.client.get(url)
        articles = list(response.context['articles'])
        slugs = [a.slug for a in articles]
        self.assertIn(self.free_a.slug, slugs)
        self.assertIn(self.paid_a.slug, slugs)


# ─── CodeArticle.save slug auto-generation ───────────────────────────────────

class CodeArticleSlugTests(TestCase):

    def setUp(self):
        self.cat = make_category('Slug Cat', 'slug-cat')

    def test_slug_is_autogenerated_from_article_number(self):
        article = CodeArticle.objects.create(
            article_number='Art. 42',
            category=self.cat,
            title='Titre quarante-deux',
            content='...',
            is_free=True,
            order=42,
        )
        self.assertNotEqual(article.slug, '')
        self.assertIn('42', article.slug)

    def test_explicit_slug_is_preserved(self):
        article = CodeArticle.objects.create(
            article_number='Art. 43',
            category=self.cat,
            title='Titre',
            slug='mon-slug-custom',
            content='...',
            is_free=True,
            order=43,
        )
        self.assertEqual(article.slug, 'mon-slug-custom')
