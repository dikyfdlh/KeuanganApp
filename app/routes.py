from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from .models import db, BiayaTetap, BiayaVariabel, Pendapatan, User, Produk, Penjualan, DetailPenjualan, Menu, CashFlow, KategoriCashFlow
from datetime import datetime, timedelta
from sqlalchemy import func, extract, desc
import calendar
from .utils import utc_to_local, format_datetime, get_current_local_time, local_to_utc
import pytz

main = Blueprint('main', __name__)

# Fungsi untuk memeriksa apakah user adalah admin
def admin_required(f):
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Silakan login terlebih dahulu.', 'warning')
            return redirect(url_for('main.login'))
        
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin():
            flash('Anda tidak memiliki akses ke halaman ini.', 'danger')
            return redirect(url_for('main.dashboard'))
            
        return f(*args, **kwargs)
    
    # Rename the function to avoid naming conflicts
    decorated_function.__name__ = f.__name__
    return decorated_function

# Route root dialihkan ke login
@main.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('main.login'))

# Login
@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['namalengkap'] = user.namalengkap
            session['role'] = user.role
            
            # Update last login time dengan waktu UTC
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            flash('Login berhasil!', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Username atau password salah.', 'danger')
    return render_template('login.html')

# Register
@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        namalengkap = request.form['namalengkap']
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('Username atau email sudah digunakan.', 'danger')
            return redirect(url_for('main.register'))

        # Jika belum ada user, jadikan admin
        is_first_user = User.query.count() == 0
        role = 'admin' if is_first_user else 'user'
        
        user = User(namalengkap=namalengkap, username=username, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Pendaftaran berhasil! Silakan login.', 'success')
        return redirect(url_for('main.login'))
    return render_template('register.html')

# Logout
@main.route('/logout')
def logout():
    session.clear()
    flash('Anda telah logout.', 'info')
    return redirect(url_for('main.login'))

# Dashboard
@main.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        flash('Silakan login terlebih dahulu.', 'warning')
        return redirect(url_for('main.login'))
    
    # Pastikan data memiliki nilai default untuk anggaran
    for bt in BiayaTetap.query.all():
        if not hasattr(bt, 'anggaran') or bt.anggaran is None:
            bt.anggaran = bt.jumlah
            bt.periode = 'bulanan'
            bt.keterangan = ''
    
    for bv in BiayaVariabel.query.all():
        if not hasattr(bv, 'anggaran') or bv.anggaran is None:
            bv.anggaran = bv.jumlah
            bv.periode = 'bulanan'
            bv.keterangan = ''
    
    for pd in Pendapatan.query.all():
        if not hasattr(pd, 'anggaran') or pd.anggaran is None:
            pd.anggaran = pd.jumlah
            pd.periode = 'bulanan'
            pd.keterangan = ''
    
    db.session.commit()
    
    # Data Keuangan
    total_bt = sum([b.jumlah for b in BiayaTetap.query.all()])
    total_bv = sum([b.jumlah for b in BiayaVariabel.query.all()])
    total_pd = sum([p.jumlah for p in Pendapatan.query.all()])
    laba_bersih = total_pd - (total_bt + total_bv)
    
    # Data Anggaran
    total_anggaran_bt = sum([b.anggaran for b in BiayaTetap.query.all()])
    total_anggaran_bv = sum([b.anggaran for b in BiayaVariabel.query.all()])
    total_anggaran_pd = sum([p.anggaran for p in Pendapatan.query.all()])
    anggaran_laba = total_anggaran_pd - (total_anggaran_bt + total_anggaran_bv)
    
    # Persentase Realisasi
    realisasi_bt = (total_bt / total_anggaran_bt * 100) if total_anggaran_bt > 0 else 0
    realisasi_bv = (total_bv / total_anggaran_bv * 100) if total_anggaran_bv > 0 else 0
    realisasi_pd = (total_pd / total_anggaran_pd * 100) if total_anggaran_pd > 0 else 0
    realisasi_laba = (laba_bersih / anggaran_laba * 100) if anggaran_laba > 0 else 0
    
    # Data Cash Flow Terbaru
    recent_cashflow = CashFlow.query.order_by(CashFlow.tanggal.desc()).limit(5).all()
    
    # Total Cash Flow
    total_pemasukan = db.session.query(func.sum(CashFlow.jumlah)).filter(CashFlow.jenis == 'pemasukan').scalar() or 0
    total_pengeluaran = db.session.query(func.sum(CashFlow.jumlah)).filter(CashFlow.jenis == 'pengeluaran').scalar() or 0
    saldo_cashflow = total_pemasukan - total_pengeluaran
    
    # Data Produk
    total_produk = Produk.query.count()
    total_stok = db.session.query(func.sum(Produk.stok)).scalar() or 0
    produk_habis = Produk.query.filter(Produk.stok == 0).count()
    
    # Produk Terlaris
    top_products = db.session.query(
        Produk.nama, 
        func.sum(DetailPenjualan.jumlah).label('total_sold')
    ).join(DetailPenjualan, Produk.id == DetailPenjualan.produk_id)\
     .group_by(Produk.id)\
     .order_by(func.sum(DetailPenjualan.jumlah).desc())\
     .limit(5).all()
    
    # Data untuk grafik perbandingan anggaran vs realisasi
    anggaran_realisasi = {
        'labels': ['Pendapatan', 'Biaya Tetap', 'Biaya Variabel', 'Laba Bersih'],
        'anggaran': [total_anggaran_pd, total_anggaran_bt, total_anggaran_bv, anggaran_laba],
        'realisasi': [total_pd, total_bt, total_bv, laba_bersih]
    }
    
    return render_template(
        'dashboard.html', 
        total_bt=total_bt, 
        total_bv=total_bv, 
        total_pd=total_pd, 
        laba=laba_bersih,
        total_anggaran_bt=total_anggaran_bt,
        total_anggaran_bv=total_anggaran_bv,
        total_anggaran_pd=total_anggaran_pd,
        anggaran_laba=anggaran_laba,
        realisasi_bt=realisasi_bt,
        realisasi_bv=realisasi_bv,
        realisasi_pd=realisasi_pd,
        realisasi_laba=realisasi_laba,
        recent_cashflow=recent_cashflow,
        total_pemasukan=total_pemasukan,
        total_pengeluaran=total_pengeluaran,
        saldo_cashflow=saldo_cashflow,
        total_produk=total_produk,
        total_stok=total_stok,
        produk_habis=produk_habis,
        top_products=top_products,
        anggaran_realisasi=anggaran_realisasi,
        format_datetime=format_datetime
    )

# Biaya Tetap
@main.route('/biaya-tetap', methods=['GET', 'POST'])
def biaya_tetap():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    if request.method == 'POST':
        nama = request.form['nama']
        jumlah = float(request.form['jumlah'])
        anggaran = float(request.form['anggaran'])
        periode = request.form['periode']
        keterangan = request.form['keterangan']
        
        biaya = BiayaTetap(
            nama=nama, 
            jumlah=jumlah, 
            anggaran=anggaran, 
            periode=periode, 
            keterangan=keterangan
        )
        db.session.add(biaya)
        db.session.commit()
        flash('Biaya tetap berhasil ditambahkan.', 'success')
        return redirect(url_for('main.biaya_tetap'))
    
    data = BiayaTetap.query.all()
    
    # Hitung total anggaran dan realisasi
    total_anggaran = sum(getattr(item, 'anggaran', 0) for item in data)
    total_realisasi = sum(getattr(item, 'jumlah', 0) for item in data)
    selisih = total_anggaran - total_realisasi
    persentase = (total_realisasi / total_anggaran * 100) if total_anggaran > 0 else 0
    
    return render_template('biaya_tetap.html', 
                          data=data, 
                          total_anggaran=total_anggaran,
                          total_realisasi=total_realisasi,
                          selisih=selisih,
                          persentase=persentase)

# Biaya Variabel
@main.route('/biaya-variabel', methods=['GET', 'POST'])
def biaya_variabel():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    if request.method == 'POST':
        nama = request.form['nama']
        jumlah = float(request.form['jumlah'])
        anggaran = float(request.form['anggaran'])
        periode = request.form['periode']
        keterangan = request.form['keterangan']
        
        biaya = BiayaVariabel(
            nama=nama, 
            jumlah=jumlah, 
            anggaran=anggaran, 
            periode=periode, 
            keterangan=keterangan
        )
        db.session.add(biaya)
        db.session.commit()
        flash('Biaya variabel berhasil ditambahkan.', 'success')
        return redirect(url_for('main.biaya_variabel'))
    
    data = BiayaVariabel.query.all()
    
    # Hitung total anggaran dan realisasi
    total_anggaran = sum(getattr(item, 'anggaran', 0) for item in data)
    total_realisasi = sum(getattr(item, 'jumlah', 0) for item in data)
    selisih = total_anggaran - total_realisasi
    persentase = (total_realisasi / total_anggaran * 100) if total_anggaran > 0 else 0
    
    return render_template('biaya_variabel.html', 
                          data=data,
                          total_anggaran=total_anggaran,
                          total_realisasi=total_realisasi,
                          selisih=selisih,
                          persentase=persentase)

# Pendapatan
@main.route('/pendapatan', methods=['GET', 'POST'])
def pendapatan():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    if request.method == 'POST':
        sumber = request.form['sumber']
        jumlah = float(request.form['jumlah'])
        anggaran = float(request.form['anggaran'])
        periode = request.form['periode']
        keterangan = request.form['keterangan']
        
        pendapatan = Pendapatan(
            sumber=sumber, 
            jumlah=jumlah, 
            anggaran=anggaran, 
            periode=periode, 
            keterangan=keterangan
        )
        db.session.add(pendapatan)
        db.session.commit()
        flash('Pendapatan berhasil ditambahkan.', 'success')
        return redirect(url_for('main.pendapatan'))
    
    data = Pendapatan.query.all()
    
    # Hitung total anggaran dan realisasi
    total_anggaran = sum(getattr(item, 'anggaran', 0) for item in data)
    total_realisasi = sum(getattr(item, 'jumlah', 0) for item in data)
    selisih = total_realisasi - total_anggaran  # Untuk pendapatan, selisih positif adalah baik
    persentase = (total_realisasi / total_anggaran * 100) if total_anggaran > 0 else 0
    
    return render_template('pendapatan.html', 
                          data=data,
                          total_anggaran=total_anggaran,
                          total_realisasi=total_realisasi,
                          selisih=selisih,
                          persentase=persentase)

# Biaya Tetap Edit
@main.route('/biaya-tetap/edit/<int:id>', methods=['GET', 'POST'])
def editBiayaTTP(id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    item = BiayaTetap.query.get_or_404(id)
    if request.method == 'POST':
        item.nama = request.form['nama']
        item.jumlah = float(request.form['jumlah'])
        item.anggaran = float(request.form['anggaran'])
        item.periode = request.form['periode']
        item.keterangan = request.form['keterangan']
        item.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Biaya tetap berhasil diperbarui.', 'success')
        return redirect(url_for('main.biaya_tetap'))
    return render_template('editBiayaTTP.html', item=item)

# Biaya Tetap Hapus
@main.route('/biaya-tetap/delete/<int:id>', methods=['GET'])
def hapusBiayaTTP(id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    item = BiayaTetap.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('main.biaya_tetap'))

# Biaya Var Edit
@main.route('/biaya-variabel/edit/<int:id>', methods=['GET', 'POST'])
def editBiayaVar(id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    item = BiayaVariabel.query.get_or_404(id)
    if request.method == 'POST':
        item.nama = request.form['nama']
        item.jumlah = float(request.form['jumlah'])
        item.anggaran = float(request.form['anggaran'])
        item.periode = request.form['periode']
        item.keterangan = request.form['keterangan']
        item.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Biaya variabel berhasil diperbarui.', 'success')
        return redirect(url_for('main.biaya_variabel'))
    return render_template('editBiayaVar.html', item=item)

# Biaya Var Hapus
@main.route('/biaya-variabel/delete/<int:id>', methods=['GET'])
def hapusBiayaVar(id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    item = BiayaVariabel.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('main.biaya_variabel'))

# Pendapatan Edit
@main.route('/pendapatan/edit/<int:id>', methods=['GET', 'POST'])
def editPendapatan(id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    item = Pendapatan.query.get_or_404(id)
    if request.method == 'POST':
        item.sumber = request.form['sumber']
        item.jumlah = float(request.form['jumlah'])
        item.anggaran = float(request.form['anggaran'])
        item.periode = request.form['periode']
        item.keterangan = request.form['keterangan']
        item.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Pendapatan berhasil diperbarui.', 'success')
        return redirect(url_for('main.pendapatan'))
    return render_template('editPendapatan.html', item=item)

# Pendapatan Hapus
@main.route('/pendapatan/delete/<int:id>', methods=['GET'])
def hapusPendapatan(id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    item = Pendapatan.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('main.pendapatan'))

# Analisa Penjualan
@main.route('/analisa-penjualan')
def analisa_penjualan():
    if 'user_id' not in session:
        flash('Silakan login terlebih dahulu.', 'warning')
        return redirect(url_for('main.login'))
        
    # Dapatkan data untuk analisis
    total_bt = sum([b.jumlah for b in BiayaTetap.query.all()])
    total_bv = sum([b.jumlah for b in BiayaVariabel.query.all()])
    total_pd = sum([p.jumlah for p in Pendapatan.query.all()])
    laba_bersih = total_pd - (total_bt + total_bv)
    
    # Data penjualan bulanan (untuk grafik)
    current_year = datetime.now().year
    monthly_sales = []
    
    for month in range(1, 13):
        # Hitung total penjualan per bulan
        sales = db.session.query(func.sum(Penjualan.total)).filter(
            extract('year', Penjualan.tanggal) == current_year,
            extract('month', Penjualan.tanggal) == month
        ).scalar() or 0
        
        monthly_sales.append({
            'month': calendar.month_name[month],
            'sales': sales
        })
    
    # Produk terlaris
    top_products = db.session.query(
        Produk.nama, 
        func.sum(DetailPenjualan.jumlah).label('total_sold')
    ).join(DetailPenjualan, Produk.id == DetailPenjualan.produk_id)\
     .group_by(Produk.id)\
     .order_by(func.sum(DetailPenjualan.jumlah).desc())\
     .limit(5).all()
    
    # Pendapatan vs Biaya (untuk grafik)
    income_expense = {
        'pendapatan': total_pd,
        'biaya_tetap': total_bt,
        'biaya_variabel': total_bv
    }
    
    return render_template(
        'analisa_penjualan.html', 
        total_bt=total_bt, 
        total_bv=total_bv, 
        total_pd=total_pd, 
        laba=laba_bersih,
        monthly_sales=monthly_sales,
        top_products=top_products,
        income_expense=income_expense
    )

# Manajemen Produk
@main.route('/daftar-produk', methods=['GET', 'POST'])
def manajemen_produk():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
        
    if request.method == 'POST':
        kode = request.form['kode']
        nama = request.form['nama']
        deskripsi = request.form['deskripsi']
        harga_beli = float(request.form['harga_beli'])
        harga_jual = float(request.form['harga_jual'])
        stok = int(request.form['stok'])
        kategori = request.form['kategori']
        
        # Cek apakah kode produk sudah ada
        existing_product = Produk.query.filter_by(kode=kode).first()
        if existing_product:
            flash('Kode produk sudah digunakan.', 'danger')
            return redirect(url_for('main.manajemen_produk'))
        
        produk = Produk(
            kode=kode,
            nama=nama,
            deskripsi=deskripsi,
            harga_beli=harga_beli,
            harga_jual=harga_jual,
            stok=stok,
            kategori=kategori
        )
        db.session.add(produk)
        db.session.commit()
        flash('Produk berhasil ditambahkan.', 'success')
        return redirect(url_for('main.manajemen_produk'))
        
    # Ambil semua produk untuk ditampilkan
    produk_list = Produk.query.all()
    return render_template('manajemen_produk.html', produk_list=produk_list, format_datetime=format_datetime)

# Edit Produk
@main.route('/daftar-produk/edit/<int:id>', methods=['GET', 'POST'])
def edit_produk(id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
        
    produk = Produk.query.get_or_404(id)
    
    if request.method == 'POST':
        produk.kode = request.form['kode']
        produk.nama = request.form['nama']
        produk.deskripsi = request.form['deskripsi']
        produk.harga_beli = float(request.form['harga_beli'])
        produk.harga_jual = float(request.form['harga_jual'])
        produk.stok = int(request.form['stok'])
        produk.kategori = request.form['kategori']
        produk.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('Produk berhasil diperbarui.', 'success')
        return redirect(url_for('main.manajemen_produk'))
        
    return render_template('edit_produk.html', produk=produk, format_datetime=format_datetime)

# Hapus Produk
@main.route('/daftar-produk/delete/<int:id>', methods=['GET'])
def hapus_produk(id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
        
    produk = Produk.query.get_or_404(id)
    
    # Cek apakah produk sudah digunakan dalam penjualan
    used_in_sales = DetailPenjualan.query.filter_by(produk_id=id).first()
    if used_in_sales:
        flash('Produk tidak dapat dihapus karena sudah digunakan dalam transaksi penjualan.', 'danger')
        return redirect(url_for('main.manajemen_produk'))
    
    db.session.delete(produk)
    db.session.commit()
    flash('Produk berhasil dihapus.', 'success')
    return redirect(url_for('main.manajemen_produk'))

# Manajemen Pengguna (Admin only)
@main.route('/manajemen-pengguna', methods=['GET'])
@admin_required
def manajemen_pengguna():
    users = User.query.all()
    return render_template('manajemen_pengguna.html', users=users, format_datetime=format_datetime)

# Tambah Pengguna (Admin only)
@main.route('/manajemen-pengguna/tambah', methods=['POST'])
@admin_required
def tambah_pengguna():
    namalengkap = request.form['namalengkap']
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    role = request.form['role']
    
    # Cek apakah username atau email sudah ada
    existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
    if existing_user:
        flash('Username atau email sudah digunakan.', 'danger')
        return redirect(url_for('main.manajemen_pengguna'))
    
    user = User(namalengkap=namalengkap, username=username, email=email, role=role)
    user.set_password(password)
    # created_at akan otomatis menggunakan datetime.utcnow() dari model
    db.session.add(user)
    db.session.commit()
    flash('Pengguna berhasil ditambahkan.', 'success')
    return redirect(url_for('main.manajemen_pengguna'))

# Edit Pengguna (Admin only)
@main.route('/manajemen-pengguna/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_pengguna(id):
    user = User.query.get_or_404(id)
    
    if request.method == 'POST':
        user.namalengkap = request.form['namalengkap']
        user.email = request.form['email']
        user.role = request.form['role']
        
        # Update password jika diisi
        if request.form['password']:
            user.set_password(request.form['password'])
            
        db.session.commit()
        flash('Pengguna berhasil diperbarui.', 'success')
        return redirect(url_for('main.manajemen_pengguna'))
        
    return render_template('edit_pengguna.html', user=user, format_datetime=format_datetime)

# Hapus Pengguna (Admin only)
@main.route('/manajemen-pengguna/delete/<int:id>', methods=['GET'])
@admin_required
def hapus_pengguna(id):
    # Pastikan admin tidak menghapus dirinya sendiri
    if id == session.get('user_id'):
        flash('Anda tidak dapat menghapus akun Anda sendiri.', 'danger')
        return redirect(url_for('main.manajemen_pengguna'))
        
    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    flash('Pengguna berhasil dihapus.', 'success')
    return redirect(url_for('main.manajemen_pengguna'))

# Manajemen Menu (Admin only)
@main.route('/manajemen-menu', methods=['GET', 'POST'])
@admin_required
def manajemen_menu():
    if request.method == 'POST':
        nama = request.form['nama']
        url = request.form['url']
        icon = request.form['icon']
        parent_id = request.form.get('parent_id')
        urutan = int(request.form['urutan'])
        
        # Konversi parent_id ke None jika string kosong
        if parent_id == '':
            parent_id = None
        
        menu = Menu(
            nama=nama,
            url=url,
            icon=icon,
            parent_id=parent_id,
            urutan=urutan,
            is_active=True
        )
        db.session.add(menu)
        db.session.commit()
        flash('Menu berhasil ditambahkan.', 'success')
        return redirect(url_for('main.manajemen_menu'))
    
    # Ambil semua menu untuk ditampilkan
    menus = Menu.query.order_by(Menu.parent_id, Menu.urutan).all()
    
    # Ambil menu parent untuk dropdown
    parent_menus = Menu.query.filter_by(parent_id=None).all()
    
    return render_template('manajemen_menu.html', menus=menus, parent_menus=parent_menus, format_datetime=format_datetime)

# Edit Menu (Admin only)
@main.route('/manajemen-menu/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_menu(id):
    menu = Menu.query.get_or_404(id)
    
    if request.method == 'POST':
        menu.nama = request.form['nama']
        menu.url = request.form['url']
        menu.icon = request.form['icon']
        
        parent_id = request.form.get('parent_id')
        if parent_id == '':
            menu.parent_id = None
        else:
            # Pastikan menu tidak menjadi parent dari dirinya sendiri
            if int(parent_id) == id:
                flash('Menu tidak dapat menjadi parent dari dirinya sendiri.', 'danger')
                return redirect(url_for('main.edit_menu', id=id))
            menu.parent_id = parent_id
            
        menu.urutan = int(request.form['urutan'])
        menu.is_active = 'is_active' in request.form
        menu.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('Menu berhasil diperbarui.', 'success')
        return redirect(url_for('main.manajemen_menu'))
    
    # Ambil menu parent untuk dropdown
    parent_menus = Menu.query.filter(Menu.id != id, Menu.parent_id != id).all()
    
    return render_template('edit_menu.html', menu=menu, parent_menus=parent_menus, format_datetime=format_datetime)

# Hapus Menu (Admin only)
@main.route('/manajemen-menu/delete/<int:id>', methods=['GET'])
@admin_required
def hapus_menu(id):
    menu = Menu.query.get_or_404(id)
    
    # Cek apakah menu memiliki child
    has_children = Menu.query.filter_by(parent_id=id).first()
    if has_children:
        flash('Menu tidak dapat dihapus karena memiliki sub-menu.', 'danger')
        return redirect(url_for('main.manajemen_menu'))
    
    db.session.delete(menu)
    db.session.commit()
    flash('Menu berhasil dihapus.', 'success')
    return redirect(url_for('main.manajemen_menu'))

# Cash Flow
@main.route('/cashflow', methods=['GET', 'POST'])
def cashflow():
    if 'user_id' not in session:
        flash('Silakan login terlebih dahulu.', 'warning')
        return redirect(url_for('main.login'))
    
    # Filter tanggal
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    if start_date_str and end_date_str:
        try:
            # Parse tanggal dari string
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            
            # Konversi ke UTC untuk query database
            start_date = local_to_utc(start_date.replace(hour=0, minute=0, second=0))
            end_date = local_to_utc((end_date + timedelta(days=1)).replace(hour=0, minute=0, second=0))
        except ValueError:
            flash('Format tanggal tidak valid.', 'danger')
            today = get_current_local_time()
            start_date = local_to_utc(today.replace(day=1, hour=0, minute=0, second=0))
            next_month = today.replace(day=28) + timedelta(days=4)
            end_date = local_to_utc(next_month.replace(day=1, hour=0, minute=0, second=0))
    else:
        # Default: bulan ini
        today = get_current_local_time()
        start_date = local_to_utc(today.replace(day=1, hour=0, minute=0, second=0))
        next_month = today.replace(day=28) + timedelta(days=4)
        end_date = local_to_utc(next_month.replace(day=1, hour=0, minute=0, second=0))
    
    # Format untuk tampilan
    start_date_display = utc_to_local(start_date).strftime('%d-%m-%Y')
    end_date_display = utc_to_local(end_date - timedelta(seconds=1)).strftime('%d-%m-%Y')
    
    # Filter kategori
    kategori = request.args.get('kategori', '')
    jenis = request.args.get('jenis', '')
    
    # Query dasar
    query = CashFlow.query.filter(CashFlow.tanggal >= start_date, CashFlow.tanggal < end_date)
    
    # Tambahkan filter jika ada
    if kategori:
        query = query.filter(CashFlow.kategori == kategori)
    if jenis:
        query = query.filter(CashFlow.jenis == jenis)
    
    # Ambil data
    cashflow_data = query.order_by(desc(CashFlow.tanggal)).all()
    
    # Hitung total pemasukan dan pengeluaran
    total_pemasukan = sum([cf.jumlah for cf in cashflow_data if cf.jenis == 'pemasukan'])
    total_pengeluaran = sum([cf.jumlah for cf in cashflow_data if cf.jenis == 'pengeluaran'])
    saldo = total_pemasukan - total_pengeluaran
    
    # Ambil semua kategori untuk dropdown filter
    all_categories = db.session.query(CashFlow.kategori).distinct().all()
    categories = [cat[0] for cat in all_categories if cat[0]]
    
    # Tambah data baru
    if request.method == 'POST':
        tanggal_str = request.form['tanggal']
        jenis = request.form['jenis']
        kategori = request.form['kategori']
        deskripsi = request.form['deskripsi']
        jumlah = float(request.form['jumlah'])
        
        try:
            # Parse tanggal dari string dan konversi ke UTC
            tanggal_local = datetime.strptime(tanggal_str, '%Y-%m-%d')
            tanggal = local_to_utc(tanggal_local)
        except ValueError:
            flash('Format tanggal tidak valid.', 'danger')
            return redirect(url_for('main.cashflow'))
        
        cashflow = CashFlow(
            tanggal=tanggal,
            jenis=jenis,
            kategori=kategori,
            deskripsi=deskripsi,
            jumlah=jumlah,
            user_id=session.get('user_id')
        )
        db.session.add(cashflow)
        db.session.commit()
        flash('Data cash flow berhasil ditambahkan.', 'success')
        return redirect(url_for('main.cashflow'))
    
    return render_template(
        'cashflow.html',
        cashflow_data=cashflow_data,
        total_pemasukan=total_pemasukan,
        total_pengeluaran=total_pengeluaran,
        saldo=saldo,
        start_date=utc_to_local(start_date).strftime('%Y-%m-%d'),
        end_date=utc_to_local(end_date - timedelta(seconds=1)).strftime('%Y-%m-%d'),
        start_date_display=start_date_display,
        end_date_display=end_date_display,
        categories=categories,
        selected_kategori=kategori,
        selected_jenis=jenis,
        format_datetime=format_datetime
    )

# Edit Cash Flow
@main.route('/cashflow/edit/<int:id>', methods=['GET', 'POST'])
def edit_cashflow(id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    cashflow = CashFlow.query.get_or_404(id)
    
    if request.method == 'POST':
        tanggal_str = request.form['tanggal']
        jenis = request.form['jenis']
        kategori = request.form['kategori']
        deskripsi = request.form['deskripsi']
        jumlah = float(request.form['jumlah'])
        
        try:
            # Parse tanggal dari string dan konversi ke UTC
            tanggal_local = datetime.strptime(tanggal_str, '%Y-%m-%d')
            tanggal = local_to_utc(tanggal_local)
        except ValueError:
            flash('Format tanggal tidak valid.', 'danger')
            return redirect(url_for('main.edit_cashflow', id=id))
        
        cashflow.tanggal = tanggal
        cashflow.jenis = jenis
        cashflow.kategori = kategori
        cashflow.deskripsi = deskripsi
        cashflow.jumlah = jumlah
        cashflow.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('Data cash flow berhasil diperbarui.', 'success')
        return redirect(url_for('main.cashflow'))
    
    return render_template('edit_cashflow.html', cashflow=cashflow, format_datetime=format_datetime)

# Laporan Cash Flow
@main.route('/cashflow/laporan', methods=['GET'])
def laporan_cashflow():
    if 'user_id' not in session:
        flash('Silakan login terlebih dahulu.', 'warning')
        return redirect(url_for('main.login'))
    
    # Filter tanggal
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    if start_date_str and end_date_str:
        try:
            # Parse tanggal dari string
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            
            # Konversi ke UTC untuk query database
            start_date = local_to_utc(start_date.replace(hour=0, minute=0, second=0))
            end_date = local_to_utc((end_date + timedelta(days=1)).replace(hour=0, minute=0, second=0))
        except ValueError:
            flash('Format tanggal tidak valid.', 'danger')
            today = get_current_local_time()
            start_date = local_to_utc(today.replace(day=1, hour=0, minute=0, second=0))
            next_month = today.replace(day=28) + timedelta(days=4)
            end_date = local_to_utc(next_month.replace(day=1, hour=0, minute=0, second=0))
    else:
        # Default: bulan ini
        today = get_current_local_time()
        start_date = local_to_utc(today.replace(day=1, hour=0, minute=0, second=0))
        next_month = today.replace(day=28) + timedelta(days=4)
        end_date = local_to_utc(next_month.replace(day=1, hour=0, minute=0, second=0))
    
    # Format untuk tampilan
    start_date_display = utc_to_local(start_date).strftime('%d-%m-%Y')
    end_date_display = utc_to_local(end_date - timedelta(seconds=1)).strftime('%d-%m-%Y')
    
    # Ambil data untuk laporan
    cashflow_data = CashFlow.query.filter(
        CashFlow.tanggal >= start_date,
        CashFlow.tanggal < end_date
    ).order_by(CashFlow.tanggal).all()
    
    # Hitung total per kategori
    kategori_pemasukan = {}
    kategori_pengeluaran = {}
    
    for cf in cashflow_data:
        if cf.jenis == 'pemasukan':
            if cf.kategori in kategori_pemasukan:
                kategori_pemasukan[cf.kategori] += cf.jumlah
            else:
                kategori_pemasukan[cf.kategori] = cf.jumlah
        else:
            if cf.kategori in kategori_pengeluaran:
                kategori_pengeluaran[cf.kategori] += cf.jumlah
            else:
                kategori_pengeluaran[cf.kategori] = cf.jumlah
    
    # Hitung total pemasukan dan pengeluaran
    total_pemasukan = sum(kategori_pemasukan.values())
    total_pengeluaran = sum(kategori_pengeluaran.values())
    saldo = total_pemasukan - total_pengeluaran
    
    # Data untuk grafik
    chart_data = {
        'labels': list(set(list(kategori_pemasukan.keys()) + list(kategori_pengeluaran.keys()))),
        'pemasukan': [kategori_pemasukan.get(k, 0) for k in set(list(kategori_pemasukan.keys()) + list(kategori_pengeluaran.keys()))],
        'pengeluaran': [kategori_pengeluaran.get(k, 0) for k in set(list(kategori_pemasukan.keys()) + list(kategori_pengeluaran.keys()))]
    }
    
    return render_template(
        'laporan_cashflow.html',
        cashflow_data=cashflow_data,
        kategori_pemasukan=kategori_pemasukan,
        kategori_pengeluaran=kategori_pengeluaran,
        total_pemasukan=total_pemasukan,
        total_pengeluaran=total_pengeluaran,
        saldo=saldo,
        start_date=utc_to_local(start_date).strftime('%Y-%m-%d'),
        end_date=utc_to_local(end_date - timedelta(seconds=1)).strftime('%Y-%m-%d'),
        start_date_display=start_date_display,
        end_date_display=end_date_display,
        chart_data=chart_data,
        format_datetime=format_datetime
    )
