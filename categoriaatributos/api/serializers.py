from rest_framework import serializers
from categoriaatributos.models import CategoriaAtributo
from category.models import Category
from atributos.models import Attribute


class CategoriaAtributoSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo CategoriaAtributo.
    Maneja la conversión entre objetos CategoriaAtributo y JSON.
    """

    # Información de la categoría y atributo
    categoria_nombre = serializers.CharField(source='categoria.name', read_only=True)
    atributo_nombre = serializers.CharField(source='atributo.name', read_only=True)

    class Meta:
        model = CategoriaAtributo
        fields = [
            'id',
            'categoria',
            'categoria_nombre',
            'atributo',
            'atributo_nombre',
            'obligatorio',
            'orden',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'categoria_nombre', 'atributo_nombre']

    def to_representation(self, instance):
        """
        Personaliza la representación JSON de la relación categoría-atributo.
        Convierte nombres de campos snake_case a camelCase para el frontend.
        """
        representation = super().to_representation(instance)

        # Convertir nombres a camelCase
        camel_case_representation = {
            'id': representation['id'],
            'categoriaId': representation['categoria'],
            'categoriaNombre': representation['categoria_nombre'],
            'atributoId': representation['atributo'],
            'atributoNombre': representation['atributo_nombre'],
            'obligatorio': representation['obligatorio'],
            'orden': representation['orden'],
            'created_at': representation['created_at'],
        }

        return camel_case_representation


class CategoriaAtributoCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para crear y actualizar relaciones categoría-atributo.
    No incluye campos de solo lectura.
    Acepta tanto camelCase (JSON del frontend) como snake_case.
    """

    # Hacer que todos los campos sean opcionales para permitir actualizaciones parciales
    categoria_id = serializers.IntegerField(required=False)
    atributo_id = serializers.IntegerField(required=False)
    obligatorio = serializers.BooleanField(required=False, default=False)
    orden = serializers.IntegerField(required=False, default=0)

    class Meta:
        model = CategoriaAtributo
        fields = [
            'categoria_id',
            'atributo_id',
            'obligatorio',
            'orden',
        ]

    def to_internal_value(self, data):
        """
        Convierte camelCase a snake_case para compatibilidad con el frontend.
        """
        # Mapeo de camelCase a snake_case
        camel_to_snake = {
            'categoriaId': 'categoria_id',
            'atributoId': 'atributo_id',
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
            if 'categoria_id' not in data:
                raise serializers.ValidationError({"categoria_id": "La categoría es requerida."})
            if 'atributo_id' not in data:
                raise serializers.ValidationError({"atributo_id": "El atributo es requerido."})

        # Validar categoria_id si fue proporcionado
        if 'categoria_id' in data:
            categoria_id = data['categoria_id']
            if not Category.objects.filter(pk=categoria_id).exists():
                raise serializers.ValidationError({"categoria_id": "La categoría especificada no existe."})

        # Validar atributo_id si fue proporcionado
        if 'atributo_id' in data:
            atributo_id = data['atributo_id']
            if not Attribute.objects.filter(pk=atributo_id).exists():
                raise serializers.ValidationError({"atributo_id": "El atributo especificado no existe."})

        # Validar unicidad de la combinación categoria-atributo
        if self.instance is None:  # Creación
            categoria_id = data.get('categoria_id')
            atributo_id = data.get('atributo_id')
            if categoria_id and atributo_id:
                if CategoriaAtributo.objects.filter(categoria_id=categoria_id, atributo_id=atributo_id).exists():
                    raise serializers.ValidationError({
                        "detail": "Ya existe una relación entre esta categoría y este atributo."
                    })
        else:  # Actualización
            categoria_id = data.get('categoria_id', self.instance.categoria_id)
            atributo_id = data.get('atributo_id', self.instance.atributo_id)
            if CategoriaAtributo.objects.filter(
                categoria_id=categoria_id,
                atributo_id=atributo_id
            ).exclude(pk=self.instance.pk).exists():
                raise serializers.ValidationError({
                    "detail": "Ya existe una relación entre esta categoría y este atributo."
                })

        return data

    def create(self, validated_data):
        """
        Crea una nueva relación categoría-atributo.
        """
        # Extraer IDs y obtener los objetos
        categoria_id = validated_data.pop('categoria_id')
        atributo_id = validated_data.pop('atributo_id')

        categoria = Category.objects.get(pk=categoria_id)
        atributo = Attribute.objects.get(pk=atributo_id)

        # Crear la relación
        categoria_atributo = CategoriaAtributo.objects.create(
            categoria=categoria,
            atributo=atributo,
            **validated_data
        )
        return categoria_atributo

    def update(self, instance, validated_data):
        """
        Actualiza una relación categoría-atributo existente.
        """
        # Si se proporciona categoria_id, obtener el objeto Category
        if 'categoria_id' in validated_data:
            categoria_id = validated_data.pop('categoria_id')
            instance.categoria = Category.objects.get(pk=categoria_id)

        # Si se proporciona atributo_id, obtener el objeto Attribute
        if 'atributo_id' in validated_data:
            atributo_id = validated_data.pop('atributo_id')
            instance.atributo = Attribute.objects.get(pk=atributo_id)

        # Actualizar los demás campos
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class CategoriaAtributoBulkCreateSerializer(serializers.Serializer):
    """
    Serializer para creación en masa de relaciones categoría-atributo.
    Acepta una lista de relaciones y las crea todas juntas.
    """
    relaciones = CategoriaAtributoCreateUpdateSerializer(many=True)

    def create(self, validated_data):
        """
        Crea múltiples relaciones categoría-atributo en una sola operación.
        """
        relaciones_data = validated_data.get('relaciones', [])
        created_relaciones = []
        errors = []

        for relacion_data in relaciones_data:
            try:
                # Extraer IDs y obtener los objetos
                categoria_id = relacion_data.pop('categoria_id')
                atributo_id = relacion_data.pop('atributo_id')

                categoria = Category.objects.get(pk=categoria_id)
                atributo = Attribute.objects.get(pk=atributo_id)

                # Verificar que no exista ya
                if CategoriaAtributo.objects.filter(categoria=categoria, atributo=atributo).exists():
                    errors.append({
                        'data': {'categoria_id': categoria_id, 'atributo_id': atributo_id},
                        'error': 'La relación ya existe'
                    })
                    continue

                # Crear la relación
                relacion = CategoriaAtributo.objects.create(
                    categoria=categoria,
                    atributo=atributo,
                    **relacion_data
                )
                created_relaciones.append(relacion)
            except Exception as e:
                errors.append({
                    'data': relacion_data,
                    'error': str(e)
                })

        return {
            'created': created_relaciones,
            'errors': errors
        }
