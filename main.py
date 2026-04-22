"""
Main Entry Point
Terapi Takip Sistemi - Uygulama başlatma
"""
import sys
from PyQt5.QtWidgets import QMessageBox

from core.application import app
from ui.main_window import MainWindow
from utils.logger import setup_logger

logger = setup_logger(__name__)


def main():
    """Ana fonksiyon"""
    try:
        # Uygulamayı başlat
        if not app.initialize():
            logger.error("Uygulama başlatılamadı!")
            sys.exit(1)
        
        # Ana pencereyi oluştur
        main_window = MainWindow()
        app.set_main_window(main_window)
        
        # Uygulamayı çalıştır
        exit_code = app.run()
        
        # Temiz çıkış
        app.shutdown()
        sys.exit(exit_code)
        
    except Exception as e:
        logger.critical(f"Kritik hata: {e}", exc_info=True)
        
        # Hata mesajı göster
        try:
            QMessageBox.critical(
                None,
                "Kritik Hata",
                f"Uygulama başlatılamadı:\n\n{str(e)}\n\nDetaylar için log dosyasını kontrol edin."
            )
        except:
            pass
        
        sys.exit(1)


if __name__ == "__main__":
    main()