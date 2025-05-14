from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from .models import db, BiayaTetap, BiayaVariabel, Pendapatan, User

main = Blueprint('main', __name__)

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

        user = User(namalengkap=namalengkap, username=username, email=email)
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
    total_bt = sum([b.jumlah for b in BiayaTetap.query.all()])
    total_bv = sum([b.jumlah for b in BiayaVariabel.query.all()])
    total_pd = sum([p.jumlah for p in Pendapatan.query.all()])
    laba_bersih = total_pd - (total_bt + total_bv)
    return render_template('dashboard.html', total_bt=total_bt, total_bv=total_bv, total_pd=total_pd, laba=laba_bersih)

# Biaya Tetap
@main.route('/biaya-tetap', methods=['GET', 'POST'])
def biaya_tetap():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    if request.method == 'POST':
        nama = request.form['nama']
        jumlah = float(request.form['jumlah'])
        db.session.add(BiayaTetap(nama=nama, jumlah=jumlah))
        db.session.commit()
        return redirect(url_for('main.biaya_tetap'))
    data = BiayaTetap.query.all()
    return render_template('biaya_tetap.html', data=data)

# Biaya Variabel
@main.route('/biaya-variabel', methods=['GET', 'POST'])
def biaya_variabel():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    if request.method == 'POST':
        nama = request.form['nama']
        jumlah = float(request.form['jumlah'])
        db.session.add(BiayaVariabel(nama=nama, jumlah=jumlah))
        db.session.commit()
        return redirect(url_for('main.biaya_variabel'))
    data = BiayaVariabel.query.all()
    return render_template('biaya_variabel.html', data=data)

# Pendapatan
@main.route('/pendapatan', methods=['GET', 'POST'])
def pendapatan():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    if request.method == 'POST':
        sumber = request.form['sumber']
        jumlah = float(request.form['jumlah'])
        db.session.add(Pendapatan(sumber=sumber, jumlah=jumlah))
        db.session.commit()
        return redirect(url_for('main.pendapatan'))
    data = Pendapatan.query.all()
    return render_template('pendapatan.html', data=data)

# Biaya Tetap Edit
@main.route('/biaya-tetap/edit/<int:id>', methods=['GET', 'POST'])
def editBiayaTTP(id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    item = BiayaTetap.query.get_or_404(id)
    if request.method == 'POST':
        item.nama = request.form['nama']
        item.jumlah = float(request.form['jumlah'])
        db.session.commit()
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
        db.session.commit()
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
        item.nama = request.form['nama']
        item.jumlah = float(request.form['jumlah'])
        db.session.commit()
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
