"""
Add Patient Dialog
Yeni danisan ekleme formu
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QComboBox, QDateEdit,
    QTextEdit, QMessageBox, QFormLayout
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont

from services.auth_service import AuthService
from services.patient_service import PatientService
from database.models import User, Patient
from core.session_manager import session_manager
from core.constants import UserRole
from utils.validators import validate_email, validate_password, validate_phone, validate_tc_no
from utils.logger import setup_logger

logger = setup_logger(__name__)


class AddPatientDialog(QDialog):
    """Yeni danisan ekleme dialog'u"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.auth_service = AuthService()
        self.patient_service = PatientService()
        self.created_patient = None
        
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """UI olustur"""
        self.setWindowTitle("Yeni Danisan Ekle")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("Yeni Danisan Bilgileri")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Form
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        # Email
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("ornek@email.com")
        form_layout.addRow("Email *:", self.email_input)
        
        # Sifre
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("En az 6 karakter")
        form_layout.addRow("Sifre *:", self.password_input)
        
        # Ad
        self.first_name_input = QLineEdit()
        self.first_name_input.setPlaceholderText("Ad")
        form_layout.addRow("Ad *:", self.first_name_input)
        
        # Soyad
        self.last_name_input = QLineEdit()
        self.last_name_input.setPlaceholderText("Soyad")
        form_layout.addRow("Soyad *:", self.last_name_input)
        
        # Telefon
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("05XXXXXXXXX")
        form_layout.addRow("Telefon:", self.phone_input)
        
        # TC No
        self.tc_input = QLineEdit()
        self.tc_input.setPlaceholderText("11 haneli TC kimlik no")
        self.tc_input.setMaxLength(11)
        form_layout.addRow("TC No:", self.tc_input)
        
        # Dogum Tarihi
        self.birth_date_input = QDateEdit()
        self.birth_date_input.setCalendarPopup(True)
        self.birth_date_input.setDate(QDate.currentDate().addYears(-25))
        self.birth_date_input.setMaximumDate(QDate.currentDate())
        form_layout.addRow("Dogum Tarihi:", self.birth_date_input)
        
        # Cinsiyet
        self.gender_combo = QComboBox()
        self.gender_combo.addItems(["Secin...", "Erkek", "Kadin", "Diger"])
        form_layout.addRow("Cinsiyet:", self.gender_combo)
        
        # Adres
        self.address_input = QTextEdit()
        self.address_input.setMaximumHeight(60)
        self.address_input.setPlaceholderText("Adres bilgisi")
        form_layout.addRow("Adres:", self.address_input)
        
        # Acil Durum Iletisim
        self.emergency_name_input = QLineEdit()
        self.emergency_name_input.setPlaceholderText("Ad Soyad")
        form_layout.addRow("Acil Durum Kisi:", self.emergency_name_input)
        
        self.emergency_phone_input = QLineEdit()
        self.emergency_phone_input.setPlaceholderText("05XXXXXXXXX")
        form_layout.addRow("Acil Durum Tel:", self.emergency_phone_input)
        
        # Tibbi Gecmis
        self.medical_history_input = QTextEdit()
        self.medical_history_input.setMaximumHeight(80)
        self.medical_history_input.setPlaceholderText("Kronik hastaliklar, alerjiler, gecmis tedaviler...")
        form_layout.addRow("Tibbi Gecmis:", self.medical_history_input)
        
        layout.addLayout(form_layout)
        
        # Info
        info_label = QLabel("* Zorunlu alanlar")
        info_label.setStyleSheet("color: #757575; font-size: 9pt;")
        layout.addWidget(info_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton("Iptal")
        self.cancel_btn.setMinimumWidth(100)
        button_layout.addWidget(self.cancel_btn)
        
        self.save_btn = QPushButton("Kaydet")
        self.save_btn.setMinimumWidth(100)
        self.save_btn.setDefault(True)
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
    
    def _connect_signals(self):
        """Signal baglantilari"""
        self.cancel_btn.clicked.connect(self.reject)
        self.save_btn.clicked.connect(self._handle_save)
    
    def _handle_save(self):
        """Kaydet butonuna tiklandiginda"""
        try:
            # Inputlari al
            email = self.email_input.text().strip()
            password = self.password_input.text()
            first_name = self.first_name_input.text().strip()
            last_name = self.last_name_input.text().strip()
            phone = self.phone_input.text().strip() or None
            tc_no = self.tc_input.text().strip() or None
            birth_date = self.birth_date_input.date().toPyDate()
            
            gender_map = {"Erkek": "male", "Kadin": "female", "Diger": "other"}
            gender_text = self.gender_combo.currentText()
            gender = gender_map.get(gender_text, None) if gender_text != "Secin..." else None
            
            address = self.address_input.toPlainText().strip() or None
            emergency_name = self.emergency_name_input.text().strip() or None
            emergency_phone = self.emergency_phone_input.text().strip() or None
            medical_history = self.medical_history_input.toPlainText().strip() or None
            
            # Zorunlu alan kontrolu
            if not all([email, password, first_name, last_name]):
                QMessageBox.warning(
                    self,
                    "Uyari",
                    "Lutfen zorunlu alanlari doldurun!"
                )
                return
            
            # Email validation
            if not validate_email(email):
                QMessageBox.warning(
                    self,
                    "Uyari",
                    "Gecersiz email adresi!"
                )
                return
            
            # Password validation
            is_valid, msg = validate_password(password)
            if not is_valid:
                QMessageBox.warning(self, "Uyari", msg)
                return
            
            # Phone validation
            if phone and not validate_phone(phone):
                QMessageBox.warning(
                    self,
                    "Uyari",
                    "Gecersiz telefon numarasi! (05XXXXXXXXX formatinda olmali)"
                )
                return
            
            # TC validation
            if tc_no and not validate_tc_no(tc_no):
                QMessageBox.warning(
                    self,
                    "Uyari",
                    "Gecersiz TC kimlik numarasi! (11 haneli olmali)"
                )
                return
            
            # Emergency phone validation
            if emergency_phone and not validate_phone(emergency_phone):
                QMessageBox.warning(
                    self,
                    "Uyari",
                    "Gecersiz acil durum telefon numarasi!"
                )
                return
            
            # Doctor ID al
            doctor_id = session_manager.get_current_user_id()
            
            if not doctor_id:
                QMessageBox.critical(
                    self,
                    "Hata",
                    "Oturum hatasi! Lutfen tekrar giris yapin."
                )
                return
            
            # Kullanici olustur (AuthService.register kullan)
            success, message, user = self.auth_service.register(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                role=UserRole.PATIENT.value
            )
            
            if not success:
                QMessageBox.critical(self, "Hata", message)
                return
            
            # Patient kaydet (parametreleri ayri gonder) - DUZELTILDI
            patient_success, patient_message, patient = self.patient_service.create_patient(
                user_id=user.id,
                doctor_id=doctor_id,
                tc_no=tc_no,
                birth_date=birth_date,
                gender=gender,
                address=address,
                emergency_contact_name=emergency_name,
                emergency_contact_phone=emergency_phone,
                medical_history=medical_history
            )
            
            if patient_success:
                QMessageBox.information(
                    self,
                    "Basarili",
                    "Danisan basariyla eklendi!"
                )
                self.created_patient = patient
                self.accept()
            else:
                QMessageBox.critical(
                    self,
                    "Hata",
                    f"Danisan eklenirken hata olustu:\n{patient_message}"
                )
        
        except Exception as e:
            logger.error(f"Danisan ekleme hatasi: {e}")
            QMessageBox.critical(
                self,
                "Hata",
                f"Beklenmeyen bir hata olustu:\n{str(e)}"
            )
    
    def get_created_patient(self) -> Patient:
        """Olusturulan danisani dondur"""
        return self.created_patient