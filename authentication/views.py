from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from .dummy_data import get_user_by_email, get_user_by_username, get_role_by_username

# View untuk login
def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        user = get_user_by_email(email)
        
        if user and user['password'] == password:
            response = redirect('dashboard')
            
            max_age = 7 * 24 * 60 * 60 
            response.set_cookie('user_id', user['username'], max_age=max_age)
            response.set_cookie('user_email', user['email'], max_age=max_age)
            response.set_cookie('user_role', user['role'], max_age=max_age)
            
            if user['nama_tengah']:
                user_fullname = f"{user['nama_depan']} {user['nama_tengah']} {user['nama_belakang']}"
            else:
                user_fullname = f"{user['nama_depan']} {user['nama_belakang']}"
                
            response.set_cookie('user_fullname', user_fullname, max_age=max_age)
            
            messages.success(request, f"Selamat datang, {user_fullname}!")
            return response
        else:
            messages.error(request, "Email atau password tidak valid.")
    
    return render(request, 'authentication/login.html')

def logout_view(request):
    response = redirect('login')
    
    response.delete_cookie('user_id')
    response.delete_cookie('user_email')
    response.delete_cookie('user_fullname')
    response.delete_cookie('user_role')
    
    messages.success(request, "Anda berhasil logout.")
    return response

# View untuk halaman dashboard
def dashboard_view(request):
    if 'user_id' not in request.COOKIES:
        messages.error(request, "Silakan login terlebih dahulu.")
        return redirect('login')
    
    user_id = request.COOKIES.get('user_id')
    user_fullname = request.COOKIES.get('user_fullname')
    user_role = request.COOKIES.get('user_role')
    
    context = {
        'user_id': user_id,
        'user_fullname': user_fullname,
        'user_role': user_role
    }
    
    return render(request, 'authentication/dashboard.html', context)

# View untuk register
def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirmation = request.POST.get('password_confirmation')
        nama_depan = request.POST.get('nama_depan')
        nama_tengah = request.POST.get('nama_tengah', '')
        nama_belakang = request.POST.get('nama_belakang')
        no_telepon = request.POST.get('no_telepon')
        
        if password != password_confirmation:
            messages.error(request, "Password dan konfirmasi password tidak sama.")
            return render(request, 'authentication/register.html')
        
        existing_user = get_user_by_email(email)
        if existing_user:
            messages.error(request, "Email sudah terdaftar.")
            return render(request, 'authentication/register.html')
        
        messages.success(request, "Registrasi berhasil! Silakan login.")
        return redirect('login')
    
    return render(request, 'authentication/register.html')

def profile_view(request):
    if 'user_id' not in request.COOKIES:
        messages.error(request, "Silakan login terlebih dahulu.")
        return redirect('login')
    
    username = request.COOKIES.get('user_id')
    user = get_user_by_username(username)
    
    if request.method == 'POST':
        # Update data profil
        email = request.POST.get('email')
        nama_depan = request.POST.get('nama_depan')
        nama_tengah = request.POST.get('nama_tengah', '')
        nama_belakang = request.POST.get('nama_belakang')
        no_telepon = request.POST.get('no_telepon')
        
        # Untuk pengunjung
        alamat = request.POST.get('alamat', '')
        tanggal_lahir = request.POST.get('tanggal_lahir', '')
        
        # Untuk dokter hewan
        spesialisasi = []
        if 'spesialisasi_mamalia' in request.POST:
            spesialisasi.append('Mamalia Besar')
        if 'spesialisasi_reptil' in request.POST:
            spesialisasi.append('Reptil')
        if 'spesialisasi_burung' in request.POST:
            spesialisasi.append('Burung Eksotis')
        if 'spesialisasi_primata' in request.POST:
            spesialisasi.append('Primata')
        if 'spesialisasi_lainnya' in request.POST and request.POST.get('spesialisasi_lainnya_text'):
            spesialisasi.append(request.POST.get('spesialisasi_lainnya_text'))
        
        # Di sini seharusnya memperbarui data di database
        # Tetapi karena kita menggunakan dummy data, kita hanya akan menampilkan pesan sukses
        
        # Memperbarui cookie nama lengkap
        if nama_tengah and nama_tengah.strip():
            user_fullname = f"{nama_depan} {nama_tengah} {nama_belakang}"
        else:
            user_fullname = f"{nama_depan} {nama_belakang}"
        
        response = redirect('profile')
        response.set_cookie('user_fullname', user_fullname)
        
        messages.success(request, "Profil berhasil diperbarui!")
        return response
        
    context = {
        'user_id': username,
        'user_fullname': request.COOKIES.get('user_fullname'),
        'user_role': request.COOKIES.get('user_role'),
        'user': user
    }
    
    return render(request, 'authentication/profile.html', context)

def change_password_view(request):
    if 'user_id' not in request.COOKIES:
        messages.error(request, "Silakan login terlebih dahulu.")
        return redirect('login')
    
    username = request.COOKIES.get('user_id')
    user = get_user_by_username(username)
    
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        # Validasi password lama
        if user['password'] != old_password:
            messages.error(request, "Password lama tidak sesuai.")
            return redirect('change_password')
        
        # Validasi konfirmasi password
        if new_password != confirm_password:
            messages.error(request, "Password baru dan konfirmasi password tidak sama.")
            return redirect('change_password')
        
        # Di sini seharusnya memperbarui password di database
        # Tetapi karena kita menggunakan dummy data, kita hanya akan menampilkan pesan sukses
        
        messages.success(request, "Password berhasil diubah!")
        return redirect('profile')
    
    context = {
        'user_id': username,
        'user_fullname': request.COOKIES.get('user_fullname'),
        'user_role': request.COOKIES.get('user_role')
    }
    
    return render(request, 'authentication/change_password.html', context)