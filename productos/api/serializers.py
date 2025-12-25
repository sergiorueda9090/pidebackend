from rest_framework import serializers
from productos.models import Producto
from category.models import Category
from brands.models import Brand
from user.models import User


class ProductoSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Producto.
    Maneja la conversión entre objetos Producto y JSON.
    Incluye campos calculados y relaciones.
    """

    # Campos calculados (properties del modelo)
    is_deleted = serializers.BooleanField(read_only=True)
    tiene_stock = serializers.BooleanField(read_only=True)
    stock_bajo = serializers.BooleanField(read_only=True)
    precio_final = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    tiene_descuento = serializers.BooleanField(read_only=True)
    margen_ganancia = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    porcentaje_ganancia = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    volumen = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    # Campos de relaciones (nombres legibles)
    categoria_nombre = serializers.CharField(read_only=True)
    marca_nombre = serializers.CharField(read_only=True)
    created_by_nombre = serializers.SerializerMethodField()
    updated_by_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Producto
        fields = [
            # IDs y básicos
            'id',
            'nombre',
            'slug',
            'sku_base',
            'descripcion_corta',
            'descripcion_larga',

            # Relaciones
            'categoria',
            'categoria_nombre',
            'marca',
            'marca_nombre',

            # Control de variantes
            'tiene_variantes',
            'tipo_producto',

            # Precios
            'precio_base',
            'precio_costo',
            'precio_descuento',
            'porcentaje_descuento',
            'moneda',
            'precio_final',
            'tiene_descuento',
            'margen_ganancia',
            'porcentaje_ganancia',

            # Inventario
            'stock_actual',
            'stock_minimo',
            'unidad_medida',
            'tiene_stock',
            'stock_bajo',

            # Dimensiones
            'peso',
            'largo',
            'ancho',
            'alto',
            'volumen',

            # SEO
            'meta_title',
            'meta_description',
            'keywords',

            # Estados
            'activo',
            'publicado',
            'destacado',
            'es_nuevo',
            'fecha_publicacion',
            'fecha_nuevo_hasta',

            # Métricas
            'vistas',
            'ventas_totales',
            'rating_promedio',
            'total_reviews',

            # Auditoría
            'created_at',
            'updated_at',
            'deleted_at',
            'is_deleted',
            'created_by',
            'created_by_nombre',
            'updated_by',
            'updated_by_nombre',
        ]
        read_only_fields = [
            'id', 'slug', 'created_at', 'updated_at', 'deleted_at', 'is_deleted',
            'tiene_stock', 'stock_bajo', 'precio_final', 'tiene_descuento',
            'margen_ganancia', 'porcentaje_ganancia', 'volumen',
            'categoria_nombre', 'marca_nombre', 'created_by_nombre', 'updated_by_nombre',
        ]

    def get_created_by_nombre(self, obj):
        """Retorna el nombre completo del usuario que creó el producto."""
        if obj.created_by:
            return f"{obj.created_by.first_name} {obj.created_by.last_name}".strip() or obj.created_by.username
        return None

    def get_updated_by_nombre(self, obj):
        """Retorna el nombre completo del usuario que actualizó el producto."""
        if obj.updated_by:
            return f"{obj.updated_by.first_name} {obj.updated_by.last_name}".strip() or obj.updated_by.username
        return None

    def to_representation(self, instance):
        """
        Personaliza la representación JSON del producto.
        Convierte nombres de campos snake_case a camelCase para el frontend.
        """
        representation = super().to_representation(instance)

        # Convertir nombres a camelCase
        camel_case_representation = {
            # IDs y básicos
            'id': representation['id'],
            'nombre': representation['nombre'],
            'slug': representation['slug'],
            'skuBase': representation['sku_base'],
            'descripcionCorta': representation['descripcion_corta'],
            'descripcionLarga': representation['descripcion_larga'],

            # Relaciones
            'categoriaId': representation['categoria'],
            'categoriaNombre': representation['categoria_nombre'],
            'marcaId': representation['marca'],
            'marcaNombre': representation['marca_nombre'],

            # Control de variantes
            'tieneVariantes': representation['tiene_variantes'],
            'tipoProducto': representation['tipo_producto'],

            # Precios
            'precioBase': representation['precio_base'],
            'precioCosto': representation['precio_costo'],
            'precioDescuento': representation['precio_descuento'],
            'porcentajeDescuento': representation['porcentaje_descuento'],
            'moneda': representation['moneda'],
            'precioFinal': representation['precio_final'],
            'tieneDescuento': representation['tiene_descuento'],
            'margenGanancia': representation['margen_ganancia'],
            'porcentajeGanancia': representation['porcentaje_ganancia'],

            # Inventario
            'stockActual': representation['stock_actual'],
            'stockMinimo': representation['stock_minimo'],
            'unidadMedida': representation['unidad_medida'],
            'tieneStock': representation['tiene_stock'],
            'stockBajo': representation['stock_bajo'],

            # Dimensiones
            'peso': representation['peso'],
            'largo': representation['largo'],
            'ancho': representation['ancho'],
            'alto': representation['alto'],
            'volumen': representation['volumen'],

            # SEO
            'metaTitle': representation['meta_title'],
            'metaDescription': representation['meta_description'],
            'keywords': representation['keywords'],

            # Estados
            'activo': representation['activo'],
            'publicado': representation['publicado'],
            'destacado': representation['destacado'],
            'esNuevo': representation['es_nuevo'],
            'fechaPublicacion': representation['fecha_publicacion'],
            'fechaNuevoHasta': representation['fecha_nuevo_hasta'],

            # Métricas
            'vistas': representation['vistas'],
            'ventasTotales': representation['ventas_totales'],
            'ratingPromedio': representation['rating_promedio'],
            'totalReviews': representation['total_reviews'],

            # Auditoría
            'createdAt': representation['created_at'],
            'updatedAt': representation['updated_at'],
            'deletedAt': representation['deleted_at'],
            'isDeleted': representation['is_deleted'],
            'createdById': representation['created_by'],
            'createdByNombre': representation['created_by_nombre'],
            'updatedById': representation['updated_by'],
            'updatedByNombre': representation['updated_by_nombre'],
        }

        return camel_case_representation


class ProductoCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para crear y actualizar productos.
    No incluye campos de solo lectura.
    Acepta tanto camelCase (JSON del frontend) como snake_case (FormData).
    """

    # Hacer que todos los campos sean opcionales para permitir actualizaciones parciales
    nombre = serializers.CharField(max_length=255, required=False)
    slug = serializers.SlugField(max_length=280, required=False)
    sku_base = serializers.CharField(max_length=50, required=False, allow_blank=True, allow_null=True)
    descripcion_corta = serializers.CharField(max_length=300, required=False, allow_blank=True)
    descripcion_larga = serializers.CharField(required=False, allow_blank=True)

    # Relaciones
    categoria = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), required=False)
    marca = serializers.PrimaryKeyRelatedField(queryset=Brand.objects.all(), required=False, allow_null=True)

    # Control de variantes
    tiene_variantes = serializers.BooleanField(required=False, default=False)
    tipo_producto = serializers.ChoiceField(
        choices=['simple', 'variable', 'digital'],
        required=False,
        default='simple'
    )

    # Precios
    precio_base = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    precio_costo = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    precio_descuento = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    porcentaje_descuento = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True)
    moneda = serializers.CharField(max_length=3, required=False, default='COP')

    # Inventario
    stock_actual = serializers.IntegerField(required=False, default=0)
    stock_minimo = serializers.IntegerField(required=False, default=0)
    unidad_medida = serializers.CharField(max_length=20, required=False, default='unidad')

    # Dimensiones
    peso = serializers.DecimalField(max_digits=8, decimal_places=2, required=False, allow_null=True)
    largo = serializers.DecimalField(max_digits=8, decimal_places=2, required=False, allow_null=True)
    ancho = serializers.DecimalField(max_digits=8, decimal_places=2, required=False, allow_null=True)
    alto = serializers.DecimalField(max_digits=8, decimal_places=2, required=False, allow_null=True)

    # SEO
    meta_title = serializers.CharField(max_length=160, required=False, allow_blank=True, allow_null=True)
    meta_description = serializers.CharField(max_length=320, required=False, allow_blank=True, allow_null=True)
    keywords = serializers.CharField(max_length=500, required=False, allow_blank=True, allow_null=True)

    # Estados
    activo = serializers.BooleanField(required=False, default=True)
    publicado = serializers.BooleanField(required=False, default=False)
    destacado = serializers.BooleanField(required=False, default=False)
    es_nuevo = serializers.BooleanField(required=False, default=False)
    fecha_publicacion = serializers.DateTimeField(required=False, allow_null=True)
    fecha_nuevo_hasta = serializers.DateTimeField(required=False, allow_null=True)

    # Auditoría
    created_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False, allow_null=True)
    updated_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False, allow_null=True)

    class Meta:
        model = Producto
        fields = [
            # Básicos
            'nombre',
            'slug',
            'sku_base',
            'descripcion_corta',
            'descripcion_larga',

            # Relaciones
            'categoria',
            'marca',

            # Control de variantes
            'tiene_variantes',
            'tipo_producto',

            # Precios
            'precio_base',
            'precio_costo',
            'precio_descuento',
            'porcentaje_descuento',
            'moneda',

            # Inventario
            'stock_actual',
            'stock_minimo',
            'unidad_medida',

            # Dimensiones
            'peso',
            'largo',
            'ancho',
            'alto',

            # SEO
            'meta_title',
            'meta_description',
            'keywords',

            # Estados
            'activo',
            'publicado',
            'destacado',
            'es_nuevo',
            'fecha_publicacion',
            'fecha_nuevo_hasta',

            # Auditoría
            'created_by',
            'updated_by',
        ]

    def to_internal_value(self, data):
        """
        Convierte camelCase a snake_case para compatibilidad con el frontend.
        Si viene FormData, ya está en snake_case, si viene JSON está en camelCase.
        """
        # Mapeo de camelCase a snake_case
        camel_to_snake = {
            'skuBase': 'sku_base',
            'descripcionCorta': 'descripcion_corta',
            'descripcionLarga': 'descripcion_larga',
            'categoriaId': 'categoria',
            'marcaId': 'marca',
            'tieneVariantes': 'tiene_variantes',
            'tipoProducto': 'tipo_producto',
            'precioBase': 'precio_base',
            'precioCosto': 'precio_costo',
            'precioDescuento': 'precio_descuento',
            'porcentajeDescuento': 'porcentaje_descuento',
            'stockActual': 'stock_actual',
            'stockMinimo': 'stock_minimo',
            'unidadMedida': 'unidad_medida',
            'metaTitle': 'meta_title',
            'metaDescription': 'meta_description',
            'esNuevo': 'es_nuevo',
            'fechaPublicacion': 'fecha_publicacion',
            'fechaNuevoHasta': 'fecha_nuevo_hasta',
            'createdById': 'created_by',
            'updatedById': 'updated_by',
        }

        # Crear una copia mutable de los datos
        if hasattr(data, 'dict'):  # Si es QueryDict (FormData)
            mutable_data = data.dict()
        else:  # Si es dict normal (JSON)
            mutable_data = dict(data)

        # Convertir camelCase a snake_case
        for camel_key, snake_key in camel_to_snake.items():
            if camel_key in mutable_data:
                mutable_data[snake_key] = mutable_data.pop(camel_key)

        return super().to_internal_value(mutable_data)

    def validate(self, data):
        """
        Validaciones generales del producto.
        """
        # Si es creación (no hay instance), el nombre y categoría son obligatorios
        if self.instance is None:
            if 'nombre' not in data:
                raise serializers.ValidationError({"nombre": "El nombre del producto es requerido."})
            if 'categoria' not in data:
                raise serializers.ValidationError({"categoria": "La categoría es requerida."})

        # Validar el nombre si fue proporcionado
        if 'nombre' in data:
            nombre = data['nombre']
            if not nombre or not nombre.strip():
                raise serializers.ValidationError({"nombre": "El nombre del producto no puede estar vacío."})

            # Limpiar el nombre
            data['nombre'] = nombre.strip()

        # Validar SKU único si fue proporcionado
        if 'sku_base' in data and data['sku_base']:
            sku = data['sku_base'].strip()
            if self.instance is None:  # Creación
                if Producto.objects.filter(sku_base__iexact=sku).exists():
                    raise serializers.ValidationError({"sku_base": "Ya existe un producto con este SKU."})
            else:  # Actualización
                if Producto.objects.filter(sku_base__iexact=sku).exclude(pk=self.instance.pk).exists():
                    raise serializers.ValidationError({"sku_base": "Ya existe un producto con este SKU."})
            data['sku_base'] = sku

        # Validar precios
        if 'precio_base' in data and data['precio_base'] is not None:
            if data['precio_base'] < 0:
                raise serializers.ValidationError({"precio_base": "El precio base no puede ser negativo."})

        if 'precio_costo' in data and data['precio_costo'] is not None:
            if data['precio_costo'] < 0:
                raise serializers.ValidationError({"precio_costo": "El precio de costo no puede ser negativo."})

        if 'precio_descuento' in data and data['precio_descuento'] is not None:
            if data['precio_descuento'] < 0:
                raise serializers.ValidationError({"precio_descuento": "El precio de descuento no puede ser negativo."})

            # Si hay precio base, validar que el descuento sea menor
            precio_base = data.get('precio_base') or (self.instance.precio_base if self.instance else None)
            if precio_base and data['precio_descuento'] >= precio_base:
                raise serializers.ValidationError({
                    "precio_descuento": "El precio con descuento debe ser menor al precio base."
                })

        if 'porcentaje_descuento' in data and data['porcentaje_descuento'] is not None:
            if data['porcentaje_descuento'] < 0 or data['porcentaje_descuento'] > 100:
                raise serializers.ValidationError({
                    "porcentaje_descuento": "El porcentaje de descuento debe estar entre 0 y 100."
                })

        # Validar stock
        if 'stock_actual' in data and data['stock_actual'] < 0:
            raise serializers.ValidationError({"stock_actual": "El stock actual no puede ser negativo."})

        if 'stock_minimo' in data and data['stock_minimo'] < 0:
            raise serializers.ValidationError({"stock_minimo": "El stock mínimo no puede ser negativo."})

        # Validar dimensiones
        for field in ['peso', 'largo', 'ancho', 'alto']:
            if field in data and data[field] is not None and data[field] < 0:
                raise serializers.ValidationError({field: f"El {field} no puede ser negativo."})

        # Validar rating
        if 'rating_promedio' in data and data['rating_promedio'] is not None:
            if data['rating_promedio'] < 0 or data['rating_promedio'] > 5:
                raise serializers.ValidationError({
                    "rating_promedio": "El rating debe estar entre 0 y 5."
                })

        return data

    def validate_categoria(self, value):
        """Valida que la categoría exista y esté activa."""
        if value and not value.is_active:
            raise serializers.ValidationError("La categoría seleccionada no está activa.")
        return value

    def validate_marca(self, value):
        """Valida que la marca exista y esté activa."""
        if value and not value.is_active:
            raise serializers.ValidationError("La marca seleccionada no está activa.")
        return value
