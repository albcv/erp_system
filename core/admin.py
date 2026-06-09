from django.contrib import admin
from .models import Status, Category, Country, Currency, PaymentMethod, PaymentTerm

# Register your models here.

admin.site.register(Status)
admin.site.register(Category)
admin.site.register(Country)
admin.site.register(Currency)
admin.site.register(PaymentMethod)
admin.site.register(PaymentTerm)