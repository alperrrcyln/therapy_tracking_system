"""
Appointments Page
Randevular sayfasi
"""
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, 
    QPushButton, QTableWidgetItem, QHeaderView, QMessageBox, QDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor

from ui.pages.base_page import BasePage
from database.repositories.appointment_repository import AppointmentRepository
from services.patient_service import PatientService
from core.session_manager import session_manager
from core.constants import PageID
from utils.logger import setup_logger
from datetime import datetime

logger = setup_logger(__name__)


class AppointmentsPage(BasePage):
    """Randevular sayfasi"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.appointment_repo = AppointmentRepository()
        self.patient_service = PatientService()
        self.appointments = []
        
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """UI olustur"""
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        self.layout.addLayout(layout)
        
        # Header
        header_layout = QHBoxLayout()
        
        # Title
        title = QLabel("Randevular")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title.setFont(title_font)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Add button
        self.add_btn = QPushButton("+ Yeni Randevu")
        self.add_btn.setMinimumHeight(40)
        add_btn_font = QFont()
        add_btn_font.setPointSize(10)
        add_btn_font.setBold(True)
        self.add_btn.setFont(add_btn_font)
        self.add_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        header_layout.addWidget(self.add_btn)
        
        layout.addLayout(header_layout)
        
        # Count label
        self.count_label = QLabel()
        self.count_label.setStyleSheet("color: #757575; font-size: 11pt;")
        layout.addWidget(self.count_label)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "#",
            "Tarih & Saat", 
            "Danışan", 
            "Süre (dk)",
            "Durum",
            "Notlar",
            "İşlemler"
        ])
        
        # Table styling
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        
        # Column widths
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        self.table.setColumnWidth(0, 50)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.Stretch)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.table)
    
    def _connect_signals(self):
        """Signal baglantilari"""
        self.add_btn.clicked.connect(self._show_add_appointment_dialog)
    
    def on_page_show(self):
        """Sayfa gosterildiginde"""
        logger.debug("Appointments page shown")
        self.load_appointments()
    
    def load_appointments(self):
        """Randevulari yukle"""
        try:
            doctor_id = session_manager.get_current_user_id()
            
            if not doctor_id:
                logger.error("Doctor ID bulunamadi!")
                return
            
            all_appointments = self.appointment_repo.find_by_doctor(doctor_id)
            now = datetime.now()
            # Sadece gelecekteki ve iptal edilmemis randevulari goster
            self.appointments = [
                a for a in all_appointments
                if a.appointment_date >= now and a.status != 'cancelled'
            ]
            self._populate_table(self.appointments)

            self.count_label.setText(
                f"Yaklaşan: {len(self.appointments)} randevu"
            )
            
            logger.info(f"{len(self.appointments)} randevu yuklendi")
            
        except Exception as e:
            logger.error(f"Randevu yukleme hatasi: {e}")
            QMessageBox.critical(
                self,
                "Hata",
                f"Randevular yuklenirken hata olustu:\n{str(e)}"
            )
    
    def _populate_table(self, appointments):
        """Tabloyu doldur"""
        self.table.setRowCount(0)
        
        for idx, appointment in enumerate(appointments):
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # Numara
            num_item = QTableWidgetItem(str(idx + 1))
            num_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, num_item)
            
            # Tarih & Saat
            date_str = appointment.appointment_date.strftime("%d.%m.%Y %H:%M")
            date_item = QTableWidgetItem(date_str)
            
           # Gelecekteki randevuyu vurgula
            if appointment.appointment_date > datetime.now() and appointment.status in ['pending', 'confirmed']:
                date_item.setBackground(QColor("#E8F5E9"))
                date_item.setForeground(QColor("#2E7D32"))
            
            self.table.setItem(row, 1, date_item)
            
            # Danisan (patient bilgisini yukle)
            patient = self.patient_service.get_patient_by_id(appointment.patient_id)
            patient_name = patient.user.full_name if patient and patient.user else "N/A"
            patient_item = QTableWidgetItem(patient_name)
            self.table.setItem(row, 2, patient_item)
            
            # Sure
            duration_item = QTableWidgetItem(str(appointment.duration_minutes))
            duration_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 3, duration_item)
            
           # Durum
            status_map = {
                'pending': '⏳ Beklemede',
                'confirmed': '✅ Onaylandı',
                'completed': '✔️ Tamamlandı',
                'cancelled': '❌ İptal'
            }
            status_text = status_map.get(appointment.status, appointment.status)
            status_item = QTableWidgetItem(status_text)
            self.table.setItem(row, 4, status_item)
            
            # Notlar
            notes_text = appointment.notes if appointment.notes else "-"
            notes_item = QTableWidgetItem(notes_text)
            self.table.setItem(row, 5, notes_item)
            
            # Islemler butonlari
            actions_widget = self._create_actions_widget(appointment)
            self.table.setCellWidget(row, 6, actions_widget)
    
    def _create_actions_widget(self, appointment):
        """Islem butonlari olustur"""
        from PyQt5.QtWidgets import QWidget
        
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(5)
        
        # Duzenle butonu
        edit_btn = QPushButton("✏️")
        edit_btn.setMaximumWidth(30)
        edit_btn.setProperty("appointment_id", appointment.id)
        edit_btn.clicked.connect(self._handle_edit_appointment)
        layout.addWidget(edit_btn)
        
        # Iptal butonu (sadece pending veya confirmed ise)
        if appointment.status in ['pending', 'confirmed']:
            cancel_btn = QPushButton("❌")
            cancel_btn.setMaximumWidth(30)
            cancel_btn.setProperty("appointment_id", appointment.id)
            cancel_btn.clicked.connect(self._handle_cancel_appointment)
            layout.addWidget(cancel_btn)
        
        # Sil butonu
        delete_btn = QPushButton("🗑️")
        delete_btn.setMaximumWidth(30)
        delete_btn.setProperty("appointment_id", appointment.id)
        delete_btn.clicked.connect(self._handle_delete_appointment)
        layout.addWidget(delete_btn)
        
        return widget
    
    def _show_add_appointment_dialog(self):
        """Yeni randevu dialog'unu ac"""
        try:
            from ui.dialogs.add_appointment_dialog import AddAppointmentDialog
            
            dialog = AddAppointmentDialog(self)
            
            if dialog.exec_() == QDialog.Accepted:
                self.load_appointments()
                logger.info("Yeni randevu eklendi")
        
        except Exception as e:
            logger.error(f"Add appointment dialog hatasi: {e}")
            QMessageBox.critical(
                self,
                "Hata",
                f"Dialog acilirken hata olustu:\n{str(e)}"
            )
    
    def _handle_edit_appointment(self):
        """Randevu duzenle"""
        try:
            button = self.sender()
            appointment_id = button.property("appointment_id")
            
            from ui.dialogs.edit_appointment_dialog import EditAppointmentDialog
            
            dialog = EditAppointmentDialog(appointment_id, self)
            
            if dialog.exec_() == QDialog.Accepted:
                self.load_appointments()
                logger.info("Randevu guncellendi")
        
        except Exception as e:
            logger.error(f"Edit appointment dialog hatasi: {e}")
            QMessageBox.critical(
                self,
                "Hata",
                f"Dialog açılırken hata oluştu:\n{str(e)}"
            )
        
    
    def _handle_cancel_appointment(self):
        """Randevu iptal et"""
        button = self.sender()
        appointment_id = button.property("appointment_id")
        
        reply = QMessageBox.question(
            self,
            "Randevu İptal",
            "Bu randevuyu iptal etmek istediğinizden emin misiniz?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            appointment = self.appointment_repo.find_by_id(appointment_id)
            if appointment:
                appointment.status = 'cancelled'
                if self.appointment_repo.update(appointment):
                    QMessageBox.information(self, "Başarılı", "Randevu iptal edildi!")
                    self.load_appointments()
                else:
                    QMessageBox.critical(self, "Hata", "Randevu iptal edilemedi!")
    
    def _handle_delete_appointment(self):
        """Randevu sil"""
        button = self.sender()
        appointment_id = button.property("appointment_id")
        
        reply = QMessageBox.question(
            self,
            "Randevu Sil",
            "Bu randevuyu kalıcı olarak silmek istediğinizden emin misiniz?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.appointment_repo.delete(appointment_id):
                QMessageBox.information(self, "Başarılı", "Randevu silindi!")
                self.load_appointments()
            else:
                QMessageBox.critical(self, "Hata", "Randevu silinemedi!")