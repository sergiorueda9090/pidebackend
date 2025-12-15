from django.contrib import admin
from django.utils.html import format_html
from .models import AttributeValue

# Register your models here.

@admin.register(AttributeValue)
class AttributeValueAdmin(admin.ModelAdmin):
    """
    Configuración del panel de administración para el modelo AttributeValue.
    """

    list_display = [
        'id',
        'atributo',
        'valor',
        'valor_extra_display',
        'orden',
        'activo',
        'status_display',
        'products_count',
        'created_at',
    ]

    list_filter = [
        'atributo',
        'activo',
        'created_at',
        'updated_at',
        ('deleted_at', admin.EmptyFieldListFilter),
    ]

    search_fields = [
        'valor',
        'valor_extra',
        'atributo__name',
    ]

    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'deleted_at',
        'products_count',
    ]

    fieldsets = (
        ('Información Básica', {
            'fields': (
                'id',
                'atributo',
                'valor',
                'valor_extra',
                'orden',
            )
        }),
        ('Estado y Control', {
            'fields': (
                'activo',
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
        Muestra todos los valores incluyendo los eliminados en el admin.
        """
        return AttributeValue.all_objects.all()

    ordering = ['atributo', 'orden', 'valor']

    list_per_page = 25

    def valor_extra_display(self, obj):
        """
        Muestra el valor extra con preview de color si es hexadecimal.
        """
        if obj.valor_extra:
            # Verificar si es un código hexadecimal
            import re
            hex_pattern = r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$'
            if re.match(hex_pattern, obj.valor_extra):
                return format_html(
                    '<span style="display: inline-flex; align-items: center; gap: 8px;">'
                    '<span style="width: 20px; height: 20px; border-radius: 50%; background: {}; border: 2px solid #ddd;"></span>'
                    '<code style="font-family: monospace; color: #667eea;">{}</code>'
                    '</span>',
                    obj.valor_extra,
                    obj.valor_extra
                )
            return format_html(
                '<span style="font-family: monospace; color: #667eea;">{}</span>',
                obj.valor_extra
            )
        return '-'
    valor_extra_display.short_description = 'Valor Extra'

    def products_count(self, obj):
        """
        Muestra el conteo de productos que usan este valor.
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
        Muestra el estado del valor (activo/eliminado).
        """
        if obj.deleted_at:
            return format_html(
                '<span style="background: #ef4444; color: white; padding: 4px 12px; border-radius: 12px; font-weight: 600;">🗑️ Eliminado</span>'
            )
        elif obj.activo:
            return format_html(
                '<span style="background: #10b981; color: white; padding: 4px 12px; border-radius: 12px; font-weight: 600;">✅ Activo</span>'
            )
        else:
            return format_html(
                '<span style="background: #f59e0b; color: white; padding: 4px 12px; border-radius: 12px; font-weight: 600;">⏸️ Inactivo</span>'
            )
    status_display.short_description = 'Estado'

    actions = ['activate_values', 'deactivate_values', 'soft_delete_values', 'restore_values']

    def activate_values(self, request, queryset):
        """
        Acción masiva para activar valores.
        """
        queryset = queryset.filter(deleted_at__isnull=True)
        updated = queryset.update(activo=True)
        self.message_user(
            request,
            f'{updated} valor(es) activado(s) exitosamente.'
        )
    activate_values.short_description = '✅ Activar valores seleccionados'

    def deactivate_values(self, request, queryset):
        """
        Acción masiva para desactivar valores.
        """
        queryset = queryset.filter(deleted_at__isnull=True)
        updated = queryset.update(activo=False)
        self.message_user(
            request,
            f'{updated} valor(es) desactivado(s) exitosamente.'
        )
    deactivate_values.short_description = '⏸️ Desactivar valores seleccionados'

    def soft_delete_values(self, request, queryset):
        """
        Acción masiva para eliminar valores (soft delete).
        """
        queryset = queryset.filter(deleted_at__isnull=True)
        count = 0
        for value in queryset:
            value.delete()  # Usa el método override que hace soft delete
            count += 1
        self.message_user(
            request,
            f'{count} valor(es) eliminado(s) exitosamente (soft delete).'
        )
    soft_delete_values.short_description = '🗑️ Eliminar valores seleccionados (soft delete)'

    def restore_values(self, request, queryset):
        """
        Acción masiva para restaurar valores eliminados.
        """
        queryset = queryset.filter(deleted_at__isnull=False)
        count = 0
        for value in queryset:
            value.restore()
            count += 1
        self.message_user(
            request,
            f'{count} valor(es) restaurado(s) exitosamente.'
        )
    restore_values.short_description = '♻️ Restaurar valores eliminados'
