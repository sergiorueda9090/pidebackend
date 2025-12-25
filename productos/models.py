from django.db import models
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from category.models import Category
from brands.models import Brand
from user.models import User


# Create your models here.
class ProductoManager(models.Manager):
    """
    Manager personalizado para manejar soft deletes.
    """
    def get_queryset(self):
        """
        Retorna solo productos no eliminados por defecto.
        """
        return super().get_queryset().filter(deleted_at__isnull=True)

    def with_deleted(self):
        """
        Retorna todos los productos incluyendo los eliminados.
        """
        return super().get_queryset()

    def only_deleted(self):
        """
        Retorna solo los productos eliminados.
        """
        return super().get_queryset().filter(deleted_at__isnull=False)


class Producto(models.Model):
    """
    Modelo para productos del e-commerce.
    Soporta productos simples, variables y digitales.
    """

    # Tipos de producto
    TIPO_PRODUCTO_CHOICES = [
        ('simple', 'Simple'),
        ('variable', 'Variable'),
        ('digital', 'Digital'),
    ]

    # Información Básica
    nombre = models.CharField(
        max_length=255,
        db_index=True,
        verbose_name="Nombre del Producto",
        help_text="Nombre descriptivo del producto"
    )

    slug = models.SlugField(
        max_length=280,
        unique=True,
        db_index=True,
        verbose_name="Slug (URL amigable)",
        help_text="URL amigable generada automáticamente desde el nombre"
    )

    sku_base = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        verbose_name="SKU Base",
        help_text="Código único de identificación del producto"
    )

    descripcion_corta = models.CharField(
        max_length=300,
        blank=True,
        verbose_name="Descripción Corta",
        help_text="Descripción breve del producto (máx. 300 caracteres)"
    )

    descripcion_larga = models.TextField(
        blank=True,
        verbose_name="Descripción Larga",
        help_text="Descripción detallada del producto con características completas"
    )

    # Relaciones
    categoria = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='productos',
        db_index=True,
        verbose_name="Categoría",
        help_text="Categoría a la que pertenece el producto"
    )

    marca = models.ForeignKey(
        Brand,
        on_delete=models.SET_NULL,
        related_name='productos',
        blank=True,
        null=True,
        db_index=True,
        verbose_name="Marca",
        help_text="Marca del producto"
    )

    # Control de variantes
    tiene_variantes = models.BooleanField(
        default=False,
        verbose_name="Tiene Variantes",
        help_text="Indica si el producto tiene variantes (tallas, colores, etc.)"
    )

    tipo_producto = models.CharField(
        max_length=10,
        choices=TIPO_PRODUCTO_CHOICES,
        default='simple',
        verbose_name="Tipo de Producto",
        help_text="Tipo de producto: simple, variable o digital"
    )

    # Precios base (si no tiene variantes)
    precio_base = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
        verbose_name="Precio Base",
        help_text="Precio de venta del producto"
    )

    precio_costo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
        verbose_name="Precio de Costo",
        help_text="Precio de costo del producto"
    )

    precio_descuento = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
        verbose_name="Precio con Descuento",
        help_text="Precio con descuento aplicado"
    )

    porcentaje_descuento = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Porcentaje de Descuento",
        help_text="Porcentaje de descuento (0-100)"
    )

    moneda = models.CharField(
        max_length=3,
        default='COP',
        verbose_name="Moneda",
        help_text="Código de moneda (ISO 4217)"
    )

    # Inventario base (si no tiene variantes)
    stock_actual = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Stock Actual",
        help_text="Cantidad disponible en inventario"
    )

    stock_minimo = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Stock Mínimo",
        help_text="Cantidad mínima de stock antes de reabastecer"
    )

    unidad_medida = models.CharField(
        max_length=20,
        default='unidad',
        verbose_name="Unidad de Medida",
        help_text="Unidad en la que se mide el producto"
    )

    # Dimensiones y peso
    peso = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
        verbose_name="Peso (gramos)",
        help_text="Peso del producto en gramos"
    )

    largo = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
        verbose_name="Largo (cm)",
        help_text="Largo del producto en centímetros"
    )

    ancho = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
        verbose_name="Ancho (cm)",
        help_text="Ancho del producto en centímetros"
    )

    alto = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
        verbose_name="Alto (cm)",
        help_text="Alto del producto en centímetros"
    )

    # Campos SEO
    meta_title = models.CharField(
        max_length=160,
        blank=True,
        null=True,
        verbose_name="Título SEO",
        help_text="Título optimizado para motores de búsqueda (máx. 160 caracteres)"
    )

    meta_description = models.CharField(
        max_length=320,
        blank=True,
        null=True,
        verbose_name="Descripción SEO",
        help_text="Descripción meta para resultados de búsqueda (máx. 320 caracteres)"
    )

    keywords = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="Palabras Clave (Keywords)",
        help_text="Palabras clave separadas por comas para SEO"
    )

    # Estados
    activo = models.BooleanField(
        default=True,
        verbose_name="Activo",
        help_text="Indica si el producto está activo en el sistema"
    )

    publicado = models.BooleanField(
        default=False,
        verbose_name="Publicado",
        help_text="Indica si el producto está publicado y visible en el catálogo"
    )

    destacado = models.BooleanField(
        default=False,
        verbose_name="Destacado",
        help_text="Indica si el producto aparece en la sección de destacados"
    )

    es_nuevo = models.BooleanField(
        default=False,
        verbose_name="Es Nuevo",
        help_text="Indica si el producto se marca como nuevo"
    )

    fecha_publicacion = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Fecha de Publicación",
        help_text="Fecha en que el producto fue publicado"
    )

    fecha_nuevo_hasta = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Fecha 'Nuevo' Hasta",
        help_text="Fecha hasta la cual el producto se considera nuevo"
    )

    # Métricas
    vistas = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Vistas",
        help_text="Número de veces que se ha visto el producto"
    )

    ventas_totales = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Ventas Totales",
        help_text="Número total de unidades vendidas"
    )

    rating_promedio = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        verbose_name="Rating Promedio",
        help_text="Calificación promedio del producto (0-5)"
    )

    total_reviews = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Total de Reviews",
        help_text="Número total de reseñas del producto"
    )

    # Auditoría
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
        help_text="Fecha en que se eliminó el producto (soft delete)"
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='productos_creados',
        null=True,
        verbose_name="Creado Por",
        help_text="Usuario que creó el producto"
    )

    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='productos_actualizados',
        blank=True,
        null=True,
        verbose_name="Actualizado Por",
        help_text="Usuario que actualizó el producto por última vez"
    )

    # Manager personalizado
    objects = ProductoManager()
    all_objects = models.Manager()  # Manager para acceder a TODOS los productos

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        db_table = "productos"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['nombre']),
            models.Index(fields=['slug']),
            models.Index(fields=['categoria']),
            models.Index(fields=['marca']),
            models.Index(fields=['activo']),
            models.Index(fields=['publicado']),
            models.Index(fields=['destacado']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        """
        Override del método save para generar automáticamente el slug
        si no existe o si el nombre ha cambiado.
        """
        if not self.slug or self.nombre:
            # Generar slug desde el nombre
            base_slug = slugify(self.nombre)
            slug = base_slug
            counter = 1

            # Asegurar que el slug sea único
            while Producto.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        """
        Override del método delete para implementar soft delete.
        No elimina físicamente el registro, solo marca deleted_at.
        """
        self.deleted_at = timezone.now()
        self.activo = False
        self.publicado = False
        self.save()

    def hard_delete(self):
        """
        Método para eliminar físicamente el registro si es necesario.
        Solo usar en casos excepcionales.
        """
        super().delete()

    def restore(self):
        """
        Restaura un producto eliminado.
        """
        self.deleted_at = None
        self.activo = True
        self.save()

    @property
    def is_deleted(self):
        """
        Indica si el producto está eliminado.
        """
        return self.deleted_at is not None

    @property
    def tiene_stock(self):
        """
        Indica si el producto tiene stock disponible.
        """
        return self.stock_actual > 0

    @property
    def stock_bajo(self):
        """
        Indica si el stock está por debajo del mínimo.
        """
        return self.stock_actual <= self.stock_minimo

    @property
    def precio_final(self):
        """
        Retorna el precio final considerando descuentos.
        """
        if self.precio_descuento:
            return self.precio_descuento
        return self.precio_base

    @property
    def tiene_descuento(self):
        """
        Indica si el producto tiene descuento aplicado.
        """
        return self.precio_descuento is not None and self.precio_descuento < self.precio_base

    @property
    def margen_ganancia(self):
        """
        Calcula el margen de ganancia del producto.
        """
        if self.precio_base and self.precio_costo:
            return self.precio_base - self.precio_costo
        return None

    @property
    def porcentaje_ganancia(self):
        """
        Calcula el porcentaje de ganancia del producto.
        """
        if self.precio_base and self.precio_costo and self.precio_costo > 0:
            return ((self.precio_base - self.precio_costo) / self.precio_costo) * 100
        return None

    @property
    def keywords_list(self):
        """
        Retorna las keywords como lista (separadas por comas).
        """
        if self.keywords:
            return [keyword.strip() for keyword in self.keywords.split(',')]
        return []

    @property
    def categoria_nombre(self):
        """
        Retorna el nombre de la categoría.
        """
        return self.categoria.name if self.categoria else None

    @property
    def marca_nombre(self):
        """
        Retorna el nombre de la marca.
        """
        return self.marca.name if self.marca else None

    @property
    def volumen(self):
        """
        Calcula el volumen del producto en cm³.
        """
        if self.largo and self.ancho and self.alto:
            return self.largo * self.ancho * self.alto
        return None

    def incrementar_vistas(self):
        """
        Incrementa el contador de vistas del producto.
        """
        self.vistas += 1
        self.save(update_fields=['vistas'])

    def incrementar_ventas(self, cantidad=1):
        """
        Incrementa el contador de ventas del producto.
        """
        self.ventas_totales += cantidad
        self.save(update_fields=['ventas_totales'])

    def actualizar_stock(self, cantidad):
        """
        Actualiza el stock del producto.
        Cantidad positiva suma, negativa resta.
        """
        self.stock_actual += cantidad
        if self.stock_actual < 0:
            self.stock_actual = 0
        self.save(update_fields=['stock_actual'])
