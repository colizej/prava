from django.contrib import admin
from .models import Plan, Order


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'key', 'price_display', 'duration_days', 'is_active', 'is_highlighted', 'sort_order']
    list_editable = ['is_active', 'is_highlighted', 'sort_order']
    list_filter = ['is_active']
    search_fields = ['name', 'key']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'plan', 'amount', 'status', 'mollie_payment_id', 'created_at', 'paid_at']
    list_filter = ['status', 'plan']
    search_fields = ['user__username', 'user__email', 'mollie_payment_id', 'id']
    raw_id_fields = ['user']
    readonly_fields = ['id', 'created_at', 'paid_at', 'mollie_payment_id']
    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        return False
