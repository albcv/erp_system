from django.urls import path
from . import views

app_name = 'purchases'

urlpatterns = [
    path('purchase_order_list/', views.purchase_order_list, name='purchase_order_list'),
    path('create/', views.purchase_order_form, name='purchase_order_form'),
    path('edit/<int:pk>/', views.purchase_order_form, name='edit_purchase_order'),
    path('create_order/', views.create_purchase_order, name='create_purchase_order'),
    path('delete/<int:pk>/', views.delete_purchase_order, name='delete_purchase_order'),
    path('api/supplier/details/<str:supplier_id>/', views.get_supplier_details, name='api_supplier_details'),
    path('api/material/details/<str:material_id>/', views.get_material_details, name='api_material_details'),
]