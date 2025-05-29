from django.shortcuts import render, redirect
from django.db import connection, transaction
from django.utils import timezone
from datetime import date, timedelta
from django.http import Http404, HttpResponseBadRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from dateutil.relativedelta import relativedelta 
import uuid


def dictfetchall(cursor):
    "Return all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def adopter_list(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM SIZOPI.adopter")
        adopters = dictfetchall(cursor)

        one_year_ago = timezone.now().date() - timedelta(days=365)
        cursor.execute("""
            SELECT a.id_adopter, ad.username_adopter, SUM(a.kontribusi_finansial) AS total
            FROM SIZOPI.adopsi a
            JOIN SIZOPI.adopter ad ON a.id_adopter = ad.id_adopter
            WHERE a.tgl_mulai_adopsi >= %s AND a.status_pembayaran = 'Lunas'
            GROUP BY a.id_adopter, ad.username_adopter
            ORDER BY total DESC
            LIMIT 5
        """, [one_year_ago])
        top_adopters = dictfetchall(cursor)

    return render(request, 'adopsi/adopter_list.html', {
        'adopters': adopters,
        'top_adopters': top_adopters
    })

def adopter_detail(request, id_adopter):
    with connection.cursor() as cursor:
        # Get adopter
        cursor.execute("SELECT * FROM SIZOPI.adopter WHERE id_adopter = %s", [id_adopter])
        adopter = dictfetchall(cursor)
        if not adopter:
            raise Http404("Adopter not found")
        adopter = adopter[0]

        # Get adoption history (Lunas only)
        cursor.execute("""
            SELECT * FROM SIZOPI.adopsi
            WHERE id_adopter = %s AND status_pembayaran = 'Lunas'
        """, [id_adopter])
        adopsi_list = dictfetchall(cursor)

    return render(request, 'adopsi/adopter_detail.html', {
        'adopter': adopter,
        'adopsi_list': adopsi_list,
        'today': timezone.now().date()
    })

def delete_adopter(request, id_adopter):
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM SIZOPI.adopter WHERE id_adopter = %s", [id_adopter])
    return redirect('adopter_list')

def delete_adopsi(request, id_adopter, id_hewan, tgl_mulai_adopsi):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT tgl_berhenti_adopsi FROM SIZOPI.adopsi
            WHERE id_adopter = %s AND id_hewan = %s AND tgl_mulai_adopsi = %s
        """, [id_adopter, id_hewan, tgl_mulai_adopsi])
        result = cursor.fetchone()
        if result and result[0] < timezone.now().date():
            cursor.execute("""
                DELETE FROM SIZOPI.adopsi
                WHERE id_adopter = %s AND id_hewan = %s AND tgl_mulai_adopsi = %s
            """, [id_adopter, id_hewan, tgl_mulai_adopsi])
    return redirect('adopter_detail', id_adopter=id_adopter)

def adopsi_home(request):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                h.id, h.nama, h.spesies, h.status_kesehatan, h.url_foto,
                a.status_pembayaran, a.tgl_mulai_adopsi, a.tgl_berhenti_adopsi,
                ad.username_adopter AS adopter_username,
                a.kontribusi_finansial
            FROM SIZOPI.hewan h
            LEFT JOIN SIZOPI.adopsi a ON h.id = a.id_hewan
            LEFT JOIN SIZOPI.adopter ad ON a.id_adopter = ad.id_adopter
        """)
        animals = dictfetchall(cursor)
    
    message = request.session.pop('alert_message', None)

    return render(request, 'adopsi/adopsi_home.html', {'animals': animals, 'alert_message': message})



