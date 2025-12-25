from django.urls import path
from . import views

urlpatterns = [
    path('list/',                 views.list_productos,   name='list_productos'),
    path('create/',               views.create_producto,  name='create_producto'),
    path('<int:pk>/',             views.get_producto,     name='get_producto'),
    path('<int:pk>/update/',      views.update_producto,  name='update_producto'),
    path('<int:pk>/delete/',      views.delete_producto,  name='delete_producto'),
    path('<int:pk>/restore/',     views.restore_producto, name='restore_producto'),
]
