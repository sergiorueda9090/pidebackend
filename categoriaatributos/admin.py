from django.contrib import admin
from .models import CategoriaAtributo


@admin.register(CategoriaAtributo)
class CategoriaAtributoAdmin(admin.ModelAdmin):
    """
    Configuración del panel de administración para el modelo CategoriaAtributo.
    """
    list_display = ['id', 'categoria', 'atributo', 'obligatorio', 'orden', 'created_at']
    list_filter = ['obligatorio', 'categoria', 'created_at']
    search_fields = ['categoria__name', 'atributo__name']
    ordering = ['categoria', 'orden', 'atributo__name']

    fieldsets = (
        ('Relación', {
            'fields': ('categoria', 'atributo')
        }),
        ('Configuración', {
            'fields': ('obligatorio', 'orden')
        }),
        ('Información de Auditoría', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at']

    # Configuración de la lista
    list_per_page = 25
    date_hierarchy = 'created_at'

    # Filtros laterales
    autocomplete_fields = []  # Puedes agregar 'categoria' y 'atributo' si configuras autocomplete en sus admins

    def get_readonly_fields(self, request, obj=None):
        """
        Hacer que categoria y atributo sean de solo lectura en edición
        para prevenir cambios accidentales en relaciones existentes.
        """
        if obj:  # Si es edición
            return self.readonly_fields + ['categoria', 'atributo']
        return self.readonly_fields
