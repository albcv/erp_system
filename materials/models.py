from django.db import models
from django.conf import settings

# Create your models here.
class Material(models.Model):
    
    name = models.CharField(max_length=100, verbose_name="Name")
    description = models.CharField(max_length=250, blank=True, verbose_name="Description")
    unit = models.CharField(max_length=50, verbose_name="Unit measure")
    material_type = models.CharField(max_length=50, verbose_name="Material type")
    status = models.CharField(max_length=50, verbose_name="Status")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name="Material"
        verbose_name="Materials"

    def __str__(self):
        return self.name