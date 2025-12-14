from django.urls import path
from . import views

urlpatterns = [
    path('list/',                 views.list_brands,   name='list_brands'),
    path('create/',               views.create_brand,   name='create_brand'),
    path('<int:pk>/',             views.get_brand,      name='get_brand'),
    path('<int:pk>/update/',      views.update_brand,   name='update_brand'),
    path('<int:pk>/delete/',      views.delete_brand,   name='delete_brand'),
    path('<int:pk>/restore/',     views.restore_brand,  name='restore_brand'),
]
