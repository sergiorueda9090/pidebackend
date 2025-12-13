from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.db import DatabaseError
from category.models import Category
from .serializers import CategorySerializer, CategoryCreateUpdateSerializer

from django.db.models import Q
from datetime import datetime


# Listar categorías con filtros y paginación
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_categories(request):
    try:
        # 1. Obtener todas las categorías (sin eliminadas por defecto)
        categories = Category.objects.all()

        # 2. Aplicar FILTROS

        # --- Filtro de Buscador (Search) ---
        search_query = request.query_params.get('search', None)
        if search_query:
            categories = categories.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(seo_keywords__icontains=search_query)
            )

        # --- Filtro por Estado (Status/is_active) ---
        status_filter = request.query_params.get('status', None)
        if status_filter is not None and status_filter != '':
            is_active_bool = status_filter == '1'
            categories = categories.filter(is_active=is_active_bool)

        # --- Filtros de Fecha de Inicio y Fecha de Fin (Date Range) ---
        start_date_str = request.query_params.get('start_date', None)
        end_date_str = request.query_params.get('end_date', None)

        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                categories = categories.filter(created_at__gte=start_date)
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
                categories = categories.filter(created_at__lte=end_date_inclusive)
            except ValueError:
                return Response(
                    {"error": "El formato de la fecha de fin debe ser YYYY-MM-DD."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # 3. Contar total después de filtros
        total_count = categories.count()

        # 4. Ordenar
        categories = categories.order_by('-id')

        # 5. Aplicar paginación
        page_size_param = request.query_params.get('page_size', 10)

        try:
            page_size_int = int(page_size_param)
        except (ValueError, TypeError):
            page_size_int = 10

        paginator = PageNumberPagination()
        paginator.page_size = page_size_int
        paginated_categories = paginator.paginate_queryset(categories, request)

        # 6. Serializar
        serializer = CategorySerializer(paginated_categories, many=True)

        return paginator.get_paginated_response(serializer.data)

    except Exception as e:
        print(f"Error en list_categories: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response(
            {"error": f"Error fetching categories: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Obtener una categoría por ID
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_category(request, pk):
    try:
        category = get_object_or_404(Category, pk=pk)
        serializer = CategorySerializer(category)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"error": f"Error retrieving category: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Crear una categoría
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_category(request):
    try:
        serializer = CategoryCreateUpdateSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()

            # Retornar la categoría creada con el serializer completo
            category = Category.objects.get(pk=serializer.instance.pk)
            response_serializer = CategorySerializer(category)

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


# Actualizar una categoría
@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_category(request, pk):
    try:
        category = get_object_or_404(Category, pk=pk)

        # Si la categoría está eliminada, no permitir actualización
        if category.deleted_at:
            return Response(
                {"error": "No se puede actualizar una categoría eliminada."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = CategoryCreateUpdateSerializer(
            category,
            data=request.data,
            partial=request.method == 'PATCH'
        )

        if serializer.is_valid():
            serializer.save()

            # Retornar la categoría actualizada
            response_serializer = CategorySerializer(category)
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
            {"error": f"Database error while updating category: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        return Response(
            {"error": f"Unexpected error: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Eliminar una categoría (soft delete)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_category(request, pk):
    try:
        category = get_object_or_404(Category, pk=pk)

        # Verificar si ya está eliminada
        if category.deleted_at:
            return Response(
                {"error": "Esta categoría ya está eliminada."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Soft delete
        category.delete()

        return Response(
            {"message": "Category deleted successfully (soft delete)"},
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {"error": f"Error deleting category: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Restaurar una categoría eliminada
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def restore_category(request, pk):
    try:
        # Buscar en todas las categorías (incluyendo eliminadas)
        category = get_object_or_404(Category.all_objects, pk=pk)

        # Verificar si está eliminada
        if not category.deleted_at:
            return Response(
                {"error": "Esta categoría no está eliminada."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Restaurar
        category.restore()

        serializer = CategorySerializer(category)
        return Response(
            {
                "message": "Category restored successfully",
                "category": serializer.data
            },
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {"error": f"Error restoring category: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
