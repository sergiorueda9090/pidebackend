from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination

from django.shortcuts import get_object_or_404
from django.db import DatabaseError
from django.db.models import Q
from datetime import datetime

from atributosvalores.models import AttributeValue
from atributos.models import Attribute
from .serializers import AttributeValueSerializer, AttributeValueCreateUpdateSerializer


# Listar valores de atributos con filtros y paginación
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_attribute_values(request):
    try:
        # 1. Obtener todos los valores de atributos (sin eliminados por defecto)
        attribute_values = AttributeValue.objects.all()

        # 2. Aplicar FILTROS

        # --- Filtro de Buscador (Search) ---
        search_query = request.query_params.get('search', None)
        if search_query:
            attribute_values = attribute_values.filter(
                Q(valor__icontains=search_query) |
                Q(valor_extra__icontains=search_query) |
                Q(atributo__name__icontains=search_query)
            )

        # --- Filtro por Atributo ---
        atributo_filter = request.query_params.get('atributo', None)
        if atributo_filter:
            attribute_values = attribute_values.filter(atributo_id=atributo_filter)

        # --- Filtro por Estado Activo ---
        activo_filter = request.query_params.get('activo', None)
        if activo_filter is not None and activo_filter != '':
            activo_bool = activo_filter.lower() == 'true' or activo_filter == '1'
            attribute_values = attribute_values.filter(activo=activo_bool)

        # --- Filtros de Fecha de Inicio y Fecha de Fin (Date Range) ---
        start_date_str = request.query_params.get('start_date', None)
        end_date_str = request.query_params.get('end_date', None)

        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                attribute_values = attribute_values.filter(created_at__gte=start_date)
            except ValueError:
                return Response(
                    {"error": "El formato de la fecha de inicio debe ser YYYY-MM-DD."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                from datetime import datetime, timedelta
                end_date_inclusive = datetime.combine(end_date, datetime.max.time())
                attribute_values = attribute_values.filter(created_at__lte=end_date_inclusive)
            except ValueError:
                return Response(
                    {"error": "El formato de la fecha de fin debe ser YYYY-MM-DD."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # 3. Contar total después de filtros
        total_count = attribute_values.count()

        # 4. Ordenar
        attribute_values = attribute_values.order_by('atributo', 'orden', 'valor')

        # 5. Aplicar paginación
        page_size_param = request.query_params.get('page_size', 10)

        try:
            page_size_int = int(page_size_param)
        except (ValueError, TypeError):
            page_size_int = 10

        paginator = PageNumberPagination()
        paginator.page_size = page_size_int
        paginated_values = paginator.paginate_queryset(attribute_values, request)

        # 6. Serializar
        serializer = AttributeValueSerializer(paginated_values, many=True)

        return paginator.get_paginated_response(serializer.data)

    except Exception as e:
        print(f"Error en list_attribute_values: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response(
            {"error": f"Error fetching attribute values: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Obtener un valor de atributo por ID
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_attribute_value(request, pk):
    try:
        attribute_value = get_object_or_404(AttributeValue, pk=pk)
        serializer = AttributeValueSerializer(attribute_value)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"error": f"Error retrieving attribute value: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Crear un valor de atributo
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_attribute_value(request):
    try:
        serializer = AttributeValueCreateUpdateSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()

            # Retornar el valor creado con el serializer completo
            attribute_value = AttributeValue.objects.get(pk=serializer.instance.pk)
            response_serializer = AttributeValueSerializer(attribute_value)

            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    except DatabaseError as e:
        return Response(
            {"error": f"Database error: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        return Response(
            {"error": f"Unexpected error: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Actualizar un valor de atributo
@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_attribute_value(request, pk):
    try:
        attribute_value = get_object_or_404(AttributeValue, pk=pk)

        # Si está eliminado, no permitir actualización
        if attribute_value.deleted_at:
            return Response(
                {"error": "No se puede actualizar un valor eliminado."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = AttributeValueCreateUpdateSerializer(
            attribute_value,
            data=request.data,
            partial=request.method == 'PATCH'
        )

        if serializer.is_valid():
            serializer.save()

            response_serializer = AttributeValueSerializer(attribute_value)
            return Response(
                response_serializer.data,
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    except DatabaseError as e:
        return Response(
            {"error": f"Database error while updating attribute value: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        return Response(
            {"error": f"Unexpected error: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Eliminar un valor de atributo (soft delete)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_attribute_value(request, pk):
    try:
        attribute_value = get_object_or_404(AttributeValue, pk=pk)

        if attribute_value.deleted_at:
            return Response(
                {"error": "Este valor ya está eliminado."},
                status=status.HTTP_400_BAD_REQUEST
            )

        attribute_value.delete()

        return Response(
            {"message": "Attribute value deleted successfully (soft delete)"},
            status=status.HTTP_204_NO_CONTENT
        )

    except Exception as e:
        return Response(
            {"error": f"Error deleting attribute value: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Restaurar un valor de atributo eliminado
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def restore_attribute_value(request, pk):
    try:
        attribute_value = get_object_or_404(AttributeValue.all_objects, pk=pk)

        if not attribute_value.deleted_at:
            return Response(
                {"error": "Este valor no está eliminado."},
                status=status.HTTP_400_BAD_REQUEST
            )

        attribute_value.restore()

        serializer = AttributeValueSerializer(attribute_value)
        return Response(
            {
                "message": "Attribute value restored successfully",
                "attributeValue": serializer.data
            },
            status=status.HTTP_200_OK
        )

    except Exception as e:
        return Response(
            {"error": f"Error restoring attribute value: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
