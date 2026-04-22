"""
Constants
Uygulama sabitleri
"""
from enum import Enum


# Uygulama sabitleri
APP_NAME = "Terapi Takip Sistemi"
WINDOW_TITLE = "Terapi Takip Sistemi"
VERSION = "1.0.0"

# Pencere boyutlari
WINDOW_MIN_WIDTH = 1200
WINDOW_MIN_HEIGHT = 800


class UserRole(Enum):
    """Kullanici rolleri"""
    DOCTOR = "doctor"
    PATIENT = "patient"


class SessionStatus(Enum):
    """Oturum durumlari"""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class EmotionType(Enum):
    """Duygu tipleri"""
    ANGRY = "angry"
    DISGUSTED = "disgusted"
    FEARFUL = "fearful"
    HAPPY = "happy"
    NEUTRAL = "neutral"
    SAD = "sad"
    SURPRISED = "surprised"


class AppointmentStatus(Enum):
    """Randevu durumları"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PageID:
    """Sayfa ID'leri"""
    # Auth
    LOGIN = 0
    
    # Doctor pages
    DOCTOR_DASHBOARD = 10
    PATIENTS_LIST = 11
    PATIENT_DETAIL = 12
    NEW_SESSION = 13
    APPOINTMENTS = 14
    ANALYTICS = 15
    ACTIVITIES = 16
    SEARCH = 17
    REPORTS = 18

    
    # Patient pages
    PATIENT_DASHBOARD = 20
    DIARY = 21
    MY_APPOINTMENTS = 22
    MY_SESSIONS = 23