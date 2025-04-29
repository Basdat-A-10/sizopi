from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.db import connection
from django.contrib.auth.hashers import check_password, make_password
import uuid
import datetime

def get_user_by_email(email):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT username, email, password, nama_depan, nama_tengah, nama_belakang, no_telepon
            FROM SIZOPI.PENGGUNA
            WHERE email = %s
        """, [email])
        user = cursor.fetchone()
        
        if user:
            user_data = {
                'username': user[0],
                'email': user[1],
                'password': user[2],
                'nama_depan': user[3],
                'nama_tengah': user[4],
                'nama_belakang': user[5],
                'no_telepon': user[6],
            }
            user_data['role'] = get_role_by_username(user[0])
            return user_data
    return None

def get_user_by_username(username):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT username, email, password, nama_depan, nama_tengah, nama_belakang, no_telepon
            FROM SIZOPI.PENGGUNA
            WHERE username = %s
        """, [username])
        user = cursor.fetchone()
        
        if user:
            user_data = {
                'username': user[0],
                'email': user[1],
                'password': user[2],
                'nama_depan': user[3],
                'nama_tengah': user[4],
                'nama_belakang': user[5],
                'no_telepon': user[6],
            }
            # Get role
            user_data['role'] = get_role_by_username(user[0])
            return user_data
    return None

def get_role_by_username(username):
    with connection.cursor() as cursor:
        # Check if user is dokter_hewan
        cursor.execute("SELECT 1 FROM SIZOPI.DOKTER_HEWAN WHERE username_DH = %s", [username])
        if cursor.fetchone():
            return 'dokter_hewan'
        
        # Check if user is penjaga_hewan
        cursor.execute("SELECT 1 FROM SIZOPI.PENJAGA_HEWAN WHERE username_jh = %s", [username])
        if cursor.fetchone():
            return 'penjaga_hewan'
        
        # Check if user is pelatih_hewan
        cursor.execute("SELECT 1 FROM SIZOPI.PELATIH_HEWAN WHERE username_lh = %s", [username])
        if cursor.fetchone():
            return 'pelatih_hewan'
        
        # Check if user is staf_admin
        cursor.execute("SELECT 1 FROM SIZOPI.STAF_ADMIN WHERE username_sa = %s", [username])
        if cursor.fetchone():
            return 'staf_admin'
        
        # Check if user is pengunjung_adopter
        cursor.execute("""
            SELECT 1 FROM SIZOPI.PENGUNJUNG p
            JOIN SIZOPI.ADOPTER a ON p.username_P = a.username_adopter
            WHERE p.username_P = %s
        """, [username])
        if cursor.fetchone():
            return 'pengunjung_adopter'
        
        # Check if user is regular pengunjung
        cursor.execute("SELECT 1 FROM SIZOPI.PENGUNJUNG WHERE username_P = %s", [username])
        if cursor.fetchone():
            return 'pengunjung'
        
        # Default role
        return None

# View untuk login
def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        user = get_user_by_email(email)
        
        if user and user['password'] == password:  # In production, use check_password()
            response = redirect('dashboard')
            
            max_age = 7 * 24 * 60 * 60  # 7 days
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
        if not nama_tengah:
            nama_tengah = None
        nama_belakang = request.POST.get('nama_belakang')
        no_telepon = request.POST.get('no_telepon')
        
        if password != password_confirmation:
            messages.error(request, "Password dan konfirmasi password tidak sama.")
            return render(request, 'authentication/register.html')
        
        existing_user = get_user_by_email(email)
        if existing_user:
            messages.error(request, "Email sudah terdaftar.")
            return render(request, 'authentication/register.html')
        
        existing_username = get_user_by_username(username)
        if existing_username:
            messages.error(request, "Username sudah digunakan.")
            return render(request, 'authentication/register.html')
        
        try:
            # Insert new user into PENGGUNA table
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO SIZOPI.PENGGUNA 
                    (username, email, password, nama_depan, nama_tengah, nama_belakang, no_telepon)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, [username, email, password, nama_depan, nama_tengah, nama_belakang, no_telepon])
                
                # Insert into PENGUNJUNG table (by default all new users are pengunjung)
                today = datetime.date.today()
                cursor.execute("""
                    INSERT INTO SIZOPI.PENGUNJUNG 
                    (username_P, alamat, tgl_lahir)
                    VALUES (%s, %s, %s)
                """, [username, 'Belum diisi', today])
            
            messages.success(request, "Registrasi berhasil! Silakan login.")
            return redirect('login')
        
        except Exception as e:
            messages.error(request, f"Terjadi kesalahan saat registrasi: {str(e)}")
            return render(request, 'authentication/register.html')
    
    return render(request, 'authentication/register.html')

