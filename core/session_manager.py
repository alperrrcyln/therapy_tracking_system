"""
Session Manager
Kullanıcı oturum yönetimi (Singleton pattern)
"""
from typing import Optional
from datetime import datetime, timedelta

from database.models import User
from core.constants import UserRole
from utils.logger import setup_logger

logger = setup_logger(__name__)


class SessionManager:
    """
    Kullanıcı oturum yöneticisi
    Singleton pattern - Uygulama genelinde tek instance
    """
    
    _instance: Optional['SessionManager'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize session manager"""
        if not hasattr(self, '_initialized'):
            self._current_user: Optional[User] = None
            self._login_time: Optional[datetime] = None
            self._session_timeout_minutes: int = 60
            self._initialized = True
            logger.info("Session Manager başlatıldı")
    
    def login(self, user: User) -> bool:
        """
        Kullanıcı girişi yap
        
        Args:
            user: Giriş yapan kullanıcı
        
        Returns:
            Başarılı mı?
        """
        try:
            self._current_user = user
            self._login_time = datetime.now()
            logger.info(f"Kullanıcı giriş yaptı: {user.email} (Role: {user.role})")
            return True
        except Exception as e:
            logger.error(f"Login hatası: {e}")
            return False
    
    def logout(self) -> None:
        """Kullanıcı çıkışı yap"""
        if self._current_user:
            logger.info(f"Kullanıcı çıkış yaptı: {self._current_user.email}")
        
        self._current_user = None
        self._login_time = None
    
    def is_logged_in(self) -> bool:
        """
        Kullanıcı giriş yapmış mı?
        
        Returns:
            Giriş yapılmış mı?
        """
        if self._current_user is None:
            return False
        
        # Session timeout kontrolü
        if self.is_session_expired():
            logger.warning("Session timeout - otomatik logout")
            self.logout()
            return False
        
        return True
    
    def is_session_expired(self) -> bool:
        """
        Oturum süresi dolmuş mu?
        
        Returns:
            Oturum dolmuş mu?
        """
        if self._login_time is None:
            return True
        
        elapsed = datetime.now() - self._login_time
        timeout = timedelta(minutes=self._session_timeout_minutes)
        
        return elapsed > timeout
    
    def refresh_session(self) -> None:
        """Oturum süresini yenile (kullanıcı aktif olduğunda çağrılır)"""
        self._login_time = datetime.now()
    
    def get_current_user(self) -> Optional[User]:
        """
        Aktif kullanıcıyı getir
        
        Returns:
            Aktif kullanıcı veya None
        """
        if self.is_logged_in():
            return self._current_user
        return None
    
    def get_current_user_id(self) -> Optional[int]:
        """
        Aktif kullanıcı ID'sini getir
        
        Returns:
            Kullanıcı ID veya None
        """
        user = self.get_current_user()
        return user.id if user else None
    
    def is_doctor(self) -> bool:
        """
        Aktif kullanıcı danışman mı?
        
        Returns:
            Danışman mı?
        """
        user = self.get_current_user()
        return user.role == UserRole.DOCTOR.value if user else False
    
    def is_patient(self) -> bool:
        """
        Aktif kullanıcı danışan mı?
        
        Returns:
            Danışan mı?
        """
        user = self.get_current_user()
        return user.role == UserRole.PATIENT.value if user else False
    
    def get_session_info(self) -> dict:
        """
        Oturum bilgilerini getir
        
        Returns:
            Oturum bilgileri dict
        """
        if not self.is_logged_in():
            return {"logged_in": False}
        
        user = self._current_user
        elapsed = datetime.now() - self._login_time
        remaining = timedelta(minutes=self._session_timeout_minutes) - elapsed
        
        return {
            "logged_in": True,
            "user_id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "login_time": self._login_time.isoformat(),
            "elapsed_minutes": int(elapsed.total_seconds() / 60),
            "remaining_minutes": int(remaining.total_seconds() / 60)
        }
    
    def set_timeout(self, minutes: int) -> None:
        """
        Session timeout süresini ayarla
        
        Args:
            minutes: Timeout süresi (dakika)
        """
        self._session_timeout_minutes = minutes
        logger.info(f"Session timeout ayarlandı: {minutes} dakika")


# Global instance
session_manager = SessionManager()