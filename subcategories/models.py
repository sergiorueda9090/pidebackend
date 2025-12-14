from django.db import models
from django.utils.text import slugify
from django.core.validators import FileExtensionValidator
from django.utils import timezone
from category.models import Category

# Create your models here.

class SubcategoryManager(models.Manager):
    """
    Manager personalizado para manejar soft deletes.
    """
    def get_queryset(self):
        """
        Retorna solo subcategorías no eliminadas por defecto.
        """
        return super().get_queryset().filter(deleted_at__isnull=True)

    def with_deleted(self):
        """
        Retorna todas las subcategorías incluyendo las eliminadas.
        """
        return super().get_queryset()

    def only_deleted(self):
        """
        Retorna solo las subcategorías eliminadas.
        """
        return super().get_queryset().filter(deleted_at__isnull=False)


class Subcategory(models.Model):
    """
    Modelo para subcategorías de productos del e-commerce.
    Cada subcategoría pertenece a una categoría padre.
    Incluye información básica, SEO, imagen e icono.
    """

    # Relación con Categoría
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='subcategories',
        verbose_name="Categoría Padre",
        help_text="Categoría a la que pertenece esta subcategoría"
    )

    # Información Básica
    name = models.CharField(
        max_length=200,
        verbose_name="Nombre de la Subcategoría",
        help_text="Nombre descriptivo de la subcategoría"
    )

    slug = models.SlugField(
        max_length=250,
        unique=True,
        verbose_name="Slug (URL amigable)",
        help_text="URL amigable generada automáticamente desde el nombre"
    )

    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Descripción",
        help_text="Descripción breve de la subcategoría para los clientes"
    )

    icon = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Icono",
        help_text="Nombre del icono de Material-UI (ej: Smartphone, Computer)"
    )

    # Imagen
    image = models.ImageField(
        upload_to='subcategories/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp'])],
        verbose_name="Imagen de la Subcategoría",
        help_text="Imagen representativa de la subcategoría (JPG, PNG, GIF, WEBP)"
    )

    # Campos SEO
    seo_title = models.CharField(
        max_length=60,
        blank=True,
        null=True,
        verbose_name="Título SEO",
        help_text="Título optimizado para motores de búsqueda (50-60 caracteres)"
    )

    seo_description = models.CharField(
        max_length=160,
        blank=True,
        null=True,
        verbose_name="Descripción SEO",
        help_text="Descripción meta para resultados de búsqueda (150-160 caracteres)"
    )

    seo_keywords = models.TextField(
        blank=True,
        null=True,
        verbose_name="Palabras Clave (Keywords)",
        help_text="Palabras clave separadas por comas para SEO"
    )

    # Estado y Control
    is_active = models.BooleanField(
        default=True,
        verbose_name="Activa",
        help_text="Indica si la subcategoría está activa y visible en el catálogo"
    )

    order = models.IntegerField(
        default=0,
        verbose_name="Orden",
        help_text="Orden de visualización de la subcategoría dentro de su categoría"
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
        help_text="Fecha en que se eliminó la subcategoría (soft delete)"
    )

    # Manager personalizado
    objects = SubcategoryManager()
    all_objects = models.Manager()  # Manager para acceder a TODAS las subcategorías

    class Meta:
        verbose_name = "Subcategoría"
        verbose_name_plural = "Subcategorías"
        db_table = "subcategories"
        ordering = ['category', 'order', 'name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active']),
            models.Index(fields=['category', 'order']),
            models.Index(fields=['-created_at']),
        ]
        unique_together = [['category', 'order']]

    def __str__(self):
        return f"{self.category.name} - {self.name}"

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
            while Subcategory.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)

    @property
    def products_count(self):
        """
        Retorna el número de productos asociados a esta subcategoría.
        """
        return self.products.filter(is_active=True).count() if hasattr(self, 'products') else 0

    @property
    def seo_keywords_list(self):
        """
        Retorna las keywords como lista (separadas por comas).
        """
        if self.seo_keywords:
            return [keyword.strip() for keyword in self.seo_keywords.split(',')]
        return []

    def delete(self, using=None, keep_parents=False):
        """
        Override del método delete para implementar soft delete.
        No elimina físicamente el registro, solo marca deleted_at.
        """
        self.deleted_at = timezone.now()
        self.is_active = False  # También desactivar la subcategoría
        self.save()

    def hard_delete(self):
        """
        Método para eliminar físicamente el registro si es necesario.
        Solo usar en casos excepcionales.
        """
        super().delete()

    def restore(self):
        """
        Restaura una subcategoría eliminada.
        """
        self.deleted_at = None
        self.is_active = True
        self.save()

    @property
    def is_deleted(self):
        """
        Indica si la subcategoría está eliminada.
        """
        return self.deleted_at is not None
