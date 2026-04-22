"""
User Repository
Kullanıcı CRUD işlemleri
"""
from typing import Optional, List
from datetime import datetime

from database.db_manager import db_manager
from database.models import User
from utils.logger import setup_logger

logger = setup_logger(__name__)


class UserRepository:
    """User tablosu için repository"""
    
    def __init__(self):
        self.db = db_manager
    
    def create(self, user: User) -> Optional[int]:
        """
        Yeni kullanıcı oluştur
        
        Args:
            user: User objesi
        
        Returns:
            Oluşturulan kullanıcı ID'si veya None
        """
        try:
            query = """
                INSERT INTO users (email, password_hash, role, first_name, last_name, phone)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            params = (
                user.email,
                user.password_hash,
                user.role,
                user.first_name,
                user.last_name,
                user.phone
            )
            
            with self.db.get_cursor() as cursor:
                cursor.execute(query, params)
                user_id = cursor.lastrowid
                logger.info(f"Yeni kullanıcı oluşturuldu: {user.email} (ID: {user_id})")
                return user_id
                
        except Exception as e:
            logger.error(f"Kullanıcı oluşturma hatası: {e}")
            return None
    
    def find_by_id(self, user_id: int) -> Optional[User]:
        """
        ID ile kullanıcı bul
        
        Args:
            user_id: Kullanıcı ID
        
        Returns:
            User objesi veya None
        """
        try:
            query = "SELECT * FROM users WHERE id = ?"
            row = self.db.fetch_one(query, (user_id,))
            
            if row:
                return self._row_to_user(row)
            return None
            
        except Exception as e:
            logger.error(f"Kullanıcı bulma hatası: {e}")
            return None
    
    def find_by_email(self, email: str) -> Optional[User]:
        """
        Email ile kullanıcı bul
        
        Args:
            email: Email adresi
        
        Returns:
            User objesi veya None
        """
        try:
            query = "SELECT * FROM users WHERE email = ?"
            row = self.db.fetch_one(query, (email,))
            
            if row:
                return self._row_to_user(row)
            return None
            
        except Exception as e:
            logger.error(f"Kullanıcı bulma hatası: {e}")
            return None
    
    def find_all_by_role(self, role: str) -> List[User]:
        """
        Role göre tüm kullanıcıları getir
        
        Args:
            role: Kullanıcı rolü (doctor/patient)
        
        Returns:
            User listesi
        """
        try:
            query = "SELECT * FROM users WHERE role = ? AND is_active = 1 ORDER BY last_name, first_name"
            rows = self.db.fetch_all(query, (role,))
            
            return [self._row_to_user(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Kullanıcıları listeleme hatası: {e}")
            return []
    
    def update(self, user: User) -> bool:
        """
        Kullanıcı bilgilerini güncelle
        
        Args:
            user: Güncellenmiş User objesi
        
        Returns:
            Başarılı mı?
        """
        try:
            query = """
                UPDATE users 
                SET first_name = ?, last_name = ?, phone = ?, updated_at = ?
                WHERE id = ?
            """
            params = (
                user.first_name,
                user.last_name,
                user.phone,
                datetime.now().isoformat(),
                user.id
            )
            
            self.db.execute_query(query, params)
            logger.info(f"Kullanıcı güncellendi: {user.id}")
            return True
            
        except Exception as e:
            logger.error(f"Kullanıcı güncelleme hatası: {e}")
            return False
    
    def update_last_login(self, user_id: int) -> bool:
        """
        Son giriş zamanını güncelle
        
        Args:
            user_id: Kullanıcı ID
        
        Returns:
            Başarılı mı?
        """
        try:
            query = "UPDATE users SET last_login = ? WHERE id = ?"
            self.db.execute_query(query, (datetime.now(), user_id))
            return True
            
        except Exception as e:
            logger.error(f"Last login güncelleme hatası: {e}")
            return False
    
    def delete(self, user_id: int) -> bool:
        """
        Kullanıcıyı sil (soft delete - is_active = 0)
        
        Args:
            user_id: Kullanıcı ID
        
        Returns:
            Başarılı mı?
        """
        try:
            query = "UPDATE users SET is_active = 0, updated_at = ? WHERE id = ?"
            self.db.execute_query(query, (datetime.now(), user_id))
            logger.info(f"Kullanıcı silindi: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Kullanıcı silme hatası: {e}")
            return False
    
    def _row_to_user(self, row) -> User:
        """
        Database row'unu User objesine dönüştür
        
        Args:
            row: sqlite3.Row
        
        Returns:
            User objesi
        """
        return User(
            id=row['id'],
            email=row['email'],
            password_hash=row['password_hash'],
            role=row['role'],
            first_name=row['first_name'],
            last_name=row['last_name'],
            phone=row['phone'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None,
            last_login=datetime.fromisoformat(row['last_login']) if row['last_login'] else None,
            is_active=bool(row['is_active'])
        )