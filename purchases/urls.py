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
    path('goods-receipt/<int:po_pk>/', views.goods_receipt_form, name='goods_receipt_form'),
    path('post_goods_receipt/', views.post_goods_receipt, name='post_goods_receipt'),
    path('purchase-invoice/<int:po_pk>/', views.purchase_invoice_form, name='purchase_invoice_form'),
    path('post_purchase_invoice/', views.post_purchase_invoice, name='post_purchase_invoice'),
    path('mark_invoice_paid/<str:invoice_id>/', views.mark_invoice_paid, name='mark_invoice_paid'),
]
