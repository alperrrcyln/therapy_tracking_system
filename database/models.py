"""
Database Models
Veritabanı model sınıfları
"""
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, date

from core.constants import UserRole, SessionStatus, EmotionType, AppointmentStatus


@dataclass
class User:
    """Kullanıcı modeli"""
    email: str
    password_hash: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    role: str = UserRole.PATIENT.value
    is_active: bool = True
    last_login: Optional[datetime] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @property
    def is_doctor(self) -> bool:
        """Doktor mu?"""
        return self.role == UserRole.DOCTOR.value
    
    @property
    def is_patient(self) -> bool:
        """Danışan mı?"""
        return self.role == UserRole.PATIENT.value
    
    @property
    def full_name(self) -> str:
        """Ad Soyad"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.email


@dataclass
class Patient:
    """Danışan modeli"""
    user_id: int
    doctor_id: int
    tc_no: Optional[str] = None
    birth_date: Optional[date] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    photo_path: Optional[str] = None
    medical_history: Optional[str] = None
    notes: Optional[str] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    user: Optional[User] = None
    
    @property
    def age(self) -> Optional[int]:
        """Yaş hesapla"""
        if self.birth_date:
            today = date.today()
            return today.year - self.birth_date.year - (
                (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
            )
        return None


@dataclass
class TherapySession:
    """Terapi oturumu modeli"""
    patient_id: int
    doctor_id: int
    session_date: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    status: str = SessionStatus.SCHEDULED.value
    session_notes: Optional[str] = None
    therapist_notes: Optional[str] = None
    diagnosis: Optional[str] = None
    video_path: Optional[str] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    patient: Optional[Patient] = None
    doctor: Optional[User] = None


@dataclass
class EmotionAnalysis:
    """Duygu analizi modeli"""
    session_id: int
    emotion_type: str  
    confidence: float
    timestamp: Optional[datetime] = None
    frame_number: Optional[int] = None
    additional_data: Optional[str] = None
    face_detected: bool = True
    id: Optional[int] = None
    created_at: Optional[datetime] = None


@dataclass
class Appointment:
    """Randevu modeli"""
    patient_id: int
    doctor_id: int
    appointment_date: datetime
    duration_minutes: int = 60
    status: str = AppointmentStatus.PENDING.value
    notes: Optional[str] = None
    cancellation_reason: Optional[str] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    patient: Optional[Patient] = None
    doctor: Optional[User] = None


@dataclass
class PatientDiary:
    """Danışan günlüğü modeli"""
    patient_id: int
    entry_date: datetime
    mood_rating: Optional[int] = None
    content: Optional[str] = None
    is_private: bool = True
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class SessionNote:
    """Oturum notu modeli"""
    session_id: int
    note_type: str
    content: str
    timestamp: Optional[datetime] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None


@dataclass
class PatientNote:
    """Danışan notu modeli"""
    patient_id: int
    note_text: str
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class Message:
    """Chat mesajı"""
    id: Optional[int] = None
    sender_id: int = 0  # User ID (doctor veya patient)
    receiver_id: int = 0  # User ID (doctor veya patient)
    session_id: Optional[int] = None  # Hangi therapy session'a ait (opsiyonel)
    message_text: str = ""
    message_type: str = "text"  # text, image, file
    sent_at: Optional[datetime] = None
    is_read: bool = False
    created_at: Optional[datetime] = None


@dataclass
class VideoSession:
    """Video/sesli görüşme kaydı"""
    id: Optional[int] = None
    doctor_id: int = 0
    patient_id: int = 0
    session_type: str = "video"  # video, audio
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    duration_seconds: int = 0
    recording_path: Optional[str] = None  # Video/audio dosya yolu
    recording_size_mb: float = 0.0
    notes: Optional[str] = None
    created_at: Optional[datetime] = None    

@dataclass
class Session:
    """Görüşme modeli"""
    id: int = None
    patient_id: int = None
    doctor_id: int = None
    session_date: datetime = None
    session_type: str = "regular"  # regular, video, audio
    duration_minutes: int = 0
    notes: str = ""
    mood_before: int = 5
    mood_after: int = 5
    created_at: datetime = None    