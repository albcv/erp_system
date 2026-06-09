from django.urls import path
from . import views

app_name = 'customers'

urlpatterns = [
    path('', views.customer_list, name="customer_list"),
    path('create/', views.create_customer, name="create_customer"),
    path('edit/<int:pk>/', views.edit_customer, name="edit_customer"),   
    path('delete/<int:pk>/', views.delete_customer, name="delete_customer"), 
    path('bulk-upload/', views.customer_bulk_create, name='customer_bulk_create'),
    path('download-template/', views.download_template_customers, name='download_template_customers'),
]