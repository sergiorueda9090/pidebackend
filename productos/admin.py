from django.contrib import admin
from django.utils.html import format_html
from .models import Producto

# Register your models here.

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    """
    Configuración del panel de administración para el modelo Producto.
    """

    list_display = [
        'id',
        'nombre',
        'sku_base',
        'categoria',
        'marca',
        'tipo_producto',
        'precio_display',
        'stock_display',
        'status_display',
        'created_at',
    ]

    list_filter = [
        'tipo_producto',
        'activo',
        'publicado',
        'destacado',
        'es_nuevo',
        'tiene_variantes',
        'categoria',
        'marca',
        'created_at',
        'updated_at',
        ('deleted_at', admin.EmptyFieldListFilter),
    ]

    search_fields = [
        'nombre',
        'sku_base',
        'descripcion_corta',
        'descripcion_larga',
        'keywords',
    ]

    prepopulated_fields = {
        'slug': ('nombre',)
    }

    readonly_fields = [
        'id',
        'slug',
        'created_at',
        'updated_at',
        'deleted_at',
        'created_by',
        'updated_by',
        'precio_final_display',
        'margen_display',
        'stock_status_display',
    ]

    fieldsets = (
        ('Información Básica', {
            'fields': (
                'id',
                'nombre',
                'slug',
                'sku_base',
                'descripcion_corta',
                'descripcion_larga',
            )
        }),
        ('Clasificación', {
            'fields': (
                'categoria',
                'marca',
                'tipo_producto',
                'tiene_variantes',
            )
        }),
        ('Precios', {
            'fields': (
                'precio_base',
                'precio_costo',
                'precio_descuento',
                'porcentaje_descuento',
                'moneda',
                'precio_final_display',
                'margen_display',
            )
        }),
        ('Inventario', {
            'fields': (
                'stock_actual',
                'stock_minimo',
                'unidad_medida',
                'stock_status_display',
            )
        }),
        ('Dimensiones y Peso', {
            'fields': (
                'peso',
                'largo',
                'ancho',
                'alto',
            ),
            'classes': ('collapse',),
        }),
        ('SEO', {
            'fields': (
                'meta_title',
                'meta_description',
                'keywords',
            ),
            'classes': ('collapse',),
        }),
        ('Estados', {
            'fields': (
                'activo',
                'publicado',
                'destacado',
                'es_nuevo',
                'fecha_publicacion',
                'fecha_nuevo_hasta',
            )
        }),
        ('Métricas', {
            'fields': (
                'vistas',
                'ventas_totales',
                'rating_promedio',
                'total_reviews',
            ),
            'classes': ('collapse',),
        }),
        ('Auditoría', {
            'fields': (
                'created_at',
                'updated_at',
                'deleted_at',
                'created_by',
                'updated_by',
            ),
            'classes': ('collapse',),
        }),
    )

    def get_queryset(self, request):
        """
        Muestra todos los productos incluyendo los eliminados en el admin.
        """
        return Producto.all_objects.all()

    ordering = ['-created_at']

    list_per_page = 25

    def precio_display(self, obj):
        """
        Muestra el precio con formato.
        """
        if obj.precio_base:
            if obj.tiene_descuento:
                return format_html(
                    '<span style="text-decoration: line-through; color: #999;">${:,.0f}</span> '
                    '<span style="color: #ef4444; font-weight: 600;">${:,.0f}</span>',
                    obj.precio_base,
                    obj.precio_final
                )
            return format_html(
                '<span style="font-weight: 600;">${:,.0f}</span>',
                obj.precio_base
            )
        return '-'
    precio_display.short_description = 'Precio'

    def stock_display(self, obj):
        """
        Muestra el stock con código de colores.
        """
        if obj.stock_bajo:
            return format_html(
                '<span style="background: #ef4444; color: white; padding: 4px 12px; border-radius: 12px; font-weight: 600;">⚠️ {}</span>',
                obj.stock_actual
            )
        elif obj.tiene_stock:
            return format_html(
                '<span style="background: #10b981; color: white; padding: 4px 12px; border-radius: 12px; font-weight: 600;">{}</span>',
                obj.stock_actual
            )
        else:
            return format_html(
                '<span style="background: #6b7280; color: white; padding: 4px 12px; border-radius: 12px; font-weight: 600;">0</span>'
            )
    stock_display.short_description = 'Stock'

    def status_display(self, obj):
        """
        Muestra el estado del producto.
        """
        if obj.deleted_at:
            return format_html(
                '<span style="background: #ef4444; color: white; padding: 4px 12px; border-radius: 12px; font-weight: 600;">🗑️ Eliminado</span>'
            )
        elif not obj.activo:
            return format_html(
                '<span style="background: #6b7280; color: white; padding: 4px 12px; border-radius: 12px; font-weight: 600;">⏸️ Inactivo</span>'
            )
        elif obj.publicado:
            return format_html(
                '<span style="background: #10b981; color: white; padding: 4px 12px; border-radius: 12px; font-weight: 600;">✅ Publicado</span>'
            )
        else:
            return format_html(
                '<span style="background: #f59e0b; color: white; padding: 4px 12px; border-radius: 12px; font-weight: 600;">📝 Borrador</span>'
            )
    status_display.short_description = 'Estado'

    def precio_final_display(self, obj):
        """
        Muestra el precio final calculado.
        """
        if obj.precio_final:
            return f'${obj.precio_final:,.0f} {obj.moneda}'
        return '-'
    precio_final_display.short_description = 'Precio Final'

    def margen_display(self, obj):
        """
        Muestra el margen de ganancia.
        """
        if obj.margen_ganancia:
            return format_html(
                '${:,.0f} ({:.1f}%)',
                obj.margen_ganancia,
                obj.porcentaje_ganancia or 0
            )
        return '-'
    margen_display.short_description = 'Margen'

    def stock_status_display(self, obj):
        """
        Muestra el estado del stock.
        """
        if obj.stock_bajo:
            return format_html(
                '<span style="color: #ef4444; font-weight: 600;">⚠️ Stock Bajo (mínimo: {})</span>',
                obj.stock_minimo
            )
        elif obj.tiene_stock:
            return format_html(
                '<span style="color: #10b981; font-weight: 600;">✅ Stock Disponible</span>'
            )
        else:
            return format_html(
                '<span style="color: #6b7280; font-weight: 600;">❌ Sin Stock</span>'
            )
    stock_status_display.short_description = 'Estado de Stock'

    actions = [
        'activate_productos',
        'deactivate_productos',
        'publish_productos',
        'unpublish_productos',
        'mark_as_featured',
        'unmark_as_featured',
        'soft_delete_productos',
        'restore_productos'
    ]

    def activate_productos(self, request, queryset):
        """
        Acción masiva para activar productos.
        """
        queryset = queryset.filter(deleted_at__isnull=True)
        updated = queryset.update(activo=True)
        self.message_user(request, f'{updated} producto(s) activado(s) exitosamente.')
    activate_productos.short_description = '✅ Activar productos seleccionados'

    def deactivate_productos(self, request, queryset):
        """
        Acción masiva para desactivar productos.
        """
        queryset = queryset.filter(deleted_at__isnull=True)
        updated = queryset.update(activo=False)
        self.message_user(request, f'{updated} producto(s) desactivado(s) exitosamente.')
    deactivate_productos.short_description = '⏸️ Desactivar productos seleccionados'

    def publish_productos(self, request, queryset):
        """
        Acción masiva para publicar productos.
        """
        queryset = queryset.filter(deleted_at__isnull=True)
        updated = queryset.update(publicado=True, activo=True)
        self.message_user(request, f'{updated} producto(s) publicado(s) exitosamente.')
    publish_productos.short_description = '📢 Publicar productos seleccionados'

    def unpublish_productos(self, request, queryset):
        """
        Acción masiva para despublicar productos.
        """
        queryset = queryset.filter(deleted_at__isnull=True)
        updated = queryset.update(publicado=False)
        self.message_user(request, f'{updated} producto(s) despublicado(s) exitosamente.')
    unpublish_productos.short_description = '📝 Despublicar productos seleccionados'

    def mark_as_featured(self, request, queryset):
        """
        Acción masiva para marcar productos como destacados.
        """
        queryset = queryset.filter(deleted_at__isnull=True)
        updated = queryset.update(destacado=True)
        self.message_user(request, f'{updated} producto(s) marcado(s) como destacado(s).')
    mark_as_featured.short_description = '⭐ Marcar como destacados'

    def unmark_as_featured(self, request, queryset):
        """
        Acción masiva para desmarcar productos como destacados.
        """
        queryset = queryset.filter(deleted_at__isnull=True)
        updated = queryset.update(destacado=False)
        self.message_user(request, f'{updated} producto(s) desmarcado(s) como destacado(s).')
    unmark_as_featured.short_description = '⚪ Quitar destacado'

    def soft_delete_productos(self, request, queryset):
        """
        Acción masiva para eliminar productos (soft delete).
        """
        queryset = queryset.filter(deleted_at__isnull=True)
        count = 0
        for producto in queryset:
            producto.delete()
            count += 1
        self.message_user(request, f'{count} producto(s) eliminado(s) exitosamente (soft delete).')
    soft_delete_productos.short_description = '🗑️ Eliminar productos seleccionados (soft delete)'

    def restore_productos(self, request, queryset):
        """
        Acción masiva para restaurar productos eliminados.
        """
        queryset = queryset.filter(deleted_at__isnull=False)
        count = 0
        for producto in queryset:
            producto.restore()
            count += 1
        self.message_user(request, f'{count} producto(s) restaurado(s) exitosamente.')
    restore_productos.short_description = '♻️ Restaurar productos eliminados'
