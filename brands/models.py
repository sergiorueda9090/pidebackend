from django.db import models
from django.utils.text import slugify
from django.core.validators import FileExtensionValidator, URLValidator
from django.utils import timezone

# Create your models here.

class BrandManager(models.Manager):
    """
    Manager personalizado para manejar soft deletes.
    """
    def get_queryset(self):
        """
        Retorna solo marcas no eliminadas por defecto.
        """
        return super().get_queryset().filter(deleted_at__isnull=True)

    def with_deleted(self):
        """
        Retorna todas las marcas incluyendo las eliminadas.
        """
        return super().get_queryset()

    def only_deleted(self):
        """
        Retorna solo las marcas eliminadas.
        """
        return super().get_queryset().filter(deleted_at__isnull=False)


class Brand(models.Model):
    """
    Modelo para marcas de productos del e-commerce.
    Incluye información básica, logo, sitio web y opciones de destacado.
    """

    # Información Básica
    name = models.CharField(
        max_length=200,
        verbose_name="Nombre de la Marca",
        help_text="Nombre de la marca (ej: Nike, Apple, Samsung)"
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
        help_text="Descripción breve de la marca"
    )

    # Logo
    logo = models.ImageField(
        upload_to='brands/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'])],
        verbose_name="Logo de la Marca",
        help_text="Logo de la marca (JPG, PNG, GIF, WEBP, SVG - preferible con fondo transparente)"
    )

    # Sitio Web
    website = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="Sitio Web",
        help_text="URL del sitio web oficial de la marca (ej: https://www.marca.com)"
    )

    # Estado y Control
    is_active = models.BooleanField(
        default=True,
        verbose_name="Activa",
        help_text="Indica si la marca está activa y visible en el catálogo"
    )

    is_featured = models.BooleanField(
        default=False,
        verbose_name="Destacada",
        help_text="Marca destacada en la página principal"
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
        help_text="Fecha en que se eliminó la marca (soft delete)"
    )

    # Manager personalizado
    objects = BrandManager()
    all_objects = models.Manager()  # Manager para acceder a TODAS las marcas

    class Meta:
        verbose_name = "Marca"
        verbose_name_plural = "Marcas"
        db_table = "brands"
        ordering = ['-is_featured', '-created_at']  # Destacadas primero, luego por fecha
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_featured']),
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
            while Brand.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)

    @property
    def products_count(self):
        """
        Retorna el número de productos asociados a esta marca.
        """
        return self.products.filter(is_active=True).count() if hasattr(self, 'products') else 0

    def delete(self, using=None, keep_parents=False):
        """
        Override del método delete para implementar soft delete.
        No elimina físicamente el registro, solo marca deleted_at.
        """
        self.deleted_at = timezone.now()
        self.is_active = False  # También desactivar la marca
        self.save()

    def hard_delete(self):
        """
        Método para eliminar físicamente el registro si es necesario.
        Solo usar en casos excepcionales.
        """
        super().delete()

    def restore(self):
        """
        Restaura una marca eliminada.
        """
        self.deleted_at = None
        self.is_active = True
        self.save()

    @property
    def is_deleted(self):
        """
        Indica si la marca está eliminada.
        """
        return self.deleted_at is not None
