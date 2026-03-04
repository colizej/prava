from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from django import forms
from django.db import models
from .models import Article, ArticleImage, Category, Tag, ArticleComment, ArticleLike, ArticleSeries, BlogSettings


class ArticleImageInline(admin.TabularInline):
    model = ArticleImage
    fields = ("order", "image", "alt", "caption")
    extra = 1



@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "status", "is_page", "is_featured", "series", "series_order", "profile_author", "published_at", "views", "likes", "category")
    list_filter = ("status", "is_page", "is_featured", "series", "profile_author", "category")
    search_fields = ("title", "description", "content_markdown", "slug")
    readonly_fields = ("reading_time", "created_at", "updated_at")
    autocomplete_fields = ["profile_author"]
    fieldsets = (
        (None, {
            "fields": ("title", "slug", "profile_author", "status", "published_at", "is_page")
        }),
        ("Featured Settings", {
            "fields": ("is_featured", "featured_order"),
            "classes": ("collapse",)
        }),
        ("Series", {
            "fields": ("series", "series_order"),
            "classes": ("collapse",)
        }),
        ("Content", {
            "fields": ("description", "content_markdown")
        }),
        ("Taxonomy", {
            "fields": ("category", "tags")
        }),
        ("Recommendations", {
            "fields": ("recommended_products",),
            "classes": ("collapse",),
            "description": "Sélectionner 4-6 produits recommandés pour cet article (pièces, exercices, livres)"
        }),
        ("SEO", {
            "fields": ("meta_title", "meta_description", "canonical_url", "og_title", "og_description")
        }),
        ("Stats", {
            "fields": ("views", "likes", "reading_time")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at")
        }),
    )
    inlines = [ArticleImageInline]
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("tags", "recommended_products")

    formfield_overrides = {
        models.TextField: {
            'widget': forms.Textarea(attrs={'rows': 5, 'cols': 80, 'style': 'width: 100% !important;'})
        },
    }

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        """Customize field widgets based on field name."""
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)

        # Description: small textarea (5 rows)
        if db_field.name == 'description':
            formfield.widget = forms.Textarea(attrs={'rows': 5, 'cols': 80, 'style': 'width: 100% !important;'})

        # Content markdown: large textarea (full width, many rows)
        elif db_field.name == 'content_markdown':
            formfield.widget = forms.Textarea(attrs={'rows': 30, 'cols': 120, 'style': 'width: 100% !important; font-family: monospace;'})

        # SEO fields: medium textareas
        elif db_field.name in ['meta_description', 'og_description']:
            formfield.widget = forms.Textarea(attrs={'rows': 3, 'cols': 80, 'style': 'width: 100% !important;'})

        return formfield

    class Media:
        js = ('admin/js/markdown-editor.js',)


@admin.register(ArticleImage)
class ArticleImageAdmin(admin.ModelAdmin):
    list_display = ("article", "order", "image", "alt")
    list_filter = ("article",)


# Note: ArticleFAQ model removed; admin interface for per-article FAQs was removed.


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "color_preview", "article_count")
    prepopulated_fields = {"slug": ("name",)}
    fieldsets = (
        (None, {
            "fields": ("name", "slug")
        }),
        ("Colors", {
            "fields": ("color_bg", "color_text"),
            "description": "Choose custom colors for category badge (hex format: #rrggbb)"
        }),
        ("SEO & Description", {
            "fields": ("description", "seo_text"),
            "classes": ("collapse",)
        }),
    )

    class Media:
        css = {
            'all': ('https://cdn.jsdelivr.net/npm/@simonwep/pickr/dist/themes/nano.min.css',)
        }
        js = (
            'https://cdn.jsdelivr.net/npm/@simonwep/pickr/dist/pickr.min.js',
        )

    def color_preview(self, obj):
        """Display color preview badge."""
        return format_html(
            '<span style="background:{}; color:{}; padding:4px 12px; border-radius:12px; font-size:11px; font-weight:600;">{}</span>',
            obj.color_bg,
            obj.color_text,
            obj.name
        )
    color_preview.short_description = 'Aperçu'

    def article_count(self, obj):
        """Display number of published articles in this category."""
        count = obj.articles.filter(status='published', is_page=False).count()
        return format_html(
            '<span style="color:#28a745; font-weight:bold;">{}</span>',
            count
        )
    article_count.short_description = 'Articles'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(ArticleComment)