def riwayat_adopsi(request, id_adopter):
    with connection.cursor() as cursor:
        # Info Adopter (corrected)
        cursor.execute("""
            SELECT 
                COALESCE(i.nama, o.nama_organisasi) AS nama_adopter,
                p.alamat,
                u.no_telepon
            FROM ADOPTER ad
            JOIN PENGUNJUNG p ON ad.username_adopter = p.username_P
            JOIN PENGGUNA u ON p.username_P = u.username
            LEFT JOIN INDIVIDU i ON ad.id_adopter = i.id_adopter
            LEFT JOIN ORGANISASI o ON ad.id_adopter = o.id_adopter
            WHERE ad.id_adopter = %s
        """, [id_adopter])
        info = cursor.fetchone()

        # Riwayat Adopsi
        cursor.execute("""
            SELECT 
                h.nama,
                h.spesies,
                a.tgl_mulai_adopsi,
                a.tgl_berhenti_adopsi,
                a.kontribusi_finansial,
                CASE 
                    WHEN a.tgl_berhenti_adopsi > CURRENT_DATE THEN 'Sedang Berlangsung'
                    ELSE 'Selesai'
                END AS status
            FROM ADOPSI a
            JOIN HEWAN h ON a.id_hewan = h.id
            WHERE a.id_adopter = %s AND a.status_pembayaran = 'Lunas'
        """, [id_adopter])
        riwayat = cursor.fetchall()

    return render(request, 'adopsi/riwayat_adopsi.html', {
        'info': info,
        'riwayat': riwayat,
        'id_adopter': id_adopter
    })



def form_individu(request):
    return render(request, 'adopsi/form_adopsi_individu.html')

def form_organisasi(request):
    return render(request, 'adopsi/form_adopsi_organisasi.html')

def adopter_home(request):
    return render(request, 'adopsi/adopsi_home_adopter.html')

