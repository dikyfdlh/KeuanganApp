from datetime import datetime
import pytz
from flask import current_app

def utc_to_local(utc_dt):
    """Mengkonversi waktu UTC ke waktu lokal (Asia/Jakarta)"""
    if utc_dt is None:
        return None
        
    if utc_dt.tzinfo is None:
        utc_dt = utc_dt.replace(tzinfo=pytz.UTC)
        
    local_tz = pytz.timezone(current_app.config['TIMEZONE'])
    local_dt = utc_dt.astimezone(local_tz)
    return local_dt

def local_to_utc(local_dt):
    """Mengkonversi waktu lokal (Asia/Jakarta) ke waktu UTC"""
    if local_dt is None:
        return None
        
    local_tz = pytz.timezone(current_app.config['TIMEZONE'])
    if local_dt.tzinfo is None:
        local_dt = local_tz.localize(local_dt)
        
    utc_dt = local_dt.astimezone(pytz.UTC)
    return utc_dt

def get_current_local_time():
    """Mendapatkan waktu lokal saat ini (Asia/Jakarta)"""
    utc_now = datetime.utcnow().replace(tzinfo=pytz.UTC)
    return utc_to_local(utc_now)

def format_datetime(dt, format='%d-%m-%Y %H:%M'):
    """Format datetime dengan timezone Asia/Jakarta"""
    if dt is None:
        return '-'
    
    # Pastikan datetime memiliki timezone info
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=pytz.UTC)
    
    # Konversi ke waktu lokal
    local_dt = utc_to_local(dt)
    return local_dt.strftime(format)
