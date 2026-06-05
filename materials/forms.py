from django import forms
from .models import Material

class MaterialForm(forms.ModelForm):


        class Meta:
                model = Material
                fields = ['id', 'name', 'description', 'unit', 'material_type', 'status']
            
