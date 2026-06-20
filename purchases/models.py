from django.db import models
from django.conf import settings
from suppliers.models import Supplier
from materials.models import Material, Unit
from core.models import Currency
from inventory.models import LocationInventory

class OrderStatus(models.Model):

   name = models.CharField(verbose_name='Name', max_length=200)
   symbol = models.CharField(verbose_name="Symbol", max_length=100)
  

   created_at = models.DateTimeField(auto_now_add=True)
   updated_at = models.DateTimeField(auto_now=True)
   created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="Created by")

   class Meta:
      verbose_name = 'Order Status'
      verbose_name_plural = 'Order Statuses'

   def __str__(self):
      return self.symbol


class PurchaseOrder(models.Model):

   id_purchase_order = models.CharField(max_length=20, unique=True, db_index=True, verbose_name="ID Purchase Order")
   id_supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, verbose_name="ID Supplier")
   issue_date = models.DateTimeField(auto_now_add=True, verbose_name="Issue Date")
   estimated_delivery_date = models.DateTimeField(verbose_name="Estimated Delivery Date")
   order_status = models.ForeignKey(OrderStatus, on_delete=models.PROTECT, verbose_name='Order Status')
   
   created_at = models.DateTimeField(auto_now_add=True)
   updated_at = models.DateTimeField(auto_now=True)
   created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="Created by")

   class Meta:
      verbose_name = 'Purchase Order'
      verbose_name_plural = 'Purchase Orders'

   def __str__(self):
      return self.id_purchase_order
   
   

class LinesPurchaseOrder(models.Model):

    id_purchase_order_line = models.CharField(verbose_name="ID Purchase Order Line", max_length=20, unique=True, db_index=True)
    id_purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, verbose_name="Purchase Order", related_name='lines_purchase_order')
    id_material = models.ForeignKey(Material, on_delete=models.PROTECT, verbose_name="Material ID")
    position = models.IntegerField(default=1, verbose_name='Position')
    quantity = models.IntegerField(default=0, verbose_name="Quantity") 
    unit_material = models.ForeignKey(Unit, verbose_name="Unit Type", on_delete=models.PROTECT)
    price = models.FloatField(verbose_name='Price')
    currency_supplier = models.ForeignKey(Currency, on_delete=models.PROTECT, verbose_name="Currency Supplier")
    receive_quantity = models.IntegerField(verbose_name='Receive Quantity')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="Created by")

    class Meta:
        verbose_name = "Lines Purchase Order"
        verbose_name_plural = "Lines Purchase Orders"

    def __str__(self):
        return self.id_purchase_order_line
    


class GoodsReceiptStatus(models.Model):
   name = models.CharField(max_length=200, verbose_name='Name')
   symbol = models.CharField(max_length=100, verbose_name='Symbol', blank=True)

   created_at = models.DateTimeField(auto_now_add=True)
   updated_at = models.DateTimeField(auto_now=True)
   created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="Created by")

   class Meta:
      verbose_name="Goods Receipt Status"
      verbose_name_plural="Goods Receipt Status"

   def __str__(self):
      return self.symbol
   

class GoodsReceipt(models.Model):

   id_goods_receipt = models.CharField(verbose_name="ID Goods Receipts", max_length=20, unique=True, db_index=True)
   id_purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.PROTECT, verbose_name='ID Purchase Order')
   receipt_date = models.DateTimeField(verbose_name="Receipt Date")
   supplier_delivery_note = models.CharField(max_length=50, blank=True, null=True, verbose_name='Supplier Delivery Note Ref')

   status = models.ForeignKey(GoodsReceiptStatus, default=1, on_delete=models.PROTECT, verbose_name='Status')

   created_at = models.DateTimeField(auto_now_add=True)
   updated_at = models.DateTimeField(auto_now=True)
   created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="Created by")

   class Meta:
      verbose_name="Goods Receipt"
      verbose_name_plural="Goods Receipt"

   def __str__(self):
      return self.id_goods_receipt
   

class LinesGoodsReceipt(models.Model):

    id_goods_receipt_line = models.CharField(verbose_name="ID Goods Receipt Line", max_length=20, unique=True, db_index=True)
    id_goods_receipt = models.ForeignKey(GoodsReceipt, on_delete=models.CASCADE, verbose_name="ID Goods Receipts", related_name='lines')
    id_purchase_order_line = models.ForeignKey(LinesPurchaseOrder, on_delete=models.CASCADE, verbose_name='ID Purchase Order Line')
    id_material = models.ForeignKey(Material, on_delete=models.PROTECT, verbose_name="Material ID")
    unit_material = models.ForeignKey(Unit, verbose_name="Unit Type", on_delete=models.PROTECT)
    receive_quantity = models.IntegerField(verbose_name='Receive Quantity')
    id_location = models.ForeignKey(LocationInventory, on_delete=models.PROTECT, verbose_name='Destination Location')
    inventory_movement_ref = models.CharField(max_length=30, blank=True, null=True, verbose_name='Inventory Movement ID')
   

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="Created by")

    class Meta:
        verbose_name = "Lines Goods Receipt"
        verbose_name_plural = "Lines Goods Receipts"

    def __str__(self):
        return self.id_goods_receipt_line
    



    