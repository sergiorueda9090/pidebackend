from django.db import models
from django.utils import timezone
from atributos.models import Attribute

# Create your models here.

class AttributeValueManager(models.Manager):
    """
    Manager personalizado para manejar soft deletes.
    """
    def get_queryset(self):
        """
        Retorna solo valores de atributos no eliminados por defecto.
        """
        return super().get_queryset().filter(deleted_at__isnull=True)

    def with_deleted(self):
        """
        Retorna todos los valores de atributos incluyendo los eliminados.
        """
        return super().get_queryset()

    def only_deleted(self):
        """
        Retorna solo los valores de atributos eliminados.
        """
        return super().get_queryset().filter(deleted_at__isnull=False)


class AttributeValue(models.Model):
    """
    Modelo para valores de atributos dinámicos del e-commerce.
    Cada valor pertenece a un atributo padre.
    Ejemplos:
    - atributo: Color | valor: "Rojo" | valor_extra: "#FF0000"
    - atributo: Talla | valor: "XL" | valor_extra: null
    - atributo: Capacidad | valor: "128GB" | valor_extra: null
    """

    # Relación con Atributo
    atributo = models.ForeignKey(
        Attribute,
        on_delete=models.CASCADE,
        related_name='values',
        verbose_name="Atributo",
        help_text="Atributo al que pertenece este valor"
    )

    # Información del Valor
    valor = models.CharField(
        max_length=100,
        verbose_name="Valor",
        help_text="Valor del atributo (ej: Rojo, XL, 128GB, Algodón)"
    )

    valor_extra = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Valor Extra (Opcional)",
        help_text="Información adicional del valor (ej: código hexadecimal #FF0000 para colores)"
    )

    # Control
    orden = models.IntegerField(
        default=0,
        verbose_name="Orden de Visualización",
        help_text="Menor número aparece primero (0 por defecto)"
    )

    activo = models.BooleanField(
        default=True,
        verbose_name="Activo",
        help_text="Indica si el valor está activo y visible en formularios"
    )

    # Campos de Auditoría
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Creación"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Fecha de Actualización"
    )

    deleted_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Fecha de Eliminación",
        help_text="Fecha en que se eliminó el valor (soft delete)"
    )

    # Manager personalizado
    objects = AttributeValueManager()
    all_objects = models.Manager()  # Manager para acceder a TODOS los valores

    class Meta:
        verbose_name = "Valor de Atributo"
        verbose_name_plural = "Valores de Atributos"
        db_table = "attribute_values"
        ordering = ['atributo', 'orden', 'valor']
        indexes = [
            models.Index(fields=['atributo', 'orden']),
            models.Index(fields=['activo']),
            models.Index(fields=['-created_at']),
        ]
        unique_together = [['atributo', 'orden']]

    def __str__(self):
        return f"{self.atributo.name} - {self.valor}"

    @property
    def atributo_nombre(self):
        """
        Retorna el nombre del atributo padre.
        """
        return self.atributo.name if self.atributo else None

    @property
    def products_count(self):
        """
        Retorna el número de productos que usan este valor.
        """
        return self.product_variations.count() if hasattr(self, 'product_variations') else 0

    def delete(self, using=None, keep_parents=False):
        """
        Override del método delete para implementar soft delete.
        No elimina físicamente el registro, solo marca deleted_at.
        """
        self.deleted_at = timezone.now()
        self.activo = False  # También desactivar el valor
        self.save()

    def hard_delete(self):
        """
        Método para eliminar físicamente el registro si es necesario.
        Solo usar en casos excepcionales.
        """
        super().delete()

    def restore(self):
        """
        Restaura un valor de atributo eliminado.
        """
        self.deleted_at = None
        self.activo = True
        self.save()

    @property
    def is_deleted(self):
        """
        Indica si el valor está eliminado.
        """
        return self.deleted_at is not None
