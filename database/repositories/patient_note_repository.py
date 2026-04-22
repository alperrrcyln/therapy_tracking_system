"""
Patient Note Repository
Danışan notları veritabanı işlemleri
"""
from typing import List, Optional
from datetime import datetime

from database.db_manager import db_manager
from database.models import PatientNote
from utils.logger import setup_logger

logger = setup_logger(__name__)


class PatientNoteRepository:
    """Danışan notları repository"""
    
    def create(self, patient_id: int, note_text: str) -> Optional[PatientNote]:
        """Yeni not oluştur"""
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO patient_notes (patient_id, note_text, created_at, updated_at)
                VALUES (?, ?, ?, ?)
            """, (patient_id, note_text, datetime.now().isoformat(), datetime.now().isoformat()))
            
            note_id = cursor.lastrowid
            conn.commit()
            
            logger.info(f"Patient note created: {note_id}")
            
            # Oluşturulan notu döndür
            return self.get_by_id(note_id)
            
        except Exception as e:
            logger.error(f"Patient note create error: {e}")
            return None
    
    def update(self, note_id: int, note_text: str) -> bool:
        """Notu güncelle"""
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE patient_notes
                SET note_text = ?, updated_at = ?
                WHERE id = ?
            """, (note_text, datetime.now().isoformat(), note_id))
            
            conn.commit()
            affected = cursor.rowcount
            
            if affected > 0:
                logger.info(f"Patient note updated: {note_id}")
                return True
            else:
                logger.warning(f"Note not found: {note_id}")
                return False
                
        except Exception as e:
            logger.error(f"Patient note update error: {e}")
            return False
    
    def delete(self, note_id: int) -> bool:
        """Notu sil"""
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM patient_notes WHERE id = ?", (note_id,))
            
            conn.commit()
            affected = cursor.rowcount
            
            if affected > 0:
                logger.info(f"Patient note deleted: {note_id}")
                return True
            else:
                logger.warning(f"Note not found: {note_id}")
                return False
                
        except Exception as e:
            logger.error(f"Patient note delete error: {e}")
            return False
    
    def get_by_id(self, note_id: int) -> Optional[PatientNote]:
        """ID ile not getir"""
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, patient_id, note_text, created_at, updated_at
                FROM patient_notes
                WHERE id = ?
            """, (note_id,))
            
            row = cursor.fetchone()
            
            if row:
                return PatientNote(
                    id=row[0],
                    patient_id=row[1],
                    note_text=row[2],
                    created_at=datetime.fromisoformat(row[3]) if row[3] else None,
                    updated_at=datetime.fromisoformat(row[4]) if row[4] else None
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Get patient note error: {e}")
            return None
    
    def find_by_patient(self, patient_id: int) -> List[PatientNote]:
        """Hastanın tüm notlarını getir (en yeni üstte)"""
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, patient_id, note_text, created_at, updated_at
                FROM patient_notes
                WHERE patient_id = ?
                ORDER BY created_at DESC
            """, (patient_id,))
            
            rows = cursor.fetchall()
            
            notes = []
            for row in rows:
                notes.append(PatientNote(
                    id=row[0],
                    patient_id=row[1],
                    note_text=row[2],
                    created_at=datetime.fromisoformat(row[3]) if row[3] else None,
                    updated_at=datetime.fromisoformat(row[4]) if row[4] else None
                ))
            
            return notes
            
        except Exception as e:
            logger.error(f"Find patient notes error: {e}")
            return []