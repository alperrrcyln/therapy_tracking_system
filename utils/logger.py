"""
Merkezi loglama sistemi
"""
import logging
import sys
from pathlib import Path
from config import LOG_FILE, LOG_LEVEL, LOG_FORMAT


def setup_logger(name: str) -> logging.Logger:
    """
    Logger oluştur ve yapılandır
    
    Args:
        name: Logger adı (genelde __name__ kullanılır)
    
    Returns:
        Yapılandırılmış logger instance
    """
    logger = logging.getLogger(name)
    
    # Eğer daha önce handler eklenmişse tekrar ekleme
    if logger.handlers:
        return logger
    
    logger.setLevel(getattr(logging, LOG_LEVEL))
    
    # Dosya handler
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(LOG_FORMAT)
    file_handler.setFormatter(file_formatter)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    
    # Handler'ları ekle
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


# Global logger instance
app_logger = setup_logger("TherapyTracker")