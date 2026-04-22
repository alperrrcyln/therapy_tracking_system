"""
Session Repository
Görüşme CRUD işlemleri - sessions tablosu
"""
from typing import List, Optional
from datetime import datetime

from database.db_manager import db_manager
from database.models import Session, TherapySession
from utils.logger import setup_logger


logger = setup_logger(__name__)


class SessionRepository:
    """Sessions tablosu için repository"""
    
    def __init__(self):
        self.db = db_manager
    
    def create(self, session: Session) -> int:
        """Yeni session oluştur"""
        query = """
            INSERT INTO sessions (
                patient_id, doctor_id, session_date, session_type,
                duration_minutes, notes, mood_before, mood_after, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            session.patient_id,
            session.doctor_id,
            session.session_date.isoformat() if session.session_date else datetime.now().isoformat(),
            session.session_type or "video",
            session.duration_minutes or 0,
            session.notes or "",
            session.mood_before or 5,
            session.mood_after or 5,
            datetime.now().isoformat()
        )
        
        logger.info(f"📝 Session oluşturuluyor...")
        logger.info(f"   Patient ID: {session.patient_id}")
        logger.info(f"   Doctor ID: {session.doctor_id}")
        logger.info(f"   Type: {session.session_type}")
        logger.info(f"   Duration: {session.duration_minutes} min")
        
        # Sorguyu çalıştır
        cursor = db_manager._connection.cursor()
        cursor.execute(query, params)
        db_manager._connection.commit()
        
        session_id = cursor.lastrowid
        
        logger.info(f"✅ Session oluşturuldu: ID={session_id}")
        
        # Doğrulama
        verify_query = "SELECT id, patient_id, session_type FROM sessions WHERE id = ?"
        cursor.execute(verify_query, (session_id,))
        result = cursor.fetchone()
        
        if result:
            logger.info(f"✅ DOĞRULANDI: Session {session_id} veritabanında mevcut")
        else:
            logger.error(f"❌ HATA: Session {session_id} veritabanında bulunamadı!")
        
        return session_id
    
    def find_by_id(self, session_id: int) -> Optional[Session]:
        """ID ile session bul"""
        try:
            query = "SELECT * FROM sessions WHERE id = ?"
            row = self.db.fetch_one(query, (session_id,))
            
            if row:
                return self._row_to_session(row)
            return None
            
        except Exception as e:
            logger.error(f"Session bulma hatası: {e}")
            return None
    
    def find_by_patient(self, patient_id: int, limit: int = 10) -> List[Session]:
        """Danışana ait sessionları getir - sessions tablosundan"""
        try:
            query = """
                SELECT * FROM sessions
                WHERE patient_id = ?
                ORDER BY session_date DESC
                LIMIT ?
            """
            rows = self.db.fetch_all(query, (patient_id, limit))
            
            sessions = [self._row_to_session(row) for row in rows]
            
            logger.info(f"📊 {len(sessions)} session bulundu (patient_id={patient_id})")
            
            return sessions
            
        except Exception as e:
            logger.error(f"Session listeleme hatası: {e}")
            return []
    
    def find_by_doctor(self, doctor_id: int, limit: int = 20) -> List[Session]:
        """Danışmana ait sessionları getir"""
        try:
            query = """
                SELECT * FROM sessions
                WHERE doctor_id = ?
                ORDER BY session_date DESC
                LIMIT ?
            """
            rows = self.db.fetch_all(query, (doctor_id, limit))
            
            return [self._row_to_session(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Session listeleme hatası: {e}")
            return []
    
    def count_by_patient(self, patient_id: int) -> int:
        """Danışanın toplam session sayısı - sessions tablosundan"""
        try:
            query = "SELECT COUNT(*) as count FROM sessions WHERE patient_id = ?"
            row = self.db.fetch_one(query, (patient_id,))
            
            count = row['count'] if row else 0
            
            logger.info(f"📊 Toplam {count} session (patient_id={patient_id})")
            
            return count
            
        except Exception as e:
            logger.error(f"Session sayma hatası: {e}")
            return 0
    
    def update(self, session: Session) -> bool:
        """Session bilgilerini güncelle"""
        try:
            query = """
                UPDATE sessions 
                SET duration_minutes = ?, notes = ?,
                    mood_before = ?, mood_after = ?
                WHERE id = ?
            """
            params = (
                session.duration_minutes,
                session.notes,
                session.mood_before,
                session.mood_after,
                session.id
            )
            
            self.db.execute_query(query, params)
            logger.info(f"Session güncellendi: {session.id}")
            return True
            
        except Exception as e:
            logger.error(f"Session güncelleme hatası: {e}")
            return False
    
    def delete(self, session_id: int) -> bool:
        """Session'ı sil"""
        try:
            query = "DELETE FROM sessions WHERE id = ?"
            self.db.execute_query(query, (session_id,))
            logger.info(f"Session silindi: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Session silme hatası: {e}")
            return False
    
    def _row_to_session(self, row) -> Session:
        """Database row'unu Session objesine dönüştür"""
        return Session(
            id=row['id'],
            patient_id=row['patient_id'],
            doctor_id=row['doctor_id'],
            session_date=datetime.fromisoformat(row['session_date']) if row['session_date'] else None,
            session_type=row['session_type'] if row['session_type'] else 'regular',
            duration_minutes=row['duration_minutes'] if row['duration_minutes'] else 0,
            notes=row['notes'] if row['notes'] else '',
            mood_before=row['mood_before'] if row['mood_before'] else 5,
            mood_after=row['mood_after'] if row['mood_after'] else 5,
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
        )
    
