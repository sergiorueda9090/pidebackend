from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.db import DatabaseError
from productos.models import Producto
from .serializers import ProductoSerializer, ProductoCreateUpdateSerializer

from django.db.models import Q
from datetime import datetime


# Listar productos con filtros y paginación
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_productos(request):
    try:
        # 1. Obtener todos los productos (sin eliminados por defecto)
        productos = Producto.objects.all()

        # 2. Aplicar FILTROS

        # --- Filtro de Buscador (Search) ---
        search_query = request.query_params.get('search', None)
        if search_query:
            productos = productos.filter(
                Q(nombre__icontains=search_query) |
                Q(descripcion_corta__icontains=search_query) |
                Q(descripcion_larga__icontains=search_query) |
                Q(sku_base__icontains=search_query) |
                Q(keywords__icontains=search_query)
            )

        # --- Filtro por Estado Activo ---
        activo_filter = request.query_params.get('activo', None)
        if activo_filter is not None and activo_filter != '':
            activo_bool = activo_filter == '1'
            productos = productos.filter(activo=activo_bool)

        # --- Filtro por Publicado ---
        publicado_filter = request.query_params.get('publicado', None)
        if publicado_filter is not None and publicado_filter != '':
            publicado_bool = publicado_filter == '1'
            productos = productos.filter(publicado=publicado_bool)

        # --- Filtro por Destacado ---
        destacado_filter = request.query_params.get('destacado', None)
        if destacado_filter is not None and destacado_filter != '':
            destacado_bool = destacado_filter == '1'
            productos = productos.filter(destacado=destacado_bool)

        # --- Filtro por Es Nuevo ---
        es_nuevo_filter = request.query_params.get('es_nuevo', None)
        if es_nuevo_filter is not None and es_nuevo_filter != '':
            es_nuevo_bool = es_nuevo_filter == '1'
            productos = productos.filter(es_nuevo=es_nuevo_bool)

        # --- Filtro por Categoría ---
        categoria_filter = request.query_params.get('categoria', None)
        if categoria_filter:
            productos = productos.filter(categoria_id=categoria_filter)

        # --- Filtro por Marca ---
        marca_filter = request.query_params.get('marca', None)
        if marca_filter:
            productos = productos.filter(marca_id=marca_filter)

        # --- Filtro por Tipo de Producto ---
        tipo_producto_filter = request.query_params.get('tipo_producto', None)
        if tipo_producto_filter:
            productos = productos.filter(tipo_producto=tipo_producto_filter)

        # --- Filtro por Tiene Variantes ---
        tiene_variantes_filter = request.query_params.get('tiene_variantes', None)
        if tiene_variantes_filter is not None and tiene_variantes_filter != '':
            tiene_variantes_bool = tiene_variantes_filter == '1'
            productos = productos.filter(tiene_variantes=tiene_variantes_bool)

        # --- Filtros de Fecha de Inicio y Fecha de Fin (Date Range) ---
        start_date_str = request.query_params.get('start_date', None)
        end_date_str = request.query_params.get('end_date', None)

        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                productos = productos.filter(created_at__gte=start_date)
            except ValueError:
                return Response(
                    {"error": "El formato de la fecha de inicio debe ser YYYY-MM-DD."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                end_date_inclusive = datetime.combine(end_date, datetime.max.time())
                productos = productos.filter(created_at__lte=end_date_inclusive)
            except ValueError:
                return Response(
                    {"error": "El formato de la fecha de fin debe ser YYYY-MM-DD."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # 3. Contar total después de filtros
        total_count = productos.count()

        # 4. Ordenar
        productos = productos.order_by('-id')

        # 5. Aplicar paginación
        page_size_param = request.query_params.get('page_size', 10)

        try:
            page_size_int = int(page_size_param)
        except (ValueError, TypeError):
            page_size_int = 10

        paginator = PageNumberPagination()
        paginator.page_size = page_size_int
        paginated_productos = paginator.paginate_queryset(productos, request)

        # 6. Serializar
        serializer = ProductoSerializer(paginated_productos, many=True)

        return paginator.get_paginated_response(serializer.data)

    except Exception as e:
        print(f"Error en list_productos: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response(
            {"error": f"Error fetching productos: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Obtener un producto por ID
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_producto(request, pk):
    try:
        producto = get_object_or_404(Producto, pk=pk)
        serializer = ProductoSerializer(producto)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"error": f"Error retrieving producto: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Crear un producto
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_producto(request):
    try:
        serializer = ProductoCreateUpdateSerializer(data=request.data)

        if serializer.is_valid():
            # Guardar con el usuario autenticado como creador
            producto = serializer.save(created_by=request.user)

            # Retornar el producto creado con el serializer completo
            response_serializer = ProductoSerializer(producto)

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


# Actualizar un producto
@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_producto(request, pk):
    try:
        producto = get_object_or_404(Producto, pk=pk)

        # Si el producto está eliminado, no permitir actualización
        if producto.deleted_at:
            return Response(
                {"error": "No se puede actualizar un producto eliminado."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ProductoCreateUpdateSerializer(
            producto,
            data=request.data,
            partial=request.method == 'PATCH'
        )

        if serializer.is_valid():
            # Guardar con el usuario autenticado como actualizador
            serializer.save(updated_by=request.user)

            # Retornar el producto actualizado
            response_serializer = ProductoSerializer(producto)
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
            {"error": f"Database error while updating producto: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        return Response(
            {"error": f"Unexpected error: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Eliminar un producto (soft delete)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_producto(request, pk):
    try:
        producto = get_object_or_404(Producto, pk=pk)

        # Verificar si ya está eliminado
        if producto.deleted_at:
            return Response(
                {"error": "Este producto ya está eliminado."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Soft delete
        producto.delete()

        return Response(
            {"message": "Producto deleted successfully (soft delete)"},
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {"error": f"Error deleting producto: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Restaurar un producto eliminado
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def restore_producto(request, pk):
    try:
        # Buscar en todos los productos (incluyendo eliminados)
        producto = get_object_or_404(Producto.all_objects, pk=pk)

        # Verificar si está eliminado
        if not producto.deleted_at:
            return Response(
                {"error": "Este producto no está eliminado."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Restaurar
        producto.restore()

        serializer = ProductoSerializer(producto)
        return Response(
            {
                "message": "Producto restored successfully",
                "producto": serializer.data
            },
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {"error": f"Error restoring producto: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
