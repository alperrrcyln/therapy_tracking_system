"""
Message Repository
Chat mesajları için CRUD işlemleri
"""
from typing import List, Optional
from datetime import datetime

from database.db_manager import db_manager
from database.models import Message
from utils.logger import setup_logger

logger = setup_logger(__name__)


class MessageRepository:
    """Message repository"""
    
    def __init__(self):
        self.db = db_manager
    
    def create(self, message: Message) -> Optional[int]:
        """Yeni mesaj ekle"""
        try:
            query = """
                INSERT INTO messages (sender_id, receiver_id, session_id, message_text, 
                                     message_type, sent_at, is_read)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(query, (
                message.sender_id,
                message.receiver_id,
                message.session_id,
                message.message_text,
                message.message_type,
                message.sent_at or datetime.now(),
                message.is_read
            ))
            
            conn.commit()
            message_id = cursor.lastrowid
            
            logger.info(f"Message created: {message_id}")
            return message_id
            
        except Exception as e:
            logger.error(f"Message create error: {e}")
            return None
    
    def find_conversation(self, user1_id: int, user2_id: int, limit: int = 100) -> List[Message]:
        """İki kullanıcı arasındaki konuşmayı getir"""
        try:
            query = """
                SELECT * FROM messages
                WHERE (sender_id = ? AND receiver_id = ?)
                   OR (sender_id = ? AND receiver_id = ?)
                ORDER BY sent_at DESC
                LIMIT ?
            """
            
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(query, (user1_id, user2_id, user2_id, user1_id, limit))
            rows = cursor.fetchall()
            
            messages = [self._row_to_message(row) for row in rows]
            messages.reverse()  # Kronolojik sıra (eski → yeni)
            
            return messages
            
        except Exception as e:
            logger.error(f"Find conversation error: {e}")
            return []
    
    def find_by_session(self, session_id: int) -> List[Message]:
        """Belirli bir session'a ait mesajları getir"""
        try:
            query = """
                SELECT * FROM messages
                WHERE session_id = ?
                ORDER BY sent_at ASC
            """
            
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(query, (session_id,))
            rows = cursor.fetchall()
            
            return [self._row_to_message(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Find by session error: {e}")
            return []
    
    def mark_as_read(self, message_id: int) -> bool:
        """Mesajı okundu olarak işaretle"""
        try:
            query = "UPDATE messages SET is_read = 1 WHERE id = ?"
            
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(query, (message_id,))
            conn.commit()
            
            return cursor.rowcount > 0
            
        except Exception as e:
            logger.error(f"Mark as read error: {e}")
            return False
    
    def mark_conversation_as_read(self, sender_id: int, receiver_id: int) -> bool:
        """Konuşmadaki tüm mesajları okundu olarak işaretle"""
        try:
            query = """
                UPDATE messages 
                SET is_read = 1 
                WHERE sender_id = ? AND receiver_id = ? AND is_read = 0
            """
            
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(query, (sender_id, receiver_id))
            conn.commit()
            
            logger.info(f"Marked {cursor.rowcount} messages as read")
            return True
            
        except Exception as e:
            logger.error(f"Mark conversation as read error: {e}")
            return False
    
    def get_unread_count(self, receiver_id: int) -> int:
        """Okunmamış mesaj sayısı"""
        try:
            query = "SELECT COUNT(*) FROM messages WHERE receiver_id = ? AND is_read = 0"
            
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(query, (receiver_id,))
            row = cursor.fetchone()
            
            return row[0] if row else 0
            
        except Exception as e:
            logger.error(f"Get unread count error: {e}")
            return 0
    
    def get_last_message(self, user1_id: int, user2_id: int) -> Optional[Message]:
        """İki kullanıcı arasındaki son mesaj"""
        try:
            query = """
                SELECT * FROM messages
                WHERE (sender_id = ? AND receiver_id = ?)
                   OR (sender_id = ? AND receiver_id = ?)
                ORDER BY sent_at DESC
                LIMIT 1
            """
            
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(query, (user1_id, user2_id, user2_id, user1_id))
            row = cursor.fetchone()
            
            return self._row_to_message(row) if row else None
            
        except Exception as e:
            logger.error(f"Get last message error: {e}")
            return None
    
    def _row_to_message(self, row) -> Message:
        """Database row'u Message objesine dönüştür"""
        return Message(
            id=row['id'],
            sender_id=row['sender_id'],
            receiver_id=row['receiver_id'],
            session_id=row['session_id'],
            message_text=row['message_text'],
            message_type=row['message_type'],
            sent_at=datetime.fromisoformat(row['sent_at']) if row['sent_at'] else None,
            is_read=bool(row['is_read']),
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
        )