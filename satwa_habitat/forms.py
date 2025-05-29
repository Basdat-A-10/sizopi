from django import forms

class HewanForm(forms.Form):
    id = forms.UUIDField()
    nama = forms.CharField(max_length=100, required=False)
    spesies = forms.CharField(max_length=100)
    asal_hewan = forms.CharField(max_length=100)
    tanggal_lahir = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    status_kesehatan = forms.ChoiceField(
        choices=[
            ('Sehat', 'Sehat'),
            ('Sakit', 'Sakit'),
            ('Dalam Pemantauan', 'Dalam Pemantauan'),
            ('Lainnya', 'Lainnya'),
        ]
    )
    nama_habitat = forms.CharField(max_length=100)
    url_foto = forms.CharField(max_length=255)

class HabitatForm(forms.Form):
    nama = forms.CharField(max_length=50)
    luas_area = forms.DecimalField(max_digits=20, decimal_places=2)
    kapasitas = forms.IntegerField()
    status = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}))
