"""
Veritabanı bağlantı yöneticisi (Singleton pattern)
"""
import sqlite3
from pathlib import Path
from typing import Optional
from contextlib import contextmanager

from config import DATABASE_PATH
from utils.logger import setup_logger
from utils.encryption import hash_password

logger = setup_logger(__name__)


class DatabaseManager:
    """
    Veritabanı bağlantı yöneticisi
    Singleton pattern ile tek instance kullanımı
    """
    
    _instance: Optional['DatabaseManager'] = None
    _connection: Optional[sqlite3.Connection] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Veritabanı bağlantısını başlat"""
        if self._connection is None:
            self.connect()
    
    def connect(self) -> None:
        """Veritabanına bağlan"""
        try:
            self._connection = sqlite3.connect(
                DATABASE_PATH,
                check_same_thread=False  # Multi-thread kullanımı için
            )
            self._connection.row_factory = sqlite3.Row  # Dict-like access
            logger.info(f"Veritabanı bağlantısı kuruldu: {DATABASE_PATH}")
            
            # Foreign keys aktif et
            self._connection.execute("PRAGMA foreign_keys = ON")
            
        except sqlite3.Error as e:
            logger.error(f"Veritabanı bağlantı hatası: {e}")
            raise
    
    def get_connection(self) -> sqlite3.Connection:
        """Bağlantı instance'ını döndür"""
        if self._connection is None:
            self.connect()
        return self._connection
    
    @contextmanager
    def get_cursor(self):
        """
        Context manager ile cursor kullanımı
        Otomatik commit/rollback
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Veritabanı işlem hatası: {e}")
            raise
        finally:
            cursor.close()
    
    def execute_query(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """
        SQL sorgusu çalıştır
        
        Args:
            query: SQL sorgusu
            params: Query parametreleri
        
        Returns:
            Cursor
        """
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor
    
    def execute_many(self, query: str, params_list: list) -> None:
        """
        Çoklu insert/update için
        
        Args:
            query: SQL sorgusu
            params_list: Parametre listesi
        """
        with self.get_cursor() as cursor:
            cursor.executemany(query, params_list)
    
    def fetch_one(self, query: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        """
        Tek satır getir
        
        Args:
            query: SQL sorgusu
            params: Query parametreleri
        
        Returns:
            Tek satır veya None
        """
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchone()
    
    def fetch_all(self, query: str, params: tuple = ()) -> list:
        """
        Tüm satırları getir
        
        Args:
            query: SQL sorgusu
            params: Query parametreleri
        
        Returns:
            Satır listesi
        """
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def init_database(self) -> None:
        """Veritabanı tablolarını oluştur"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Users tablosu
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    first_name TEXT,
                    last_name TEXT,
                    phone TEXT,
                    role TEXT NOT NULL DEFAULT 'patient',
                    is_active BOOLEAN DEFAULT 1,
                    last_login TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Patients tablosu
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS patients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE NOT NULL,
                    doctor_id INTEGER NOT NULL,
                    tc_no TEXT,
                    birth_date DATE,
                    gender TEXT,
                    address TEXT,
                    emergency_contact_name TEXT,
                    emergency_contact_phone TEXT,
                    photo_path TEXT,
                    medical_history TEXT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (doctor_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # Therapy Sessions tablosu
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS therapy_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id INTEGER NOT NULL,
                    doctor_id INTEGER NOT NULL,
                    session_date TIMESTAMP,
                    duration_minutes INTEGER,
                    status TEXT DEFAULT 'scheduled',
                    session_notes TEXT,
                    therapist_notes TEXT,
                    diagnosis TEXT,
                    video_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
                    FOREIGN KEY (doctor_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # Emotion Analysis tablosu
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS emotion_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    emotion_type TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    timestamp TIMESTAMP,
                    frame_number INTEGER,
                    additional_data TEXT,
                    face_detected BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES therapy_sessions(id) ON DELETE CASCADE
                )
            """)
            
            # Appointments tablosu
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS appointments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id INTEGER NOT NULL,
                    doctor_id INTEGER NOT NULL,
                    appointment_date TIMESTAMP NOT NULL,
                    duration_minutes INTEGER DEFAULT 60,
                    status TEXT DEFAULT 'pending',
                    notes TEXT,
                    cancellation_reason TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
                    FOREIGN KEY (doctor_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # Patient Notes tablosu
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS patient_notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id INTEGER NOT NULL,
                    note_text TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
                )
            """)
            
            # Messages tablosu (Chat)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender_id INTEGER NOT NULL,
                    receiver_id INTEGER NOT NULL,
                    session_id INTEGER,
                    message_text TEXT NOT NULL,
                    message_type TEXT DEFAULT 'text',
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_read BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (sender_id) REFERENCES users(id),
                    FOREIGN KEY (receiver_id) REFERENCES users(id),
                    FOREIGN KEY (session_id) REFERENCES therapy_sessions(id)
                )
            """)
            
            # Video Sessions tablosu
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS video_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    doctor_id INTEGER NOT NULL,
                    patient_id INTEGER NOT NULL,
                    session_type TEXT DEFAULT 'video',
                    started_at TIMESTAMP,
                    ended_at TIMESTAMP,
                    duration_seconds INTEGER DEFAULT 0,
                    recording_path TEXT,
                    recording_size_mb REAL DEFAULT 0.0,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (doctor_id) REFERENCES users(id),
                    FOREIGN KEY (patient_id) REFERENCES users(id)
                )
            """)
            
            conn.commit()
            logger.info("All tables created/verified (including messages and video_sessions)")

            # Hiç kullanıcı yoksa varsayılan admin oluştur
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            if user_count == 0:
                admin_hash = hash_password("admin123")
                cursor.execute(
                    """INSERT INTO users (email, password_hash, role, first_name, last_name, is_active)
                       VALUES (?, ?, 'doctor', 'Admin', 'Doctor', 1)""",
                    ("admin@therapy.com", admin_hash)
                )
                conn.commit()
                logger.info("Varsayılan admin kullanıcısı oluşturuldu: admin@therapy.com")

        except Exception as e:
            logger.error(f"Database init error: {e}")
            raise
    
    def close(self) -> None:
        """Veritabanı bağlantısını kapat"""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("Veritabanı bağlantısı kapatıldı")
    
    def __del__(self):
        """Destructor - bağlantıyı kapat"""
        self.close()


# Global instance
db_manager = DatabaseManager()