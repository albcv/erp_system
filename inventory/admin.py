from django.contrib import admin
from .models import MovementType, LocationInventory, InventoryMovement, Stock

# Register your models here.

@admin.register(MovementType)
class MovementTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'symbol')

@admin.register(LocationInventory)
class LocationInventoryAdmin(admin.ModelAdmin):
    list_display = ('id_location', 'name', 'code', 'status', 'main_location', 'location')

@admin.register(InventoryMovement)
class InventoryMovementAdmin(admin.ModelAdmin):
    list_display = ('id_inventory_movement', 'id_location', 'id_material', 'quantity', 'unit_type', 'movement_type', 'price', 'currency', 'exchange_rate')


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('date', 'id_location', 'id_material', 'quantity','unit_type', 'avg_price_usd', 'total_value_usd')