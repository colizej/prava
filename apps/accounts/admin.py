from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, DailyQuota


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name = 'Profil'
    fields = (
        'language', 'avatar', 'bio',
        'is_premium', 'premium_until',
        'total_questions_answered', 'correct_answers',
    )
    readonly_fields = ('total_questions_answered', 'correct_answers')


class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = (
        'username', 'email', 'is_active',
        'get_is_premium', 'get_questions_answered', 'date_joined',
    )

    @admin.display(boolean=True, description='Premium')
    def get_is_premium(self, obj):
        return hasattr(obj, 'profile') and obj.profile.has_active_premium

    @admin.display(description='Questions')
    def get_questions_answered(self, obj):
        if hasattr(obj, 'profile'):
            return obj.profile.total_questions_answered
        return 0


# Re-register User with custom admin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(DailyQuota)
class DailyQuotaAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'questions_answered', 'max_questions', 'remaining')
    list_filter = ('date',)
    search_fields = ('user__username',)
    readonly_fields = ('user', 'date', 'questions_answered')

    @admin.display(description='Restant')
    def remaining(self, obj):
        return obj.remaining
