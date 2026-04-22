"""
Uygulama konfigürasyon ayarları
"""
import os
from pathlib import Path

# Proje kök dizini
BASE_DIR = Path(__file__).parent

# Veritabanı ayarları
DATABASE_PATH = BASE_DIR / "data" / "database.db"

# Klasör yolları
DATA_DIR = BASE_DIR / "data"
VIDEO_DIR = DATA_DIR / "videos"
LOG_DIR = DATA_DIR / "logs"
MODELS_DIR = BASE_DIR / "ml" / "models"
RESOURCES_DIR = BASE_DIR / "resources"
ICONS_DIR = RESOURCES_DIR / "icons"
STYLES_DIR = RESOURCES_DIR / "styles"

# Gerekli klasörleri oluştur
for directory in [DATA_DIR, VIDEO_DIR, LOG_DIR, MODELS_DIR, RESOURCES_DIR, ICONS_DIR, STYLES_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Loglama ayarları
LOG_FILE = LOG_DIR / "app.log"
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Güvenlik ayarları
PASSWORD_MIN_LENGTH = 6
SESSION_TIMEOUT_MINUTES = 60
PASSWORD_SALT_ROUNDS = 12

# ML Model ayarları
EMOTION_MODEL_PATH = MODELS_DIR / "emotion_model.h5"
FACE_CASCADE_PATH = "haarcascade_frontalface_default.xml"  # OpenCV default

# UI Ayarları
THEME = "light"  # light veya dark
ACCENT_COLOR = "#2196F3"

# Video kayıt ayarları
VIDEO_CODEC = "XVID"
VIDEO_FPS = 30
VIDEO_RESOLUTION = (640, 480)

# Debug mode
DEBUG = True