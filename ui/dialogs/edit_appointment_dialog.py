"""
Edit Appointment Dialog
Randevu düzenleme dialogu
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QDateEdit, QTimeEdit, QSpinBox,
    QTextEdit, QPushButton, QMessageBox, QFormLayout
)
from PyQt5.QtCore import Qt, QDate, QTime
from PyQt5.QtGui import QFont
from datetime import datetime

from database.repositories.appointment_repository import AppointmentRepository
from services.patient_service import PatientService
from database.models import Appointment
from core.constants import AppointmentStatus
from utils.logger import setup_logger

logger = setup_logger(__name__)


class EditAppointmentDialog(QDialog):
    """Randevu düzenleme dialogu"""
    
    def __init__(self, appointment_id: int, parent=None):
        super().__init__(parent)
        
        self.appointment_id = appointment_id
        self.appointment_repo = AppointmentRepository()
        self.patient_service = PatientService()
        
        self.appointment = None
        self.patients = []
        
        self._setup_ui()
        self._load_appointment()
        self._connect_signals()
    
    def _setup_ui(self):
        """UI olustur"""
        self.setWindowTitle("Randevu Düzenle")
        self.setMinimumWidth(500)
        self.setModal(True)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("Randevu Bilgilerini Düzenle")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Form layout
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        
        # Danisan (read-only)
        self.patient_label = QLabel()
        self.patient_label.setStyleSheet("color: #2C3E50; font-weight: 600;")
        form_layout.addRow("Danışan:", self.patient_label)
        
        # Tarih secimi
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setMinimumDate(QDate.currentDate())
        self.date_edit.setMinimumHeight(35)
        self.date_edit.setDisplayFormat("dd.MM.yyyy")
        form_layout.addRow("Tarih:", self.date_edit)
        
        # Saat secimi
        self.time_edit = QTimeEdit()
        self.time_edit.setMinimumHeight(35)
        self.time_edit.setDisplayFormat("HH:mm")
        form_layout.addRow("Saat:", self.time_edit)
        
        # Sure secimi
        self.duration_spin = QSpinBox()
        self.duration_spin.setMinimum(15)
        self.duration_spin.setMaximum(240)
        self.duration_spin.setSingleStep(15)
        self.duration_spin.setSuffix(" dakika")
        self.duration_spin.setMinimumHeight(35)
        form_layout.addRow("Süre:", self.duration_spin)
        
        # Durum secimi
        self.status_combo = QComboBox()
        self.status_combo.addItem("⏳ Beklemede", AppointmentStatus.PENDING.value)
        self.status_combo.addItem("✅ Onaylandı", AppointmentStatus.CONFIRMED.value)
        self.status_combo.addItem("✔️ Tamamlandı", AppointmentStatus.COMPLETED.value)
        self.status_combo.addItem("❌ İptal", AppointmentStatus.CANCELLED.value)
        self.status_combo.setMinimumHeight(35)
        form_layout.addRow("Durum:", self.status_combo)
        
        # Notlar
        self.notes_text = QTextEdit()
        self.notes_text.setPlaceholderText("Randevu notları...")
        self.notes_text.setMaximumHeight(100)
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
        """Signal baglantilari"""
        self.save_btn.clicked.connect(self._handle_save)
        self.cancel_btn.clicked.connect(self.reject)
    
    def _load_appointment(self):
        """Randevu bilgilerini yukle"""
        try:
            self.appointment = self.appointment_repo.find_by_id(self.appointment_id)
            
            if not self.appointment:
                QMessageBox.critical(
                    self,
                    "Hata",
                    "Randevu bulunamadı!"
                )
                self.reject()
                return
            
            # Danisan bilgisi
            patient = self.patient_service.get_patient_by_id(self.appointment.patient_id)
            if patient and patient.user:
                self.patient_label.setText(patient.user.full_name)
            else:
                self.patient_label.setText("N/A")
            
            # Tarih ve saat
            apt_date = self.appointment.appointment_date
            self.date_edit.setDate(QDate(apt_date.year, apt_date.month, apt_date.day))
            self.time_edit.setTime(QTime(apt_date.hour, apt_date.minute))
            
            # Sure
            self.duration_spin.setValue(self.appointment.duration_minutes)
            
            # Durum
            status_index = self.status_combo.findData(self.appointment.status)
            if status_index >= 0:
                self.status_combo.setCurrentIndex(status_index)
            
            # Notlar
            if self.appointment.notes:
                self.notes_text.setPlainText(self.appointment.notes)
            
            logger.info(f"Randevu yuklendi: {self.appointment_id}")
            
        except Exception as e:
            logger.error(f"Randevu yukleme hatasi: {e}")
            QMessageBox.critical(
                self,
                "Hata",
                f"Randevu yüklenirken hata oluştu:\n{str(e)}"
            )
            self.reject()
    
    def _handle_save(self):
        """Randevu guncelle"""
        try:
            # Tarih ve saat birlestir
            date = self.date_edit.date().toPyDate()
            time = self.time_edit.time().toPyTime()
            appointment_datetime = datetime.combine(date, time)
            
            # Randevu bilgilerini guncelle
            self.appointment.appointment_date = appointment_datetime
            self.appointment.duration_minutes = self.duration_spin.value()
            self.appointment.status = self.status_combo.currentData()
            self.appointment.notes = self.notes_text.toPlainText().strip() or None
            
            # Database'e kaydet
            if self.appointment_repo.update(self.appointment):
                logger.info(f"Randevu guncellendi: {self.appointment_id}")
                QMessageBox.information(
                    self,
                    "Başarılı",
                    "Randevu başarıyla güncellendi!"
                )
                self.accept()
            else:
                QMessageBox.critical(
                    self,
                    "Hata",
                    "Randevu güncellenemedi!"
                )
        
        except Exception as e:
            logger.error(f"Randevu guncelleme hatasi: {e}")
            QMessageBox.critical(
                self,
                "Hata",
                f"Randevu güncellenirken hata oluştu:\n{str(e)}"
            )