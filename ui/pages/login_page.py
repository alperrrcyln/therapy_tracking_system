"""
Login Page
Kullanıcı giriş ekranı
"""
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QFrame, QMessageBox, QCheckBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QSettings
from PyQt5.QtGui import QFont

from ui.pages.base_page import BasePage
from services.auth_service import AuthService
from core.constants import PageID
from utils.logger import setup_logger

logger = setup_logger(__name__)


class LoginPage(BasePage):
    """Login sayfası"""
    
    # Custom signals
    login_success = pyqtSignal(object)  # User objesi ile
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.auth_service = AuthService()
        self.settings = QSettings("TerapiTakip", "LoginSettings")
        
        self._setup_ui()
        self._connect_signals()
        self._load_saved_email()
    
    def _setup_ui(self):
        """UI bileşenlerini oluştur"""
        # Ana layout
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignCenter)
        self.layout.addLayout(main_layout)
        
       # Login card frame
        card = QFrame()
        card.setProperty("class", "card")
        card.setMaximumWidth(700)
        card.setMinimumWidth(650)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(30)
        card_layout.setContentsMargins(60, 50, 60, 50)
        
        # Logo / Title
        title_label = QLabel("Terapi Takip Sistemi")
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(22)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #2C3E50; margin-bottom: 5px;")
        card_layout.addWidget(title_label)
        
        # Subtitle
        subtitle_label = QLabel("Danışman ve Danışan Giriş Portalı")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("color: #5D6D7E; font-size: 11pt; margin-bottom: 20px;")
        card_layout.addWidget(subtitle_label)
        
        # Email field
        email_label = QLabel("Email:")
        email_label.setStyleSheet("font-weight: 600; color: #2C3E50; font-size: 11pt;")
        card_layout.addWidget(email_label)
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("ornek@email.com")
        self.email_input.setStyleSheet("""
            QLineEdit {
                padding: 14px 16px;
                font-size: 12pt;
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 2px solid #2196F3;
            }
        """)
        self.email_input.setMinimumHeight(50)
        card_layout.addWidget(self.email_input)
        
        # Password field
        password_label = QLabel("Şifre:")
        password_label.setStyleSheet("font-weight: 600; color: #2C3E50; font-size: 11pt; margin-top: 10px;")
        card_layout.addWidget(password_label)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("••••••••")
        self.password_input.setStyleSheet("""
            QLineEdit {
                padding: 14px 16px;
                font-size: 12pt;
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 2px solid #2196F3;
            }
        """)
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(50)
        card_layout.addWidget(self.password_input)
        
        # Remember me checkbox
        self.remember_checkbox = QCheckBox("Beni Hatırla")
        self.remember_checkbox.setStyleSheet("color: #5D6D7E; font-size: 10pt; margin-top: 5px;")
        card_layout.addWidget(self.remember_checkbox)
        
        # Spacer
        card_layout.addSpacing(15)
        
        # Login button
        self.login_btn = QPushButton("Giriş Yap")
        self.login_btn.setMinimumHeight(50)
        login_btn_font = QFont()
        login_btn_font.setPointSize(12)
        login_btn_font.setBold(True)
        self.login_btn.setFont(login_btn_font)
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 14px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
            }
        """)
        card_layout.addWidget(self.login_btn)
        
        main_layout.addWidget(card)
        
        # Background - Yumuşak gradient
        self.setStyleSheet("""
            LoginPage {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #F7F9FC,
                    stop:1 #E3F2FD
                );
            }
        """)
    
    def _connect_signals(self):
        """Signal bağlantıları"""
        self.login_btn.clicked.connect(self._handle_login)
        self.password_input.returnPressed.connect(self._handle_login)
        self.email_input.returnPressed.connect(self.password_input.setFocus)
    
    def _load_saved_email(self):
        """Kaydedilmiş email'i yükle"""
        saved_email = self.settings.value("remembered_email", "")
        if saved_email:
            self.email_input.setText(saved_email)
            self.remember_checkbox.setChecked(True)
            self.password_input.setFocus()
    
    def _save_email_if_checked(self, email: str):
        """Checkbox işaretliyse email'i kaydet"""
        if self.remember_checkbox.isChecked():
            self.settings.setValue("remembered_email", email)
        else:
            self.settings.remove("remembered_email")
    
    def _handle_login(self):
        """Login işlemini gerçekleştir"""
        email = self.email_input.text().strip()
        password = self.password_input.text()
        
        # Boş alan kontrolü
        if not email or not password:
            QMessageBox.warning(
                self,
                "Uyarı",
                "Lütfen email ve şifre alanlarını doldurun."
            )
            return
        
        # Login butonunu devre dışı bırak
        self.login_btn.setEnabled(False)
        self.login_btn.setText("Giriş yapılıyor...")
        
        # Auth service ile login
        success, message, user = self.auth_service.login(email, password)
        
        # Butonu tekrar aktif et
        self.login_btn.setEnabled(True)
        self.login_btn.setText("Giriş Yap")
        
        if success:
            logger.info(f"Login başarılı: {user.email} ({user.role})")
            
            # Email'i kaydet (eğer checkbox işaretliyse)
            self._save_email_if_checked(email)
            
            # Şifreyi temizle
            self.password_input.clear()
            
            # Success signal emit et
            self.login_success.emit(user)
            
            # Role göre sayfa yönlendirmesi
            if user.is_doctor:
                self.navigate_to(PageID.DOCTOR_DASHBOARD)
            else:
                self.navigate_to(PageID.PATIENT_DASHBOARD)
        else:
            logger.warning(f"Login başarısız: {email}")
            QMessageBox.critical(
                self,
                "Giriş Başarısız",
                message
            )
    
    def on_page_show(self):
        """Sayfa gösterildiğinde"""
        # Focus email veya password (email doluysa password'e)
        if self.email_input.text():
            self.password_input.setFocus()
        else:
            self.email_input.setFocus()
        
        # Şifreyi temizle
        self.password_input.clear()