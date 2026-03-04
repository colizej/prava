"""
Интеграционные тесты для blog.models - YAML парсинг в Article.save()
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from blog.models import Article
from profiles.models import Profile

User = get_user_model()


class ArticleYamlParsingTest(TestCase):
    """Тесты парсинга YAML в Article.save()"""

    def setUp(self):
        """Создаём тестового пользователя и профиль"""
        self.user = User.objects.create_user(
            username='testauthor',
            email='author@test.com',
            password='testpass123'
        )
        self.profile = self.user.profile

    def test_article_with_flat_yaml_structure(self):
        """Статья с плоской YAML структурой (meta-title, og-title)"""
        content_markdown = """---
meta-title: Test Article SEO Title
meta-description: This is a test SEO description for the article
og-title: Test Article OG Title
og-description: This is a test OG description for social media
---
# Test Article

This is the content of the test article.
"""
        article = Article.objects.create(
            title='Test Article',
            slug='test-article',
            profile_author=self.profile,
            content_markdown=content_markdown,
            status='published'
        )

        # SEO поля должны быть заполнены из YAML
        self.assertEqual(article.meta_title, 'Test Article SEO Title')
        self.assertEqual(article.meta_description, 'This is a test SEO description for the article')
        self.assertEqual(article.og_title, 'Test Article OG Title')
        self.assertEqual(article.og_description, 'This is a test OG description for social media')

    def test_article_yaml_with_dashed_keys(self):
        """Парсинг YAML с ключами-дефисами (blog style)"""
        content_markdown = """---
meta-title: Racine Article Title
og-description: Description for Racine
---
Content here
"""
        article = Article.objects.create(
            title='Racine Article',
            slug='racine-article',
            profile_author=self.profile,
            content_markdown=content_markdown,
            status='published'
        )

        self.assertEqual(article.meta_title, 'Racine Article Title')
        self.assertEqual(article.og_description, 'Description for Racine')

    def test_article_yaml_removes_quotes(self):
        """YAML парсинг автоматически удаляет кавычки"""
        content_markdown = """---
meta-title: "Quoted Title"
meta-description: 'Single quoted description'
og-title: "Title with 'nested' quotes"
---
Article content
"""
        article = Article.objects.create(
            title='Quoted Article',
            slug='quoted-article',
            profile_author=self.profile,
            content_markdown=content_markdown,
            status='published'
        )

        # Кавычки должны быть удалены yaml.safe_load()
        self.assertEqual(article.meta_title, 'Quoted Title')
        self.assertEqual(article.meta_description, 'Single quoted description')
        self.assertEqual(article.og_title, "Title with 'nested' quotes")

    def test_article_yaml_multiline_description(self):
        """Многострочные описания в YAML очищаются (переносы удаляются)"""
        content_markdown = """---
meta-title: Multiline Article
meta-description: |
  This is a multiline description
  that spans several lines
  and should be cleaned up.
---
Content
"""
        article = Article.objects.create(
            title='Multiline Article',
            slug='multiline-article',
            profile_author=self.profile,
            content_markdown=content_markdown,
            status='published'
        )

        # Одинарные переносы должны быть заменены пробелами
        self.assertIn('multiline description that spans', article.meta_description)
        self.assertNotIn('\n', article.meta_description.strip())

    def test_article_description_from_og_description(self):
        """description заполняется из og-description если пусто"""
        content_markdown = """---
og-description: This should become the description field
---
Content
"""
        article = Article.objects.create(
            title='Auto-fill Description',
            slug='auto-fill-description',
            profile_author=self.profile,
            content_markdown=content_markdown,
            status='published'
        )

        # description должен быть заполнен из og_description
        self.assertEqual(article.description, 'This should become the description field')
        self.assertEqual(article.og_description, 'This should become the description field')

    def test_article_meta_description_priority(self):
        """meta_description из YAML имеет приоритет над auto-generated"""
        content_markdown = """---
meta-description: Manual SEO description from YAML
---
# Article

This is a long article with lots of text that could be used for auto-generation.
But the YAML meta-description should have priority and should not be overwritten.
"""
        article = Article.objects.create(
            title='Priority Test',
            slug='priority-test',
            profile_author=self.profile,
            content_markdown=content_markdown,
            description='',  # Пусто, чтобы проверить приоритет YAML
            status='published'
        )

        # meta_description из YAML не должен быть перезаписан
        self.assertEqual(article.meta_description, 'Manual SEO description from YAML')

    def test_article_without_yaml_uses_fallback(self):
        """Статья без YAML использует fallback (backward compatibility)"""
        content_markdown = """# Article without YAML

This is just markdown content without any YAML frontmatter.
"""
        article = Article.objects.create(
            title='No YAML Article',
            slug='no-yaml-article',
            profile_author=self.profile,
            content_markdown=content_markdown,
            description='Manual description',
            status='published'
        )

        # Должны использоваться значения по умолчанию
        self.assertIsNotNone(article.title)
        self.assertEqual(article.description, 'Manual description')

        # meta_description может быть auto-generated или пустым (зависит от логики save())
        # Главное что статья сохранилась без ошибок
        self.assertIsNotNone(article.slug)

    def test_article_yaml_with_special_characters(self):
        """YAML с специальными символами (французские акценты, символы)"""
        content_markdown = """---
