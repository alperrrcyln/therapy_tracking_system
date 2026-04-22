"""
Video Session Repository
Video/sesli görüşme kayıtları için CRUD işlemleri
"""
from typing import List, Optional
from datetime import datetime

from database.db_manager import db_manager
from database.models import VideoSession
from utils.logger import setup_logger

logger = setup_logger(__name__)


class VideoSessionRepository:
    """Video session repository"""
    
    def __init__(self):
        self.db = db_manager
    
    def create(self, video_session: VideoSession) -> Optional[int]:
        """Yeni video session ekle"""
        try:
            query = """
                INSERT INTO video_sessions (doctor_id, patient_id, session_type, 
                                          started_at, ended_at, duration_seconds,
                                          recording_path, recording_size_mb, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(query, (
                video_session.doctor_id,
                video_session.patient_id,
                video_session.session_type,
                video_session.started_at,
                video_session.ended_at,
                video_session.duration_seconds,
                video_session.recording_path,
                video_session.recording_size_mb,
                video_session.notes
            ))
            
            conn.commit()
            session_id = cursor.lastrowid
            
            logger.info(f"Video session created: {session_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Video session create error: {e}")
            return None
    
    def find_by_id(self, session_id: int) -> Optional[VideoSession]:
        """ID'ye göre video session getir"""
        try:
            query = "SELECT * FROM video_sessions WHERE id = ?"
            
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(query, (session_id,))
            row = cursor.fetchone()
            
            return self._row_to_video_session(row) if row else None
            
        except Exception as e:
            logger.error(f"Find by id error: {e}")
            return None
    
    def find_by_patient(self, patient_id: int, limit: int = 50) -> List[VideoSession]:
        """Hastaya göre video sessionları getir"""
        try:
            query = """
                SELECT * FROM video_sessions
                WHERE patient_id = ?
                ORDER BY started_at DESC
                LIMIT ?
            """
            
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(query, (patient_id, limit))
            rows = cursor.fetchall()
            
            return [self._row_to_video_session(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Find by patient error: {e}")
            return []
    
    def find_by_doctor(self, doctor_id: int, limit: int = 50) -> List[VideoSession]:
        """Doktora göre video sessionları getir"""
        try:
            query = """
                SELECT * FROM video_sessions
                WHERE doctor_id = ?
                ORDER BY started_at DESC
                LIMIT ?
            """
            
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(query, (doctor_id, limit))
            rows = cursor.fetchall()
            
            return [self._row_to_video_session(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Find by doctor error: {e}")
            return []
    
    def find_by_users(self, doctor_id: int, patient_id: int, limit: int = 50) -> List[VideoSession]:
        """Doktor ve hastaya göre video sessionları getir"""
        try:
            query = """
                SELECT * FROM video_sessions
                WHERE doctor_id = ? AND patient_id = ?
                ORDER BY started_at DESC
                LIMIT ?
            """
            
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(query, (doctor_id, patient_id, limit))
            rows = cursor.fetchall()
            
            return [self._row_to_video_session(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Find by users error: {e}")
            return []
    
    def update(self, video_session: VideoSession) -> bool:
        """Video session güncelle"""
        try:
            query = """
                UPDATE video_sessions
                SET ended_at = ?,
                    duration_seconds = ?,
                    recording_path = ?,
                    recording_size_mb = ?,
                    notes = ?
                WHERE id = ?
            """
            
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(query, (
                video_session.ended_at,
                video_session.duration_seconds,
                video_session.recording_path,
                video_session.recording_size_mb,
                video_session.notes,
                video_session.id
            ))
            
            conn.commit()
            
            return cursor.rowcount > 0
            
        except Exception as e:
            logger.error(f"Video session update error: {e}")
            return False
    
    def delete(self, session_id: int) -> bool:
        """Video session sil"""
        try:
            query = "DELETE FROM video_sessions WHERE id = ?"
            
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(query, (session_id,))
            conn.commit()
            
            logger.info(f"Video session deleted: {session_id}")
            return cursor.rowcount > 0
            
        except Exception as e:
            logger.error(f"Video session delete error: {e}")
            return False
    
    def _row_to_video_session(self, row) -> VideoSession:
        """Database row'u VideoSession objesine dönüştür"""
        return VideoSession(
            id=row['id'],
            doctor_id=row['doctor_id'],
            patient_id=row['patient_id'],
            session_type=row['session_type'],
            started_at=datetime.fromisoformat(row['started_at']) if row['started_at'] else None,
            ended_at=datetime.fromisoformat(row['ended_at']) if row['ended_at'] else None,
            duration_seconds=row['duration_seconds'],
            recording_path=row['recording_path'],
            recording_size_mb=row['recording_size_mb'],
            notes=row['notes'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
        )