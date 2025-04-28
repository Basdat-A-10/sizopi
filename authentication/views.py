from django.shortcuts import render, redirect
from django.db import connection
from django.http import HttpResponse
from django.contrib import messages

# View untuk login
def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        with connection.cursor() as cursor:
            cursor.execute("SET search_path TO SIZOPI;")
            cursor.execute("""
                SELECT 
                    username,
                    email,
                    nama_depan,
                    nama_tengah,
                    nama_belakang
                FROM PENGGUNA
                WHERE email = %s AND password = %s
            """, [email, password])
            
            user = cursor.fetchone()
            
            if user:
                # Jika user ditemukan, buat response redirect
                response = redirect('dashboard')
                
                # Simpan informasi user di cookie
                response.set_cookie('user_id', user[0])
                response.set_cookie('user_email', user[1])
                
                # Membuat nama lengkap
                if user[3]:  # Jika nama_tengah ada
                    user_fullname = f"{user[2]} {user[3]} {user[4]}"
                else:
                    user_fullname = f"{user[2]} {user[4]}"
                    
                response.set_cookie('user_fullname', user_fullname)
                
                return response
            else:
                # Jika login gagal, tampilkan pesan error
                error_message = "Email atau password tidak valid."
                return render(request, 'authentication/login.html', {'error_message': error_message})
    
    return render(request, 'authentication/login.html')

# View untuk logout
def logout_view(request):
    # Buat response redirect
    response = redirect('login')
    
    # Hapus cookie
    response.delete_cookie('user_id')
    response.delete_cookie('user_email')
    response.delete_cookie('user_fullname')
    
    return response

# View untuk halaman dashboard
def dashboard_view(request):
    # Cek apakah user sudah login dengan memeriksa cookie
    if 'user_id' not in request.COOKIES:
        return redirect('login')
    
    # Ambil informasi user dari cookie
    user_id = request.COOKIES.get('user_id')
    user_fullname = request.COOKIES.get('user_fullname')
    
    # Render dashboard dengan informasi user
    return render(request, 'authentication/dashboard.html', {
        'user_id': user_id,
        'user_fullname': user_fullname
    })

# View untuk register (opsional, jika dibutuhkan)
def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        nama_depan = request.POST.get('nama_depan')
        nama_tengah = request.POST.get('nama_tengah', '')  # Opsional
        nama_belakang = request.POST.get('nama_belakang')
        no_telepon = request.POST.get('no_telepon')
        
        # Tidak perlu hash password karena di database disimpan plaintext
        
        # Validasi data (bisa ditambahkan sesuai kebutuhan)
        
        with connection.cursor() as cursor:
            cursor.execute("SET search_path TO SIZOPI;")
            
            # Cek apakah username/email sudah terdaftar
            cursor.execute("SELECT COUNT(*) FROM PENGGUNA WHERE username = %s OR email = %s", 
                           [username, email])
            if cursor.fetchone()[0] > 0:
                messages.error(request, "Username atau email sudah terdaftar.")
                return render(request, 'authentication/register.html')
            
            # Insert user baru
            cursor.execute("""
                INSERT INTO PENGGUNA 
                    (username, email, password, nama_depan, nama_tengah, nama_belakang, no_telepon)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, [username, email, password, nama_depan, nama_tengah, nama_belakang, no_telepon])
            
            messages.success(request, "Registrasi berhasil! Silakan login.")
            return redirect('login')
    
    return render(request, 'authentication/register.html')