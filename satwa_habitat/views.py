from django.shortcuts import render, redirect, get_object_or_404
from django.db import connection
from .forms import HabitatForm, HewanForm
import uuid
from django.shortcuts import render, redirect
from django.db import DatabaseError, IntegrityError
from django.contrib import messages
import uuid
from django.shortcuts import redirect
from django.contrib import messages

def role_required(allowed_roles):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            user_role = request.COOKIES.get('user_role')
            if user_role not in allowed_roles:
                messages.error(request, "Anda tidak memiliki akses ke halaman ini.")
                return redirect('dashboard')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def fetch_all(query, params=None):
    with connection.cursor() as cursor:
        cursor.execute(query, params or [])
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

def fetch_one(query, params=None):
    with connection.cursor() as cursor:
        cursor.execute(query, params or [])
        row = cursor.fetchone()
        if row is None:
            return None
        columns = [col[0] for col in cursor.description]
        return dict(zip(columns, row))

def execute(query, params=None):
    with connection.cursor() as cursor:
        cursor.execute(query, params or [])


@role_required(['penjaga_hewan', 'staf_admin'])
def habitat_list(request):
    habitats = fetch_all("SELECT * FROM habitat")
    return render(request, 'habitat_list.html', {'habitats': habitats})


@role_required(['penjaga_hewan', 'staf_admin'])
def habitat_create(request):
    if request.method == 'POST':
        form = HabitatForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            execute(
                "INSERT INTO habitat (nama, luas_area, kapasitas, status) VALUES (%s, %s, %s, %s)",
                [data['nama'], data['luas_area'], data['kapasitas'], data['status']]
            )
            return redirect('habitat_list')
    else:
        form = HabitatForm()
    return render(request, 'habitat_form.html', {'form': form, 'title': 'Tambah Habitat'})


@role_required(['penjaga_hewan', 'staf_admin'])
def habitat_update(request, pk):
    habitat = fetch_one("SELECT * FROM habitat WHERE nama = %s", [pk])
    if habitat is None:
        return render(request, '404.html')

    if request.method == 'POST':
        form = HabitatForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            execute(
                "UPDATE habitat SET luas_area = %s, kapasitas = %s, status = %s WHERE nama = %s",
                [data['luas_area'], data['kapasitas'], data['status'], pk]
            )
            return redirect('habitat_list')
    else:
        form = HabitatForm(initial=habitat)
    return render(request, 'habitat_form.html', {'form': form, 'title': 'Edit Habitat'})


@role_required(['penjaga_hewan', 'staf_admin'])
def habitat_delete(request, pk):
    execute("DELETE FROM habitat WHERE nama = %s", [pk])
    return redirect('habitat_list')


@role_required(['penjaga_hewan', 'staf_admin'])
def habitat_detail(request, pk):
    habitat = fetch_one("SELECT * FROM habitat WHERE nama = %s", [pk])
    if habitat is None:
        return render(request, '404.html')  # or raise 404
    hewans = fetch_all("SELECT * FROM hewan WHERE nama_habitat = %s", [pk])
    return render(request, 'habitat_detail.html', {
        'habitat': habitat,
        'hewans': hewans
    })

@role_required(['dokter_hewan', 'penjaga_hewan', 'staf_admin'])
def hewan_list(request):
    hewans = fetch_all("""
        SELECT h.*, hb.nama as habitat_nama
        FROM hewan h
        LEFT JOIN habitat hb ON h.nama_habitat = hb.nama
    """)
    return render(request, 'hewan_list.html', {'hewans': hewans})

@role_required(['dokter_hewan', 'penjaga_hewan', 'staf_admin'])
def hewan_create(request):
    if request.method == 'POST':
        form = HewanForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            try:
                id_hewan = str(uuid.uuid4())
                execute("""
                    INSERT INTO hewan (id, nama, spesies, asal_hewan, tanggal_lahir, status_kesehatan, nama_habitat, url_foto)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, [
                    id_hewan,
                    data.get('nama'),
                    data['spesies'],
                    data['asal_hewan'],
                    data.get('tanggal_lahir'),
                    data['status_kesehatan'],
                    data['nama_habitat'],
                    data['url_foto']
                ])
                messages.success(request, 'Data satwa berhasil ditambahkan.')
                return redirect('hewan_list')
            except (DatabaseError, IntegrityError) as e:
                form.add_error(None, str(e))
    else:
        form = HewanForm()

    return render(request, 'hewan_form.html', {'form': form, 'title': 'Tambah Satwa'})

@role_required(['dokter_hewan', 'penjaga_hewan', 'staf_admin'])
def hewan_update(request, pk):
    hewan = fetch_one("SELECT * FROM hewan WHERE id = %s", [pk])
    if hewan is None:
        return render(request, '404.html')

    if request.method == 'POST':
        form = HewanForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            execute("""
                UPDATE hewan
                SET nama = %s, spesies = %s, asal_hewan = %s, tanggal_lahir = %s,
                    status_kesehatan = %s, nama_habitat = %s, url_foto = %s
                WHERE id = %s
            """, [
                data.get('nama'),
                data['spesies'],
                data['asal_hewan'],
                data.get('tanggal_lahir'),
                data['status_kesehatan'],
                data['nama_habitat'],
                data['url_foto'],
                pk
            ])
            return redirect('hewan_list')
    else:
        form = HewanForm(initial=hewan)
    return render(request, 'hewan_form.html', {'form': form, 'title': 'Edit Satwa'})

@role_required(['dokter_hewan', 'penjaga_hewan', 'staf_admin'])
def hewan_delete(request, pk):
    execute("DELETE FROM hewan WHERE id = %s", [pk])
    return redirect('hewan_list')
