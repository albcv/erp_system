from django import forms
from .models import Material

class MaterialForm(forms.ModelForm):


        class Meta:
                model = Material
                fields = ['id_material', 'name', 'description', 'unit', 'material_type', 'status']


class CsvUploadForm(forms.Form):
    csv_file = forms.FileField(
        label='Materials CSV File',
        help_text='The CSV file must contain headers that match the model fields: id_material, name, description, unit, material_type, status'
    )
            
