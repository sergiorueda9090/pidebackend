from django.db import models
from django.utils.text import slugify
from django.utils import timezone

# Create your models here.

class AttributeManager(models.Manager):
    """
    Manager personalizado para manejar soft deletes.
    """
    def get_queryset(self):
        """
        Retorna solo atributos no eliminados por defecto.
        """
        return super().get_queryset().filter(deleted_at__isnull=True)

    def with_deleted(self):
        """
        Retorna todos los atributos incluyendo los eliminados.
        """
        return super().get_queryset()

    def only_deleted(self):
        """
        Retorna solo los atributos eliminados.
        """
        return super().get_queryset().filter(deleted_at__isnull=False)


class Attribute(models.Model):
    """
    Modelo para atributos dinámicos de productos del e-commerce.
    Define los tipos de atributos disponibles (Color, Talla, Capacidad, Material, etc.).
    """

    # Choices para tipo de input
    INPUT_TYPE_CHOICES = [
        ('text', 'Texto'),
        ('number', 'Número'),
        ('select', 'Selección'),
        ('color', 'Color'),
        ('checkbox', 'Checkbox'),
        ('radio', 'Radio'),
    ]

    # Choices para tipo de dato
    DATA_TYPE_CHOICES = [
        ('string', 'String'),
        ('integer', 'Integer'),
        ('float', 'Float'),
        ('boolean', 'Boolean'),
    ]

    # Información Básica
    name = models.CharField(
        max_length=200,
        verbose_name="Nombre del Atributo",
        help_text="Nombre del atributo (ej: Color, Talla, Capacidad, Material)"
    )

    slug = models.SlugField(
        max_length=250,
        unique=True,
        verbose_name="Slug (URL amigable)",
        help_text="URL amigable generada automáticamente desde el nombre"
    )

    descripcion = models.TextField(
        blank=True,
        null=True,
        verbose_name="Descripción",
        help_text="Descripción opcional del atributo"
    )

    # Configuración del Tipo
    tipo_input = models.CharField(
        max_length=20,
        choices=INPUT_TYPE_CHOICES,
        default='text',
        verbose_name="Tipo de Input",
        help_text="Define cómo se mostrará el atributo en el formulario"
    )

    tipo_dato = models.CharField(
        max_length=20,
        choices=DATA_TYPE_CHOICES,
        default='string',
        verbose_name="Tipo de Dato",
        help_text="Tipo de dato que almacenará el atributo"
    )

    # Opciones Avanzadas
    es_variable = models.BooleanField(
        default=True,
        verbose_name="Es Variable",
        help_text="Si afecta precio y/o stock de los productos"
    )

    es_filtrable = models.BooleanField(
        default=True,
        verbose_name="Es Filtrable",
        help_text="Si aparece en los filtros de búsqueda del catálogo"
    )

    orden = models.IntegerField(
        default=0,
        verbose_name="Orden de Visualización",
        help_text="Menor número = mayor prioridad (0 por defecto)"
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
        help_text="Fecha en que se eliminó el atributo (soft delete)"
    )

    # Manager personalizado
    objects = AttributeManager()
    all_objects = models.Manager()  # Manager para acceder a TODOS los atributos

    class Meta:
        verbose_name = "Atributo"
        verbose_name_plural = "Atributos"
        db_table = "attributes"
        ordering = ['orden', 'name']  # Por orden, luego por nombre
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['tipo_input']),
            models.Index(fields=['es_variable']),
            models.Index(fields=['es_filtrable']),
            models.Index(fields=['orden']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """
        Override del método save para generar automáticamente el slug
        si no existe o si el nombre ha cambiado.
        """
        if not self.slug or self.name:
            # Generar slug desde el nombre
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1

            # Asegurar que el slug sea único
            while Attribute.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)

    @property
    def values_count(self):
        """
        Retorna el número de valores asociados a este atributo.
        """
        return self.values.count() if hasattr(self, 'values') else 0

    def delete(self, using=None, keep_parents=False):
        """
        Override del método delete para implementar soft delete.
        No elimina físicamente el registro, solo marca deleted_at.
        """
        self.deleted_at = timezone.now()
        self.save()

    def hard_delete(self):
        """
        Método para eliminar físicamente el registro si es necesario.
        Solo usar en casos excepcionales.
        """
        super().delete()

    def restore(self):
        """
        Restaura un atributo eliminado.
        """
        self.deleted_at = None
        self.save()

    @property
    def is_deleted(self):
        """
        Indica si el atributo está eliminado.
        """
        return self.deleted_at is not None
