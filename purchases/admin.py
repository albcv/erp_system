from django.contrib import admin
from .models import OrderStatus, PurchaseOrder, LinesPurchaseOrder, GoodsReceiptStatus, GoodsReceipt, LinesGoodsReceipt, InvoiceStatus, PurchaseInvoice, LinesPurchaseInvoice

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


@admin.register(InvoiceStatus)
class InvoiceStatusAdmin(admin.ModelAdmin):
    list_display = ('name', 'symbol')

@admin.register(PurchaseInvoice)
class PurchaseInvoiceAdmin(admin.ModelAdmin):
    list_display = ('id_invoice', 'id_purchase_order', 'invoice_date', 'due_date', 'total_amount', 'currency_invoice', 'status', 'created_at', 'updated_at', 'created_by')


@admin.register(LinesPurchaseInvoice)
class LinesPurchaseInvoiceAdmin(admin.ModelAdmin):
    list_display = ('id_purchase_invoice', 'id_purchase_order_line', 'price', 'currency_invoice_line', 'quantity', 'created_at', 'updated_at', 'created_by')


