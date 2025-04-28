from django.shortcuts import render, redirect, get_object_or_404
from .models import Habitat, Hewan
from .forms import HabitatForm, HewanForm

def habitat_list(request):
    habitats = Habitat.objects.all()
    return render(request, 'habitat_list.html', {'habitats': habitats})

def habitat_create(request):
    if request.method == 'POST':
        form = HabitatForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('habitat_list')
    else:
        form = HabitatForm()
    return render(request, 'habitat_form.html', {'form': form, 'title': 'Tambah Habitat'})

def habitat_update(request, pk):
    habitat = get_object_or_404(Habitat, pk=pk)
    if request.method == 'POST':
        form = HabitatForm(request.POST, instance=habitat)
        if form.is_valid():
            form.save()
            return redirect('habitat_list')
    else:
        form = HabitatForm(instance=habitat)
    return render(request, 'habitat_form.html', {'form': form, 'title': 'Edit Habitat'})

def habitat_delete(request, pk):
    habitat = get_object_or_404(Habitat, pk=pk)
    habitat.delete()
    return redirect('habitat_list')

def habitat_detail(request, pk):
    habitat = get_object_or_404(Habitat, pk=pk)
    hewans = Hewan.objects.filter(nama_habitat=habitat)
    return render(request, 'habitat_detail.html', {
        'habitat': habitat,
        'hewans': hewans
    })

def hewan_list(request):
    hewans = Hewan.objects.select_related('nama_habitat').all()
    return render(request, 'hewan_list.html', {'hewans': hewans})

def hewan_create(request):
    if request.method == 'POST':
        form = HewanForm(request.POST)
        if form.is_valid():
            # prevent duplicate based on nama_individu + spesies
            nama_individu = form.cleaned_data.get('nama_individu')
            spesies = form.cleaned_data['spesies']
            existing = Hewan.objects.filter(nama_individu=nama_individu, spesies=spesies).exists()
            if not existing:
                form.save()
                return redirect('hewan_list')
            else:
                form.add_error(None, 'Data hewan ini sudah terdaftar.')
    else:
        form = HewanForm()
    return render(request, 'hewan_form.html', {'form': form, 'title': 'Tambah Satwa'})

def hewan_update(request, pk):
    hewan = get_object_or_404(Hewan, pk=pk)
    if request.method == 'POST':
        form = HewanForm(request.POST, instance=hewan)
        if form.is_valid():
            form.save()
            return redirect('hewan_list')
    else:
        form = HewanForm(instance=hewan)
    return render(request, 'hewan_form.html', {'form': form, 'title': 'Edit Satwa'})

def hewan_delete(request, pk):
    hewan = get_object_or_404(Hewan, pk=pk)
    hewan.delete()
    return redirect('hewan_list')
