from django.urls import path
from . import views

app_name = 'materials'

urlpatterns = [
    path('', views.material_list, name="material_list"),
    path('create/', views.create_material, name="create_material"),
    path('edit/<int:pk>/', views.edit_material, name="edit_material"),   # <-- añadir <int:pk>
    path('delete/<int:pk>/', views.delete_material, name="delete_material"), # <-- añadir <int:pk>
]