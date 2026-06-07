from django.db import models
from django.conf import settings

class Supplier(models.Model):
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
    ]

    CATEGORY_CHOICES = [
        ('manufacturer', 'Manufacturer'),
        ('distributor', 'Distributor'),
        ('retailer', 'Retailer'),
        ('service', 'Service Provider'),
        ('other', 'Other'),
    ]

    PAYMENT_TERMS_CHOICES = [
        ('net_30', 'Net 30'),
        ('net_60', 'Net 60'),
        ('net_90', 'Net 90'),
        ('cod', 'Cash on Delivery'),
        ('advance', 'Advance Payment'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash'),
        ('check', 'Check'),
        ('credit_card', 'Credit Card'),
    ]

    CURRENCY_CHOICES = [
        ('USD', 'US Dollar'),
        ('EUR', 'Euro'),
        ('GBP', 'British Pound'),
        ('MXN', 'Mexican Peso'),
        ('COP', 'Colombian Peso'),
        ('ARS', 'Argentine Peso'),
    ]

    # Campos principales
    id_supplier = models.CharField(max_length=50, unique=True, db_index=True, verbose_name="Supplier ID")
    legal_name = models.CharField(max_length=150, blank=True, verbose_name="Legal name")
    name = models.CharField(max_length=100, db_index=True, verbose_name="Name")
    tax_id = models.CharField(max_length=30, unique=True, verbose_name="Tax ID")  
    country = models.CharField(max_length=60, db_index=True, verbose_name="Country") 
    state_province = models.CharField(max_length=60, verbose_name="State/Province")
    city = models.CharField(max_length=100, verbose_name="City")
    address = models.TextField(max_length=255, verbose_name="Address")  
    zip_code = models.CharField(max_length=20, verbose_name="Zip Code")  
    phone = models.CharField(max_length=30, verbose_name="Phone")  
    email = models.EmailField(unique=True, verbose_name="Email")  

    # Datos de contacto y comerciales
    contact_name = models.CharField(max_length=150, verbose_name="Contact name")
    contact_role = models.CharField(max_length=150, blank=True, verbose_name="Contact role")  # Opcional
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other', verbose_name="Category")
    payment_terms = models.CharField(max_length=50, choices=PAYMENT_TERMS_CHOICES, default='net_30', verbose_name="Payment terms")
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES, default='bank_transfer', verbose_name="Payment method")
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD', verbose_name="Currency")
    bank_account = models.CharField(max_length=150, verbose_name="Bank account")

    # Estado y auditoría
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active', db_index=True, verbose_name="Status")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="Created by")  # Cambiado a SET_NULL

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