from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.db import DatabaseError
from brands.models import Brand
from .serializers import BrandSerializer, BrandCreateUpdateSerializer

from django.db.models import Q
from datetime import datetime


# Listar marcas con filtros y paginación
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_brands(request):
    try:
        # 1. Obtener todas las marcas (sin eliminadas por defecto)
        brands = Brand.objects.all()

        # 2. Aplicar FILTROS

        # --- Filtro de Buscador (Search) ---
        search_query = request.query_params.get('search', None)
        if search_query:
            brands = brands.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(website__icontains=search_query)
            )

        # --- Filtro por Estado (Status/is_active) ---
        status_filter = request.query_params.get('status', None)
        if status_filter is not None and status_filter != '':
            is_active_bool = status_filter == '1'
            brands = brands.filter(is_active=is_active_bool)

        # --- Filtro por Destacadas (is_featured) ---
        featured_filter = request.query_params.get('featured', None)
        if featured_filter is not None and featured_filter != '':
            is_featured_bool = featured_filter == '1'
            brands = brands.filter(is_featured=is_featured_bool)

        # --- Filtros de Fecha de Inicio y Fecha de Fin (Date Range) ---
        start_date_str = request.query_params.get('start_date', None)
        end_date_str = request.query_params.get('end_date', None)

        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                brands = brands.filter(created_at__gte=start_date)
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
                brands = brands.filter(created_at__lte=end_date_inclusive)
            except ValueError:
                return Response(
                    {"error": "El formato de la fecha de fin debe ser YYYY-MM-DD."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # 3. Contar total después de filtros
        total_count = brands.count()

        # 4. Ordenar (destacadas primero, luego por ID descendente)
        brands = brands.order_by('-is_featured', '-id')

        # 5. Aplicar paginación
        page_size_param = request.query_params.get('page_size', 10)

        try:
            page_size_int = int(page_size_param)
        except (ValueError, TypeError):
            page_size_int = 10

        paginator = PageNumberPagination()
        paginator.page_size = page_size_int
        paginated_brands = paginator.paginate_queryset(brands, request)

        # 6. Serializar
        serializer = BrandSerializer(paginated_brands, many=True)

        return paginator.get_paginated_response(serializer.data)

    except Exception as e:
        print(f"Error en list_brands: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response(
            {"error": f"Error fetching brands: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Obtener una marca por ID
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_brand(request, pk):
    try:
        brand = get_object_or_404(Brand, pk=pk)
        serializer = BrandSerializer(brand)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"error": f"Error retrieving brand: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Crear una marca
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_brand(request):
    try:
        serializer = BrandCreateUpdateSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()

            # Retornar la marca creada con el serializer completo
            brand = Brand.objects.get(pk=serializer.instance.pk)
            response_serializer = BrandSerializer(brand)

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


# Actualizar una marca
@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_brand(request, pk):
    try:
        brand = get_object_or_404(Brand, pk=pk)

        # Si la marca está eliminada, no permitir actualización
        if brand.deleted_at:
            return Response(
                {"error": "No se puede actualizar una marca eliminada."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = BrandCreateUpdateSerializer(
            brand,
            data=request.data,
            partial=request.method == 'PATCH'
        )

        if serializer.is_valid():
            serializer.save()

            # Retornar la marca actualizada
            response_serializer = BrandSerializer(brand)
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
            {"error": f"Database error while updating brand: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        return Response(
            {"error": f"Unexpected error: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Eliminar una marca (soft delete)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_brand(request, pk):
    try:
        brand = get_object_or_404(Brand, pk=pk)

        # Verificar si ya está eliminada
        if brand.deleted_at:
            return Response(
                {"error": "Esta marca ya está eliminada."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Soft delete
        brand.delete()

        return Response(
            {"message": "Brand deleted successfully (soft delete)"},
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {"error": f"Error deleting brand: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Restaurar una marca eliminada
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def restore_brand(request, pk):
    try:
        # Buscar en todas las marcas (incluyendo eliminadas)
        brand = get_object_or_404(Brand.all_objects, pk=pk)

        # Verificar si está eliminada
        if not brand.deleted_at:
            return Response(
                {"error": "Esta marca no está eliminada."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Restaurar
        brand.restore()

        serializer = BrandSerializer(brand)
        return Response(
            {
                "message": "Brand restored successfully",
                "brand": serializer.data
            },
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {"error": f"Error restoring brand: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
