from django.urls import path
from . import views

urlpatterns = [
    path('list/',                 views.list_categories,   name='list_categories'),
    path('create/',               views.create_category,   name='create_category'),
    path('<int:pk>/',             views.get_category,      name='get_category'),
    path('<int:pk>/update/',      views.update_category,   name='update_category'),
    path('<int:pk>/delete/',      views.delete_category,   name='delete_category'),
    path('<int:pk>/restore/',     views.restore_category,  name='restore_category'),
]
