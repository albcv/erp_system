from django.db import models
from django.conf import settings
from core.models import Status


class Unit(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Unit Name")
    symbol = models.CharField(max_length=10, unique=True, verbose_name="Symbol")

    class Meta:
        verbose_name = "Unit"
        verbose_name_plural = "Units"

    def __str__(self):
        return f"{self.symbol}"
    

class MaterialType(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Material Type Name")
    symbol = models.CharField(max_length=10, unique=True, verbose_name="Symbol")

    class Meta:
        verbose_name = "Material Type"
        verbose_name_plural = "Material Types"

    def __str__(self):
        return f"{self.name} ({self.symbol})"


class Material(models.Model):
    
    id_material = models.CharField(max_length=50, unique=True, verbose_name="Material ID")
    name = models.CharField(max_length=100, verbose_name="Name")  
    description = models.CharField(max_length=250, blank=True, verbose_name="Description")     

    material_type = models.ForeignKey(MaterialType, default=1, on_delete=models.PROTECT, verbose_name="Material Type")
    unit = models.ForeignKey(Unit, default=1, on_delete=models.PROTECT, verbose_name="Unit")
    status = models.ForeignKey(Status, default=1, on_delete=models.PROTECT, verbose_name="Status")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True)

    class Meta:
        verbose_name = "Material"
        verbose_name_plural = "Materials"
        constraints = [
            models.UniqueConstraint(fields=['name', 'material_type'], name='unique_name_per_type')
        ]

    def __str__(self):
        return f"{self.id_material}"