from rest_framework import serializers
from atributos.models import Attribute


class AttributeSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Attribute.
    Maneja la conversión entre objetos Attribute y JSON.
    """

    # Campo calculado para mostrar si está eliminado
    is_deleted = serializers.BooleanField(read_only=True)

    # Campo calculado para el conteo de valores
    values_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Attribute
        fields = [
            'id',
            'name',
            'slug',
            'tipo_input',
            'tipo_dato',
            'es_variable',
            'es_filtrable',
            'orden',
            'descripcion',
            'is_deleted',
            'values_count',
            'created_at',
            'updated_at',
            'deleted_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'deleted_at', 'is_deleted', 'values_count']

    def to_representation(self, instance):
        """
        Personaliza la representación JSON del atributo.
        Convierte nombres de campos snake_case a camelCase para el frontend.
        """
        representation = super().to_representation(instance)

        # Convertir nombres a camelCase
        camel_case_representation = {
            'id': representation['id'],
            'name': representation['name'],
            'slug': representation['slug'],
            'tipoInput': representation['tipo_input'],
            'tipoDato': representation['tipo_dato'],
            'esVariable': representation['es_variable'],
            'esFiltrable': representation['es_filtrable'],
            'orden': representation['orden'],
            'descripcion': representation['descripcion'],
            'isDeleted': representation['is_deleted'],
            'valuesCount': representation['values_count'],
            'created_at': representation['created_at'],
            'updated_at': representation['updated_at'],
            'deleted_at': representation['deleted_at'],
        }

        return camel_case_representation


class AttributeCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para crear y actualizar atributos.
    No incluye campos de solo lectura.
    Acepta tanto camelCase (JSON del frontend) como snake_case.
    """

    # Hacer que todos los campos sean opcionales para permitir actualizaciones parciales
    name = serializers.CharField(max_length=200, required=False)
    slug = serializers.SlugField(max_length=250, required=False)
    tipo_input = serializers.ChoiceField(
        choices=Attribute.INPUT_TYPE_CHOICES,
        required=False
    )
    tipo_dato = serializers.ChoiceField(
        choices=Attribute.DATA_TYPE_CHOICES,
        required=False
    )
    es_variable = serializers.BooleanField(required=False)
    es_filtrable = serializers.BooleanField(required=False)
    orden = serializers.IntegerField(required=False)
    descripcion = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = Attribute
        fields = [
            'name',
            'slug',
            'tipo_input',
            'tipo_dato',
            'es_variable',
            'es_filtrable',
            'orden',
            'descripcion',
        ]

    def to_internal_value(self, data):
        """
        Convierte camelCase a snake_case para compatibilidad con el frontend.
        """
        # Mapeo de camelCase a snake_case
        camel_to_snake = {
            'tipoInput': 'tipo_input',
            'tipoDato': 'tipo_dato',
            'esVariable': 'es_variable',
            'esFiltrable': 'es_filtrable',
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
            raise serializers.ValidationError({"name": "El nombre del atributo es requerido."})

        # Validar el nombre si fue proporcionado
        if 'name' in data:
            name = data['name']
            if not name or not name.strip():
                raise serializers.ValidationError({"name": "El nombre del atributo no puede estar vacío."})

            # Validar unicidad
            if self.instance is None:  # Creación
                if Attribute.objects.filter(name__iexact=name).exists():
                    raise serializers.ValidationError({"name": "Ya existe un atributo con este nombre."})
            else:  # Actualización
                if Attribute.objects.filter(name__iexact=name).exclude(pk=self.instance.pk).exists():
                    raise serializers.ValidationError({"name": "Ya existe un atributo con este nombre."})

            # Limpiar el nombre
            data['name'] = name.strip()

        # Validar tipo_input si fue proporcionado
        if 'tipo_input' in data:
            valid_types = [choice[0] for choice in Attribute.INPUT_TYPE_CHOICES]
            if data['tipo_input'] not in valid_types:
                raise serializers.ValidationError({
                    "tipo_input": f"Tipo de input inválido. Opciones válidas: {', '.join(valid_types)}"
                })

        # Validar tipo_dato si fue proporcionado
        if 'tipo_dato' in data:
            valid_types = [choice[0] for choice in Attribute.DATA_TYPE_CHOICES]
            if data['tipo_dato'] not in valid_types:
                raise serializers.ValidationError({
                    "tipo_dato": f"Tipo de dato inválido. Opciones válidas: {', '.join(valid_types)}"
                })

        # Validar orden si fue proporcionado
        if 'orden' in data:
            if data['orden'] < 0:
                raise serializers.ValidationError({"orden": "El orden no puede ser negativo."})

        return data
