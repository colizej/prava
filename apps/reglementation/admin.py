from django.contrib import admin
from .models import RuleCategory, CodeArticle, TrafficSign


@admin.register(RuleCategory)
class RuleCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'name_nl', 'name_ru', 'slug', 'order', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('order', 'is_active')
    search_fields = ('name', 'name_nl', 'name_ru')


@admin.register(CodeArticle)
class CodeArticleAdmin(admin.ModelAdmin):
    list_display = ('article_number', 'title', 'category', 'is_free', 'order')
    list_filter = ('category', 'is_free')
    search_fields = ('article_number', 'title', 'content', 'title_nl', 'title_ru')
    prepopulated_fields = {'slug': ('article_number', 'title')}
    list_editable = ('is_free', 'order')
    ordering = ('order', 'article_number')

    fieldsets = (
        ('Identification', {
            'fields': ('article_number', 'slug', 'category', 'is_free', 'order'),
        }),
        ('Contenu FR', {
            'fields': ('title', 'content'),
        }),
        ('Contenu NL', {
            'fields': ('title_nl', 'content_nl'),
            'classes': ('collapse',),
        }),
        ('Contenu RU', {
            'fields': ('title_ru', 'content_ru'),
            'classes': ('collapse',),
        }),
    )


@admin.register(TrafficSign)
class TrafficSignAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'sign_type', 'category', 'order')
    list_filter = ('sign_type', 'category')
    search_fields = ('code', 'name', 'name_nl', 'name_ru')
    list_editable = ('order',)
    ordering = ('sign_type', 'order', 'code')
