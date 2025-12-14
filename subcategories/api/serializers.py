from rest_framework import serializers
from subcategories.models import Subcategory
from category.models import Category


class SubcategorySerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Subcategory.
    Maneja la conversión entre objetos Subcategory y JSON.
    """

    # Campos calculados
    is_deleted = serializers.BooleanField(read_only=True)
    products_count = serializers.IntegerField(read_only=True)

    # Información de la categoría padre
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Subcategory
        fields = [
            'id',
            'category',
            'category_name',
            'name',
            'slug',
            'description',
            'icon',
            'image',
            'seo_title',
            'seo_description',
            'seo_keywords',
            'is_active',
            'order',
            'is_deleted',
            'products_count',
            'created_at',
            'updated_at',
            'deleted_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'deleted_at', 'is_deleted', 'products_count', 'category_name']

    def to_representation(self, instance):
        """
        Personaliza la representación JSON de la subcategoría.
        Convierte nombres de campos snake_case a camelCase para el frontend.
        """
        representation = super().to_representation(instance)

        # Convertir nombres a camelCase
        camel_case_representation = {
            'id': representation['id'],
            'categoryId': representation['category'],
            'categoryName': representation['category_name'],
            'name': representation['name'],
            'slug': representation['slug'],
            'description': representation['description'],
            'icon': representation['icon'],
            'image': representation['image'],
            'seoTitle': representation['seo_title'],
            'seoDescription': representation['seo_description'],
            'seoKeywords': representation['seo_keywords'],
            'is_active': representation['is_active'],
            'order': representation['order'],
            'isDeleted': representation['is_deleted'],
            'productsCount': representation['products_count'],
            'created_at': representation['created_at'],
            'updated_at': representation['updated_at'],
            'deleted_at': representation['deleted_at'],
        }

        return camel_case_representation


class SubcategoryCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para crear y actualizar subcategorías.
    No incluye campos de solo lectura.
    Acepta tanto camelCase (JSON del frontend) como snake_case (FormData).
    """

    # Hacer que todos los campos sean opcionales para permitir actualizaciones parciales
    category_id = serializers.IntegerField(required=False)
    name = serializers.CharField(max_length=200, required=False)
    slug = serializers.SlugField(max_length=250, required=False)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    icon = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)
    image = serializers.ImageField(required=False, allow_null=True)
    seo_title = serializers.CharField(max_length=60, required=False, allow_blank=True, allow_null=True)
    seo_description = serializers.CharField(max_length=160, required=False, allow_blank=True, allow_null=True)
    seo_keywords = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    is_active = serializers.BooleanField(required=False)
    order = serializers.IntegerField(required=False)

    class Meta:
        model = Subcategory
        fields = [
            'category_id',
            'name',
            'slug',
            'description',
            'icon',
            'image',
            'seo_title',
            'seo_description',
            'seo_keywords',
            'is_active',
            'order',
        ]

    def to_internal_value(self, data):
        """
        Convierte camelCase a snake_case para compatibilidad con el frontend.
        Si viene FormData, ya está en snake_case, si viene JSON está en camelCase.
        """
        # Mapeo de camelCase a snake_case
        camel_to_snake = {
            'categoryId': 'category_id',
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
        Valida que los campos requeridos estén presentes en creación.
        """
        # Si es creación (no hay instance), validar campos obligatorios
        if self.instance is None:
            if 'name' not in data:
                raise serializers.ValidationError({"name": "El nombre de la subcategoría es requerido."})
            if 'category_id' not in data:
                raise serializers.ValidationError({"category_id": "La categoría es requerida."})

        # Validar el nombre si fue proporcionado
        if 'name' in data:
            name = data['name']
            if not name or not name.strip():
                raise serializers.ValidationError({"name": "El nombre de la subcategoría no puede estar vacío."})

            # Validar unicidad del nombre
            if self.instance is None:  # Creación
                if Subcategory.objects.filter(name__iexact=name).exists():
                    raise serializers.ValidationError({"name": "Ya existe una subcategoría con este nombre."})
            else:  # Actualización
                if Subcategory.objects.filter(name__iexact=name).exclude(pk=self.instance.pk).exists():
                    raise serializers.ValidationError({"name": "Ya existe una subcategoría con este nombre."})

            # Limpiar el nombre
            data['name'] = name.strip()

        # Validar category_id si fue proporcionado
        if 'category_id' in data:
            category_id = data['category_id']
            if not Category.objects.filter(pk=category_id).exists():
                raise serializers.ValidationError({"category_id": "La categoría especificada no existe."})

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

    def create(self, validated_data):
        """
        Crea una nueva subcategoría.
        """
        # Extraer category_id y obtener el objeto Category
        category_id = validated_data.pop('category_id')
        category = Category.objects.get(pk=category_id)

        # Crear la subcategoría con la categoría asociada
        subcategory = Subcategory.objects.create(category=category, **validated_data)
        return subcategory

    def update(self, instance, validated_data):
        """
        Actualiza una subcategoría existente.
        """
        # Si se proporciona category_id, obtener el objeto Category
        if 'category_id' in validated_data:
            category_id = validated_data.pop('category_id')
            instance.category = Category.objects.get(pk=category_id)

        # Actualizar los demás campos
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class SubcategoryBulkCreateSerializer(serializers.Serializer):
    """
    Serializer para creación en masa de subcategorías.
    Acepta una lista de subcategorías y las crea todas juntas.
    """
    subcategories = SubcategoryCreateUpdateSerializer(many=True)

    def create(self, validated_data):
        """
        Crea múltiples subcategorías en una sola operación.
        """
        subcategories_data = validated_data.get('subcategories', [])
        created_subcategories = []
        errors = []

        for subcategory_data in subcategories_data:
            try:
                # Extraer category_id y obtener el objeto Category
                category_id = subcategory_data.pop('category_id')
                category = Category.objects.get(pk=category_id)

                # Crear la subcategoría
                subcategory = Subcategory.objects.create(category=category, **subcategory_data)
                created_subcategories.append(subcategory)
            except Exception as e:
                errors.append({
                    'data': subcategory_data,
                    'error': str(e)
                })

        return {
            'created': created_subcategories,
            'errors': errors
        }
