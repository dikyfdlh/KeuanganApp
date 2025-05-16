from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from . import db
from .utils import get_current_local_time, local_to_utc

class BiayaTetap(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100))
    jumlah = db.Column(db.Float)
    anggaran = db.Column(db.Float, default=0)
    periode = db.Column(db.String(20), default='bulanan')  # bulanan, tahunan
    keterangan = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def persentase_realisasi(self):
        if self.anggaran > 0:
            return (self.jumlah / self.anggaran) * 100
        return 0

class BiayaVariabel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100))
    jumlah = db.Column(db.Float)
    anggaran = db.Column(db.Float, default=0)
    periode = db.Column(db.String(20), default='bulanan')  # bulanan, tahunan
    keterangan = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def persentase_realisasi(self):
        if self.anggaran > 0:
            return (self.jumlah / self.anggaran) * 100
        return 0

class Pendapatan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sumber = db.Column(db.String(100))
    jumlah = db.Column(db.Float)
    anggaran = db.Column(db.Float, default=0)
    periode = db.Column(db.String(20), default='bulanan')  # bulanan, tahunan
    keterangan = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def persentase_realisasi(self):
        if self.anggaran > 0:
            return (self.jumlah / self.anggaran) * 100
        return 0
    
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    namalengkap= db.Column(db.String(150), unique=True, nullable=False)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='user')  # 'admin' atau 'user'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    def is_admin(self):
        return self.role == 'admin'

# Model untuk Produk
class Produk(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    kode = db.Column(db.String(20), unique=True)
    nama = db.Column(db.String(100), nullable=False)
    deskripsi = db.Column(db.Text)
    harga_beli = db.Column(db.Float, default=0)
    harga_jual = db.Column(db.Float, default=0)
    stok = db.Column(db.Integer, default=0)
    kategori = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def profit(self):
        return self.harga_jual - self.harga_beli
        
    def profit_percentage(self):
        if self.harga_beli > 0:
            return (self.profit() / self.harga_beli) * 100
        return 0

# Model untuk Penjualan
class Penjualan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nomor_invoice = db.Column(db.String(20), unique=True)
    tanggal = db.Column(db.DateTime, default=datetime.utcnow)
    total = db.Column(db.Float, default=0)
    keterangan = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relasi dengan detail penjualan
    details = db.relationship('DetailPenjualan', backref='penjualan', lazy=True, cascade="all, delete-orphan")

# Model untuk Detail Penjualan
class DetailPenjualan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    penjualan_id = db.Column(db.Integer, db.ForeignKey('penjualan.id'), nullable=False)
    produk_id = db.Column(db.Integer, db.ForeignKey('produk.id'), nullable=False)
    jumlah = db.Column(db.Integer, default=1)
    harga = db.Column(db.Float)
    subtotal = db.Column(db.Float)
    
    # Relasi dengan produk
    produk = db.relationship('Produk', backref='detail_penjualan')

# Model untuk Menu
class Menu(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(255))
    icon = db.Column(db.String(50))
    parent_id = db.Column(db.Integer, db.ForeignKey('menu.id'), nullable=True)
    urutan = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relasi self-referential untuk menu parent-child
    children = db.relationship('Menu', backref=db.backref('parent', remote_side=[id]))

# Model untuk Cash Flow
class CashFlow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tanggal = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    jenis = db.Column(db.String(20), nullable=False)  # 'pemasukan' atau 'pengeluaran'
    kategori = db.Column(db.String(50), nullable=False)
    deskripsi = db.Column(db.Text)
    jumlah = db.Column(db.Float, default=0, nullable=False)
    saldo = db.Column(db.Float, default=0)  # Saldo setelah transaksi ini
    bukti = db.Column(db.String(255))  # Path ke file bukti transaksi (opsional)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relasi dengan user
    user = db.relationship('User', backref='cashflows')
    
    def is_pemasukan(self):
        return self.jenis == 'pemasukan'
    
    def is_pengeluaran(self):
        return self.jenis == 'pengeluaran'
    
    def get_jumlah_signed(self):
        """Mengembalikan jumlah dengan tanda (positif untuk pemasukan, negatif untuk pengeluaran)"""
        if self.is_pengeluaran():
            return -self.jumlah
        return self.jumlah
    
    def get_tanggal_lokal(self):
        """Mengembalikan tanggal dalam zona waktu lokal (Asia/Jakarta)"""
        from .utils import utc_to_local
        return utc_to_local(self.tanggal)

# Model untuk Kategori Cash Flow
class KategoriCashFlow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(50), nullable=False, unique=True)
    jenis = db.Column(db.String(20), nullable=False)  # 'pemasukan' atau 'pengeluaran' atau 'keduanya'
    deskripsi = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
