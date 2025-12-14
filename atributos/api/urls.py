from django.urls import path
from . import views

urlpatterns = [
    path('list/',                 views.list_attributes,   name='list_attributes'),
    path('create/',               views.create_attribute,   name='create_attribute'),
    path('<int:pk>/',             views.get_attribute,      name='get_attribute'),
    path('<int:pk>/update/',      views.update_attribute,   name='update_attribute'),
    path('<int:pk>/delete/',      views.delete_attribute,   name='delete_attribute'),
    path('<int:pk>/restore/',     views.restore_attribute,  name='restore_attribute'),
]