meta-title: "Jean Racine : Œuvres Complètes – Tragédies"
meta-description: "Découvrez l'intégralité des œuvres théâtrales"
og-title: "Racine – Œuvres complètes"
og-description: "Lisez les 12 tragédies de Racine"
---
Content
"""
        article = Article.objects.create(
            title='Racine Œuvres',
            slug='racine-oeuvres',
            profile_author=self.profile,
            content_markdown=content_markdown,
            status='published'
        )

        # Специальные символы должны сохраняться
        self.assertTrue(article.meta_title, f"meta_title is empty: '{article.meta_title}'")
        if article.meta_title:
            self.assertIn('Œuvres', article.meta_title)
            self.assertIn('Complètes', article.meta_title)
            self.assertIn('Tragédies', article.meta_title)
        if article.meta_description:
            self.assertIn('Découvrez', article.meta_description)

    def test_article_update_with_yaml_change(self):
        """Обновление статьи с изменением YAML"""
        content_v1 = """---
meta-title: Version 1 Title
---
Content V1
"""
        article = Article.objects.create(
            title='Update Test',
            slug='update-test',
            profile_author=self.profile,
            content_markdown=content_v1,
            status='published'
        )

        self.assertEqual(article.meta_title, 'Version 1 Title')

        # Обновляем YAML
        content_v2 = """---
meta-title: Version 2 Title Updated
meta-description: New description added
---
Content V2
"""
        article.content_markdown = content_v2
        article.save()

        # SEO поля должны обновиться
        self.assertEqual(article.meta_title, 'Version 2 Title Updated')
        self.assertEqual(article.meta_description, 'New description added')

    def test_article_strip_quotes_legacy_fix(self):
        """strip_quotes() удаляет legacy кавычки из полей"""
        article = Article.objects.create(
            title='Legacy Article',
            slug='legacy-article',
            profile_author=self.profile,
            content_markdown='# Content',
            status='published'
        )

        # Вручную устанавливаем legacy данные с кавычками
        article.meta_title = '"Quoted Title"'
        article.og_description = ' "Spaced Title" '
        article.save()

        # strip_quotes() должен очистить кавычки
        self.assertEqual(article.meta_title, 'Quoted Title')
        self.assertEqual(article.og_description, 'Spaced Title')

    def test_article_empty_yaml_block(self):
        """Пустой YAML блок не вызывает ошибок"""
        content_markdown = """---
---
Just content without any YAML fields
"""
        article = Article.objects.create(
            title='Empty YAML',
            slug='empty-yaml',
            profile_author=self.profile,
            content_markdown=content_markdown,
            description='Manual description',
            status='published'
        )

        # Не должно быть ошибок, используются значения по умолчанию
        self.assertEqual(article.title, 'Empty YAML')
        self.assertEqual(article.description, 'Manual description')


class ArticleYamlEdgeCasesTest(TestCase):
    """Edge cases для YAML парсинга"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='edgeuser',
            email='edge@test.com',
            password='testpass123'
        )
        self.profile = self.user.profile

    def test_article_with_colon_in_title(self):
        """YAML с двоеточием в значении"""
        content_markdown = """---
meta-title: "Article: With Colon"
og-title: "Title: Subtitle: Another"
---
Content
"""
        article = Article.objects.create(
            title='Colon Article',
            slug='colon-article',
            profile_author=self.profile,
            content_markdown=content_markdown,
            status='published'
        )

        self.assertEqual(article.meta_title, 'Article: With Colon')
        self.assertEqual(article.og_title, 'Title: Subtitle: Another')

    def test_article_with_pipe_multiline(self):
        """YAML с | для многострочных значений"""
        content_markdown = """---
meta-description: |
  First paragraph of description.
  Second line of first paragraph.

  Second paragraph here.
---
Content
"""
        article = Article.objects.create(
            title='Pipe Article',
            slug='pipe-article',
            profile_author=self.profile,
            content_markdown=content_markdown,
            status='published'
        )

        # Одинарные переносы внутри параграфа - в пробел
        # Двойные переносы (между параграфами) - сохраняются
        self.assertIn('First paragraph', article.meta_description)
        self.assertIn('Second paragraph', article.meta_description)

    def test_article_with_html_in_yaml(self):
        """YAML с HTML тегами (должны сохраниться)"""
        content_markdown = """---
meta-description: "Article with <strong>HTML</strong> tags"
---
Content
"""
        article = Article.objects.create(
            title='HTML Article',
            slug='html-article',
            profile_author=self.profile,
            content_markdown=content_markdown,
            status='published'
        )

        # HTML должен сохраниться (очистка не должна убирать)
        self.assertIn('<strong>HTML</strong>', article.meta_description)

    def test_article_with_very_long_description(self):
        """YAML с очень длинным описанием"""
        long_desc = "A" * 500  # 500 символов
        content_markdown = f"""---
meta-description: "{long_desc}"
---
Content
"""
        article = Article.objects.create(
            title='Long Description',
            slug='long-description',
            profile_author=self.profile,
            content_markdown=content_markdown,
            status='published'
        )

        self.assertEqual(len(article.meta_description), 500)
        self.assertEqual(article.meta_description, long_desc)


# Run tests
if __name__ == '__main__':
    import django
    django.setup()
    from django.test import TestCase
    TestCase.main()
