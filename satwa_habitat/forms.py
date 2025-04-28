from django import forms
from .models import Hewan, Habitat

class HewanForm(forms.ModelForm):
    class Meta:
        model = Hewan
        fields = '__all__'
        widgets = {
            'tanggal_lahir': forms.DateInput(attrs={'type': 'date'}),
        }

class HabitatForm(forms.ModelForm):
    class Meta:
        model = Habitat
        fields = ['nama', 'luas_area', 'kapasitas', 'status']
        widgets = {
            'status': forms.Textarea(attrs={'rows': 3}),
        }