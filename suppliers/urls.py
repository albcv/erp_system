from django.urls import path
from . import views

app_name = 'suppliers'

urlpatterns = [
    path('', views.supplier_list, name="supplier_list"),
    path('create/', views.create_supplier, name="create_supplier"),
    path('edit/<int:pk>/', views.edit_supplier, name="edit_supplier"),   
    path('delete/<int:pk>/', views.delete_supplier, name="delete_supplier"), 
]