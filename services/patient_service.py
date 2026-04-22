"""
Patient Service
Danışan işlemleri (CRUD ve iş mantığı)
"""
from typing import Optional, List, Tuple
from datetime import date

from database.repositories.patient_repository import PatientRepository
from database.repositories.user_repository import UserRepository
from database.models import Patient, User
from core.constants import UserRole
from utils.validators import validate_tc_no, validate_phone, validate_age
from utils.logger import setup_logger

logger = setup_logger(__name__)


class PatientService:
    """Patient Service"""
    
    def __init__(self):
        self.patient_repo = PatientRepository()
        self.user_repo = UserRepository()
    
    def create_patient(
        self,
        user_id: int,
        doctor_id: int,
        tc_no: Optional[str] = None,
        birth_date: Optional[date] = None,
        gender: Optional[str] = None,
        address: Optional[str] = None,
        emergency_contact_name: Optional[str] = None,
        emergency_contact_phone: Optional[str] = None,
        medical_history: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Tuple[bool, str, Optional[Patient]]:
        """
        Yeni danışan profili oluştur
        
        Args:
            user_id: User ID
            doctor_id: Atanacak danışman ID
            tc_no: TC Kimlik No
            birth_date: Doğum tarihi
            gender: Cinsiyet
            address: Adres
            emergency_contact_name: Acil durum iletişim adı
            emergency_contact_phone: Acil durum telefon
            medical_history: Tıbbi geçmiş
            notes: Notlar
        
        Returns:
            (success, message, patient)
        """
        try:
            # Validasyonlar
            if tc_no:
                is_valid, error_msg = validate_tc_no(tc_no)
                if not is_valid:
                    return False, error_msg, None
            
            if emergency_contact_phone:
                is_valid, error_msg = validate_phone(emergency_contact_phone)
                if not is_valid:
                    return False, error_msg, None
            
            # User'ın patient rolünde olduğunu kontrol et
            user = self.user_repo.find_by_id(user_id)
            if not user or user.role != UserRole.PATIENT.value:
                return False, "Geçersiz kullanıcı", None
            
            # Doctor kontrolü
            doctor = self.user_repo.find_by_id(doctor_id)
            if not doctor or doctor.role != UserRole.DOCTOR.value:
                return False, "Geçersiz danışman", None
            
            # Patient profili zaten var mı?
            existing = self.patient_repo.find_by_user_id(user_id)
            if existing:
                return False, "Bu kullanıcının danışan profili zaten mevcut", None
            
            # Patient oluştur
            patient = Patient(
                user_id=user_id,
                doctor_id=doctor_id,
                tc_no=tc_no,
                birth_date=birth_date,
                gender=gender,
                address=address,
                emergency_contact_name=emergency_contact_name,
                emergency_contact_phone=emergency_contact_phone,
                medical_history=medical_history,
                notes=notes
            )
            
            patient_id = self.patient_repo.create(patient)
            if patient_id is None:
                return False, "Danışan profili oluşturulamadı", None
            
            patient.id = patient_id
            patient.user = user
            
            logger.info(f"Danışan profili oluşturuldu: user_id={user_id}, patient_id={patient_id}")
            return True, "Danışan profili oluşturuldu", patient
            
        except Exception as e:
            logger.error(f"Danışan oluşturma hatası: {e}")
            return False, "Bir hata oluştu", None
    
    def get_patient_by_id(self, patient_id: int) -> Optional[Patient]:
        """
        Danışan ID ile getir
        
        Args:
            patient_id: Danışan ID
        
        Returns:
            Patient objesi veya None
        """
        return self.patient_repo.find_by_id(patient_id)
    
    def get_patient_by_user_id(self, user_id: int) -> Optional[Patient]:
        """
        User ID ile danışan getir
        
        Args:
            user_id: User ID
        
        Returns:
            Patient objesi veya None
        """
        return self.patient_repo.find_by_user_id(user_id)
    
    def get_patients_by_doctor(self, doctor_id: int) -> List[Patient]:
        """
        Bir danışmana ait tüm danışanları getir
        
        Args:
            doctor_id: Danışman ID
        
        Returns:
            Patient listesi
        """
        return self.patient_repo.find_all_by_doctor(doctor_id)
    
    def search_patients(self, doctor_id: int, search_term: str) -> List[Patient]:
        """
        Danışan ara
        
        Args:
            doctor_id: Danışman ID
            search_term: Arama terimi
        
        Returns:
            Eşleşen Patient listesi
        """
        if not search_term or len(search_term.strip()) < 2:
            return self.get_patients_by_doctor(doctor_id)
        
        return self.patient_repo.search_patients(doctor_id, search_term.strip())
    
    def update_patient(self, patient: Patient) -> Tuple[bool, str]:
        """
        Danışan bilgilerini güncelle
        
        Args:
            patient: Güncellenmiş Patient objesi
        
        Returns:
            (success, message)
        """
        try:
            # Validasyonlar
            if patient.tc_no:
                is_valid, error_msg = validate_tc_no(patient.tc_no)
                if not is_valid:
                    return False, error_msg
            
            if patient.emergency_contact_phone:
                is_valid, error_msg = validate_phone(patient.emergency_contact_phone)
                if not is_valid:
                    return False, error_msg
            
            success = self.patient_repo.update(patient)
            
            if success:
                logger.info(f"Danışan güncellendi: patient_id={patient.id}")
                return True, "Danışan bilgileri güncellendi"
            else:
                return False, "Güncelleme başarısız"
            
        except Exception as e:
            logger.error(f"Danışan güncelleme hatası: {e}")
            return False, "Bir hata oluştu"
    
    def delete_patient(self, patient_id: int) -> Tuple[bool, str]:
        """
        Danışanı sil
        
        Args:
            patient_id: Danışan ID
        
        Returns:
            (success, message)
        """
        try:
            # Önce danışanı kontrol et
            patient = self.get_patient_by_id(patient_id)
            if not patient:
                return False, "Danışan bulunamadı"
            
            success = self.patient_repo.delete(patient_id)
            
            if success:
                logger.info(f"Danışan silindi: patient_id={patient_id}")
                return True, "Danışan silindi"
            else:
                return False, "Silme başarısız"
            
        except Exception as e:
            logger.error(f"Danışan silme hatası: {e}")
            return False, "Bir hata oluştu"
    
    def assign_doctor(self, patient_id: int, doctor_id: int) -> Tuple[bool, str]:
        """
        Danışana danışman ata
        
        Args:
            patient_id: Danışan ID
            doctor_id: Danışman ID
        
        Returns:
            (success, message)
        """
        try:
            patient = self.get_patient_by_id(patient_id)
            if not patient:
                return False, "Danışan bulunamadı"
            
            doctor = self.user_repo.find_by_id(doctor_id)
            if not doctor or doctor.role != UserRole.DOCTOR.value:
                return False, "Geçersiz danışman"
            
            patient.doctor_id = doctor_id
            success = self.patient_repo.update(patient)
            
            if success:
                logger.info(f"Danışman atandı: patient_id={patient_id}, doctor_id={doctor_id}")
                return True, "Danışman atandı"
            else:
                return False, "Atama başarısız"
            
        except Exception as e:
            logger.error(f"Danışman atama hatası: {e}")
            return False, "Bir hata oluştu"
    
    def get_patient_count_by_doctor(self, doctor_id: int) -> int:
        """
        Danışmanın toplam danışan sayısı
        
        Args:
            doctor_id: Danışman ID
        
        Returns:
            Danışan sayısı
        """
        patients = self.get_patients_by_doctor(doctor_id)
        return len(patients)