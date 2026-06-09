from django.db import models
from django.conf import settings
from core.models import Status

class SupplierCountry(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Country Name")
    code = models.CharField(max_length=3, unique=True, verbose_name="Country Code")  

    class Meta:
        verbose_name = "Country"
        verbose_name_plural = "Countries"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"

class SupplierCategory(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Category Name")
    description = models.CharField(max_length=200, blank=True, verbose_name="Description")

    class Meta:
        verbose_name = "Supplier Category"
        verbose_name_plural = "Supplier Categories"

    def __str__(self):
        return self.name

class SupplierPaymentTerm(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Payment Term")
    days = models.IntegerField(default=0, verbose_name="Days (net)")

    class Meta:
        verbose_name = "Payment Term"
        verbose_name_plural = "Payment Terms"

    def __str__(self):
        return self.name

class SupplierPaymentMethod(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Payment Method")
    description = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = "Payment Method"
        verbose_name_plural = "Payment Methods"

    def __str__(self):
        return self.name

class SupplierCurrency(models.Model):
    code = models.CharField(max_length=3, unique=True, verbose_name="Currency Code")
    name = models.CharField(max_length=50, verbose_name="Currency Name")
    symbol = models.CharField(max_length=5, blank=True, verbose_name="Symbol")

    class Meta:
        verbose_name = "Currency"
        verbose_name_plural = "Currencies"

    def __str__(self):
        return f"{self.code} - {self.name}"

class Supplier(models.Model):
    # Campos principales
    id_supplier = models.CharField(max_length=50, unique=True, db_index=True, verbose_name="Supplier ID")
    legal_name = models.CharField(max_length=150, blank=True, verbose_name="Legal name")
    name = models.CharField(max_length=100, db_index=True, verbose_name="Name")
    tax_id = models.CharField(max_length=30, unique=True, verbose_name="Tax ID")

    # País (ahora FK)
    country = models.ForeignKey(SupplierCountry, on_delete=models.PROTECT, default=1, verbose_name="Country")

    state_province = models.CharField(max_length=60, verbose_name="State/Province")
    city = models.CharField(max_length=100, verbose_name="City")
    address = models.TextField(max_length=255, verbose_name="Address")
    zip_code = models.CharField(max_length=20, verbose_name="Zip Code")
    phone = models.CharField(max_length=30, verbose_name="Phone")
    email = models.EmailField(unique=True, verbose_name="Email")

    # Datos de contacto y comerciales 
    contact_name = models.CharField(max_length=150, verbose_name="Contact name")
    contact_role = models.CharField(max_length=150, blank=True, verbose_name="Contact role")
    category = models.ForeignKey(SupplierCategory, on_delete=models.PROTECT, default=1, verbose_name="Category")
    payment_terms = models.ForeignKey(SupplierPaymentTerm, on_delete=models.PROTECT, default=1, verbose_name="Payment terms")
    payment_method = models.ForeignKey(SupplierPaymentMethod, on_delete=models.PROTECT, default=1, verbose_name="Payment method")
    currency = models.ForeignKey(SupplierCurrency, on_delete=models.PROTECT, default=1, verbose_name="Currency")
    bank_account = models.CharField(max_length=150, verbose_name="Bank account")

    # Estado y auditoría
    status = models.ForeignKey(Status, on_delete=models.PROTECT, default=1, verbose_name="Status")  # reutiliza core.Status
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