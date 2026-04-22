"""
Edit Patient Dialog
Danışan bilgilerini düzenleme dialogu
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QDateEdit, QComboBox, QTextEdit,
    QPushButton, QMessageBox, QFormLayout
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont
from datetime import date

from database.repositories.patient_repository import PatientRepository
from database.repositories.user_repository import UserRepository
from database.models import Patient, User
from utils.logger import setup_logger
from PyQt5.QtWidgets import QDialog

logger = setup_logger(__name__)


class EditPatientDialog(QDialog):
    """Danışan düzenleme dialogu"""
    
    def __init__(self, patient_id: int, parent=None):
        super().__init__(parent)
        
        self.patient_id = patient_id
        self.patient_repo = PatientRepository()
        self.user_repo = UserRepository()
        
        self.patient = None
        self.user = None
        
        self._setup_ui()
        self._load_patient()
        self._connect_signals()
    
    def _setup_ui(self):
        """UI oluştur"""
        self.setWindowTitle("Danışan Bilgilerini Düzenle")
        self.setMinimumWidth(550)
        self.setModal(True)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("Danışan Bilgilerini Güncelle")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Form layout
        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        
        # Kişisel Bilgiler Başlık
        personal_header = QLabel("Kişisel Bilgiler")
        personal_header.setStyleSheet("color: #2196F3; font-weight: bold; font-size: 11pt; margin-top: 5px;")
        form_layout.addRow(personal_header)
        
        # Ad
        self.first_name_input = QLineEdit()
        self.first_name_input.setPlaceholderText("Adı")
        self.first_name_input.setMinimumHeight(35)
        form_layout.addRow("Ad:", self.first_name_input)
        
        # Soyad
        self.last_name_input = QLineEdit()
        self.last_name_input.setPlaceholderText("Soyadı")
        self.last_name_input.setMinimumHeight(35)
        form_layout.addRow("Soyad:", self.last_name_input)
        
        # Email (read-only)
        self.email_label = QLabel()
        self.email_label.setStyleSheet("color: #757575;")
        form_layout.addRow("Email:", self.email_label)
        
        # Telefon
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("05XXXXXXXXX")
        self.phone_input.setMinimumHeight(35)
        form_layout.addRow("Telefon:", self.phone_input)
        
        # TC No
        self.tc_input = QLineEdit()
        self.tc_input.setPlaceholderText("11 haneli TC kimlik numarası")
        self.tc_input.setMinimumHeight(35)
        self.tc_input.setMaxLength(11)
        form_layout.addRow("TC No:", self.tc_input)
        
        # Doğum Tarihi
        self.birth_date_edit = QDateEdit()
        self.birth_date_edit.setCalendarPopup(True)
        self.birth_date_edit.setMaximumDate(QDate.currentDate())
        self.birth_date_edit.setMinimumHeight(35)
        self.birth_date_edit.setDisplayFormat("dd.MM.yyyy")
        form_layout.addRow("Doğum Tarihi:", self.birth_date_edit)
        
        # Cinsiyet
        self.gender_combo = QComboBox()
        self.gender_combo.addItem("Belirtilmemiş", None)
        self.gender_combo.addItem("Erkek", "male")
        self.gender_combo.addItem("Kadın", "female")
        self.gender_combo.addItem("Diğer", "other")
        self.gender_combo.setMinimumHeight(35)
        form_layout.addRow("Cinsiyet:", self.gender_combo)
        
        # Adres
        self.address_text = QTextEdit()
        self.address_text.setPlaceholderText("Adres bilgisi...")
        self.address_text.setMaximumHeight(70)
        form_layout.addRow("Adres:", self.address_text)
        
        # Acil Durum Bilgileri Başlık
        emergency_header = QLabel("Acil Durum İletişim")
        emergency_header.setStyleSheet("color: #2196F3; font-weight: bold; font-size: 11pt; margin-top: 10px;")
        form_layout.addRow(emergency_header)
        
        # Acil İletişim Ad
        self.emergency_name_input = QLineEdit()
        self.emergency_name_input.setPlaceholderText("Acil durumda aranacak kişinin adı")
        self.emergency_name_input.setMinimumHeight(35)
        form_layout.addRow("Acil İletişim:", self.emergency_name_input)
        
        # Acil İletişim Telefon
        self.emergency_phone_input = QLineEdit()
        self.emergency_phone_input.setPlaceholderText("05XXXXXXXXX")
        self.emergency_phone_input.setMinimumHeight(35)
        form_layout.addRow("Acil Telefon:", self.emergency_phone_input)
        
        # Tıbbi Geçmiş
        medical_header = QLabel("Tıbbi Bilgiler")
        medical_header.setStyleSheet("color: #2196F3; font-weight: bold; font-size: 11pt; margin-top: 10px;")
        form_layout.addRow(medical_header)
        
        self.medical_history_text = QTextEdit()
        self.medical_history_text.setPlaceholderText("Tıbbi geçmiş, ilaç kullanımı, alerjiler vb...")
        self.medical_history_text.setMaximumHeight(80)
        form_layout.addRow("Tıbbi Geçmiş:", self.medical_history_text)
        
        # Notlar
        self.notes_text = QTextEdit()
        self.notes_text.setPlaceholderText("Genel notlar...")
        self.notes_text.setMaximumHeight(70)
        form_layout.addRow("Notlar:", self.notes_text)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton("İptal")
        self.cancel_btn.setMinimumHeight(35)
        self.cancel_btn.setMinimumWidth(100)
        button_layout.addWidget(self.cancel_btn)
        
        self.save_btn = QPushButton("Güncelle")
        self.save_btn.setMinimumHeight(35)
        self.save_btn.setMinimumWidth(100)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
    
    def _connect_signals(self):
        """Signal bağlantıları"""
        self.save_btn.clicked.connect(self._handle_save)
        self.cancel_btn.clicked.connect(self.reject)
    
    def _load_patient(self):
        """Danışan bilgilerini yükle"""
        try:
            self.patient = self.patient_repo.find_by_id(self.patient_id)
            
            if not self.patient:
                QMessageBox.critical(self, "Hata", "Danışan bulunamadı!")
                self.reject()
                return
            
            self.user = self.patient.user
            
            if not self.user:
                QMessageBox.critical(self, "Hata", "Kullanıcı bilgisi bulunamadı!")
                self.reject()
                return
            
            # User bilgileri
            self.first_name_input.setText(self.user.first_name or "")
            self.last_name_input.setText(self.user.last_name or "")
            self.email_label.setText(self.user.email)
            self.phone_input.setText(self.user.phone or "")
            
            # Patient bilgileri
            self.tc_input.setText(self.patient.tc_no or "")
            
            if self.patient.birth_date:
                bd = self.patient.birth_date
                self.birth_date_edit.setDate(QDate(bd.year, bd.month, bd.day))
            
            if self.patient.gender:
                gender_index = self.gender_combo.findData(self.patient.gender)
                if gender_index >= 0:
                    self.gender_combo.setCurrentIndex(gender_index)
            
            self.address_text.setPlainText(self.patient.address or "")
            self.emergency_name_input.setText(self.patient.emergency_contact_name or "")
            self.emergency_phone_input.setText(self.patient.emergency_contact_phone or "")
            self.medical_history_text.setPlainText(self.patient.medical_history or "")
            self.notes_text.setPlainText(self.patient.notes or "")
            
            logger.info(f"Danışan bilgileri yüklendi: {self.patient_id}")
            
        except Exception as e:
            logger.error(f"Danışan yükleme hatası: {e}")
            QMessageBox.critical(self, "Hata", f"Danışan yüklenirken hata oluştu:\n{str(e)}")
            self.reject()
    
    def _handle_save(self):
        """Değişiklikleri kaydet"""
        try:
            # Validasyon
            first_name = self.first_name_input.text().strip()
            last_name = self.last_name_input.text().strip()
            
            if not first_name or not last_name:
                QMessageBox.warning(self, "Uyarı", "Ad ve soyad alanları zorunludur!")
                return
            
            # User bilgilerini güncelle
            self.user.first_name = first_name
            self.user.last_name = last_name
            self.user.phone = self.phone_input.text().strip() or None
            
            # Patient bilgilerini güncelle
            self.patient.tc_no = self.tc_input.text().strip() or None
            
            birth_date = self.birth_date_edit.date().toPyDate()
            self.patient.birth_date = birth_date
            
            self.patient.gender = self.gender_combo.currentData()
            self.patient.address = self.address_text.toPlainText().strip() or None
            self.patient.emergency_contact_name = self.emergency_name_input.text().strip() or None
            self.patient.emergency_contact_phone = self.emergency_phone_input.text().strip() or None
            self.patient.medical_history = self.medical_history_text.toPlainText().strip() or None
            self.patient.notes = self.notes_text.toPlainText().strip() or None
            
            # Database'e kaydet
            user_updated = self.user_repo.update(self.user)
            patient_updated = self.patient_repo.update(self.patient)
            
            if user_updated and patient_updated:
                logger.info(f"Danışan güncellendi: {self.patient_id}")
                QMessageBox.information(self, "Başarılı", "Danışan bilgileri güncellendi!")
                self.accept()
            else:
                QMessageBox.critical(self, "Hata", "Bilgiler güncellenirken hata oluştu!")
        
        except Exception as e:
            logger.error(f"Danışan güncelleme hatası: {e}")
            QMessageBox.critical(self, "Hata", f"Güncellenirken hata oluştu:\n{str(e)}")