@csrf_exempt
def update_status_pembayaran(request, id_hewan):
    if request.method == 'POST':
        new_status = request.POST.get('status_pembayaran')
        new_status_db = 'Lunas' if new_status == 'Lunas' else 'Belum'

        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE SIZOPI.adopsi 
                SET status_pembayaran = %s 
                WHERE id_hewan = %s
            """, [new_status_db, id_hewan])

            # Jika status 'Lunas', panggil fungsi untuk sinkronisasi kontribusi
            if new_status_db == 'Lunas':
                cursor.execute("SELECT id_adopter FROM SIZOPI.adopsi WHERE id_hewan = %s LIMIT 1", [id_hewan])
                id_adopter = cursor.fetchone()[0]
                cursor.execute("SELECT sync_total_kontribusi_adopter(%s)", [id_adopter])
                message = cursor.fetchone()[0]
            else:
                message = "Status pembayaran diubah menjadi 'Belum'."

        # Simpan message ke session
        request.session['alert_message'] = message
        return redirect('adopsi_home')

    raise Http404("Invalid request")


@csrf_exempt
def verifikasi_adopter(request, id_hewan):
    if request.method == "POST":
        username = request.POST.get("adopterUsername")
        adopter_type = request.POST.get("adopterType")

        if adopter_type == "individu":
            return render(request, 'adopsi/form_adopsi_individu.html', {
                'username': username,
                'id_hewan': id_hewan
            })
        elif adopter_type == "organisasi":
            return render(request, 'adopsi/form_adopsi_organisasi.html', {
                'username': username,
                'id_hewan': id_hewan
            })
        else:
            return redirect('adopsi_home') 
        
@csrf_exempt
def submit_adopsi_individu(request):
    if request.method == "POST":
        username = request.POST.get("username")
        id_hewan = request.POST.get("id_hewan")
        
        try:
            # Pastikan kontribusi adalah angka (integer atau float sesuai kebutuhan)
            kontribusi = int(request.POST.get("kontribusi_finansial")) 
        except (ValueError, TypeError):
            return HttpResponse("Nominal kontribusi tidak valid.", status=400)

        try:
            periode_bulan = int(request.POST.get("periode_adopsi"))
        except (ValueError, TypeError):
            return HttpResponse("Periode adopsi tidak valid.", status=400)

        # Validasi dasar untuk field yang wajib ada
        if not username or not id_hewan:
            return HttpResponse("Username atau ID Hewan tidak boleh kosong.", status=400)
        if kontribusi < 10000: # Sesuai min="10000" di form Anda
             return HttpResponse("Nominal kontribusi minimal Rp 10.000.", status=400)


        tgl_mulai = timezone.now().date()
        tgl_berhenti = tgl_mulai + relativedelta(months=periode_bulan)

        with connection.cursor() as cursor:
            
            cursor.execute("""
                INSERT INTO SIZOPI.ADOPTER (id_adopter, username_adopter, total_kontribusi)
                VALUES (%s, %s, %s)
                ON CONFLICT (username_adopter) DO UPDATE SET
                    total_kontribusi = SIZOPI.ADOPTER.total_kontribusi + EXCLUDED.total_kontribusi
                RETURNING id_adopter;
            """, [str(uuid.uuid4()), username, kontribusi])
            
            result = cursor.fetchone()
            if not result:
                # Ini seharusnya tidak terjadi jika query UPSERT berhasil
                return HttpResponse("Gagal membuat atau memperbarui data adopter.", status=500)
            
            id_adopter_val = result[0]

            # Langkah 3: Insert ke tabel ADOPSI
            cursor.execute("""
                INSERT INTO SIZOPI.ADOPSI (
                    id_adopter, id_hewan, status_pembayaran,
                    tgl_mulai_adopsi, tgl_berhenti_adopsi, kontribusi_finansial
                )
                VALUES (%s, %s, %s, %s, %s, %s)
            """, [
                id_adopter_val, id_hewan, "Belum", 
                tgl_mulai, tgl_berhenti, kontribusi
            ])

            cursor.execute("SELECT sync_total_kontribusi_adopter(%s)", [id_adopter_val])

        return redirect("adopsi_home")
    else:
        return HttpResponse("Metode request tidak valid.", status=405)

@csrf_exempt
def submit_adopsi_organisasi(request):
    if request.method == "POST":
        try:

            username = request.POST.get("username")
            npp = request.POST.get("npp")
            nama_organisasi = request.POST.get("nama_organisasi")
            id_hewan = request.POST.get("id_hewan")
            kontribusi = int(request.POST.get("kontribusi_finansial"))
            periode = int(request.POST.get("periode_adopsi"))

            if not all([username, npp, nama_organisasi, id_hewan, kontribusi, periode]):
                return HttpResponseBadRequest("Form tidak lengkap")

            with connection.cursor() as cursor, transaction.atomic():
                # 1. Pastikan adopter sudah ada atau tambahkan
                cursor.execute("SELECT id_adopter FROM SIZOPI.adopter WHERE username_adopter = %s", [username])
                row = cursor.fetchone()

                if row:
                    id_adopter = row[0]
                else:
                    id_adopter = str(uuid.uuid4())
                    cursor.execute("""
                        INSERT INTO SIZOPI.adopter (id_adopter, username_adopter, total_kontribusi)
                        VALUES (%s, %s, %s)
                    """, [id_adopter, username, kontribusi])

                cursor.execute("SELECT sync_total_kontribusi_adopter(%s)", [id_adopter])

                # 2. Tambahkan organisasi jika belum ada
                cursor.execute("SELECT * FROM SIZOPI.organisasi WHERE npp = %s", [npp])
                if cursor.fetchone() is None:
                    cursor.execute("""
                        INSERT INTO SIZOPI.organisasi (npp, nama_organisasi, id_adopter)
                        VALUES (%s, %s, %s)
                    """, [npp, nama_organisasi, id_adopter])

                # 3. Hitung tanggal mulai & berhenti adopsi
                tgl_mulai = date.today()
                tgl_berhenti = tgl_mulai + timedelta(days=30 * periode)

                # 4. Tambahkan adopsi
                cursor.execute("""
                    INSERT INTO SIZOPI.adopsi (
                        id_adopter, id_hewan, status_pembayaran,
                        tgl_mulai_adopsi, tgl_berhenti_adopsi, kontribusi_finansial
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                """, [id_adopter, id_hewan, "Belum", tgl_mulai, tgl_berhenti, kontribusi])

                

                # 5. Tambahkan kontribusi total adopter
                cursor.execute("""
                    UPDATE SIZOPI.adopter
                    SET total_kontribusi = total_kontribusi + %s
                    WHERE id_adopter = %s
                """, [kontribusi, id_adopter])

            return redirect("adopsi_home")

        except Exception as e:
            return HttpResponseBadRequest(f"Terjadi kesalahan: {e}")

    return HttpResponseBadRequest("Metode tidak diperbolehkan")

def adopsi_home_adopter(request):
    username = request.COOKIES.get('user_id')
    print(username)

    with connection.cursor() as cursor:
        # Fetch daftar hewan yang diadopsi
        cursor.execute("""
            SELECT h.id, h.nama, h.spesies, h.status_kesehatan, hb.nama, 
                   a.tgl_mulai_adopsi, a.tgl_berhenti_adopsi, a.kontribusi_finansial, h.url_foto
            FROM SIZOPI.hewan h
            JOIN SIZOPI.habitat hb ON h.nama_habitat = hb.nama
            JOIN SIZOPI.adopsi a ON h.id = a.id_hewan
            JOIN SIZOPI.adopter ad ON a.id_adopter = ad.id_adopter
            WHERE ad.username_adopter = %s
        """, [username])
        rows = cursor.fetchall()

        adopted_animals = []
        for row in rows:
            animal_id = row[0]
            # Fetch rekam medis untuk hewan ini
            cursor.execute("""
                SELECT cm.tanggal_pemeriksaan, dh.username_dh, cm.status_kesehatan,
                       cm.diagnosis, cm.pengobatan, cm.catatan_tindak_lanjut
                FROM SIZOPI.catatan_medis cm
                JOIN SIZOPI.dokter_hewan dh ON cm.username_dh = dh.username_dh
                WHERE cm.id_hewan = %s
                ORDER BY cm.tanggal_pemeriksaan DESC
            """, [animal_id])
            medis_rows = cursor.fetchall()

            rekam_medis = [
                {
                    "tanggal": m[0],
                    "dokter": m[1],
                    "status": m[2],
                    "diagnosis": m[3],
                    "pengobatan": m[4],
                    "catatan": m[5]
                } for m in medis_rows
            ]

            # Cek apakah adopter ini individu
            cursor.execute("""
                SELECT COUNT(*) FROM SIZOPI.individu i
                JOIN SIZOPI.adopter ad ON i.id_adopter = ad.id_adopter
                WHERE ad.username_adopter = %s
            """, [username])
            is_individu = cursor.fetchone()[0] > 0

            adopted_animals.append({
                "id": row[0],
                "nama": row[1],
                "spesies": row[2],
                "status_kesehatan": row[3],
                "habitat": row[4],
                "tgl_mulai": row[5],
                "tgl_berhenti": row[6],
                "kontribusi": row[7],
                "url_foto": row[8],
                "rekam_medis": rekam_medis,
                "is_individu": is_individu,
            })

    return render(request, 'adopsi/adopsi_home_adopter.html', {
        'adopted_animals': adopted_animals
    })

def hentikan_adopsi(request, id_hewan):
    username = request.COOKIES.get('user_id')
    
    with connection.cursor() as cursor:
        cursor.execute("""
            DELETE FROM SIZOPI.adopsi
            WHERE id_hewan = %s AND id_adopter = (
                SELECT id_adopter FROM SIZOPI.adopter WHERE username_adopter = %s
            )
        """, [str(id_hewan), username])

    return redirect('adopsi_home_adopter')

@csrf_exempt
def perpanjang_adopsi_individu(request, id_hewan):
    if request.method == "POST":
        username = request.COOKIES.get("user_id")
        try:
            tambahan_kontribusi = int(request.POST.get("kontribusi_finansial"))
            periode_bulan = int(request.POST.get("periode_adopsi"))
        except:
            return HttpResponseBadRequest("Input tidak valid.")

        with connection.cursor() as cursor:
            # Ambil data adopsi yang aktif
            cursor.execute("""
                SELECT tgl_mulai_adopsi, tgl_berhenti_adopsi
                FROM SIZOPI.adopsi a
                JOIN SIZOPI.adopter ad ON a.id_adopter = ad.id_adopter
                WHERE ad.username_adopter = %s AND a.id_hewan = %s
                ORDER BY tgl_berhenti_adopsi DESC
                LIMIT 1
            """, [username, id_hewan])
            result = cursor.fetchone()

            if not result:
                return HttpResponseBadRequest("Data adopsi tidak ditemukan.")

            old_start, old_end = result
            new_start = old_end + timedelta(days=1)
            new_end = new_start + relativedelta(months=periode_bulan)

            # Ambil id_adopter
            cursor.execute("SELECT id_adopter FROM SIZOPI.adopter WHERE username_adopter = %s", [username])
            id_adopter = cursor.fetchone()[0]

            # Insert periode baru
            cursor.execute("""
                INSERT INTO SIZOPI.adopsi (
                    id_adopter, id_hewan, status_pembayaran,
                    tgl_mulai_adopsi, tgl_berhenti_adopsi, kontribusi_finansial
                )
                VALUES (%s, %s, 'Belum', %s, %s, %s)
            """, [id_adopter, id_hewan, new_start, new_end, tambahan_kontribusi])

            cursor.execute("""
                UPDATE SIZOPI.adopter
                SET total_kontribusi = total_kontribusi + %s
                WHERE id_adopter = %s
            """, [tambahan_kontribusi, id_adopter])

        print("POST:", request.POST)
        print("user_id cookie:", request.COOKIES.get("user_id"))

        return redirect("adopsi_home_adopter")
    
    print("POST:", request.POST)
    print("user_id cookie:", request.COOKIES.get("user_id"))


    return HttpResponseBadRequest("Metode tidak diperbolehkan")

@csrf_exempt
def perpanjang_adopsi_organisasi(request, id_hewan):
    if request.method == "POST":
        username = request.COOKIES.get("user_id")
        try:
            tambahan_kontribusi = int(request.POST.get("kontribusi_finansial"))
            periode_bulan = int(request.POST.get("periode_adopsi"))
        except:
            return HttpResponseBadRequest("Input tidak valid.")

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT tgl_mulai_adopsi, tgl_berhenti_adopsi
                FROM SIZOPI.adopsi a
                JOIN SIZOPI.adopter ad ON a.id_adopter = ad.id_adopter
                WHERE ad.username_adopter = %s AND a.id_hewan = %s
                ORDER BY tgl_berhenti_adopsi DESC
                LIMIT 1
            """, [username, id_hewan])
            result = cursor.fetchone()

            if not result:
                return HttpResponseBadRequest("Data adopsi tidak ditemukan.")

            old_start, old_end = result
            new_start = old_end + timedelta(days=1)
            new_end = new_start + relativedelta(months=periode_bulan)

            cursor.execute("SELECT id_adopter FROM SIZOPI.adopter WHERE username_adopter = %s", [username])
            id_adopter = cursor.fetchone()[0]

            cursor.execute("""
                INSERT INTO SIZOPI.adopsi (
                    id_adopter, id_hewan, status_pembayaran,
                    tgl_mulai_adopsi, tgl_berhenti_adopsi, kontribusi_finansial
                )
                VALUES (%s, %s, 'Belum', %s, %s, %s)
            """, [id_adopter, id_hewan, new_start, new_end, tambahan_kontribusi])

            cursor.execute("""
                UPDATE SIZOPI.adopter
                SET total_kontribusi = total_kontribusi + %s
                WHERE id_adopter = %s
            """, [tambahan_kontribusi, id_adopter])

        return redirect("adopsi_home_adopter")

    return HttpResponseBadRequest("Metode tidak diperbolehkan")
