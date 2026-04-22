"""
Appointment Repository
Randevu CRUD islemleri
"""
from typing import Optional, List
from datetime import datetime, date

from database.db_manager import db_manager
from database.models import Appointment, Patient, User
from utils.logger import setup_logger

logger = setup_logger(__name__)


class AppointmentRepository:
    """Appointment tablosu repository"""
    
    def __init__(self):
        self.db = db_manager
    
    def create(self, appointment: Appointment) -> Optional[int]:
        """Yeni randevu olustur"""
        try:
            query = """
                INSERT INTO appointments (
                    patient_id, doctor_id, appointment_date, 
                    duration_minutes, notes
                )
                VALUES (?, ?, ?, ?, ?)
            """
            params = (
                appointment.patient_id,
                appointment.doctor_id,
                appointment.appointment_date.isoformat(),
                appointment.duration_minutes,
                appointment.notes
            )
            
            with self.db.get_cursor() as cursor:
                cursor.execute(query, params)
                appointment_id = cursor.lastrowid
                logger.info(f"Yeni randevu olusturuldu: {appointment_id}")
                return appointment_id
                
        except Exception as e:
            logger.error(f"Randevu olusturma hatasi: {e}")
            return None
    
    def find_by_id(self, appointment_id: int) -> Optional[Appointment]:
        """ID ile randevu bul"""
        try:
            query = "SELECT * FROM appointments WHERE id = ?"
            row = self.db.fetch_one(query, (appointment_id,))
            
            if row:
                return self._row_to_appointment(row)
            return None
            
        except Exception as e:
            logger.error(f"Randevu bulma hatasi: {e}")
            return None
    
    def find_by_doctor(self, doctor_id: int, limit: int = 50) -> List[Appointment]:
        """Doktora ait randevular"""
        try:
            query = """
                SELECT * FROM appointments
                WHERE doctor_id = ?
                ORDER BY appointment_date DESC
                LIMIT ?
            """
            rows = self.db.fetch_all(query, (doctor_id, limit))
            return [self._row_to_appointment(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Randevu listeleme hatasi: {e}")
            return []
    
    def find_by_patient(self, patient_id: int) -> List[Appointment]:
        """Danisana ait randevular"""
        try:
            query = """
                SELECT * FROM appointments
                WHERE patient_id = ?
                ORDER BY appointment_date DESC
            """
            rows = self.db.fetch_all(query, (patient_id,))
            return [self._row_to_appointment(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Randevu listeleme hatasi: {e}")
            return []
    
    def find_upcoming(self, doctor_id: int) -> List[Appointment]:
        """Yaklasan randevular (gelecek)"""
        try:
            now = datetime.now().isoformat()
            query = """
                SELECT * FROM appointments
                WHERE doctor_id = ? AND appointment_date >= ? AND status IN ('pending', 'confirmed')
                ORDER BY appointment_date ASC
            """
            rows = self.db.fetch_all(query, (doctor_id, now))
            return [self._row_to_appointment(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Yaklasan randevu listeleme hatasi: {e}")
            return []
    
    def update(self, appointment: Appointment) -> bool:
        """Randevu guncelle"""
        try:
            query = """
                UPDATE appointments
                SET appointment_date = ?, duration_minutes = ?, 
                    status = ?, notes = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """
            params = (
                appointment.appointment_date.isoformat(),
                appointment.duration_minutes,
                appointment.status,
                appointment.notes,
                appointment.id
            )
            
            with self.db.get_cursor() as cursor:
                cursor.execute(query, params)
                logger.info(f"Randevu guncellendi: {appointment.id}")
                return True
                
        except Exception as e:
            logger.error(f"Randevu guncelleme hatasi: {e}")
            return False
    
    def delete(self, appointment_id: int) -> bool:
        """Randevu sil"""
        try:
            query = "DELETE FROM appointments WHERE id = ?"
            
            with self.db.get_cursor() as cursor:
                cursor.execute(query, (appointment_id,))
                logger.info(f"Randevu silindi: {appointment_id}")
                return True
                
        except Exception as e:
            logger.error(f"Randevu silme hatasi: {e}")
            return False
    
    def _row_to_appointment(self, row) -> Appointment:
        """Database satiri -> Appointment objesi"""
        return Appointment(
            id=row['id'],
            patient_id=row['patient_id'],
            doctor_id=row['doctor_id'],
            appointment_date=datetime.fromisoformat(row['appointment_date']),
            duration_minutes=row['duration_minutes'],
            status=row['status'],
            notes=row['notes'],
            cancellation_reason=None,  # Tabloda yok
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
        )