class TherapySessionRepository:
    """Therapy Sessions tablosu için repository (ESKİ sistem)"""
    
    def __init__(self):
        self.db = db_manager

    def create(self, session: TherapySession) -> int:
        """Yeni therapy session oluştur"""
        query = """
            INSERT INTO therapy_sessions (
                patient_id, doctor_id, session_date, duration_minutes,
                status, session_notes, therapist_notes, video_path, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            session.patient_id,
            session.doctor_id,
            session.session_date.isoformat() if session.session_date else datetime.now().isoformat(),
            session.duration_minutes or 0,
            session.status or "completed",
            session.session_notes or "",
            session.therapist_notes or "",
            session.video_path or "",
            datetime.now().isoformat()
        )
        
        logger.info(f"📝 Therapy session oluşturuluyor...")
        logger.info(f"   Patient ID: {session.patient_id}")
        logger.info(f"   Doctor ID: {session.doctor_id}")
        logger.info(f"   Duration: {session.duration_minutes} min")
        logger.info(f"   Video: {session.video_path}")
        
        cursor = db_manager._connection.cursor()
        cursor.execute(query, params)
        db_manager._connection.commit()
        
        session_id = cursor.lastrowid
        
        logger.info(f"✅ Therapy session oluşturuldu: ID={session_id}")
        
        # Doğrulama
        verify_query = "SELECT id, patient_id, video_path FROM therapy_sessions WHERE id = ?"
        cursor.execute(verify_query, (session_id,))
        result = cursor.fetchone()
        
        if result:
            logger.info(f"✅ DOĞRULANDI: Therapy session {session_id} veritabanında mevcut")
        else:
            logger.error(f"❌ HATA: Therapy session {session_id} veritabanında bulunamadı!")
        
        return session_id    
    
    def find_by_id(self, session_id: int) -> Optional[TherapySession]:
        """ID ile oturum bul"""
        try:
            query = "SELECT * FROM therapy_sessions WHERE id = ?"
            row = self.db.fetch_one(query, (session_id,))
            if row:
                return self._row_to_therapy_session_simple(row)
            return None
        except Exception as e:
            logger.error(f"Oturum bulma hatasi: {e}")
            return None
    
    def find_by_patient(self, patient_id: int, limit: int = 10) -> List[TherapySession]:
        """Danisana ait oturumlari getir"""
        try:
            query = """
                SELECT * FROM therapy_sessions
                WHERE patient_id = ?
                ORDER BY session_date DESC
                LIMIT ?
            """
            rows = self.db.fetch_all(query, (patient_id, limit))

            return [self._row_to_therapy_session_simple(row) for row in rows]

        except Exception as e:
            logger.error(f"Oturum listeleme hatasi: {e}")
            return []
    
    def find_by_doctor(self, doctor_id: int, limit: int = 20) -> List[TherapySession]:
        """Danismana ait oturumlari getir"""
        try:
            query = """
                SELECT * FROM therapy_sessions
                WHERE doctor_id = ?
                ORDER BY session_date DESC
                LIMIT ?
            """
            rows = self.db.fetch_all(query, (doctor_id, limit))
            return [self._row_to_therapy_session_simple(row) for row in rows]
        except Exception as e:
            logger.error(f"Oturum listeleme hatasi: {e}")
            return []

    def count_by_patient(self, patient_id: int) -> int:
        """Danisanin toplam oturum sayisi"""
        try:
            query = "SELECT COUNT(*) as count FROM therapy_sessions WHERE patient_id = ?"
            row = self.db.fetch_one(query, (patient_id,))
            return row['count'] if row else 0
        except Exception as e:
            logger.error(f"Oturum sayma hatasi: {e}")
            return 0

    def update(self, session: TherapySession) -> bool:
        """Therapy session güncelle"""
        try:
            query = """
                UPDATE therapy_sessions
                SET duration_minutes = ?, status = ?, session_notes = ?,
                    therapist_notes = ?, video_path = ?, updated_at = ?
                WHERE id = ?
            """
            params = (
                session.duration_minutes,
                session.status,
                session.session_notes,
                session.therapist_notes,
                session.video_path,
                datetime.now().isoformat(),
                session.id
            )
            self.db.execute_query(query, params)
            logger.info(f"Therapy session güncellendi: {session.id}")
            return True
        except Exception as e:
            logger.error(f"Therapy session güncelleme hatası: {e}")
            return False

    def delete(self, session_id: int) -> bool:
        """Oturumu sil"""
        try:
            query = "DELETE FROM therapy_sessions WHERE id = ?"
            self.db.execute_query(query, (session_id,))
            logger.info(f"Oturum silindi: {session_id}")
            return True

        except Exception as e:
            logger.error(f"Oturum silme hatasi: {e}")
            return False
    
    def _row_to_therapy_session_simple(self, row) -> TherapySession:
        """Basit row'u TherapySession'a dönüştür (row.get() kullanmaz)"""
        keys = row.keys()
        return TherapySession(
            id=row['id'],
            patient_id=row['patient_id'],
            doctor_id=row['doctor_id'],
            session_date=datetime.fromisoformat(row['session_date']) if row['session_date'] else None,
            duration_minutes=row['duration_minutes'],
            status=row['status'] if row['status'] else 'completed',
            session_notes=row['session_notes'] if 'session_notes' in keys else None,
            therapist_notes=row['therapist_notes'] if 'therapist_notes' in keys else None,
            diagnosis=row['diagnosis'] if 'diagnosis' in keys else None,
            video_path=row['video_path'] if 'video_path' in keys else None,
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if ('updated_at' in keys and row['updated_at']) else None
        )

    def _row_to_therapy_session(self, row) -> TherapySession:
        """Database row'unu TherapySession objesine donustur"""
        from database.models import Patient, User
        keys = row.keys()
        session = TherapySession(
            id=row['id'],
            patient_id=row['patient_id'],
            doctor_id=row['doctor_id'],
            session_date=datetime.fromisoformat(row['session_date']) if row['session_date'] else None,
            duration_minutes=row['duration_minutes'],
            status=row['status'] if row['status'] else 'completed',
            session_notes=row['session_notes'] if 'session_notes' in keys else None,
            therapist_notes=row['therapist_notes'] if 'therapist_notes' in keys else None,
            diagnosis=row['diagnosis'] if 'diagnosis' in keys else None,
            video_path=row['video_path'] if 'video_path' in keys else None,
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if ('updated_at' in keys and row['updated_at']) else None
        )
        
        # Patient bilgilerini ekle (basit versiyon)
        session.patient = Patient(
            id=row['patient_id'],
            user_id=row['patient_user_id'],
            doctor_id=row['doctor_id']
        )
        
        session.patient.user = User(
            id=row['patient_user_id'],
            email=row['patient_email'],
            first_name=row['patient_first_name'],
            last_name=row['patient_last_name']
        )
        
        # Doctor bilgilerini ekle
        session.doctor = User(
            id=row['doctor_id'],
            email=row['doctor_email'],
            first_name=row['doctor_first_name'],
            last_name=row['doctor_last_name']
        )
        
        return session    