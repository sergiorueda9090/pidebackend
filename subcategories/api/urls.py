from django.urls import path
from . import views

urlpatterns = [
    path('list/',                     views.list_subcategories,          name='list_subcategories'),
    path('create/',                   views.create_subcategory,          name='create_subcategory'),
    path('bulk-create/',              views.bulk_create_subcategories,   name='bulk_create_subcategories'),
    path('<int:pk>/',                 views.get_subcategory,             name='get_subcategory'),
    path('<int:pk>/update/',          views.update_subcategory,          name='update_subcategory'),
    path('<int:pk>/delete/',          views.delete_subcategory,          name='delete_subcategory'),
    path('<int:pk>/restore/',         views.restore_subcategory,         name='restore_subcategory'),
]
