"""
Base Page
Tüm sayfaların miras aldığı temel sınıf
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import pyqtSignal

from utils.logger import setup_logger

logger = setup_logger(__name__)


class BasePage(QWidget):
    """
    Temel sayfa sınıfı
    Tüm sayfalar bundan türer
    """
    
    # Signals
    page_changed = pyqtSignal(int)  # Yeni sayfa ID'si
    logout_requested = pyqtSignal()  # Logout isteği
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        logger.debug(f"{self.__class__.__name__} initialized")
    
    def on_page_show(self):
        """
        Sayfa gösterildiğinde çağrılır
        Alt sınıflar override edebilir
        """
        pass
    
    def on_page_hide(self):
        """
        Sayfa gizlendiğinde çağrılır
        Alt sınıflar override edebilir
        """
        pass
    
    def refresh_data(self):
        """
        Sayfa verilerini yenile
        Alt sınıflar override edebilir
        """
        pass
    
    def navigate_to(self, page_id: int):
        """
        Başka bir sayfaya geçiş yap
        
        Args:
            page_id: Hedef sayfa ID'si
        """
        logger.debug(f"Navigation request: {page_id}")
        self.page_changed.emit(page_id)
    
    def request_logout(self):
        """Logout isteği gönder"""
        logger.debug("Logout requested")
        self.logout_requested.emit()