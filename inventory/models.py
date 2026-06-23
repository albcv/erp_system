from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from core.models import Status, Currency
from materials.models import Material, Unit
from datetime import date


# Create your models here.

class MovementType(models.Model):

    name = models.CharField(verbose_name="Name", max_length=50)
    symbol = models.CharField(verbose_name="Symbol", max_length=10)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="Created by")

    class Meta:
        verbose_name = "Movement Type"
        verbose_name_plural = "Movement Types"

    def __str__(self):
        return f"{self.symbol}"
    

class LocationInventory(models.Model):

    id_location = models.CharField(verbose_name="Location ID", max_length=20, unique=True, db_index=True)
    name = models.CharField(verbose_name="Name", max_length=100) 
    code = models.CharField(verbose_name="Code", max_length=20) 
    main_location = models.BooleanField(verbose_name="Main Location", default=False)
    location = models.TextField(verbose_name="Address", blank=True) 

    status = models.ForeignKey(Status, on_delete=models.PROTECT, default=1, verbose_name="Status")  

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="Created by")

    class Meta:
        verbose_name = "Inventory Location"
        verbose_name_plural = "Inventory Locations"

    def __str__(self):
        return f"{self.id_location}-{self.name}"



class InventoryMovement(models.Model):

    id_inventory_movement = models.CharField(verbose_name="Inventory Movement ID", max_length=20, unique=True, db_index=True)

    id_location = models.ForeignKey(LocationInventory, on_delete=models.PROTECT, verbose_name="Location ID")
    id_material = models.ForeignKey(Material, on_delete=models.PROTECT, verbose_name="Material ID")
    quantity = models.IntegerField(verbose_name="Quantity") 
    unit_type = models.ForeignKey(Unit, verbose_name="Unit Type", on_delete=models.PROTECT)
    movement_type = models.ForeignKey(MovementType, on_delete=models.PROTECT, verbose_name="Movement ID")

    exchange_rate = models.DecimalField(max_digits=18, decimal_places=6, default=1.0, verbose_name='Exchange Rate')

    price = models.FloatField(verbose_name='Price', default=0.0)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, verbose_name='Currency')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="Created by")

    class Meta:
        verbose_name = "Inventory Movement"
        verbose_name_plural = "Inventory Movements"

    def __str__(self):
        return f"{self.id_inventory_movement} - {self.movement_type.name} {self.quantity} {self.unit_type.symbol} of {self.id_material.name} at {self.id_location.name}"
    


class Stock(models.Model):

    id_location = models.ForeignKey(LocationInventory, on_delete=models.CASCADE, verbose_name='ID Location')
    id_material = models.ForeignKey(Material, on_delete=models.CASCADE, verbose_name='ID Material')
    date = models.DateField(default=date.today, verbose_name='Journal Date')
    quantity = models.IntegerField(default=0, verbose_name='Quantity')
    unit_type = models.ForeignKey(Unit, verbose_name="Unit Type", on_delete=models.PROTECT)

    avg_price_usd = models.DecimalField(max_digits=18, decimal_places=6, default=0.0)
    total_value_usd = models.DecimalField(max_digits=18, decimal_places=4, default=0.0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
  

    class Meta:
        verbose_name = "Stock"
        verbose_name_plural = "Stocks"
        unique_together = ('date', 'id_location', 'id_material')

    def save(self, *args, **kwargs):
       self.total_value_usd = float(self.quantity)*float(self.avg_price_usd)
       super().save(*args, **kwargs)
