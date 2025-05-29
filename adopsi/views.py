from django.shortcuts import render, redirect
from django.db import connection, transaction
from django.utils import timezone
from datetime import timedelta
from django.http import Http404, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt  
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
    return render(request, 'adopsi/adopsi_home.html', {'animals': animals})



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
        if new_status == 'Lunas':
            new_status_db = 'Lunas'
        else:
            new_status_db = 'Belum'
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE SIZOPI.adopsi 
                SET status_pembayaran = %s 
                WHERE id_hewan = %s
            """, [new_status_db, id_hewan])
        return redirect('adopsi_home')
    raise Http404("Invalid request")

def hentikan_adopsi(request, id_hewan):
    with connection.cursor() as cursor:
        cursor.execute("""
            DELETE FROM SIZOPI.adopsi
            WHERE id_hewan = %s
        """, [str(id_hewan)])

    return redirect('adopsi_home') 

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
        kontribusi = request.POST.get("kontribusi_finansial")
        periode_bulan = int(request.POST.get("periode_adopsi"))

        tgl_mulai = timezone.now().date()
        tgl_berhenti = tgl_mulai + relativedelta(months=periode_bulan)

        with connection.cursor() as cursor:
            id_adopter = str(uuid.uuid4())

            cursor.execute("""
                INSERT INTO ADOPTER (username_adopter, id_adopter, total_kontribusi)
                VALUES (%s, %s, %s)
                ON CONFLICT (username_adopter) DO NOTHING
            """, [username, id_adopter, kontribusi])

            if cursor.rowcount == 0:
                cursor.execute("SELECT id_adopter FROM ADOPTER WHERE username_adopter = %s", [username])
                id_adopter = cursor.fetchone()[0]

            cursor.execute("""
                INSERT INTO ADOPSI (
                    id_adopter, id_hewan, status_pembayaran,
                    tgl_mulai_adopsi, tgl_berhenti_adopsi, kontribusi_finansial
                )
                VALUES (%s, %s, %s, %s, %s, %s)
            """, [
                id_adopter, id_hewan, "Belum",
                tgl_mulai, tgl_berhenti, kontribusi
            ])

        return redirect("adopsi_home")

@csrf_exempt
def submit_adopsi_organisasi(request):
    if request.method == "POST":
        try:
            username = request.POST.get("username")
            npp = request.POST.get("npp")
            nama_organisasi = request.POST.get("nama_organisasi")
            id_hewan = request.POST.get("id_hewan")
            kontribusi = int(request.POST.get("kontribusi"))
            periode = int(request.POST.get("periode"))

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