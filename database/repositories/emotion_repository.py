"""
Emotion Analysis Repository
Duygu analiz kayitlari CRUD islemleri
"""
from typing import Optional, List
from datetime import datetime

from database.db_manager import db_manager
from database.models import EmotionAnalysis
from utils.logger import setup_logger

logger = setup_logger(__name__)


class EmotionAnalysisRepository:
    """Emotion Analysis tablosu icin repository"""
    
    def __init__(self):
        self.db = db_manager
    
    def create(self, emotion: EmotionAnalysis) -> Optional[int]:
        """Yeni duygu analiz kaydi olustur"""
        try:
            query = """
                INSERT INTO emotion_analysis (
                    session_id, emotion_type, confidence, frame_number, additional_data
                )
                VALUES (?, ?, ?, ?, ?)
            """
            params = (
                emotion.session_id,
                emotion.emotion_type,
                emotion.confidence,
                emotion.frame_number,
                emotion.additional_data
            )
            
            with self.db.get_cursor() as cursor:
                cursor.execute(query, params)
                emotion_id = cursor.lastrowid
                return emotion_id
                
        except Exception as e:
            logger.error(f"Emotion kayit hatasi: {e}")
            return None
    
    def find_by_session(self, session_id: int) -> List[EmotionAnalysis]:
        """Session'a ait tum duygu kayitlarini getir"""
        try:
            query = """
                SELECT * FROM emotion_analysis
                WHERE session_id = ?
                ORDER BY timestamp ASC
            """
            rows = self.db.fetch_all(query, (session_id,))
            
            emotions = []
            for row in rows:
                emotion = EmotionAnalysis(
                    id=row['id'],
                    session_id=row['session_id'],
                    timestamp=datetime.fromisoformat(row['timestamp']) if row['timestamp'] else None,
                    emotion_type=row['emotion_type'],  # emotion -> emotion_type
                    confidence=row['confidence'],
                    frame_number=row['frame_number'],
                    additional_data=row['additional_data']
                )
                emotions.append(emotion)
            
            return emotions
            
        except Exception as e:
            logger.error(f"Emotion listeleme hatasi: {e}")
            return []
    
    def get_emotion_stats(self, session_id: int) -> dict:
        """Session'daki duygu dagilimini getir"""
        try:
            query = """
                SELECT emotion_type, COUNT(*) as count, AVG(confidence) as avg_confidence
                FROM emotion_analysis
                WHERE session_id = ?
                GROUP BY emotion_type
                ORDER BY count DESC
            """
            rows = self.db.fetch_all(query, (session_id,))
            
            stats = {}
            for row in rows:
                stats[row['emotion_type']] = {
                    'count': row['count'],
                    'avg_confidence': row['avg_confidence']
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"Emotion stats hatasi: {e}")
            return {}
    
    def count_by_session(self, session_id: int) -> int:
        """Session'daki toplam duygu kaydi sayisi"""
        try:
            query = "SELECT COUNT(*) as count FROM emotion_analysis WHERE session_id = ?"
            row = self.db.fetch_one(query, (session_id,))
            return row['count'] if row else 0
        except Exception as e:
            logger.error(f"Emotion sayma hatasi: {e}")
            return 0