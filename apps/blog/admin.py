from django.contrib import admin
from .models import BlogCategory, BlogPost


@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'name_nl', 'name_ru', 'slug', 'order')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('order',)


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'category', 'author', 'is_published',
        'published_at', 'views_count', 'read_time',
    )
    list_filter = ('is_published', 'category', 'author', 'created_at')
    search_fields = ('title', 'content', 'title_nl', 'title_ru')
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ('is_published',)
    date_hierarchy = 'published_at'
    readonly_fields = ('views_count', 'read_time', 'created_at', 'updated_at')

    fieldsets = (
        ('Contenu FR', {
            'fields': ('title', 'slug', 'content', 'excerpt'),
        }),
        ('Contenu NL', {
            'fields': ('title_nl', 'content_nl', 'excerpt_nl'),
            'classes': ('collapse',),
        }),
        ('Contenu RU', {
            'fields': ('title_ru', 'content_ru', 'excerpt_ru'),
            'classes': ('collapse',),
        }),
        ('Média', {
            'fields': ('featured_image', 'featured_image_alt'),
        }),
        ('Publication', {
            'fields': ('author', 'category', 'is_published', 'published_at'),
        }),
        ('SEO', {
            'fields': (
                'meta_title', 'meta_description', 'keywords',
                'canonical_url', 'no_index',
            ),
            'classes': ('collapse',),
        }),
        ('Statistiques', {
            'fields': ('views_count', 'read_time', 'created_at', 'updated_at'),
        }),
    )
