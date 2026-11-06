from django.contrib import admin

from apps.services.models import Service


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "category",
        "order",
        "is_active",
    )

    list_editable = ("order", "is_active")

    search_fields = (
        "title",
        "category",
    )

    list_filter = (
        "category",
        "is_active",
    )

    prepopulated_fields = {
        "slug": ("title",),
    }

    ordering = ("order", "id")