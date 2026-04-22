"""
Chat Service
Mesajlaşma iş mantığı
"""
from typing import List, Dict, Optional
from datetime import datetime

from database.repositories.message_repository import MessageRepository
from database.repositories.patient_repository import PatientRepository
from database.repositories.user_repository import UserRepository
from database.models import Message, User
from utils.logger import setup_logger

logger = setup_logger(__name__)


class ChatService:
    """Chat servisi"""
    
    def __init__(self):
        self.message_repo = MessageRepository()
        self.patient_repo = PatientRepository()
        self.user_repo = UserRepository()
    
    def send_message(self, sender_id: int, receiver_id: int, 
                    message_text: str, session_id: Optional[int] = None) -> Optional[int]:
        """Mesaj gönder"""
        try:
            message = Message(
                sender_id=sender_id,
                receiver_id=receiver_id,
                session_id=session_id,
                message_text=message_text,
                message_type="text",
                sent_at=datetime.now(),
                is_read=False
            )
            
            message_id = self.message_repo.create(message)
            
            if message_id:
                logger.info(f"Message sent: {sender_id} -> {receiver_id}")
            
            return message_id
            
        except Exception as e:
            logger.error(f"Send message error: {e}")
            return None
    
    def get_conversation(self, user1_id: int, user2_id: int, limit: int = 100) -> List[Message]:
        """İki kullanıcı arasındaki konuşmayı getir"""
        try:
            messages = self.message_repo.find_conversation(user1_id, user2_id, limit)
            
            # Okunmamış mesajları okundu olarak işaretle (alıcı user1 ise)
            self.message_repo.mark_conversation_as_read(user2_id, user1_id)
            
            return messages
            
        except Exception as e:
            logger.error(f"Get conversation error: {e}")
            return []
    
    def get_doctor_patients_with_last_message(self, doctor_id: int) -> List[Dict]:
        """Doktorun hastalarını son mesajla birlikte getir"""
        try:
            patients = self.patient_repo.find_all_by_doctor(doctor_id)
            
            patient_list = []
            for patient in patients:
                if not patient.user:
                    continue
                
                # Son mesaj
                last_message = self.message_repo.get_last_message(doctor_id, patient.user_id)
                
                # Okunmamış mesaj sayısı
                unread_count = self.message_repo.get_unread_count(doctor_id)
                
                patient_list.append({
                    'patient': patient,
                    'user': patient.user,
                    'last_message': last_message,
                    'unread_count': unread_count,
                    'last_activity': last_message.sent_at if last_message else patient.created_at
                })
            
            # Son aktiviteye göre sırala
            patient_list.sort(key=lambda x: x['last_activity'], reverse=True)
            
            return patient_list
            
        except Exception as e:
            logger.error(f"Get patients with messages error: {e}")
            return []
    
    def get_unread_count(self, user_id: int) -> int:
        """Okunmamış mesaj sayısı"""
        return self.message_repo.get_unread_count(user_id)
    
    def mark_as_read(self, sender_id: int, receiver_id: int) -> bool:
        """Konuşmayı okundu olarak işaretle"""
        return self.message_repo.mark_conversation_as_read(sender_id, receiver_id)