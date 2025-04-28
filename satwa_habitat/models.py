from django.db import models

class Habitat(models.Model):
    nama = models.CharField(max_length=50, primary_key=True)
    luas_area = models.DecimalField(max_digits=20, decimal_places=2)
    kapasitas = models.IntegerField()
    status = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'habitat'

    def __str__(self):
        return self.nama

class Hewan(models.Model):
    STATUS_CHOICES = [
        ('Sehat', 'Sehat'),
        ('Sakit', 'Sakit'),
        ('Dalam Pemantauan', 'Dalam Pemantauan'),
        ('Lainnya', 'Lainnya'),
    ]

    id = models.UUIDField(primary_key=True)
    nama = models.CharField(max_length=100, null=True, blank=True)
    spesies = models.CharField(max_length=100)
    asal_hewan = models.CharField(max_length=100)
    tanggal_lahir = models.DateField(null=True, blank=True)
    status_kesehatan = models.CharField(max_length=50, choices=STATUS_CHOICES)
    nama_habitat = models.ForeignKey(
        Habitat,
        to_field='nama',
        db_column='nama_habitat',
        on_delete=models.DO_NOTHING
    )
    url_foto = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'hewan'

    def __str__(self):
        return self.nama or self.spesies
