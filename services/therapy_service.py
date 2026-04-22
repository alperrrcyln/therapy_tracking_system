"""
Therapy Service
Terapi oturumu islemleri
"""
from typing import Optional, List, Tuple
from datetime import datetime

from database.repositories.session_repository import TherapySessionRepository
from database.models import TherapySession
from core.constants import SessionStatus
from utils.logger import setup_logger

logger = setup_logger(__name__)


class TherapyService:
    """Therapy Service"""

    def __init__(self):
        self.session_repo = TherapySessionRepository()
    
    def create_session(
        self,
        patient_id: int,
        doctor_id: int,
        session_notes: Optional[str] = None,
        therapist_notes: Optional[str] = None,
        video_path: Optional[str] = None
    ) -> Tuple[bool, str, Optional[TherapySession]]:
        """
        Yeni terapi oturumu olustur
        
        Args:
            patient_id: Danisan ID
            doctor_id: Danisma ID
            session_notes: Oturum notlari
            therapist_notes: Terapist notlari
            video_path: Video dosya yolu
        
        Returns:
            (success, message, session)
        """
        try:
            session = TherapySession(
                patient_id=patient_id,
                doctor_id=doctor_id,
                session_date=datetime.now(),
                status=SessionStatus.IN_PROGRESS.value,
                session_notes=session_notes,
                therapist_notes=therapist_notes,
                video_path=video_path
            )
            
            session_id = self.session_repo.create(session)
            
            if session_id is None:
                return False, "Oturum olusturulamadi", None
            
            session.id = session_id
            logger.info(f"Yeni oturum olusturuldu: {session_id}")
            
            return True, "Oturum basariyla olusturuldu", session
            
        except Exception as e:
            logger.error(f"Oturum olusturma hatasi: {e}")
            return False, "Bir hata olustu", None
    
    def get_session_by_id(self, session_id: int) -> Optional[TherapySession]:
        """Oturum ID ile getir"""
        return self.session_repo.find_by_id(session_id)
    
    def get_sessions_by_patient(self, patient_id: int, limit: int = 10) -> List[TherapySession]:
        """Danisana ait oturumlari getir"""
        return self.session_repo.find_by_patient(patient_id, limit)
    
    def get_sessions_by_doctor(self, doctor_id: int, limit: int = 20) -> List[TherapySession]:
        """Danismana ait oturumlari getir"""
        return self.session_repo.find_by_doctor(doctor_id, limit)
    
    def complete_session(
        self,
        session_id: int,
        duration_minutes: int,
        session_notes: Optional[str] = None,
        therapist_notes: Optional[str] = None,
        video_path: Optional[str] = None
    ) -> bool:
        """
        Oturumu tamamla
        
        Args:
            session_id: Oturum ID
            duration_minutes: Sure (dakika)
            session_notes: Oturum notlari
            therapist_notes: Terapist notlari
            video_path: Video dosya yolu
        
        Returns:
            success
        """
        try:
            session = self.session_repo.find_by_id(session_id)
            
            if not session:
                logger.error(f"Oturum bulunamadi: {session_id}")
                return False
            
            # Guncelle
            session.status = SessionStatus.COMPLETED.value
            session.duration_minutes = duration_minutes
            
            if session_notes:
                session.session_notes = session_notes
            
            if therapist_notes:
                session.therapist_notes = therapist_notes
            
            if video_path:
                session.video_path = video_path
            
            success = self.session_repo.update(session)
            
            if success:
                logger.info(f"Oturum tamamlandi: {session_id}, sure={duration_minutes}dk")
                return True
            else:
                logger.error(f"Oturum guncellenemedi: {session_id}")
                return False
            
        except Exception as e:
            logger.error(f"Oturum tamamlama hatasi: {e}")
            return False
    
    def update_session(self, session: TherapySession) -> Tuple[bool, str]:
        """Oturum bilgilerini guncelle"""
        try:
            success = self.session_repo.update(session)
            
            if success:
                return True, "Oturum guncellendi"
            else:
                return False, "Oturum guncellenemedi"
                
        except Exception as e:
            logger.error(f"Oturum guncelleme hatasi: {e}")
            return False, "Bir hata olustu"
    
    def get_patient_session_count(self, patient_id: int) -> int:
        """Danisanin toplam oturum sayisi"""
        return self.session_repo.count_by_patient(patient_id)