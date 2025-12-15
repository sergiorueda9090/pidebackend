from rest_framework import serializers
from atributosvalores.models import AttributeValue
from atributos.models import Attribute


class AttributeValueSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo AttributeValue.
    Maneja la conversión entre objetos AttributeValue y JSON.
    """

    # Campos calculados
    is_deleted = serializers.BooleanField(read_only=True)
    products_count = serializers.IntegerField(read_only=True)

    # Información del atributo padre
    atributo_nombre = serializers.CharField(source='atributo.name', read_only=True)

    class Meta:
        model = AttributeValue
        fields = [
            'id',
            'atributo',
            'atributo_nombre',
            'valor',
            'valor_extra',
            'orden',
            'activo',
            'is_deleted',
            'products_count',
            'created_at',
            'updated_at',
            'deleted_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'deleted_at', 'is_deleted', 'products_count', 'atributo_nombre']

    def to_representation(self, instance):
        """
        Personaliza la representación JSON del valor de atributo.
        Convierte nombres de campos snake_case a camelCase para el frontend.
        """
        representation = super().to_representation(instance)

        # Convertir nombres a camelCase
        camel_case_representation = {
            'id': representation['id'],
            'atributoId': representation['atributo'],
            'atributoNombre': representation['atributo_nombre'],
            'valor': representation['valor'],
            'valorExtra': representation['valor_extra'],
            'orden': representation['orden'],
            'activo': representation['activo'],
            'isDeleted': representation['is_deleted'],
            'productsCount': representation['products_count'],
            'createdAt': representation['created_at'],
            'updatedAt': representation['updated_at'],
            'deletedAt': representation['deleted_at'],
        }

        return camel_case_representation


class AttributeValueCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para crear y actualizar valores de atributos.
    No incluye campos de solo lectura.
    Acepta tanto camelCase (JSON del frontend) como snake_case.
    """

    # Hacer que todos los campos sean opcionales para permitir actualizaciones parciales
    atributo_id = serializers.IntegerField(required=False)
    valor = serializers.CharField(max_length=100, required=False)
    valor_extra = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)
    orden = serializers.IntegerField(required=False)
    activo = serializers.BooleanField(required=False)

    class Meta:
        model = AttributeValue
        fields = [
            'atributo_id',
            'valor',
            'valor_extra',
            'orden',
            'activo',
        ]

    def to_internal_value(self, data):
        """
        Convierte camelCase a snake_case para compatibilidad con el frontend.
        Si viene FormData, ya está en snake_case, si viene JSON está en camelCase.
        """
        # Mapeo de camelCase a snake_case
        camel_to_snake = {
            'atributoId': 'atributo_id',
            'valorExtra': 'valor_extra',
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
            if 'valor' not in data:
                raise serializers.ValidationError({"valor": "El valor es requerido."})
            if 'atributo_id' not in data:
                raise serializers.ValidationError({"atributo_id": "El atributo es requerido."})

        # Validar el valor si fue proporcionado
        if 'valor' in data:
            valor = data['valor']
            if not valor or not valor.strip():
                raise serializers.ValidationError({"valor": "El valor no puede estar vacío."})

            # Limpiar el valor
            data['valor'] = valor.strip()

        # Validar atributo_id si fue proporcionado
        if 'atributo_id' in data:
            atributo_id = data['atributo_id']
            if not Attribute.objects.filter(pk=atributo_id).exists():
                raise serializers.ValidationError({"atributo_id": "El atributo especificado no existe."})

        # Validar orden si fue proporcionado
        if 'orden' in data:
            if data['orden'] < 0:
                raise serializers.ValidationError({"orden": "El orden no puede ser negativo."})

        return data

    def create(self, validated_data):
        """
        Crea un nuevo valor de atributo.
        """
        # Extraer atributo_id y obtener el objeto Attribute
        atributo_id = validated_data.pop('atributo_id')
        atributo = Attribute.objects.get(pk=atributo_id)

        # Crear el valor de atributo con el atributo asociado
        attribute_value = AttributeValue.objects.create(atributo=atributo, **validated_data)
        return attribute_value

    def update(self, instance, validated_data):
        """
        Actualiza un valor de atributo existente.
        """
        # Si se proporciona atributo_id, obtener el objeto Attribute
        if 'atributo_id' in validated_data:
            atributo_id = validated_data.pop('atributo_id')
            instance.atributo = Attribute.objects.get(pk=atributo_id)

        # Actualizar los demás campos
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance
