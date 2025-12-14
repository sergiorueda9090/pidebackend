from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.db import DatabaseError
from subcategories.models import Subcategory
from .serializers import SubcategorySerializer, SubcategoryCreateUpdateSerializer

from django.db.models import Q
from datetime import datetime


# Listar subcategorías con filtros y paginación
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_subcategories(request):
    try:
        # 1. Obtener todas las subcategorías (sin eliminadas por defecto)
        subcategories = Subcategory.objects.all()

        # 2. Aplicar FILTROS

        # --- Filtro de Buscador (Search) ---
        search_query = request.query_params.get('search', None)
        if search_query:
            subcategories = subcategories.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(seo_keywords__icontains=search_query) |
                Q(category__name__icontains=search_query)
            )

        # --- Filtro por Estado (Status/is_active) ---
        status_filter = request.query_params.get('status', None)
        if status_filter is not None and status_filter != '':
            is_active_bool = status_filter == '1'
            subcategories = subcategories.filter(is_active=is_active_bool)

        # --- Filtro por Categoría ---
        category_filter = request.query_params.get('category', None)
        if category_filter:
            subcategories = subcategories.filter(category_id=category_filter)

        # --- Filtros de Fecha de Inicio y Fecha de Fin (Date Range) ---
        start_date_str = request.query_params.get('start_date', None)
        end_date_str = request.query_params.get('end_date', None)

        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                subcategories = subcategories.filter(created_at__gte=start_date)
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
                subcategories = subcategories.filter(created_at__lte=end_date_inclusive)
            except ValueError:
                return Response(
                    {"error": "El formato de la fecha de fin debe ser YYYY-MM-DD."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # 3. Contar total después de filtros
        total_count = subcategories.count()

        # 4. Ordenar
        subcategories = subcategories.order_by('category', 'order', 'name')

        # 5. Aplicar paginación
        page_size_param = request.query_params.get('page_size', 10)

        try:
            page_size_int = int(page_size_param)
        except (ValueError, TypeError):
            page_size_int = 10

        paginator = PageNumberPagination()
        paginator.page_size = page_size_int
        paginated_subcategories = paginator.paginate_queryset(subcategories, request)

        # 6. Serializar
        serializer = SubcategorySerializer(paginated_subcategories, many=True)

        return paginator.get_paginated_response(serializer.data)

    except Exception as e:
        print(f"Error en list_subcategories: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response(
            {"error": f"Error fetching subcategories: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Obtener una subcategoría por ID
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_subcategory(request, pk):
    try:
        subcategory = get_object_or_404(Subcategory, pk=pk)
        serializer = SubcategorySerializer(subcategory)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"error": f"Error retrieving subcategory: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Crear una subcategoría
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_subcategory(request):
    try:
        serializer = SubcategoryCreateUpdateSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()

            # Retornar la subcategoría creada con el serializer completo
            subcategory = Subcategory.objects.get(pk=serializer.instance.pk)
            response_serializer = SubcategorySerializer(subcategory)

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


# Crear múltiples subcategorías (bulk create)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_create_subcategories(request):
    try:
        # El frontend envía un array directamente
        subcategories_data = request.data

        # Validar que sea una lista
        if not isinstance(subcategories_data, list):
            return Response(
                {"error": "Se esperaba una lista de subcategorías."},
                status=status.HTTP_400_BAD_REQUEST
            )

        created_count = 0
        error_count = 0
        errors_detail = []

        # Crear cada subcategoría
        for index, subcategory_data in enumerate(subcategories_data):
            serializer = SubcategoryCreateUpdateSerializer(data=subcategory_data)

            if serializer.is_valid():
                try:
                    serializer.save()
                    created_count += 1
                except Exception as e:
                    error_count += 1
                    errors_detail.append({
                        'index': index,
                        'data': subcategory_data,
                        'error': str(e)
                    })
            else:
                error_count += 1
                errors_detail.append({
                    'index': index,
                    'data': subcategory_data,
                    'errors': serializer.errors
                })

        # Preparar respuesta
        response_data = {
            'success_count': created_count,
            'error_count': error_count,
            'message': f'Se crearon {created_count} subcategorías correctamente.'
        }

        if errors_detail:
            response_data['errors'] = errors_detail

        # Determinar el código de estado
        if created_count > 0 and error_count == 0:
            return Response(response_data, status=status.HTTP_201_CREATED)
        elif created_count > 0 and error_count > 0:
            return Response(response_data, status=status.HTTP_207_MULTI_STATUS)
        else:
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response(
            {"error": f"Unexpected error: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Actualizar una subcategoría
@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_subcategory(request, pk):
    try:
        subcategory = get_object_or_404(Subcategory, pk=pk)

        # Si la subcategoría está eliminada, no permitir actualización
        if subcategory.deleted_at:
            return Response(
                {"error": "No se puede actualizar una subcategoría eliminada."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = SubcategoryCreateUpdateSerializer(
            subcategory,
            data=request.data,
            partial=request.method == 'PATCH'
        )

        if serializer.is_valid():
            serializer.save()

            # Retornar la subcategoría actualizada
            response_serializer = SubcategorySerializer(subcategory)
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
            {"error": f"Database error while updating subcategory: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        return Response(
            {"error": f"Unexpected error: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Eliminar una subcategoría (soft delete)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_subcategory(request, pk):
    try:
        subcategory = get_object_or_404(Subcategory, pk=pk)

        # Verificar si ya está eliminada
        if subcategory.deleted_at:
            return Response(
                {"error": "Esta subcategoría ya está eliminada."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Soft delete
        subcategory.delete()

        return Response(
            {"message": "Subcategory deleted successfully (soft delete)"},
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {"error": f"Error deleting subcategory: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Restaurar una subcategoría eliminada
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def restore_subcategory(request, pk):
    try:
        # Buscar en todas las subcategorías (incluyendo eliminadas)
        subcategory = get_object_or_404(Subcategory.all_objects, pk=pk)

        # Verificar si está eliminada
        if not subcategory.deleted_at:
            return Response(
                {"error": "Esta subcategoría no está eliminada."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Restaurar
        subcategory.restore()

        serializer = SubcategorySerializer(subcategory)
        return Response(
            {
                "message": "Subcategory restored successfully",
                "subcategory": serializer.data
            },
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {"error": f"Error restoring subcategory: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
