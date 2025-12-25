from django.db import models
from category.models import Category
from atributos.models import Attribute


class CategoriaAtributo(models.Model):
    """
    Modelo para relacionar categorías con atributos.
    Define qué atributos están disponibles para cada categoría,
    si son obligatorios y su orden de visualización.
    """

    # Relaciones
    categoria = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='categoria_atributos',
        verbose_name="Categoría",
        help_text="Categoría a la que pertenece este atributo"
    )

    atributo = models.ForeignKey(
        Attribute,
        on_delete=models.CASCADE,
        related_name='categoria_atributos',
        verbose_name="Atributo",
        help_text="Atributo asociado a la categoría"
    )

    # Configuración
    obligatorio = models.BooleanField(
        default=False,
        verbose_name="Obligatorio",
        help_text="Indica si este atributo es obligatorio para productos de esta categoría"
    )

    orden = models.IntegerField(
        default=0,
        verbose_name="Orden de Visualización",
        help_text="Define el orden en que se muestra el atributo (menor número = mayor prioridad)"
    )

    # Campos de Auditoría
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Creación"
    )

    class Meta:
        verbose_name = "Categoría-Atributo"
        verbose_name_plural = "Categorías-Atributos"
        db_table = "categoria_atributos"
        ordering = ['categoria', 'orden', 'atributo__name']
        unique_together = [['categoria', 'atributo']]  # No permitir duplicados
        indexes = [
            models.Index(fields=['categoria', 'orden']),
            models.Index(fields=['atributo']),
            models.Index(fields=['obligatorio']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.categoria.name} - {self.atributo.name} {'(Obligatorio)' if self.obligatorio else ''}"

    @property
    def categoria_nombre(self):
        """
        Retorna el nombre de la categoría.
        """
        return self.categoria.name if self.categoria else ""

    @property
    def atributo_nombre(self):
        """
        Retorna el nombre del atributo.
        """
        return self.atributo.name if self.atributo else ""
