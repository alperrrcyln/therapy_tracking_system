"""
Sifre hash ve dogrulama fonksiyonlari
"""
import hashlib
import os
import base64


def hash_password(password: str) -> str:
    """
    Sifreyi hash'le (SHA-256 + salt)
    
    Args:
        password: Hashlenecek sifre
    
    Returns:
        salt + hash birlesmisi (base64 encoded)
    """
    # Random salt olustur
    salt = os.urandom(32)
    
    # Salt + password hash'le
    pwd_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        100000  # Iterasyon sayisi
    )
    
    # Salt ve hash'i birlestir ve base64 encode et
    combined = salt + pwd_hash
    return base64.b64encode(combined).decode('utf-8')


def verify_password(provided_password: str, stored_password: str) -> bool:
    """
    Sifreyi dogrula
    
    Args:
        provided_password: Kullanicinin girdigi sifre
        stored_password: Veritabaninda saklanan hash
    
    Returns:
        Sifre dogru mu?
    """
    try:
        # Base64 decode
        combined = base64.b64decode(stored_password.encode('utf-8'))
        
        # Salt ve hash'i ayir
        salt = combined[:32]
        stored_hash = combined[32:]
        
        # Girilen sifreyi ayni salt ile hash'le
        pwd_hash = hashlib.pbkdf2_hmac(
            'sha256',
            provided_password.encode('utf-8'),
            salt,
            100000
        )
        
        # Karsilastir
        return pwd_hash == stored_hash
    
    except Exception:
        return False