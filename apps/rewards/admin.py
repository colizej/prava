from django.contrib import admin
from django.utils.html import format_html

from .models import KeySettings, KeyTransaction, KeyWallet


# ---------------------------------------------------------------------------
# KeySettings — singleton, prevent adding more than one
# ---------------------------------------------------------------------------

@admin.register(KeySettings)
class KeySettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Apparence', {
            'fields': ('icon', 'currency_plural', 'currency_singular'),
        }),
        ('Gains', {
            'fields': ('daily_visit_award', 'min_visit_minutes', 'test_pass_award'),
        }),
        ('Dépenses', {
            'fields': ('keys_per_pack', 'questions_per_pack'),
        }),
        ('Pénalité d\'inactivité', {
            'fields': ('inactivity_grace_days', 'decay_per_day'),
        }),
    )

    def has_add_permission(self, request):
        # Only one singleton row allowed
        return not KeySettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False  # forbid deletion of singleton


# ---------------------------------------------------------------------------
# KeyWallet — read-only overview
# ---------------------------------------------------------------------------

@admin.register(KeyWallet)
class KeyWalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance_display', 'last_active_date',
                    'today_minutes', 'awarded_today', 'created_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('user', 'balance', 'last_active_date',
                       'today_minutes', 'awarded_today',
                       'created_at', 'updated_at')

    @admin.display(description='Solde')
    def balance_display(self, obj):
        try:
            icon = KeySettings.get().icon
        except Exception:
            icon = '🔑'
        return format_html('<strong>{} {}</strong>', icon, obj.balance)

    def has_add_permission(self, request):
        return False  # wallets are created automatically


# ---------------------------------------------------------------------------
# KeyTransaction — full log, read-only
# ---------------------------------------------------------------------------

@admin.register(KeyTransaction)
class KeyTransactionAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'user_link', 'amount_display',
                    'reason', 'balance_after', 'note')
    list_filter = ('reason', 'created_at')
    search_fields = ('wallet__user__username', 'note')
    readonly_fields = ('wallet', 'amount', 'reason', 'note',
                       'balance_after', 'created_at')
    date_hierarchy = 'created_at'

    @admin.display(description='Utilisateur')
    def user_link(self, obj):
        return obj.wallet.user.username

    @admin.display(description='Montant')
    def amount_display(self, obj):
        try:
            icon = KeySettings.get().icon
        except Exception:
            icon = '🔑'
        colour = 'green' if obj.amount >= 0 else 'red'
        sign = '+' if obj.amount >= 0 else ''
        return format_html(
            '<span style="color:{}">{}{} {}</span>',
            colour, sign, obj.amount, icon,
        )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False  # transactions must never be deleted
