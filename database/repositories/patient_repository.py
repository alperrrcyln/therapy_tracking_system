"""
Patient Repository
Danisan CRUD islemleri
"""
from typing import Optional, List
from datetime import datetime, date

from database.db_manager import db_manager
from database.models import Patient, User
from utils.logger import setup_logger

logger = setup_logger(__name__)


class PatientRepository:
    """Patient tablosu icin repository"""
    
    def __init__(self):
        self.db = db_manager
    
    def create(self, patient: Patient) -> Optional[int]:
        """Yeni danisan olustur"""
        try:
            query = """
                INSERT INTO patients (
                    user_id, doctor_id, tc_no, birth_date, gender, 
                    address, emergency_contact_name, emergency_contact_phone,
                    photo_path, medical_history, notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                patient.user_id,
                patient.doctor_id,
                patient.tc_no,
                patient.birth_date.isoformat() if patient.birth_date else None,
                patient.gender,
                patient.address,
                patient.emergency_contact_name,
                patient.emergency_contact_phone,
                patient.photo_path,
                patient.medical_history,
                patient.notes
            )
            
            with self.db.get_cursor() as cursor:
                cursor.execute(query, params)
                patient_id = cursor.lastrowid
                logger.info(f"Yeni danisan olusturuldu: user_id={patient.user_id}, patient_id={patient_id}")
                return patient_id
                
        except Exception as e:
            logger.error(f"Danisan olusturma hatasi: {e}")
            return None
    
    def find_by_id(self, patient_id: int) -> Optional[Patient]:
        """ID ile danisan bul"""
        try:
            query = """
                SELECT p.*, u.email, u.first_name, u.last_name, u.phone
                FROM patients p
                JOIN users u ON p.user_id = u.id
                WHERE p.id = ?
            """
            row = self.db.fetch_one(query, (patient_id,))
            
            if row:
                return self._row_to_patient(row)
            return None
            
        except Exception as e:
            logger.error(f"Danisan bulma hatasi: {e}")
            return None
    
    def find_by_user_id(self, user_id: int) -> Optional[Patient]:
        """User ID ile danisan bul"""
        try:
            query = """
                SELECT p.*, u.email, u.first_name, u.last_name, u.phone
                FROM patients p
                JOIN users u ON p.user_id = u.id
                WHERE p.user_id = ?
            """
            row = self.db.fetch_one(query, (user_id,))
            
            if row:
                return self._row_to_patient(row)
            return None
            
        except Exception as e:
            logger.error(f"Danisan bulma hatasi: {e}")
            return None
    
    def find_all_by_doctor(self, doctor_id: int) -> List[Patient]:
        """Bir danismana ait tum danisanlari getir"""
        try:
            query = """
                SELECT p.*, u.email, u.first_name, u.last_name, u.phone
                FROM patients p
                JOIN users u ON p.user_id = u.id
                WHERE p.doctor_id = ?
                ORDER BY u.last_name, u.first_name
            """
            rows = self.db.fetch_all(query, (doctor_id,))
            
            return [self._row_to_patient(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Danisan listeleme hatasi: {e}")
            return []
    
    def search_patients(self, doctor_id: int, search_term: str) -> List[Patient]:
        """Danisan ara"""
        try:
            query = """
                SELECT p.*, u.email, u.first_name, u.last_name, u.phone
                FROM patients p
                JOIN users u ON p.user_id = u.id
                WHERE p.doctor_id = ?
                AND (
                    u.first_name LIKE ? OR 
                    u.last_name LIKE ? OR 
                    u.email LIKE ? OR
                    p.tc_no LIKE ?
                )
                ORDER BY u.last_name, u.first_name
            """
            search_pattern = f"%{search_term}%"
            params = (doctor_id, search_pattern, search_pattern, search_pattern, search_pattern)
            
            rows = self.db.fetch_all(query, params)
            return [self._row_to_patient(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Danisan arama hatasi: {e}")
            return []
    
    def update(self, patient: Patient) -> bool:
        """Danisan bilgilerini guncelle"""
        try:
            query = """
                UPDATE patients 
                SET doctor_id = ?, tc_no = ?, birth_date = ?, gender = ?,
                    address = ?, emergency_contact_name = ?, emergency_contact_phone = ?,
                    photo_path = ?, medical_history = ?, notes = ?, updated_at = ?
                WHERE id = ?
            """
            params = (
                patient.doctor_id,
                patient.tc_no,
                patient.birth_date.isoformat() if patient.birth_date else None,
                patient.gender,
                patient.address,
                patient.emergency_contact_name,
                patient.emergency_contact_phone,
                patient.photo_path,
                patient.medical_history,
                patient.notes,
                datetime.now().isoformat(),
                patient.id
            )
            
            self.db.execute_query(query, params)
            logger.info(f"Danisan guncellendi: {patient.id}")
            return True
            
        except Exception as e:
            logger.error(f"Danisan guncelleme hatasi: {e}")
            return False
    
    def delete(self, patient_id: int) -> bool:
        """Danisani sil"""
        try:
            query = "DELETE FROM patients WHERE id = ?"
            self.db.execute_query(query, (patient_id,))
            logger.info(f"Danisan silindi: {patient_id}")
            return True
            
        except Exception as e:
            logger.error(f"Danisan silme hatasi: {e}")
            return False
    
    def _row_to_patient(self, row) -> Patient:
        """Database row'unu Patient objesine donustur"""
        patient = Patient(
            id=row['id'],
            user_id=row['user_id'],
            doctor_id=row['doctor_id'],
            tc_no=row['tc_no'],
            birth_date=date.fromisoformat(row['birth_date']) if row['birth_date'] else None,
            gender=row['gender'],
            address=row['address'],
            emergency_contact_name=row['emergency_contact_name'],
            emergency_contact_phone=row['emergency_contact_phone'],
            photo_path=row['photo_path'],
            medical_history=row['medical_history'],
            notes=row['notes'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
        )
        
        patient.user = User(
            id=row['user_id'],
            email=row['email'],
            first_name=row['first_name'],
            last_name=row['last_name'],
            phone=row['phone']
        )
        
        return patient