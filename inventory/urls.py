from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('movement_list/', views.movement_list, name='movement_list'),
    path('movements/create/', views.create_movement, name='create_movement'),
    path('movements/post/', views.post_inventory_movement, name='post_inventory_movement'),
    path('movements/edit/<int:pk>/', views.edit_movement, name='edit_movement'),
    path('movements/delete/<int:pk>/', views.delete_movement, name='delete_movement'),
    path('movements/update/<int:pk>/', views.update_inventory_movement, name='update_inventory_movement'),
    path('stock_list/', views.stock_list, name='stock_list'),
]