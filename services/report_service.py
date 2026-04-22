"""
Report Service
Rapor oluşturma ve veri analizi servisi
"""
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

from database.repositories.patient_repository import PatientRepository
from database.repositories.session_repository import TherapySessionRepository
from database.repositories.emotion_repository import EmotionAnalysisRepository
from database.repositories.appointment_repository import AppointmentRepository
from database.models import Patient, TherapySession, EmotionAnalysis
from utils.logger import setup_logger

logger = setup_logger(__name__)


class ReportService:
    """Rapor servisi"""
    
    def __init__(self):
        self.patient_repo = PatientRepository()
        self.therapy_repo = TherapySessionRepository()
        self.emotion_repo = EmotionAnalysisRepository()
        self.appointment_repo = AppointmentRepository()
    
    def get_patient_summary_report(self, patient_id: int) -> Optional[Dict]:
        """Hasta özet raporu"""
        try:
            # Hastayı getir
            patient = self.patient_repo.find_by_id(patient_id)
            if not patient:
                logger.warning(f"Patient not found: {patient_id}")
                return None
            
            sessions = self.therapy_repo.find_by_patient(patient_id, limit=1000)
            total_sessions = len(sessions)
            completed_sessions = len([s for s in sessions if s.status == 'completed'])
            
            # Son 30 gün
            thirty_days_ago = datetime.now() - timedelta(days=30)
            recent_sessions = [s for s in sessions if s.session_date and s.session_date >= thirty_days_ago]
            
            # Toplam süre
            total_minutes = sum(s.duration_minutes or 0 for s in sessions)
            
            # Emotion analizi
            emotion_summary = self._get_emotion_summary(patient_id)
            
            return {
                'patient': patient,
                'total_sessions': total_sessions,
                'completed_sessions': completed_sessions,
                'recent_sessions_count': len(recent_sessions),
                'total_duration_hours': round(total_minutes / 60, 1),
                'emotion_summary': emotion_summary,
                'sessions': sessions[:10],  # Son 10
                'generated_at': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Patient summary report error: {e}")
            return None
    
    def get_period_report(self, doctor_id: int, start_date: datetime, end_date: datetime) -> Dict:
        """Dönem raporu (belirli tarih aralığı)"""
        try:
            # Tüm hastalar
            patients = self.patient_repo.find_all_by_doctor(doctor_id)
            
            # Dönem içi görüşmeler
            sessions = []
            for patient in patients:
                patient_sessions = self.therapy_repo.find_by_patient(patient.id, limit=1000)
                sessions.extend([
                    s for s in patient_sessions 
                    if s.session_date and start_date <= s.session_date <= end_date
                ])
            
            # İstatistikler
            total_patients = len(patients)
            active_patients = len(set(s.patient_id for s in sessions))
            total_sessions = len(sessions)
            completed = len([s for s in sessions if s.status == 'completed'])
            cancelled = len([s for s in sessions if s.status == 'cancelled'])
            
            total_minutes = sum(s.duration_minutes or 0 for s in sessions)
            
            # Günlük dağılım
            daily_distribution = self._get_daily_distribution(sessions)
            
            return {
                'period': {
                    'start': start_date,
                    'end': end_date,
                    'days': (end_date - start_date).days
                },
                'statistics': {
                    'total_patients': total_patients,
                    'active_patients': active_patients,
                    'total_sessions': total_sessions,
                    'completed_sessions': completed,
                    'cancelled_sessions': cancelled,
                    'total_hours': round(total_minutes / 60, 1),
                    'avg_session_duration': round(total_minutes / total_sessions, 0) if total_sessions > 0 else 0
                },
                'daily_distribution': daily_distribution,
                'sessions': sessions,
                'generated_at': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Period report error: {e}")
            return {}
    
    def get_emotion_analysis_report(self, patient_id: int) -> Dict:
        """Duygu analizi raporu"""
        try:
            sessions = self.therapy_repo.find_by_patient(patient_id, limit=1000)
            
            emotion_data = []
            for session in sessions:
                emotions = self.emotion_repo.find_by_session(session.id)
                if emotions:
                    emotion_data.append({
                        'session': session,
                        'emotions': emotions,
                        'summary': self._analyze_session_emotions(emotions)
                    })
            
            # Genel trend
            overall_trend = self._calculate_emotion_trend(emotion_data)
            
            return {
                'patient_id': patient_id,
                'total_sessions_analyzed': len(emotion_data),
                'emotion_data': emotion_data,
                'overall_trend': overall_trend,
                'generated_at': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Emotion analysis report error: {e}")
            return {}
    
    def get_doctor_performance_report(self, doctor_id: int) -> Dict:
        """Doktor performans raporu"""
        try:
            # Son 90 gün
            ninety_days_ago = datetime.now() - timedelta(days=90)
            
            patients = self.patient_repo.find_by_doctor(doctor_id)
            
            all_sessions = []
            for patient in patients:
                sessions = self.therapy_repo.find_by_patient(patient.id)
                all_sessions.extend(sessions)
            
            recent_sessions = [s for s in all_sessions if s.session_date and s.session_date >= ninety_days_ago]
            
            # Haftalık dağılım
            weekly_stats = self._get_weekly_stats(recent_sessions)
            
            # Hasta memnuniyeti (tamamlama oranı)
            completion_rate = self._calculate_completion_rate(all_sessions)
            
            return {
                'doctor_id': doctor_id,
                'total_patients': len(patients),
                'total_sessions_90_days': len(recent_sessions),
                'weekly_stats': weekly_stats,
                'completion_rate': completion_rate,
                'avg_sessions_per_week': len(recent_sessions) / 13 if recent_sessions else 0,
                'generated_at': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Doctor performance report error: {e}")
            return {}
    
    def _get_emotion_summary(self, patient_id: int) -> Dict:
        """Hasta için duygu özeti"""
        sessions = self.therapy_repo.find_by_patient(patient_id, limit=1000)
        
        emotion_counts = defaultdict(int)
        total_emotions = 0
        
        for session in sessions:
            emotions = self.emotion_repo.find_by_session(session.id)
            for emotion in emotions:
                emotion_counts[emotion.emotion_type] += 1
                total_emotions += 1
        
        # Yüzdelik
        emotion_percentages = {}
        if total_emotions > 0:
            for emotion, count in emotion_counts.items():
                emotion_percentages[emotion] = round((count / total_emotions) * 100, 1)
        
        return {
            'total_analyzed': total_emotions,
            'distribution': dict(emotion_counts),
            'percentages': emotion_percentages,
            'dominant_emotion': max(emotion_counts, key=emotion_counts.get) if emotion_counts else None
        }
    
    def _get_daily_distribution(self, sessions: List[TherapySession]) -> Dict:
        """Günlük görüşme dağılımı"""
        daily_counts = defaultdict(int)
        
        for session in sessions:
            if session.session_date:
                date_str = session.session_date.strftime('%Y-%m-%d')
                daily_counts[date_str] += 1
        
        return dict(sorted(daily_counts.items()))
    
    def _analyze_session_emotions(self, emotions: List[EmotionAnalysis]) -> Dict:
        """Bir görüşmenin duygu analizi"""
        if not emotions:
            return {}
        
        emotion_counts = defaultdict(int)
        total_confidence = 0
        
        for emotion in emotions:
            emotion_counts[emotion.emotion_type] += 1
            total_confidence += emotion.confidence
        
        return {
            'total_frames': len(emotions),
            'dominant_emotion': max(emotion_counts, key=emotion_counts.get),
            'avg_confidence': round(total_confidence / len(emotions), 2),
            'distribution': dict(emotion_counts)
        }
    
    def _calculate_emotion_trend(self, emotion_data: List[Dict]) -> Dict:
        """Duygu trendi hesapla"""
        if not emotion_data:
            return {}
        
        # Zaman içinde dominant emotion değişimi
        trend = []
        for data in emotion_data:
            trend.append({
                'date': data['session'].session_date,
                'emotion': data['summary'].get('dominant_emotion')
            })
        
        return {'trend': trend}
    
    def _get_weekly_stats(self, sessions: List[TherapySession]) -> List[Dict]:
        """Haftalık istatistikler"""
        weekly_data = defaultdict(int)
        
        for session in sessions:
            if session.session_date:
                week_start = session.session_date - timedelta(days=session.session_date.weekday())
                week_key = week_start.strftime('%Y-%m-%d')
                weekly_data[week_key] += 1
        
        return [{'week': k, 'sessions': v} for k, v in sorted(weekly_data.items())]
    
    def _calculate_completion_rate(self, sessions: List[TherapySession]) -> float:
        """Tamamlama oranı"""
        if not sessions:
            return 0.0
        
        completed = len([s for s in sessions if s.status == 'completed'])
        return round((completed / len(sessions)) * 100, 1)