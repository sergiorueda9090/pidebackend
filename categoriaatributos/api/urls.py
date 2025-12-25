from django.urls import path
from . import views

urlpatterns = [
    # CRUD endpoints
    path('list/',                                views.list_categoria_atributos,        name='list_categoria_atributos'),
    path('create/',                              views.create_categoria_atributo,       name='create_categoria_atributo'),
    path('bulk-create/',                         views.bulk_create_categoria_atributos, name='bulk_create_categoria_atributos'),
    path('<int:pk>/',                            views.get_categoria_atributo,          name='get_categoria_atributo'),
    path('<int:pk>/update/',                     views.update_categoria_atributo,       name='update_categoria_atributo'),
    path('<int:pk>/delete/',                     views.delete_categoria_atributo,       name='delete_categoria_atributo'),
    # Utility endpoints
    path('categoria/<int:categoria_id>/',        views.get_atributos_by_categoria,      name='get_atributos_by_categoria'),
]
