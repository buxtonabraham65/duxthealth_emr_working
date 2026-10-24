from django.contrib import admin
from .models import AccessRequest

@admin.register(AccessRequest)
class AccessRequestAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'profession', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'profession', 'created_at')
    search_fields = ('full_name', 'email', 'profession')
    ordering = ('-created_at',)
