from django.contrib import admin
from .models import Material, MaterialType, Unit

# Register your models here.
admin.site.register(Material)
admin.site.register(MaterialType)
admin.site.register(Unit)