from django.db import models
from django.conf import settings

class Material(models.Model):
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
    ]
    UNIT_CHOICES = [
        ('unit', 'Unit'),
        ('kg', 'Kilogram'),
        ('m', 'Meter'),
        ('piece', 'Piece'),
    ]

    id_material = models.CharField(max_length=50, unique=True, verbose_name="Material ID")
    name = models.CharField(max_length=100, verbose_name="Name")  
    description = models.CharField(max_length=250, blank=True, verbose_name="Description")     
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, verbose_name="Unit measure")
    material_type = models.CharField(max_length=50, verbose_name="Material type")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active', verbose_name="Status")

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
        return f"{self.id_material} - {self.name}"