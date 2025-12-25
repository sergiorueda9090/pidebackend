from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.db import DatabaseError
from categoriaatributos.models import CategoriaAtributo
from .serializers import (
    CategoriaAtributoSerializer,
    CategoriaAtributoCreateUpdateSerializer,
    CategoriaAtributoBulkCreateSerializer
)

from django.db.models import Q
from datetime import datetime


# Listar relaciones categoría-atributo con filtros y paginación
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_categoria_atributos(request):
    try:
        # 1. Obtener todas las relaciones
        relaciones = CategoriaAtributo.objects.all()

        # 2. Aplicar FILTROS

        # --- Filtro de Buscador (Search) ---
        search_query = request.query_params.get('search', None)
        if search_query:
            relaciones = relaciones.filter(
                Q(categoria__name__icontains=search_query) |
                Q(atributo__name__icontains=search_query)
            )

        # --- Filtro por Categoría ---
        categoria_filter = request.query_params.get('categoria', None)
        if categoria_filter:
            relaciones = relaciones.filter(categoria_id=categoria_filter)

        # --- Filtro por Atributo ---
        atributo_filter = request.query_params.get('atributo', None)
        if atributo_filter:
            relaciones = relaciones.filter(atributo_id=atributo_filter)

        # --- Filtro por Obligatorio ---
        obligatorio_filter = request.query_params.get('obligatorio', None)
        if obligatorio_filter is not None and obligatorio_filter != '':
            obligatorio_bool = obligatorio_filter == '1' or obligatorio_filter.lower() == 'true'
            relaciones = relaciones.filter(obligatorio=obligatorio_bool)

        # --- Filtros de Fecha de Inicio y Fecha de Fin (Date Range) ---
        start_date_str = request.query_params.get('start_date', None)
        end_date_str = request.query_params.get('end_date', None)

        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                relaciones = relaciones.filter(created_at__gte=start_date)
            except ValueError:
                return Response(
                    {"error": "El formato de la fecha de inicio debe ser YYYY-MM-DD."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                end_date_inclusive = datetime.combine(end_date, datetime.max.time())
                relaciones = relaciones.filter(created_at__lte=end_date_inclusive)
            except ValueError:
                return Response(
                    {"error": "El formato de la fecha de fin debe ser YYYY-MM-DD."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # 3. Contar total después de filtros
        total_count = relaciones.count()

        # 4. Ordenar (por categoría, orden, luego por nombre de atributo)
        relaciones = relaciones.order_by('categoria', 'orden', 'atributo__name')

        # 5. Aplicar paginación
        page_size_param = request.query_params.get('page_size', 10)

        try:
            page_size_int = int(page_size_param)
        except (ValueError, TypeError):
            page_size_int = 10

        paginator = PageNumberPagination()
        paginator.page_size = page_size_int
        paginated_relaciones = paginator.paginate_queryset(relaciones, request)

        # 6. Serializar
        serializer = CategoriaAtributoSerializer(paginated_relaciones, many=True)

        return paginator.get_paginated_response(serializer.data)

    except Exception as e:
        print(f"Error en list_categoria_atributos: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response(
            {"error": f"Error fetching categoria-atributo relations: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Obtener una relación categoría-atributo por ID
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_categoria_atributo(request, pk):
    try:
        relacion = get_object_or_404(CategoriaAtributo, pk=pk)
        serializer = CategoriaAtributoSerializer(relacion)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"error": f"Error retrieving categoria-atributo relation: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Crear una relación categoría-atributo
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_categoria_atributo(request):
    try:
        serializer = CategoriaAtributoCreateUpdateSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()

            # Retornar la relación creada con el serializer completo
            relacion = CategoriaAtributo.objects.get(pk=serializer.instance.pk)
            response_serializer = CategoriaAtributoSerializer(relacion)

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


# Crear múltiples relaciones categoría-atributo (bulk create)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_create_categoria_atributos(request):
    try:
        # El frontend envía un array directamente
        relaciones_data = request.data

        # Validar que sea una lista
        if not isinstance(relaciones_data, list):
            return Response(
                {"error": "Se esperaba una lista de relaciones categoría-atributo."},
                status=status.HTTP_400_BAD_REQUEST
            )

        created_count = 0
        error_count = 0
        errors_detail = []

        # Crear cada relación
        for index, relacion_data in enumerate(relaciones_data):
            serializer = CategoriaAtributoCreateUpdateSerializer(data=relacion_data)

            if serializer.is_valid():
                try:
                    serializer.save()
                    created_count += 1
                except Exception as e:
                    error_count += 1
                    errors_detail.append({
                        'index': index,
                        'data': relacion_data,
                        'error': str(e)
                    })
            else:
                error_count += 1
                errors_detail.append({
                    'index': index,
                    'data': relacion_data,
                    'errors': serializer.errors
                })

        # Preparar respuesta
        response_data = {
            'success_count': created_count,
            'error_count': error_count,
            'message': f'Se crearon {created_count} relaciones correctamente.'
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


# Actualizar una relación categoría-atributo
@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_categoria_atributo(request, pk):
    try:
        relacion = get_object_or_404(CategoriaAtributo, pk=pk)

        serializer = CategoriaAtributoCreateUpdateSerializer(
            relacion,
            data=request.data,
            partial=request.method == 'PATCH'
        )

        if serializer.is_valid():
            serializer.save()

            # Retornar la relación actualizada
            response_serializer = CategoriaAtributoSerializer(relacion)
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
            {"error": f"Database error while updating categoria-atributo: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        return Response(
            {"error": f"Unexpected error: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Eliminar una relación categoría-atributo (hard delete)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_categoria_atributo(request, pk):
    try:
        relacion = get_object_or_404(CategoriaAtributo, pk=pk)

        # Obtener información antes de eliminar (para el mensaje)
        categoria_nombre = relacion.categoria.name
        atributo_nombre = relacion.atributo.name

        # Eliminar físicamente (hard delete)
        relacion.delete()

        return Response(
            {
                "message": f"Relación eliminada: {categoria_nombre} - {atributo_nombre}",
                "deleted": True
            },
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {"error": f"Error deleting categoria-atributo relation: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Listar atributos de una categoría específica
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_atributos_by_categoria(request, categoria_id):
    """
    Obtiene todos los atributos asociados a una categoría específica.
    Útil para el frontend cuando necesita cargar atributos al seleccionar una categoría.
    """
    try:
        relaciones = CategoriaAtributo.objects.filter(categoria_id=categoria_id).order_by('orden', 'atributo__name')
        serializer = CategoriaAtributoSerializer(relaciones, many=True)

        return Response(
            {
                "categoria_id": categoria_id,
                "total": relaciones.count(),
                "atributos": serializer.data
            },
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {"error": f"Error fetching atributos for categoria: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
