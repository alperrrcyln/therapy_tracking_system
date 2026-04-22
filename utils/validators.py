"""
Veri doğrulama fonksiyonları
"""
import re
from typing import Tuple
from config import PASSWORD_MIN_LENGTH


def validate_email(email: str) -> Tuple[bool, str]:
    """
    Email formatını doğrula
    
    Args:
        email: Kontrol edilecek email
    
    Returns:
        (is_valid, error_message)
    """
    if not email:
        return False, "Email boş olamaz"
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "Geçersiz email formatı"
    
    return True, ""


def validate_password(password: str) -> Tuple[bool, str]:
    """
    Şifre güvenliğini doğrula
    
    Args:
        password: Kontrol edilecek şifre
    
    Returns:
        (is_valid, error_message)
    """
    if not password:
        return False, "Şifre boş olamaz"
    
    if len(password) < PASSWORD_MIN_LENGTH:
        return False, f"Şifre en az {PASSWORD_MIN_LENGTH} karakter olmalıdır"
    
    return True, ""


def validate_phone(phone: str) -> Tuple[bool, str]:
    """
    Telefon numarası formatını doğrula
    
    Args:
        phone: Kontrol edilecek telefon
    
    Returns:
        (is_valid, error_message)
    """
    if not phone:
        return True, ""  # Telefon opsiyonel olabilir
    
    # Türkiye telefon formatı: 05XX XXX XX XX
    pattern = r'^05\d{9}$|^05\d{2}\s?\d{3}\s?\d{2}\s?\d{2}$'
    cleaned = phone.replace(" ", "").replace("-", "")
    
    if not re.match(pattern, cleaned):
        return False, "Geçersiz telefon formatı (05XX XXX XX XX)"
    
    return True, ""


def validate_name(name: str, field_name: str = "İsim") -> Tuple[bool, str]:
    """
    İsim doğrulama
    
    Args:
        name: Kontrol edilecek isim
        field_name: Hata mesajında gösterilecek alan adı
    
    Returns:
        (is_valid, error_message)
    """
    if not name or not name.strip():
        return False, f"{field_name} boş olamaz"
    
    if len(name.strip()) < 2:
        return False, f"{field_name} en az 2 karakter olmalıdır"
    
    return True, ""


def validate_tc_no(tc_no: str) -> Tuple[bool, str]:
    """
    TC Kimlik No doğrulama
    
    Args:
        tc_no: Kontrol edilecek TC No
    
    Returns:
        (is_valid, error_message)
    """
    if not tc_no:
        return True, ""  # TC No opsiyonel olabilir
    
    # TC No 11 haneli olmalı ve sayısal olmalı
    if not tc_no.isdigit() or len(tc_no) != 11:
        return False, "TC Kimlik No 11 haneli olmalıdır"
    
    if tc_no[0] == '0':
        return False, "TC Kimlik No 0 ile başlayamaz"
    
    return True, ""


def validate_age(age: int) -> Tuple[bool, str]:
    """
    Yaş doğrulama
    
    Args:
        age: Kontrol edilecek yaş
    
    Returns:
        (is_valid, error_message)
    """
    if age < 0:
        return False, "Yaş negatif olamaz"
    
    if age > 150:
        return False, "Geçersiz yaş değeri"
    
    return True, ""