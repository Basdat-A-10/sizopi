<<<<<<< HEAD
from django.db import models

# Create your models here.
=======
import uuid
from django.db import models

class Adopter(models.Model):
    id_adopter = models.UUIDField(primary_key=True)
    username_adopter = models.CharField(max_length=50, unique=True)
    total_kontribusi = models.IntegerField()

    class Meta:
        managed = False  # Ini wajib, supaya Django tahu tabel sudah ada
        db_table = 'adopter'

    def __str__(self):
        return self.username_adopter

class Adopsi(models.Model):
    id_adopter = models.ForeignKey(Adopter, on_delete=models.CASCADE, db_column='id_adopter', primary_key=True)
    id_hewan = models.UUIDField()
    status_pembayaran = models.CharField(max_length=10)
    tgl_mulai_adopsi = models.DateField()
    tgl_berhenti_adopsi = models.DateField()
    kontribusi_finansial = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'adopsi'
        unique_together = ('id_adopter', 'id_hewan', 'tgl_mulai_adopsi')

    def is_ongoing(self):
        from django.utils import timezone
        return self.tgl_berhenti_adopsi >= timezone.now().date()

    def __str__(self):
        return f'{self.id_adopter} - {self.id_hewan}'
>>>>>>> 1be7431a32b3a155ded74136348c4611c55e5da1
