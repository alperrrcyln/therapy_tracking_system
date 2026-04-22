"""
Sidebar Menu Widget
Role göre dinamik menü
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, 
    QFrame, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from core.constants import PageID, UserRole
from database.models import User
from utils.logger import setup_logger

logger = setup_logger(__name__)


class SidebarMenu(QWidget):
    """
    Sidebar menü widget'ı
    Role göre menü öğelerini gösterir
    """
    
    # Signals
    menu_item_clicked = pyqtSignal(int)  # Page ID
    logout_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.current_user: User = None
        self.active_button: QPushButton = None
        self.menu_buttons = {}
        
        self._setup_ui()
    
    def _setup_ui(self):
        """UI oluştur"""
        self.setFixedWidth(280)
        self.setStyleSheet("""
            SidebarMenu {
                background-color: #F5F7FA;
            }
        """)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = QFrame()
        header.setStyleSheet("background-color: #2196F3; padding: 20px;")
        header_layout = QVBoxLayout(header)
        
        app_name = QLabel("Terapi\nSistemi")
        app_name.setAlignment(Qt.AlignCenter)
        app_name.setStyleSheet("color: white; font-size: 14pt; font-weight: bold; padding: 5px;")
        header_layout.addWidget(app_name)
        
        layout.addWidget(header)
        
        # User info section
        self.user_frame = QFrame()
        self.user_frame.setStyleSheet("""
            QFrame {
                background-color: #455A64;
                padding: 15px;
            }
        """)
        user_layout = QVBoxLayout(self.user_frame)
        user_layout.setSpacing(5)
        
        self.user_name_label = QLabel()
        self.user_name_label.setWordWrap(True)
        self.user_name_label.setStyleSheet("color: white; font-weight: bold; font-size: 10pt;")
        user_layout.addWidget(self.user_name_label)
        
        self.user_role_label = QLabel()
        self.user_role_label.setStyleSheet("color: #B0BEC5; font-size: 9pt;")
        user_layout.addWidget(self.user_role_label)
        
        layout.addWidget(self.user_frame)
        
        # Menu items container
        self.menu_container = QVBoxLayout()
        self.menu_container.setContentsMargins(0, 10, 0, 0)
        self.menu_container.setSpacing(5)
        layout.addLayout(self.menu_container)
        
        # Spacer
        layout.addStretch()
        
        # Logout button
        self.logout_btn = self._create_menu_button("🚪 Çıkış Yap", is_logout=True)
        self.logout_btn.clicked.connect(self.logout_clicked.emit)
        layout.addWidget(self.logout_btn)
    
    def set_user(self, user: User):
        """
        Kullanıcıyı ayarla ve menüyü oluştur
        
        Args:
            user: Aktif kullanıcı
        """
        self.current_user = user
        
        # User info güncelle
        self.user_name_label.setText(user.full_name)
        role_text = "Danışman" if user.is_doctor else "Danışan"
        self.user_role_label.setText(role_text)
        
        # Menüyü oluştur
        self._build_menu()
    
    def _build_menu(self):
        """Role göre menü öğelerini oluştur"""
        # Önce mevcut menü öğelerini temizle
        self._clear_menu()
        
        if self.current_user.is_doctor:
            self._build_doctor_menu()
        else:
            self._build_patient_menu()
    
    def _build_doctor_menu(self):
        """Danışman menüsü"""
        menu_items = [
            ("🏠 Ana Sayfa", PageID.DOCTOR_DASHBOARD),
            ("👥 Danışanlarım", PageID.PATIENTS_LIST),
            ("📝 Sohbet", PageID.NEW_SESSION),
            ("📅 Randevular", PageID.APPOINTMENTS),
            ("📜 Aktivite Geçmişi", PageID.ACTIVITIES),
            ("📊 Raporlar", PageID.REPORTS),
            ("📈 Analizler", PageID.ANALYTICS),
        ]
        
        for text, page_id in menu_items:
            btn = self._create_menu_button(text)
            btn.clicked.connect(lambda checked, pid=page_id: self._on_menu_click(pid))
            self.menu_buttons[page_id] = btn
            self.menu_container.addWidget(btn)
    
    def _build_patient_menu(self):
        """Danışan menüsü"""
        menu_items = [
            ("🏠 Ana Sayfa", PageID.PATIENT_DASHBOARD),
            ("📖 Günlüğüm", PageID.DIARY),
            ("📅 Randevularım", PageID.MY_APPOINTMENTS),
            ("📋 Görüşmelerim", PageID.MY_SESSIONS),
        ]
        
        for text, page_id in menu_items:
            btn = self._create_menu_button(text)
            btn.clicked.connect(lambda checked, pid=page_id: self._on_menu_click(pid))
            self.menu_buttons[page_id] = btn
            self.menu_container.addWidget(btn)
    
    def _create_menu_button(self, text: str, is_logout: bool = False) -> QPushButton:
        """
        Menü butonu oluştur
        
        Args:
            text: Buton metni
            is_logout: Logout butonu mu?
        
        Returns:
            QPushButton
        """
        btn = QPushButton(text)
        btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #2C3E50;
                border: none;
                text-align: left;
                padding: 12px 20px;
                font-size: 10pt;
                font-weight: 500;
            }

            QPushButton:hover {
                background-color: #E8F4F8;
                color: #2196F3;
            }

            QPushButton:pressed {
                background-color: #BBDEFB;
            }

            QPushButton[class="active"] {
                background-color: #2196F3;
                color: white;
                border-left: 4px solid #1565C0;
            }
        """)
        
        if is_logout:
            btn.setStyleSheet(btn.styleSheet() + """
                QPushButton {
                    border-top: 1px solid #E0E0E0;
                    margin-top: 10px;
                    color: #E74C3C;
                }
                QPushButton:hover {
                    background-color: #FFEBEE;
                    color: #C62828;
                }
            """)
        
        return btn
    
    def _on_menu_click(self, page_id: int):
        """
        Menü öğesine tıklandığında
        
        Args:
            page_id: Sayfa ID
        """
        logger.debug(f"Menu clicked: {page_id}")
        
        # Aktif butonu güncelle
        self.set_active_page(page_id)
        
        # Signal emit et
        self.menu_item_clicked.emit(page_id)
    
    def set_active_page(self, page_id: int):
        """
        Aktif sayfayı işaretle
        
        Args:
            page_id: Aktif sayfa ID
        """
        # Önceki aktif butonu sıfırla
        if self.active_button:
            self.active_button.setProperty("class", "")
            self.active_button.style().unpolish(self.active_button)
            self.active_button.style().polish(self.active_button)
        
        # Yeni aktif butonu ayarla
        if page_id in self.menu_buttons:
            self.active_button = self.menu_buttons[page_id]
            self.active_button.setProperty("class", "active")
            self.active_button.style().unpolish(self.active_button)
            self.active_button.style().polish(self.active_button)
    
    def _clear_menu(self):
        """Menü öğelerini temizle"""
        for i in reversed(range(self.menu_container.count())):
            widget = self.menu_container.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        self.menu_buttons.clear()
        self.active_button = None