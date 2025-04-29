from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum
from django.utils import timezone
from .models import Adopter, Adopsi

def adopter_list(request):
    # Ambil semua adopter
    adopters = Adopter.objects.all()

    # Hitung top 5 adopter berdasarkan kontribusi dalam 1 tahun terakhir
    one_year_ago = timezone.now().date() - timezone.timedelta(days=365)
    top_adopters = (
        Adopsi.objects.filter(tgl_mulai_adopsi__gte=one_year_ago, status_pembayaran='Lunas')
        .values('id_adopter', 'id_adopter__username_adopter')
        .annotate(total=Sum('kontribusi_finansial'))
        .order_by('-total')[:5]
    )

    context = {
        'adopters': adopters,
        'top_adopters': top_adopters,
    }
    return render(request, 'adopsi/adopter_list.html', context)

def adopter_detail(request, id_adopter):
    # Ambil adopter berdasarkan ID
    adopter = get_object_or_404(Adopter, id_adopter=id_adopter)

    # Ambil semua riwayat adopsi yang pembayarannya sudah lunas
    adopsi_list = Adopsi.objects.filter(id_adopter=adopter, status_pembayaran='Lunas')

    context = {
        'adopter': adopter,
        'adopsi_list': adopsi_list,
        'today': timezone.now().date(),
    }
    return render(request, 'adopsi/adopter_detail.html', context)

def delete_adopter(request, id_adopter):
    adopter = get_object_or_404(Adopter, id_adopter=id_adopter)
    adopter.delete()
    return redirect('adopter_list')

def delete_adopsi(request, id_adopter, id_hewan, tgl_mulai_adopsi):
    # Cari adopsi berdasarkan primary key composite
    adopsi = get_object_or_404(
        Adopsi,
        id_adopter=id_adopter,
        id_hewan=id_hewan,
        tgl_mulai_adopsi=tgl_mulai_adopsi
    )
    if adopsi.tgl_berhenti_adopsi < timezone.now().date():
        adopsi.delete()
    return redirect('adopter_detail', id_adopter=id_adopter)

def adopsi_home(request):
    return render(request, 'adopsi/adopsi_home.html')

def form_individu(request):
    return render(request, 'adopsi/form_adopsi_individu.html')

def form_organisasi(request):
    return render(request, 'adopsi/form_adopsi_organisasi.html')

def adopter_home(request):
    return render(request, 'adopsi/adopsi_home_adopter.html')
