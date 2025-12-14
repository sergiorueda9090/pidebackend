from django.contrib import admin
from django.utils.html import format_html
from .models import Subcategory

# Register your models here.

@admin.register(Subcategory)
class SubcategoryAdmin(admin.ModelAdmin):
    """
    Configuración del panel de administración para el modelo Subcategory.
    """

    list_display = [
        'id',
        'name',
        'category',
        'order',
        'slug',
        'icon_display',
        'image_preview',
        'is_active',
        'status_display',
        'products_count',
        'created_at',
    ]

    list_filter = [
        'category',
        'is_active',
        'created_at',
        'updated_at',
        ('deleted_at', admin.EmptyFieldListFilter),
    ]

    search_fields = [
        'name',
        'slug',
        'description',
        'seo_title',
        'seo_keywords',
        'category__name',
    ]

    prepopulated_fields = {
        'slug': ('name',)
    }

    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'deleted_at',
        'image_preview',
        'products_count',
    ]

    fieldsets = (
        ('Información Básica', {
            'fields': (
                'id',
                'category',
                'name',
                'slug',
                'description',
                'icon',
                'order',
            )
        }),
        ('Imagen', {
            'fields': (
                'image',
                'image_preview',
            )
        }),
        ('SEO', {
            'fields': (
                'seo_title',
                'seo_description',
                'seo_keywords',
            ),
            'classes': ('collapse',),
        }),
        ('Estado y Control', {
            'fields': (
                'is_active',
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
        Muestra todas las subcategorías incluyendo las eliminadas en el admin.
        """
        return Subcategory.all_objects.all()

    ordering = ['category', 'order', 'name']

    list_per_page = 25

    def icon_display(self, obj):
        """
        Muestra el nombre del icono en la lista.
        """
        if obj.icon:
            return format_html(
                '<span style="font-family: monospace; color: #667eea; font-weight: 600;">{}</span>',
                obj.icon
            )
        return '-'
    icon_display.short_description = 'Icono'

    def image_preview(self, obj):
        """
        Muestra una miniatura de la imagen en el admin.
        """
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 200px; max-height: 200px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);" />',
                obj.image.url
            )
        return format_html('<span style="color: #999;">Sin imagen</span>')
    image_preview.short_description = 'Vista Previa de Imagen'

    def products_count(self, obj):
        """
        Muestra el conteo de productos de la subcategoría.
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
        Muestra el estado de la subcategoría (activa/eliminada).
        """
        if obj.deleted_at:
            return format_html(
                '<span style="background: #ef4444; color: white; padding: 4px 12px; border-radius: 12px; font-weight: 600;">🗑️ Eliminada</span>'
            )
        elif obj.is_active:
            return format_html(
                '<span style="background: #10b981; color: white; padding: 4px 12px; border-radius: 12px; font-weight: 600;">✅ Activa</span>'
            )
        else:
            return format_html(
                '<span style="background: #f59e0b; color: white; padding: 4px 12px; border-radius: 12px; font-weight: 600;">⏸️ Inactiva</span>'
            )
    status_display.short_description = 'Estado'

    actions = ['activate_subcategories', 'deactivate_subcategories', 'soft_delete_subcategories', 'restore_subcategories']

    def activate_subcategories(self, request, queryset):
        """
        Acción masiva para activar subcategorías.
        """
        # Filtrar solo subcategorías no eliminadas
        queryset = queryset.filter(deleted_at__isnull=True)
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            f'{updated} subcategoría(s) activada(s) exitosamente.'
        )
    activate_subcategories.short_description = '✅ Activar subcategorías seleccionadas'

    def deactivate_subcategories(self, request, queryset):
        """
        Acción masiva para desactivar subcategorías.
        """
        # Filtrar solo subcategorías no eliminadas
        queryset = queryset.filter(deleted_at__isnull=True)
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f'{updated} subcategoría(s) desactivada(s) exitosamente.'
        )
    deactivate_subcategories.short_description = '⏸️ Desactivar subcategorías seleccionadas'

    def soft_delete_subcategories(self, request, queryset):
        """
        Acción masiva para eliminar subcategorías (soft delete).
        """
        # Filtrar solo subcategorías no eliminadas
        queryset = queryset.filter(deleted_at__isnull=True)
        count = 0
        for subcategory in queryset:
            subcategory.delete()  # Usa el método override que hace soft delete
            count += 1
        self.message_user(
            request,
            f'{count} subcategoría(s) eliminada(s) exitosamente (soft delete).'
        )
    soft_delete_subcategories.short_description = '🗑️ Eliminar subcategorías seleccionadas (soft delete)'

    def restore_subcategories(self, request, queryset):
        """
        Acción masiva para restaurar subcategorías eliminadas.
        """
        # Filtrar solo subcategorías eliminadas
        queryset = queryset.filter(deleted_at__isnull=False)
        count = 0
        for subcategory in queryset:
            subcategory.restore()
            count += 1
        self.message_user(
            request,
            f'{count} subcategoría(s) restaurada(s) exitosamente.'
        )
    restore_subcategories.short_description = '♻️ Restaurar subcategorías eliminadas'
