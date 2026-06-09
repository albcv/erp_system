from django.contrib import admin
from .models import Supplier, SupplierCategory, SupplierCountry, SupplierCurrency, SupplierPaymentMethod, SupplierPaymentTerm

# Register your models here.
admin.site.register(Supplier)
admin.site.register(SupplierCategory)
admin.site.register(SupplierCountry)
admin.site.register(SupplierCurrency)
admin.site.register(SupplierPaymentMethod)
admin.site.register(SupplierPaymentTerm)