from django.db import models
from django.conf import settings
from core.models import Country, Currency, Status

class AccountNature(models.Model):
   id_account_nature = models.CharField(max_length=20, unique=True, db_index=True, verbose_name="Account Nature ID")
   name = models.CharField(verbose_name='Name', max_length=50)
   symbol = models.CharField(verbose_name="Symbol", max_length=10)
   effect_on_balance = models.TextField(verbose_name='Effect on Balance')

   created_at = models.DateTimeField(auto_now_add=True)
   updated_at = models.DateTimeField(auto_now=True)
   created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="Created by")

   class Meta:
      verbose_name = 'Account Nature'
      verbose_name_plural = 'Account Natures'

   def __str__(self):
      return self.name
   

class AccountGroup(models.Model):
   id_account_group = models.CharField(max_length=20, unique=True, db_index=True, verbose_name="Account Group ID")
   name = models.CharField(verbose_name='Name', max_length=100)
   code_prefix = models.CharField(verbose_name="Code Prefix", max_length=10)
   description = models.TextField(verbose_name='Description', blank=True)

   created_at = models.DateTimeField(auto_now_add=True)
   updated_at = models.DateTimeField(auto_now=True)
   created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="Created by")

   class Meta:
      verbose_name = "Account Group"
      verbose_name_plural = 'Account Groups'

   def __str__(self):
      return self.name
   

class AccountType(models.Model):
   id_account_type = models.CharField(max_length=20, unique=True, db_index=True, verbose_name="Account Type")
   name = models.CharField(verbose_name='Name', max_length=50)
   description = models.TextField(verbose_name='Description', blank=True)

   created_at = models.DateTimeField(auto_now_add=True)
   updated_at = models.DateTimeField(auto_now=True)
   created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="Created by")

   class Meta:
      verbose_name = "Account Type"
      verbose_name_plural = 'Account Types'

   def __str__(self):
      return self.name
   

class AccountAccount(models.Model):
   id_account = models.CharField(max_length=20, unique=True, db_index=True, verbose_name="Account ID")
   name = models.CharField(verbose_name='Name', max_length=100)
   code = models.CharField(verbose_name="Code", max_length=20)
   description = models.TextField(verbose_name='Description', blank=True)

   account_type = models.ForeignKey(AccountType, on_delete=models.PROTECT, verbose_name="Account Type")
   account_group = models.ForeignKey(AccountGroup, on_delete=models.PROTECT, verbose_name="Account Group")
   nature = models.ForeignKey(AccountNature, on_delete=models.PROTECT, verbose_name="Account Nature")
   currency = models.ForeignKey(Currency, on_delete=models.PROTECT, verbose_name="Currency ID")
   country = models.ForeignKey(Country, on_delete=models.PROTECT, verbose_name="Country ID")
   is_control_account = models.BooleanField(verbose_name='Is Control Account', default=False)
   parent_account = models.ForeignKey('self', on_delete=models.SET_NULL, verbose_name='Parent Account', null=True, blank=True)

   status = models.ForeignKey(Status, on_delete=models.PROTECT, verbose_name='Status', default=1)

   created_at = models.DateTimeField(auto_now_add=True)
   updated_at = models.DateTimeField(auto_now=True)
   created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="Created by")

   class Meta:
      verbose_name = "Account"
      verbose_name_plural = 'Accounts'

   def __str__(self):
      return f"{self.code} - {self.name}"
   


class Journal(models.Model):

   id_journal = models.CharField(max_length=20, unique=True, db_index=True, verbose_name="Journal ID")
   group_journal = models.CharField(verbose_name='Group Journal ID', max_length=10)
   reference = models.CharField(verbose_name='Reference', max_length=100)
   id_account = models.ForeignKey(AccountAccount, verbose_name="Account ID", on_delete=models.PROTECT)
   credit = models.FloatField(verbose_name="Credit", default=0.0)
   debit = models.FloatField(verbose_name="Debit", default=0.0)
   currency = models.ForeignKey(Currency, verbose_name="Currency", on_delete=models.PROTECT)

   status = models.ForeignKey(Status, on_delete=models.PROTECT, verbose_name='Status', default=1)

   created_at = models.DateTimeField(auto_now_add=True)
   updated_at = models.DateTimeField(auto_now=True)
   created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="Created by")

   class Meta:
      verbose_name = "Journal"
      verbose_name_plural = 'Journals'

   def __str__(self):
      return self.id_journal
   
