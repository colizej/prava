from django.contrib import admin
from .models import Glossary, ContactMessage


@admin.register(Glossary)
class GlossaryAdmin(admin.ModelAdmin):
    list_display = ('term', 'term_nl', 'term_ru', 'category', 'order')
    list_filter = ('category',)
    search_fields = ('term', 'term_nl', 'term_ru', 'definition')
    list_editable = ('order',)
    ordering = ('order', 'term')


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('name', 'email', 'subject', 'message')
    list_editable = ('is_read',)
    readonly_fields = ('name', 'email', 'subject', 'message', 'created_at')
    ordering = ('-created_at',)
