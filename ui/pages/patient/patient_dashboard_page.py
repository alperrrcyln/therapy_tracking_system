"""
Patient Dashboard Page
Danışan ana sayfası
"""
from PyQt5.QtWidgets import QVBoxLayout, QLabel
from PyQt5.QtGui import QFont

from ui.pages.base_page import BasePage
from core.session_manager import session_manager
from utils.logger import setup_logger

logger = setup_logger(__name__)


class PatientDashboardPage(BasePage):
    """Danışan dashboard"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """UI oluştur"""
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        self.layout.addLayout(layout)
        
        # Title
        title = QLabel("Danışan Ana Sayfası")
        title.setProperty("class", "title")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Welcome message
        self.welcome_label = QLabel()
        self.welcome_label.setStyleSheet("font-size: 14pt; color: #757575;")
        layout.addWidget(self.welcome_label)
        
        # Info
        info = QLabel("📊 Bu sayfada günlük girişi, yaklaşan randevular ve analiz sonuçlarınız olacak.")
        info.setStyleSheet("color: #757575; padding: 20px; background-color: #E3F2FD; border-radius: 8px;")
        info.setWordWrap(True)
        layout.addWidget(info)
        
        layout.addStretch()
    
    def on_page_show(self):
        """Sayfa gösterildiğinde"""
        user = session_manager.get_current_user()
        if user:
            self.welcome_label.setText(f"Hoş geldiniz, {user.first_name} 👋")
        
        logger.debug("Patient dashboard shown")