def profile_view(request):
    if 'user_id' not in request.COOKIES:
        messages.error(request, "Silakan login terlebih dahulu.")
        return redirect('login')
    
    username = request.COOKIES.get('user_id')
    user = get_user_by_username(username)
    user_role = request.COOKIES.get('user_role')
    
    # Get additional data based on role
    additional_data = {}
    with connection.cursor() as cursor:
        if user_role == 'dokter_hewan':
            cursor.execute("SELECT no_STR FROM SIZOPI.DOKTER_HEWAN WHERE username_DH = %s", [username])
            dh_data = cursor.fetchone()
            if dh_data:
                additional_data['nomor_sertifikasi'] = dh_data[0]  
            # Get spesialisasi
            cursor.execute("SELECT nama_spesialisasi FROM SIZOPI.SPESIALISASI WHERE username_SH = %s", [username])
            spesialisasi_list = cursor.fetchall()
            additional_data['spesialisasi'] = [spec[0] for spec in spesialisasi_list]
        
        elif user_role == 'pengunjung' or user_role == 'pengunjung_adopter':
            cursor.execute("SELECT alamat, tgl_lahir FROM SIZOPI.PENGUNJUNG WHERE username_P = %s", [username])
            pengunjung_data = cursor.fetchone()
            if pengunjung_data:
                additional_data['alamat'] = pengunjung_data[0]
                additional_data['tgl_lahir'] = pengunjung_data[1]
            
            if user_role == 'pengunjung_adopter':
                cursor.execute("SELECT id_adopter, total_kontribusi FROM SIZOPI.ADOPTER WHERE username_adopter = %s", [username])
                adopter_data = cursor.fetchone()
                if adopter_data:
                    additional_data['id_adopter'] = adopter_data[0]
                    additional_data['total_kontribusi'] = adopter_data[1]
        
        elif user_role in ['penjaga_hewan', 'pelatih_hewan', 'staf_admin']:
            # Tentukan kolom yang sesuai berdasarkan role
            if user_role == 'penjaga_hewan':
                id_column = 'username_jh'
                table_name = 'PENJAGA_HEWAN'
            elif user_role == 'pelatih_hewan':
                id_column = 'username_lh'
                table_name = 'PELATIH_HEWAN'
            else:  # staf_admin
                id_column = 'username_sa'
                table_name = 'STAF_ADMIN'
                
            cursor.execute(f"SELECT id_staf FROM SIZOPI.{table_name} WHERE {id_column} = %s", [username])
            staff_data = cursor.fetchone()
            if staff_data:
                additional_data['id_staf'] = staff_data[0]
    
    # Gabungkan data user dan additional_data
    user.update(additional_data)
    
    if request.method == 'POST':
        email = request.POST.get('email')
        nama_depan = request.POST.get('nama_depan')
        nama_tengah = request.POST.get('nama_tengah', '')
        if not nama_tengah:
            nama_tengah = None
        nama_belakang = request.POST.get('nama_belakang')
        no_telepon = request.POST.get('no_telepon')
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE SIZOPI.PENGGUNA 
                    SET email = %s, nama_depan = %s, nama_tengah = %s, nama_belakang = %s, no_telepon = %s
                    WHERE username = %s
                """, [email, nama_depan, nama_tengah, nama_belakang, no_telepon, username])
                
                # For pengunjung role
                if user_role in ['pengunjung', 'pengunjung_adopter']:
                    alamat = request.POST.get('alamat', '')
                    tanggal_lahir = request.POST.get('tanggal_lahir', '')
                    if tanggal_lahir:
                        cursor.execute("""
                            UPDATE SIZOPI.PENGUNJUNG 
                            SET alamat = %s, tgl_lahir = %s
                            WHERE username_P = %s
                        """, [alamat, tanggal_lahir, username])
                    else:
                        cursor.execute("""
                            UPDATE SIZOPI.PENGUNJUNG 
                            SET alamat = %s
                            WHERE username_P = %s
                        """, [alamat, username])
            
            if nama_tengah:
                user_fullname = f"{nama_depan} {nama_tengah} {nama_belakang}"
            else:
                user_fullname = f"{nama_depan} {nama_belakang}"
            
            response = redirect('profile')
            response.set_cookie('user_fullname', user_fullname)
            response.set_cookie('user_email', email)
            
            messages.success(request, "Profil berhasil diperbarui!")
            return response
        
        except Exception as e:
            messages.error(request, f"Terjadi kesalahan saat memperbarui profil: {str(e)}")
    
    context = {
        'user_id': username,
        'user_fullname': request.COOKIES.get('user_fullname'),
        'user_role': user_role,
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
        
        if user['password'] != old_password:
            messages.error(request, "Password lama tidak sesuai.")
            return redirect('change_password')
        
        if new_password != confirm_password:
            messages.error(request, "Password baru dan konfirmasi password tidak sama.")
            return redirect('change_password')
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE SIZOPI.PENGGUNA 
                    SET password = %s
                    WHERE username = %s
                """, [new_password, username])
            
            messages.success(request, "Password berhasil diubah!")
            return redirect('profile')
        
        except Exception as e:
            messages.error(request, f"Terjadi kesalahan saat mengubah password: {str(e)}")
    
    context = {
        'user_id': username,
        'user_fullname': request.COOKIES.get('user_fullname'),
        'user_role': request.COOKIES.get('user_role')
    }
    
    return render(request, 'authentication/change_password.html', context)