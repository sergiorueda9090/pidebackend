from django.urls import path
from . import views

urlpatterns = [
    path('list/',                 views.list_attribute_values,   name='list_attribute_values'),
    path('create/',               views.create_attribute_value,   name='create_attribute_value'),
    path('<int:pk>/',             views.get_attribute_value,      name='get_attribute_value'),
    path('<int:pk>/update/',      views.update_attribute_value,   name='update_attribute_value'),
    path('<int:pk>/delete/',      views.delete_attribute_value,   name='delete_attribute_value'),
    path('<int:pk>/restore/',     views.restore_attribute_value,  name='restore_attribute_value'),
]
