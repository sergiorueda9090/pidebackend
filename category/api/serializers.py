from rest_framework import serializers
from category.models import Category


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Category.
    Maneja la conversión entre objetos Category y JSON.
    """

    # Campo calculado para mostrar si está eliminada
    is_deleted = serializers.BooleanField(read_only=True)

    # Campo calculado para el conteo de productos
    products_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Category
        fields = [
            'id',
            'name',
            'slug',
            'description',
            'icon',
            'image',
            'seo_title',
            'seo_description',
            'seo_keywords',
            'is_active',
            'is_deleted',
            'products_count',
            'created_at',
            'updated_at',
            'deleted_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'deleted_at', 'is_deleted', 'products_count']

    def to_representation(self, instance):
        """
        Personaliza la representación JSON de la categoría.
        Convierte nombres de campos snake_case a camelCase para el frontend.
        """
        representation = super().to_representation(instance)

        # Convertir nombres a camelCase
        camel_case_representation = {
            'id': representation['id'],
            'name': representation['name'],
            'slug': representation['slug'],
            'description': representation['description'],
            'icon': representation['icon'],
            'image': representation['image'],
            'seoTitle': representation['seo_title'],
            'seoDescription': representation['seo_description'],
            'seoKeywords': representation['seo_keywords'],
            'is_active': representation['is_active'],
            'isDeleted': representation['is_deleted'],
            'productsCount': representation['products_count'],
            'created_at': representation['created_at'],
            'updated_at': representation['updated_at'],
            'deleted_at': representation['deleted_at'],
        }

        return camel_case_representation


class CategoryCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para crear y actualizar categorías.
    No incluye campos de solo lectura.
    Acepta tanto camelCase (JSON del frontend) como snake_case (FormData).
    """

    # Hacer que todos los campos sean opcionales para permitir actualizaciones parciales
    name = serializers.CharField(max_length=200, required=False)
    slug = serializers.SlugField(max_length=250, required=False)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    icon = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)
    image = serializers.ImageField(required=False, allow_null=True)
    seo_title = serializers.CharField(max_length=60, required=False, allow_blank=True, allow_null=True)
    seo_description = serializers.CharField(max_length=160, required=False, allow_blank=True, allow_null=True)
    seo_keywords = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    is_active = serializers.BooleanField(required=False)

    class Meta:
        model = Category
        fields = [
            'name',
            'slug',
            'description',
            'icon',
            'image',
            'seo_title',
            'seo_description',
            'seo_keywords',
            'is_active',
        ]

    def to_internal_value(self, data):
        """
        Convierte camelCase a snake_case para compatibilidad con el frontend.
        Si viene FormData, ya está en snake_case, si viene JSON está en camelCase.
        """
        # Mapeo de camelCase a snake_case
        camel_to_snake = {
            'seoTitle': 'seo_title',
            'seoDescription': 'seo_description',
            'seoKeywords': 'seo_keywords',
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
        Valida que el nombre sea requerido en creación y único.
        """
        # Si es creación (no hay instance), el nombre es obligatorio
        if self.instance is None and 'name' not in data:
            raise serializers.ValidationError({"name": "El nombre de la categoría es requerido."})

        # Validar el nombre si fue proporcionado
        if 'name' in data:
            name = data['name']
            if not name or not name.strip():
                raise serializers.ValidationError({"name": "El nombre de la categoría no puede estar vacío."})

            # Validar unicidad
            if self.instance is None:  # Creación
                if Category.objects.filter(name__iexact=name).exists():
                    raise serializers.ValidationError({"name": "Ya existe una categoría con este nombre."})
            else:  # Actualización
                if Category.objects.filter(name__iexact=name).exclude(pk=self.instance.pk).exists():
                    raise serializers.ValidationError({"name": "Ya existe una categoría con este nombre."})

            # Limpiar el nombre
            data['name'] = name.strip()

        return data

    def validate_image(self, value):
        """
        Valida el tamaño y tipo de la imagen.
        """
        if value:
            # Validar tamaño (máximo 5MB)
            if value.size > 5 * 1024 * 1024:
                raise serializers.ValidationError("La imagen no puede superar los 5MB.")

            # Validar extensión
            valid_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp']
            ext = value.name.split('.')[-1].lower()
            if ext not in valid_extensions:
                raise serializers.ValidationError(
                    f"Formato de imagen no válido. Use: {', '.join(valid_extensions)}"
                )

        return value
