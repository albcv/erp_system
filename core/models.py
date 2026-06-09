from django.db import models

# Create your models here.

class Status(models.Model):

    name = models.CharField(max_length=50, unique=True, verbose_name='Status Name')
    is_active = models.BooleanField(default=True, verbose_name="Is Active?")

    class Meta:
        verbose_name = "Status"
        verbose_name_plural = "Statuses"


    def __str__(self):
        return self.name
    

class Country(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Country Name")
    code = models.CharField(max_length=3, unique=True, verbose_name="Country Code")  

    class Meta:
        verbose_name = "Country"
        verbose_name_plural = "Countries"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"

class Category(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Category Name")
    description = models.CharField(max_length=200, blank=True, verbose_name="Description")

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

class PaymentTerm(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Payment Term")
    days = models.IntegerField(default=0, verbose_name="Days (net)")

    class Meta:
        verbose_name = "Payment Term"
        verbose_name_plural = "Payment Terms"

    def __str__(self):
        return self.name

class PaymentMethod(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Payment Method")
    description = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = "Payment Method"
        verbose_name_plural = "Payment Methods"

    def __str__(self):
        return self.name

class Currency(models.Model):
    code = models.CharField(max_length=3, unique=True, verbose_name="Currency Code")
    name = models.CharField(max_length=50, verbose_name="Currency Name")
    symbol = models.CharField(max_length=5, blank=True, verbose_name="Symbol")

    class Meta:
        verbose_name = "Currency"
        verbose_name_plural = "Currencies"

    def __str__(self):
        return f"{self.code} - {self.name}"
