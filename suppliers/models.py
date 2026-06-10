from django.db import models
from django.conf import settings
from core.models import Status, Country, Currency, PaymentTerm, PaymentMethod, Category

class Supplier(models.Model):
    # Campos principales
    id_supplier = models.CharField(max_length=20, unique=True, db_index=True, verbose_name="Supplier ID")
    legal_name = models.CharField(max_length=150, blank=True, verbose_name="Legal name")
    name = models.CharField(max_length=100, db_index=True, verbose_name="Name")
    tax_id = models.CharField(max_length=30, unique=True, verbose_name="Tax ID")

    # País (ahora FK)
    country = models.ForeignKey(Country, on_delete=models.PROTECT, default=1, verbose_name="Country")

    state_province = models.CharField(max_length=60, verbose_name="State/Province")
    city = models.CharField(max_length=100, verbose_name="City")
    address = models.TextField(max_length=255, verbose_name="Address")
    zip_code = models.CharField(max_length=20, verbose_name="Zip Code")
    phone = models.CharField(max_length=30, verbose_name="Phone")
    email = models.EmailField(unique=True, verbose_name="Email")

    # Datos de contacto y comerciales 
    contact_name = models.CharField(max_length=150, verbose_name="Contact name")
    contact_role = models.CharField(max_length=150, blank=True, verbose_name="Contact role")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, default=1, verbose_name="Category")
    payment_terms = models.ForeignKey(PaymentTerm, on_delete=models.PROTECT, default=1, verbose_name="Payment terms")
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.PROTECT, default=1, verbose_name="Payment method")
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, default=1, verbose_name="Currency")
    bank_account = models.CharField(max_length=150, verbose_name="Bank account")

    # Estado y auditoría
    status = models.ForeignKey(Status, on_delete=models.PROTECT, default=1, verbose_name="Status")  
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="Created by")

    class Meta:
        verbose_name = "Supplier"
        verbose_name_plural = "Suppliers"
        ordering = ['name']
        indexes = [
            models.Index(fields=['name', 'status']),
        ]

    def __str__(self):
        if self.legal_name:
            return f"{self.id_supplier} - {self.name} ({self.legal_name})"
        return f"{self.id_supplier} - {self.name}"