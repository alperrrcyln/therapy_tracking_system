"""
Add Appointment Dialog
Yeni randevu ekleme dialogu
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QDateEdit, QTimeEdit, QSpinBox,
    QTextEdit, QPushButton, QMessageBox, QFormLayout
)
from PyQt5.QtCore import Qt, QDate, QTime
from PyQt5.QtGui import QFont
from datetime import datetime, timedelta

from database.repositories.appointment_repository import AppointmentRepository
from services.patient_service import PatientService
from database.models import Appointment
from core.session_manager import session_manager
from core.constants import AppointmentStatus
from utils.logger import setup_logger

logger = setup_logger(__name__)


class AddAppointmentDialog(QDialog):
    """Yeni randevu ekleme dialogu"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.appointment_repo = AppointmentRepository()
        self.patient_service = PatientService()
        
        self.patients = []
        
        self._setup_ui()
        self._load_patients()
        self._connect_signals()
    
    def _setup_ui(self):
        """UI olustur"""
        self.setWindowTitle("Yeni Randevu Ekle")
        self.setMinimumWidth(500)
        self.setModal(True)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("Yeni Randevu Oluştur")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Form layout
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        
        # Danisan secimi
        self.patient_combo = QComboBox()
        self.patient_combo.setMinimumHeight(35)
        form_layout.addRow("Danışan:", self.patient_combo)
        
        # Tarih secimi
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setMinimumDate(QDate.currentDate())
        self.date_edit.setMinimumHeight(35)
        self.date_edit.setDisplayFormat("dd.MM.yyyy")
        form_layout.addRow("Tarih:", self.date_edit)
        
        # Saat secimi
        self.time_edit = QTimeEdit()
        self.time_edit.setTime(QTime(9, 0))  # Default: 09:00
        self.time_edit.setMinimumHeight(35)
        self.time_edit.setDisplayFormat("HH:mm")
        form_layout.addRow("Saat:", self.time_edit)
        
        # Sure secimi
        self.duration_spin = QSpinBox()
        self.duration_spin.setMinimum(15)
        self.duration_spin.setMaximum(240)
        self.duration_spin.setValue(60)
        self.duration_spin.setSingleStep(15)
        self.duration_spin.setSuffix(" dakika")
        self.duration_spin.setMinimumHeight(35)
        form_layout.addRow("Süre:", self.duration_spin)
        
        # Notlar
        self.notes_text = QTextEdit()
        self.notes_text.setPlaceholderText("Randevu notları (opsiyonel)...")
        self.notes_text.setMaximumHeight(100)
        form_layout.addRow("Notlar:", self.notes_text)
        
        layout.addLayout(form_layout)
        
        # Info label
        info_label = QLabel("💡 Randevu oluşturulduktan sonra danışana bildirim gönderilebilir.")
        info_label.setStyleSheet("color: #757575; font-size: 9pt; font-style: italic;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton("İptal")
        self.cancel_btn.setMinimumHeight(35)
        self.cancel_btn.setMinimumWidth(100)
        button_layout.addWidget(self.cancel_btn)
        
        self.save_btn = QPushButton("Kaydet")
        self.save_btn.setMinimumHeight(35)
        self.save_btn.setMinimumWidth(100)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
    
    def _connect_signals(self):
        """Signal baglantilari"""
        self.save_btn.clicked.connect(self._handle_save)
        self.cancel_btn.clicked.connect(self.reject)
    
    def _load_patients(self):
        """Danisanlari yukle"""
        try:
            doctor_id = session_manager.get_current_user_id()
            
            if not doctor_id:
                logger.error("Doctor ID bulunamadi!")
                return
            
            self.patients = self.patient_service.get_patients_by_doctor(doctor_id)
            
            # Combo'ya ekle
            self.patient_combo.clear()
            for patient in self.patients:
                display_text = patient.user.full_name if patient.user else f"Patient {patient.id}"
                self.patient_combo.addItem(display_text, patient.id)
            
            logger.info(f"{len(self.patients)} danisan yuklendi")
            
        except Exception as e:
            logger.error(f"Danisan yukleme hatasi: {e}")
            QMessageBox.critical(
                self,
                "Hata",
                f"Danışanlar yüklenirken hata oluştu:\n{str(e)}"
            )
    
    def _handle_save(self):
        """Randevu kaydet"""
        try:
            # Validasyon
            if self.patient_combo.count() == 0:
                QMessageBox.warning(
                    self,
                    "Uyarı",
                    "Lütfen bir danışan seçin!"
                )
                return
            
            # Secilen danisan
            patient_id = self.patient_combo.currentData()
            
            if not patient_id:
                QMessageBox.warning(
                    self,
                    "Uyarı",
                    "Geçerli bir danışan seçin!"
                )
                return
            
            # Tarih ve saat birlestir
            date = self.date_edit.date().toPyDate()
            time = self.time_edit.time().toPyTime()
            appointment_datetime = datetime.combine(date, time)
            
            # Gecmis tarih kontrolu
            if appointment_datetime < datetime.now():
                QMessageBox.warning(
                    self,
                    "Uyarı",
                    "Geçmiş bir tarih seçemezsiniz!"
                )
                return
            
            # Randevu objesi olustur
            doctor_id = session_manager.get_current_user_id()
            
            appointment = Appointment(
                patient_id=patient_id,
                doctor_id=doctor_id,
                appointment_date=appointment_datetime,
                duration_minutes=self.duration_spin.value(),
                status=AppointmentStatus.CONFIRMED.value,
                notes=self.notes_text.toPlainText().strip() or None
            )
            
            # Database'e kaydet
            appointment_id = self.appointment_repo.create(appointment)
            
            if appointment_id:
                logger.info(f"Randevu kaydedildi: {appointment_id}")
                QMessageBox.information(
                    self,
                    "Başarılı",
                    "Randevu başarıyla oluşturuldu!"
                )
                self.accept()
            else:
                QMessageBox.critical(
                    self,
                    "Hata",
                    "Randevu kaydedilemedi!"
                )
        
        except Exception as e:
            logger.error(f"Randevu kaydetme hatasi: {e}")
            QMessageBox.critical(
                self,
                "Hata",
                f"Randevu kaydedilirken hata oluştu:\n{str(e)}"
            )