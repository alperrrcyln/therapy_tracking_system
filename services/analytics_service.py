"""
Analytics Service
Gelişmiş veri analizi ve istatistikler
"""
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

from database.repositories.patient_repository import PatientRepository
from database.repositories.session_repository import TherapySessionRepository
from database.repositories.emotion_repository import EmotionAnalysisRepository
from database.repositories.appointment_repository import AppointmentRepository
from utils.logger import setup_logger

logger = setup_logger(__name__)


class AnalyticsService:
    """Analitik servisi"""
    
    def __init__(self):
        self.patient_repo = PatientRepository()
        self.session_repo = TherapySessionRepository()
        self.emotion_repo = EmotionAnalysisRepository()
        self.appointment_repo = AppointmentRepository()
    
    def get_session_trends(self, doctor_id: int, days: int = 90) -> Dict:
        """Görüşme trendleri (son X gün)"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Doktorun tüm hastaları
            patients = self.patient_repo.find_all_by_doctor(doctor_id)
            
            # Tüm görüşmeler
            all_sessions = []
            for patient in patients:
                sessions = self.session_repo.find_by_patient(patient.id, limit=1000)
                all_sessions.extend(sessions)
            
            # Dönem içi görüşmeler
            period_sessions = [
                s for s in all_sessions
                if s.session_date and start_date <= s.session_date <= end_date
            ]
            
            # Günlük dağılım
            daily_counts = defaultdict(int)
            for session in period_sessions:
                if session.session_date:
                    date_key = session.session_date.date()
                    daily_counts[date_key] += 1
            
            # Haftalık ortalama
            weekly_avg = len(period_sessions) / (days / 7) if days >= 7 else 0
            
            # Durum dağılımı
            status_distribution = defaultdict(int)
            for session in period_sessions:
                status_distribution[session.status] += 1
            
            return {
                'total_sessions': len(period_sessions),
                'daily_counts': dict(sorted(daily_counts.items())),
                'weekly_average': round(weekly_avg, 1),
                'status_distribution': dict(status_distribution),
                'period_days': days
            }
            
        except Exception as e:
            logger.error(f"Session trends error: {e}")
            return {}
    
    def get_emotion_trends(self, patient_id: int) -> Dict:
        """Hasta duygu trendleri"""
        try:
            sessions = self.session_repo.find_by_patient(patient_id, limit=1000)
            
            # Her görüşme için dominant emotion
            session_emotions = []
            for session in sessions:
                if not session.session_date:
                    continue
                
                emotions = self.emotion_repo.find_by_session(session.id)
                if not emotions:
                    continue
                
                # En çok görülen emotion
                emotion_counts = defaultdict(int)
                for emotion in emotions:
                    emotion_counts[emotion.emotion_type] += 1
                
                if emotion_counts:
                    dominant = max(emotion_counts, key=emotion_counts.get)
                    session_emotions.append({
                        'date': session.session_date,
                        'dominant_emotion': dominant,
                        'emotion_counts': dict(emotion_counts),
                        'total_frames': len(emotions)
                    })
            
            # Tarih sıralı
            session_emotions.sort(key=lambda x: x['date'])
            
            # Genel dağılım
            overall_distribution = defaultdict(int)
            for se in session_emotions:
                overall_distribution[se['dominant_emotion']] += 1
            
            return {
                'session_emotions': session_emotions,
                'overall_distribution': dict(overall_distribution),
                'total_analyzed_sessions': len(session_emotions)
            }
            
        except Exception as e:
            logger.error(f"Emotion trends error: {e}")
            return {}
    
    def get_patient_progress(self, patient_id: int) -> Dict:
        """Hasta ilerlemesi"""
        try:
            sessions = self.session_repo.find_by_patient(patient_id, limit=1000)
            
            if not sessions:
                return {'has_data': False}
            
            # Tarih sıralı
            sessions.sort(key=lambda x: x.session_date if x.session_date else datetime.min)
            
            # İlk ve son görüşme
            first_session = sessions[0] if sessions else None
            last_session = sessions[-1] if sessions else None
            
            # Görüşme sıklığı
            if len(sessions) >= 2 and first_session and last_session:
                if first_session.session_date and last_session.session_date:
                    days_span = (last_session.session_date - first_session.session_date).days
                    if days_span > 0:
                        frequency = len(sessions) / (days_span / 30)  # Aylık ortalama
                    else:
                        frequency = 0
                else:
                    frequency = 0
            else:
                frequency = 0
            
            # Süre ortalaması
            durations = [s.duration_minutes for s in sessions if s.duration_minutes]
            avg_duration = statistics.mean(durations) if durations else 0
            
            # Son 3 ay trend
            three_months_ago = datetime.now() - timedelta(days=90)
            recent_sessions = [s for s in sessions if s.session_date and s.session_date >= three_months_ago]
            
            return {
                'has_data': True,
                'total_sessions': len(sessions),
                'first_session_date': first_session.session_date if first_session else None,
                'last_session_date': last_session.session_date if last_session else None,
                'monthly_frequency': round(frequency, 1),
                'avg_duration_minutes': round(avg_duration, 0),
                'recent_sessions_count': len(recent_sessions),
                'sessions_timeline': [
                    {
                        'date': s.session_date,
                        'duration': s.duration_minutes,
                        'status': s.status
                    }
                    for s in sessions if s.session_date
                ]
            }
            
        except Exception as e:
            logger.error(f"Patient progress error: {e}")
            return {'has_data': False}
    
    def get_completion_rates(self, doctor_id: int, days: int = 30) -> Dict:
        """Tamamlama oranları"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            patients = self.patient_repo.find_all_by_doctor(doctor_id)
            
            # Randevular
            all_appointments = []
            for patient in patients:
                appointments = self.appointment_repo.find_by_patient(patient.id)
                all_appointments.extend(appointments)
            
            period_appointments = [
                a for a in all_appointments
                if a.appointment_date and start_date <= a.appointment_date <= end_date
            ]
            
            # Durum dağılımı
            status_counts = defaultdict(int)
            for appointment in period_appointments:
                status_counts[appointment.status] += 1
            
            total = len(period_appointments)
            
            rates = {}
            if total > 0:
                for status, count in status_counts.items():
                    rates[status] = round((count / total) * 100, 1)
            
            return {
                'total_appointments': total,
                'status_counts': dict(status_counts),
                'completion_rates': rates,
                'period_days': days
            }
            
        except Exception as e:
            logger.error(f"Completion rates error: {e}")
            return {}
    
    def get_peak_hours(self, doctor_id: int, days: int = 90) -> Dict:
        """En yoğun saatler"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            patients = self.patient_repo.find_all_by_doctor(doctor_id)
            
            all_sessions = []
            for patient in patients:
                sessions = self.session_repo.find_by_patient(patient.id, limit=1000)
                all_sessions.extend(sessions)
            
            period_sessions = [
                s for s in all_sessions
                if s.session_date and start_date <= s.session_date <= end_date
            ]
            
            # Saatlere göre dağılım
            hour_counts = defaultdict(int)
            for session in period_sessions:
                if session.session_date:
                    hour = session.session_date.hour
                    hour_counts[hour] += 1
            
            # Günlere göre dağılım
            weekday_counts = defaultdict(int)
            for session in period_sessions:
                if session.session_date:
                    weekday = session.session_date.strftime('%A')
                    weekday_counts[weekday] += 1
            
            return {
                'hourly_distribution': dict(sorted(hour_counts.items())),
                'weekday_distribution': dict(weekday_counts),
                'peak_hour': max(hour_counts, key=hour_counts.get) if hour_counts else None,
                'peak_day': max(weekday_counts, key=weekday_counts.get) if weekday_counts else None
            }
            
        except Exception as e:
            logger.error(f"Peak hours error: {e}")
            return {}