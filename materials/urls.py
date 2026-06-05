from django.urls import path
from . import views

app_name = 'materials'

urlpatterns = [
    path('', views.material_list, name="material_list"),
    path('create/', views.create_material, name="create_material"),
   
]
