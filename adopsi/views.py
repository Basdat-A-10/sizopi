from django.shortcuts import render, redirect
from django.db import connection
from django.utils import timezone
from datetime import timedelta
from django.http import Http404

def dictfetchall(cursor):
    "Return all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def adopter_list(request):
    with connection.cursor() as cursor:
        # Get all adopters
        cursor.execute("SELECT * FROM SIZOPI.adopter")
        adopters = dictfetchall(cursor)

        # Top 5 adopters by total contribution (lunas) in the last year
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
    return render(request, 'adopsi/adopsi_home.html')

def form_individu(request):
    return render(request, 'adopsi/form_adopsi_individu.html')

def form_organisasi(request):
    return render(request, 'adopsi/form_adopsi_organisasi.html')

def adopter_home(request):
    return render(request, 'adopsi/adopsi_home_adopter.html')
