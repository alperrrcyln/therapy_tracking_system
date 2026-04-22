"""
Authentication Service
Kimlik dogrulama islemleri
"""
from typing import Optional, Tuple
from datetime import datetime

from database.repositories.user_repository import UserRepository
from database.models import User
from core.constants import UserRole
from utils.encryption import hash_password, verify_password
from utils.validators import validate_email, validate_password
from utils.logger import setup_logger

logger = setup_logger(__name__)


class AuthService:
    """Authentication Service"""
    
    def __init__(self):
        self.user_repo = UserRepository()
    
    def login(self, email: str, password: str) -> Tuple[bool, str, Optional[User]]:
        """
        Kullanici girisi
        
        Args:
            email: Email
            password: Sifre
        
        Returns:
            (success, message, user)
        """
        try:
            # Email validation
            if not validate_email(email):
                return False, "Gecersiz email adresi", None
            
            # Kullaniciyi bul
            user = self.user_repo.find_by_email(email)
            
            if not user:
                logger.warning(f"Basarisiz giris denemesi: {email} - Kullanici bulunamadi")
                return False, "Email veya sifre hatali", None
            
            # Aktif mi kontrol et
            if not user.is_active:
                logger.warning(f"Basarisiz giris denemesi: {email} - Hesap aktif degil")
                return False, "Hesabiniz aktif degil", None
            
            # Sifre dogrulama - DUZELTILDI: dogru parametre sirasi
            if not verify_password(password, user.password_hash):
                logger.warning(f"Basarisiz giris denemesi: {email} - Yanlis sifre")
                return False, "Email veya sifre hatali", None
            
            # Son giris tarihini guncelle
            self.user_repo.update_last_login(user.id)
            
            logger.info(f"Basarili giris: {email}")
            return True, "Giris basarili", user
            
        except Exception as e:
            logger.error(f"Login hatasi: {e}")
            return False, "Bir hata olustu", None
    
    def register(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        phone: Optional[str] = None,
        role: str = UserRole.PATIENT.value
    ) -> Tuple[bool, str, Optional[User]]:
        """
        Yeni kullanici kaydi
        
        Args:
            email: Email
            password: Sifre
            first_name: Ad
            last_name: Soyad
            phone: Telefon (opsiyonel)
            role: Rol (doctor veya patient)
        
        Returns:
            (success, message, user)
        """
        try:
            # Validations
            if not validate_email(email):
                return False, "Gecersiz email adresi", None
            
            is_valid, msg = validate_password(password)
            if not is_valid:
                return False, msg, None
            
            # Email kontrolu
            existing_user = self.user_repo.find_by_email(email)
            if existing_user:
                return False, "Bu email adresi zaten kayitli", None
            
            # Sifre hash'le
            password_hash = hash_password(password)
            
            # User olustur
            user = User(
                email=email,
                password_hash=password_hash,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                role=role
            )
            
            # Kaydet
            user_id = self.user_repo.create(user)
            
            if user_id is None:
                return False, "Kullanici olusturulamadi", None
            
            user.id = user_id
            logger.info(f"Yeni kullanici kaydi: {email}")
            
            return True, "Kayit basarili", user
            
        except Exception as e:
            logger.error(f"Register hatasi: {e}")
            return False, "Bir hata olustu", None
    
    def change_password(
        self,
        user_id: int,
        old_password: str,
        new_password: str
    ) -> Tuple[bool, str]:
        """
        Sifre degistir
        
        Args:
            user_id: Kullanici ID
            old_password: Eski sifre
            new_password: Yeni sifre
        
        Returns:
            (success, message)
        """
        try:
            # Kullaniciyi bul
            user = self.user_repo.find_by_id(user_id)
            
            if not user:
                return False, "Kullanici bulunamadi"
            
            # Eski sifre kontrolu - DUZELTILDI: dogru parametre sirasi
            if not verify_password(old_password, user.password_hash):
                return False, "Eski sifre hatali"
            
            # Yeni sifre validasyonu
            is_valid, msg = validate_password(new_password)
            if not is_valid:
                return False, msg
            
            # Yeni sifre hash'le
            new_password_hash = hash_password(new_password)
            
            # Guncelle
            success = self.user_repo.update_password(user_id, new_password_hash)
            
            if success:
                logger.info(f"Sifre degistirildi: user_id={user_id}")
                return True, "Sifre basariyla degistirildi"
            else:
                return False, "Sifre degistirilemedi"
            
        except Exception as e:
            logger.error(f"Change password hatasi: {e}")
            return False, "Bir hata olustu"