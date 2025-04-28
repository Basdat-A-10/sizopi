from django.db import models
import uuid

class Pengguna(models.Model):
    username = models.CharField(primary_key=True, max_length=50)
    email = models.EmailField(max_length=100)
    password = models.CharField(max_length=50)
    nama_depan = models.CharField(max_length=50)
    nama_tengah = models.CharField(max_length=50, blank=True, null=True)
    nama_belakang = models.CharField(max_length=50)
    no_telepon = models.CharField(max_length=15)

    class Meta:
        db_table = 'sizopi"."pengguna'
        managed = False  

    def get_full_name(self):
        return f"{self.nama_depan} {self.nama_tengah or ''} {self.nama_belakang}".strip()

    def get_role(self):
        if hasattr(self, 'stafadmin'):
            return 'Staf Admin'
        elif hasattr(self, 'dokterhewan'):
            return 'Dokter Hewan'
        elif hasattr(self, 'penjagahewan'):
            return 'Penjaga Hewan'
        elif hasattr(self, 'pelatihhewan'):
            return 'Pelatih Hewan'
        elif hasattr(self, 'pengunjung'):
            return 'Pengunjung'
        else:
            return 'User'


class Pengunjung(models.Model):
    pengguna = models.OneToOneField(Pengguna, on_delete=models.CASCADE, primary_key=True, db_column='username_P')
    alamat = models.CharField(max_length=200)
    tgl_lahir = models.DateField()

    class Meta:
        db_table = 'sizopi"."pengunjung'
        managed = False  

class DokterHewan(models.Model):
    username_dh = models.OneToOneField(Pengguna, on_delete=models.CASCADE, primary_key=True, db_column='username_dh')
    no_str = models.CharField(max_length=50)

    class Meta:
        db_table = 'sizopi"."dokter_hewan'
        managed = False


class PenjagaHewan(models.Model):
    pengguna = models.OneToOneField(Pengguna, on_delete=models.CASCADE, primary_key=True, db_column='username_jh')
    id_staf = models.UUIDField()

    class Meta:
        db_table = 'sizopi"."penjaga_hewan'
        managed = False  

class PelatihHewan(models.Model):
    pengguna = models.OneToOneField(Pengguna, on_delete=models.CASCADE, primary_key=True, db_column='username_lh')
    id_staf = models.UUIDField()

    class Meta:
        db_table = 'sizopi"."pelatih_hewan'
        managed = False  

class StafAdmin(models.Model):
    pengguna = models.OneToOneField(Pengguna, on_delete=models.CASCADE, primary_key=True, db_column='username_sa')
    id_staf = models.UUIDField()

    class Meta:
        db_table = 'sizopi"."staf_admin'
        managed = False  


class Spesialisasi(models.Model):
    username_sh = models.ForeignKey(
        DokterHewan,
        on_delete=models.CASCADE,
        db_column='username_sh',
        to_field='username_dh',
    )
    nama_spesialisasi = models.CharField(max_length=100)

    class Meta:
        db_table = 'sizopi"."spesialisasi'
        managed = False
        unique_together = (('username_sh', 'nama_spesialisasi'),)

