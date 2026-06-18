from django.contrib import admin
from .models import OrderStatus, PurchaseOrder, LinesPurchaseOrder, GoodsReceiptStatus, GoodsReceipt, LinesGoodsReceipt

@admin.register(OrderStatus)
class OrderStatusAdmin(admin.ModelAdmin):
    list_display = ('name', 'symbol')


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('id_purchase_order', 'id_supplier', 'issue_date', 'estimated_delivery_date', 'order_status')


@admin.register(LinesPurchaseOrder)
class LinesPurchaseOrdersAdmin(admin.ModelAdmin):
    list_display = ('id_purchase_order_line', 'id_purchase_order', 'id_material', 'quantity', 'unit_material')

@admin.register(GoodsReceiptStatus)
class GoodReceiptStatusAdmin(admin.ModelAdmin):
    list_display = ('name', 'symbol')

admin.site.register(GoodsReceipt)
admin.site.register(LinesGoodsReceipt)

