from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination

from django.shortcuts import get_object_or_404
from django.db import DatabaseError
from django.db.models import Q
from datetime import datetime

from atributos.models import Attribute
from .serializers import AttributeSerializer, AttributeCreateUpdateSerializer


# Listar atributos con filtros y paginación
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_attributes(request):
    try:
        # 1) Obtener atributos (NO eliminados por defecto gracias al manager)
        attributes = Attribute.objects.all()

        # 2) FILTROS

        # --- Search (name + descripcion + slug) ---
        search_query = request.query_params.get('search', None)
        if search_query:
            attributes = attributes.filter(
                Q(name__icontains=search_query) |
                Q(descripcion__icontains=search_query) |
                Q(slug__icontains=search_query)
            )

        # --- Filtro es_variable ---
        variable_filter = request.query_params.get('variable', None)  # '1'/'0'
        if variable_filter is not None and variable_filter != '':
            is_variable_bool = variable_filter == '1'
            attributes = attributes.filter(es_variable=is_variable_bool)

        # --- Filtro es_filtrable ---
        filtrable_filter = request.query_params.get('filtrable', None)  # '1'/'0'
        if filtrable_filter is not None and filtrable_filter != '':
            is_filtrable_bool = filtrable_filter == '1'
            attributes = attributes.filter(es_filtrable=is_filtrable_bool)

        # --- Filtro tipo_input ---
        tipo_input = request.query_params.get('tipo_input', None)
        if tipo_input:
            attributes = attributes.filter(tipo_input=tipo_input)

        # --- Filtro tipo_dato ---
        tipo_dato = request.query_params.get('tipo_dato', None)
        if tipo_dato:
            attributes = attributes.filter(tipo_dato=tipo_dato)

        # --- Date range (created_at) ---
        start_date_str = request.query_params.get('start_date', None)
        end_date_str = request.query_params.get('end_date', None)

        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                attributes = attributes.filter(created_at__gte=start_date)
            except ValueError:
                return Response(
                    {"error": "El formato de la fecha de inicio debe ser YYYY-MM-DD."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                from datetime import datetime as dt
                end_date_inclusive = dt.combine(end_date, dt.max.time())
                attributes = attributes.filter(created_at__lte=end_date_inclusive)
            except ValueError:
                return Response(
                    {"error": "El formato de la fecha de fin debe ser YYYY-MM-DD."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # 3) Total después de filtros
        total_count = attributes.count()

        # 4) Ordenamiento
        # Por defecto: primero orden asc, luego nombre asc, luego id desc para estabilidad
        ordering = request.query_params.get('ordering', None)
        allowed_ordering = {
            "id": "id",
            "-id": "-id",
            "name": "name",
            "-name": "-name",
            "orden": "orden",
            "-orden": "-orden",
            "created_at": "created_at",
            "-created_at": "-created_at",
        }

        if ordering in allowed_ordering:
            attributes = attributes.order_by(allowed_ordering[ordering])
        else:
            attributes = attributes.order_by('orden', 'name', '-id')

        # 5) Paginación
        page_size_param = request.query_params.get('page_size', 10)
        try:
            page_size_int = int(page_size_param)
        except (ValueError, TypeError):
            page_size_int = 10

        paginator = PageNumberPagination()
        paginator.page_size = page_size_int
        paginated_attributes = paginator.paginate_queryset(attributes, request)

        # 6) Serializar
        serializer = AttributeSerializer(paginated_attributes, many=True)

        # (Opcional) si quieres devolver también total_count aparte
        response = paginator.get_paginated_response(serializer.data)
        # response.data['total_count'] = total_count  # descomenta si lo quieres explícito

        return response

    except Exception as e:
        print(f"Error en list_attributes: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response(
            {"error": f"Error fetching attributes: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Obtener un atributo por ID
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_attribute(request, pk):
    try:
        attribute = get_object_or_404(Attribute, pk=pk)
        serializer = AttributeSerializer(attribute)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"error": f"Error retrieving attribute: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Crear un atributo
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_attribute(request):
    try:
        serializer = AttributeCreateUpdateSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()

            attribute = Attribute.objects.get(pk=serializer.instance.pk)
            response_serializer = AttributeSerializer(attribute)

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


# Actualizar un atributo
@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_attribute(request, pk):
    try:
        attribute = get_object_or_404(Attribute, pk=pk)

        # Si está eliminado, no permitir actualización
        if attribute.deleted_at:
            return Response(
                {"error": "No se puede actualizar un atributo eliminado."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = AttributeCreateUpdateSerializer(
            attribute,
            data=request.data,
            partial=request.method == 'PATCH'
        )

        if serializer.is_valid():
            serializer.save()

            response_serializer = AttributeSerializer(attribute)
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
            {"error": f"Database error while updating attribute: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        return Response(
            {"error": f"Unexpected error: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Eliminar un atributo (soft delete)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_attribute(request, pk):
    try:
        attribute = get_object_or_404(Attribute, pk=pk)

        if attribute.deleted_at:
            return Response(
                {"error": "Este atributo ya está eliminado."},
                status=status.HTTP_400_BAD_REQUEST
            )

        attribute.delete()

        return Response(
            {"message": "Attribute deleted successfully (soft delete)"},
            status=status.HTTP_200_OK
        )

    except Exception as e:
        return Response(
            {"error": f"Error deleting attribute: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Restaurar un atributo eliminado
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def restore_attribute(request, pk):
    try:
        attribute = get_object_or_404(Attribute.all_objects, pk=pk)

        if not attribute.deleted_at:
            return Response(
                {"error": "Este atributo no está eliminado."},
                status=status.HTTP_400_BAD_REQUEST
            )

        attribute.restore()

        serializer = AttributeSerializer(attribute)
        return Response(
            {
                "message": "Attribute restored successfully",
                "attribute": serializer.data
            },
            status=status.HTTP_200_OK
        )

    except Exception as e:
        return Response(
            {"error": f"Error restoring attribute: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