class ArticleCommentAdmin(admin.ModelAdmin):
    list_display = ['comment_id', 'author_display', 'article_title', 'comment_preview', 'status_badge', 'created_at', 'ip_address']
    list_display_links = ['comment_id', 'comment_preview']
    list_filter = ['status', 'created_at', 'moderated_at']
    search_fields = ['author_name', 'author_email', 'comment', 'article__title']
    readonly_fields = ['article', 'author_profile', 'author_name', 'author_email', 'ip_address', 'user_agent', 'created_at', 'updated_at', 'moderated_by', 'moderated_at', 'edited_at']
    actions = ['approve_comments', 'reject_comments', 'mark_as_pending']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Commentaire', {
            'fields': ('article', 'comment', 'status')
        }),
        ('Auteur', {
            'fields': ('author_profile', 'author_name', 'author_email')
        }),
        ('Modération', {
            'fields': ('moderation_note', 'moderated_by', 'moderated_at')
        }),
        ('Threading', {
            'fields': ('parent',),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('ip_address', 'user_agent', 'likes_count'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'edited_at'),
            'classes': ('collapse',)
        }),
    )

    def comment_id(self, obj):
        """Display comment ID for clicking."""
        return f"#{obj.id}"
    comment_id.short_description = 'ID'

    def author_display(self, obj):
        """Display author without link (read-only)."""
        if obj.author_profile:
            return format_html(
                '{} <span style="color:#999;">(inscrit)</span>',
                obj.author_profile.display_name
            )
        return format_html(
            '{} <span style="color:#999;">(invité)</span>',
            obj.author_name
        )
    author_display.short_description = 'Auteur'

    def article_title(self, obj):
        """Display article title without link (read-only)."""
        return obj.article.title[:50]
    article_title.short_description = 'Article'

    def comment_preview(self, obj):
        """Show comment preview."""
        preview = obj.comment[:80] + '...' if len(obj.comment) > 80 else obj.comment
        return format_html('<div style="max-width:400px;">{}</div>', preview)
    comment_preview.short_description = 'Commentaire'

    def status_badge(self, obj):
        """Show status with color badge."""
        colors = {
            'pending': '#ffc107',
            'approved': '#28a745',
            'rejected': '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background:{}; color:#fff; padding:3px 8px; border-radius:3px; font-size:11px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Statut'

    def approve_comments(self, request, queryset):
        """Approve selected comments."""
        updated = queryset.filter(status__in=['pending', 'rejected']).update(
            status='approved',
            moderated_by=request.user,
            moderated_at=timezone.now()
        )
        self.message_user(request, f"{updated} commentaire(s) approuvé(s).")
    approve_comments.short_description = "Approuver les commentaires sélectionnés"

    def reject_comments(self, request, queryset):
        """Reject selected comments."""
        updated = queryset.update(
            status='rejected',
            moderated_by=request.user,
            moderated_at=timezone.now()
        )
        self.message_user(request, f"{updated} commentaire(s) rejeté(s).")
    reject_comments.short_description = "Rejeter les commentaires sélectionnés"

    def mark_as_pending(self, request, queryset):
        """Mark comments as pending."""
        updated = queryset.update(status='pending')
        self.message_user(request, f"{updated} commentaire(s) marqué(s) en attente.")
    mark_as_pending.short_description = "Marquer en attente"


@admin.register(ArticleSeries)
class ArticleSeriesAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'article_count', 'created_at']
    search_fields = ['title', 'description']
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ['created_at', 'updated_at']

    def article_count(self, obj):
        """Display number of articles in series."""
        count = obj.articles.filter(status='published', is_page=False).count()
        return format_html(
            '<span style="color:#28a745; font-weight:bold;">{} article{}</span>',
            count,
            's' if count != 1 else ''
        )
    article_count.short_description = 'Articles'


@admin.register(ArticleLike)
class ArticleLikeAdmin(admin.ModelAdmin):
    list_display = ['article', 'user_display', 'ip_address', 'created_at']
    list_filter = ['created_at']
    search_fields = ['article__title', 'user__username', 'user__email', 'ip_address', 'session_key']
    readonly_fields = ['article', 'user', 'session_key', 'ip_address', 'created_at']
    date_hierarchy = 'created_at'

    def user_display(self, obj):
        """Display user or session info."""
        if obj.user:
            return format_html(
                '<strong>{}</strong> <span style="color:#999;">(inscrit)</span>',
                obj.user.username
            )
        return format_html(
            '<span style="color:#999;">Session: {}</span>',
            obj.session_key[:12] + '...' if len(obj.session_key) > 12 else obj.session_key
        )
    user_display.short_description = 'Utilisateur'


@admin.register(BlogSettings)
class BlogSettingsAdmin(admin.ModelAdmin):
    """Admin interface for Blog main page settings (singleton)."""

    fieldsets = (
        ("Page Header", {
            "fields": ("title", "header_text"),
            "description": "Content displayed at the top of the blog main page"
        }),
        ("Page Footer", {
            "fields": ("footer_text",),
            "description": "SEO-optimized text displayed at the bottom of the blog page"
        }),
        ("SEO Meta Tags", {
            "fields": ("meta_title", "meta_description"),
            "classes": ("collapse",)
        }),
    )

    def has_add_permission(self, request):
        """Prevent creating multiple instances (singleton)."""
        return not BlogSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """Prevent deleting the singleton instance."""
        return False