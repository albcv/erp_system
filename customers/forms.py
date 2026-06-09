from django import forms
from .models import Customer

class CustomerForm(forms.ModelForm):


        class Meta:
                model = Customer
                fields = ['id_customer', 'legal_name', 'name', 'tax_id', 'country', 'state_province', 'city', 'address', 'zip_code', 'phone', 'email', 'contact_name',
                           'contact_role', 'category', 'payment_terms','payment_method', 'currency', 'bank_account', 'status']
            
class CsvUploadForm(forms.Form):
        csv_file = forms.FileField(

                label='Customer CSV File',
                help_text='The field must contain headers that match the model fields'

        )