"""
Application Class
Ana uygulama yaşam döngüsü yönetimi (Singleton pattern)
"""
import sys
from typing import Optional
from PyQt5.QtWidgets import QApplication

from database.db_manager import db_manager
from core.session_manager import session_manager
from core.constants import WINDOW_TITLE
from utils.logger import setup_logger

logger = setup_logger(__name__)


class Application:
    """
    Ana uygulama sınıfı
    Singleton pattern - Uygulama yaşam döngüsünü yönetir
    """
    
    _instance: Optional['Application'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize application"""
        if not hasattr(self, '_initialized'):
            self.qapp: Optional[QApplication] = None
            self.main_window = None
            self._initialized = True
            logger.info("Application instance oluşturuldu")
    
    def initialize(self) -> bool:
        """
        Uygulamayı başlat
        
        Returns:
            Başlatma başarılı mı?
        """
        try:
            logger.info(f"=== {WINDOW_TITLE} Başlatılıyor ===")
            
            # 1. Qt Application oluştur
            self.qapp = QApplication(sys.argv)
            self.qapp.setApplicationName(WINDOW_TITLE)
            logger.info("Qt Application oluşturuldu")
            
            # 2. Veritabanını başlat
            self._initialize_database()
            
            # 3. Session manager hazır (zaten singleton)
            logger.info("Session Manager hazır")
            
            logger.info("=== Uygulama başlatma tamamlandı ===")
            return True
            
        except Exception as e:
            logger.error(f"Uygulama başlatma hatası: {e}")
            return False
    
    def _initialize_database(self) -> None:
        """Veritabanını başlat"""
        try:
            from config import DATABASE_PATH
            
            logger.info("Veritabanı bağlantısı kontrol ediliyor...")
            
            # Veritabanı dosyası yoksa oluştur
            if not DATABASE_PATH.exists():
                logger.info("Veritabanı dosyası bulunamadı, yeni oluşturuluyor...")
                db_manager.init_database()
                return

            # Dosya var, tablolar var mı kontrol et
            logger.info("Veritabanı dosyası mevcut")

            # Users tablosu var mı kontrol et
            needs_migration = False

            try:
                # Direkt SQL ile kontrol et
                conn = db_manager.get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
                result = cursor.fetchone()
                cursor.close()

                if result is None:
                    logger.warning("Tablolar bulunamadı, migration gerekli")
                    needs_migration = True
                else:
                    logger.info("Tablolar mevcut")

            except Exception as check_error:
                logger.warning(f"Tablo kontrolü hatası: {check_error}")
                needs_migration = True

            # Migration gerekiyorsa çalıştır
            if needs_migration:
                logger.info("Migration çalıştırılıyor...")
                db_manager.init_database()
                logger.info("Migration tamamlandı")
                
        except Exception as e:
            logger.error(f"Veritabanı başlatma hatası: {e}")
            raise
    
    def set_main_window(self, window) -> None:
        """
        Ana pencereyi kaydet
        
        Args:
            window: MainWindow instance
        """
        self.main_window = window
        logger.info("Ana pencere kaydedildi")
    
    def get_main_window(self):
        """
        Ana pencereyi getir
        
        Returns:
            MainWindow instance
        """
        return self.main_window
    
    def run(self) -> int:
        """
        Uygulamayı çalıştır
        
        Returns:
            Exit code
        """
        try:
            if self.main_window is None:
                raise RuntimeError("Ana pencere ayarlanmadı!")
            
            logger.info("Uygulama ana döngüsü başlatılıyor...")
            self.main_window.show()
            
            # Qt event loop
            exit_code = self.qapp.exec_()
            
            logger.info(f"Uygulama sonlandırıldı (exit code: {exit_code})")
            return exit_code
            
        except Exception as e:
            logger.error(f"Uygulama çalıştırma hatası: {e}")
            return 1
    
    def shutdown(self) -> None:
        """Uygulamayı temiz şekilde kapat"""
        try:
            logger.info("=== Uygulama kapatılıyor ===")
            
            # Session'ı temizle
            if session_manager.is_logged_in():
                session_manager.logout()
            
            # Veritabanı bağlantısını kapat
            db_manager.close()
            
            logger.info("=== Uygulama başarıyla kapatıldı ===")
            
        except Exception as e:
            logger.error(f"Shutdown hatası: {e}")
    
    def restart(self) -> None:
        """Uygulamayı yeniden başlat"""
        logger.info("Uygulama yeniden başlatılıyor...")
        self.shutdown()
        # Yeniden başlatma için QApplication.quit() ve yeni process başlatmak gerekir
        # Bu kısım main.py'da handle edilecek


# Global instance
app = Application()