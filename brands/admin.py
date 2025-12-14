from django.contrib import admin
from django.utils.html import format_html
from .models import Brand

# Register your models here.

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    """
    Configuración del panel de administración para el modelo Brand.
    """

    list_display = [
        'id',
        'name',
        'slug',
        'logo_preview',
        'website_link',
        'is_active',
        'is_featured',
        'status_display',
        'products_count',
        'created_at',
    ]

    list_filter = [
        'is_active',
        'is_featured',
        'created_at',
        'updated_at',
        ('deleted_at', admin.EmptyFieldListFilter),
    ]

    search_fields = [
        'name',
        'slug',
        'description',
        'website',
    ]

    prepopulated_fields = {
        'slug': ('name',)
    }

    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'deleted_at',
        'logo_preview',
        'products_count',
    ]

    fieldsets = (
        ('Información Básica', {
            'fields': (
                'id',
                'name',
                'slug',
                'description',
                'website',
            )
        }),
        ('Logo', {
            'fields': (
                'logo',
                'logo_preview',
            )
        }),
        ('Estado y Control', {
            'fields': (
                'is_active',
                'is_featured',
                'products_count',
            )
        }),
        ('Auditoría', {
            'fields': (
                'created_at',
                'updated_at',
                'deleted_at',
            ),
            'classes': ('collapse',),
        }),
    )

    def get_queryset(self, request):
        """
        Muestra todas las marcas incluyendo las eliminadas en el admin.
        """
        return Brand.all_objects.all()

    ordering = ['-is_featured', '-created_at']

    list_per_page = 25

    def logo_preview(self, obj):
        """
        Muestra una miniatura del logo en el admin.
        """
        if obj.logo:
            return format_html(
                '<img src="{}" style="max-width: 150px; max-height: 80px; object-fit: contain; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); background: white; padding: 8px;" />',
                obj.logo.url
            )
        return format_html('<span style="color: #999;">Sin logo</span>')
    logo_preview.short_description = 'Logo'

    def website_link(self, obj):
        """
        Muestra el sitio web como un enlace clickeable.
        """
        if obj.website:
            # Extraer dominio sin protocolo para mostrar
            display_url = obj.website.replace('https://', '').replace('http://', '')
            if len(display_url) > 30:
                display_url = display_url[:27] + '...'

            return format_html(
                '<a href="{}" target="_blank" style="color: #667eea; text-decoration: none; font-weight: 500;">🌐 {}</a>',
                obj.website,
                display_url
            )
        return format_html('<span style="color: #999;">-</span>')
    website_link.short_description = 'Sitio Web'

    def products_count(self, obj):
        """
        Muestra el conteo de productos de la marca.
        """
        count = obj.products_count
        if count > 0:
            return format_html(
                '<span style="background: #4ade80; color: white; padding: 4px 12px; border-radius: 12px; font-weight: 600;">{}</span>',
                count
            )
        return format_html(
            '<span style="background: #e5e7eb; color: #6b7280; padding: 4px 12px; border-radius: 12px;">0</span>'
        )
    products_count.short_description = 'Productos'

    def status_display(self, obj):
        """
        Muestra el estado de la marca (activa/eliminada/destacada).
        """
        if obj.deleted_at:
            return format_html(
                '<span style="background: #ef4444; color: white; padding: 4px 12px; border-radius: 12px; font-weight: 600;">🗑️ Eliminada</span>'
            )
        elif obj.is_featured and obj.is_active:
            return format_html(
                '<span style="background: #f59e0b; color: white; padding: 4px 12px; border-radius: 12px; font-weight: 600;">⭐ Destacada</span>'
            )
        elif obj.is_active:
            return format_html(
                '<span style="background: #10b981; color: white; padding: 4px 12px; border-radius: 12px; font-weight: 600;">✅ Activa</span>'
            )
        else:
            return format_html(
                '<span style="background: #94a3b8; color: white; padding: 4px 12px; border-radius: 12px; font-weight: 600;">⏸️ Inactiva</span>'
            )
    status_display.short_description = 'Estado'

    actions = [
        'activate_brands',
        'deactivate_brands',
        'mark_as_featured',
        'unmark_as_featured',
        'soft_delete_brands',
        'restore_brands'
    ]

    def activate_brands(self, request, queryset):
        """
        Acción masiva para activar marcas.
        """
        queryset = queryset.filter(deleted_at__isnull=True)
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            f'{updated} marca(s) activada(s) exitosamente.'
        )
    activate_brands.short_description = '✅ Activar marcas seleccionadas'

    def deactivate_brands(self, request, queryset):
        """
        Acción masiva para desactivar marcas.
        """
        queryset = queryset.filter(deleted_at__isnull=True)
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f'{updated} marca(s) desactivada(s) exitosamente.'
        )
    deactivate_brands.short_description = '⏸️ Desactivar marcas seleccionadas'

    def mark_as_featured(self, request, queryset):
        """
        Acción masiva para marcar marcas como destacadas.
        """
        queryset = queryset.filter(deleted_at__isnull=True)
        updated = queryset.update(is_featured=True)
        self.message_user(
            request,
            f'{updated} marca(s) marcada(s) como destacada(s) exitosamente.'
        )
    mark_as_featured.short_description = '⭐ Marcar como destacadas'

    def unmark_as_featured(self, request, queryset):
        """
        Acción masiva para quitar marcas de destacadas.
        """
        queryset = queryset.filter(deleted_at__isnull=True)
        updated = queryset.update(is_featured=False)
        self.message_user(
            request,
            f'{updated} marca(s) quitada(s) de destacadas exitosamente.'
        )
    unmark_as_featured.short_description = '➖ Quitar de destacadas'

    def soft_delete_brands(self, request, queryset):
        """
        Acción masiva para eliminar marcas (soft delete).
        """
        queryset = queryset.filter(deleted_at__isnull=True)
        count = 0
        for brand in queryset:
            brand.delete()  # Usa el método override que hace soft delete
            count += 1
        self.message_user(
            request,
            f'{count} marca(s) eliminada(s) exitosamente (soft delete).'
        )
    soft_delete_brands.short_description = '🗑️ Eliminar marcas seleccionadas (soft delete)'

    def restore_brands(self, request, queryset):
        """
        Acción masiva para restaurar marcas eliminadas.
        """
        queryset = queryset.filter(deleted_at__isnull=False)
        count = 0
        for brand in queryset:
            brand.restore()
            count += 1
        self.message_user(
            request,
            f'{count} marca(s) restaurada(s) exitosamente.'
        )
    restore_brands.short_description = '♻️ Restaurar marcas eliminadas'
