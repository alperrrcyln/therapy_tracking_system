"""
Search Page
Global arama sayfası
"""
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QListWidget, QListWidgetItem, QComboBox, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor

from ui.pages.base_page import BasePage
from core.session_manager import session_manager
from database.repositories.appointment_repository import AppointmentRepository
from services.patient_service import PatientService
from services.therapy_service import TherapyService
from core.constants import PageID
from utils.logger import setup_logger
from datetime import datetime

logger = setup_logger(__name__)


class SearchPage(BasePage):
    """Global arama sayfası"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.appointment_repo = AppointmentRepository()
        self.patient_service = PatientService()
        self.therapy_service = TherapyService()
        
        self.all_results = []
        
        self._setup_ui()
    
    def _setup_ui(self):
        """UI oluştur"""
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        self.layout.addLayout(layout)
        
        # Header
        title = QLabel("🔍 Global Arama")
        title.setStyleSheet("color: #2C3E50; font-size: 24pt; font-weight: bold;")
        layout.addWidget(title)
        
        # Arama kutusu
        search_layout = QHBoxLayout()
        search_layout.setSpacing(10)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Hasta adı, TC No, randevu, görüşme notu ara...")
        self.search_input.setMinimumHeight(45)
        self.search_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                padding: 10px;
                font-size: 12pt;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #2196F3;
            }
        """)
        self.search_input.returnPressed.connect(self._perform_search)
        search_layout.addWidget(self.search_input, 3)
        
        # Filtre
        self.filter_combo = QComboBox()
        self.filter_combo.addItem("🔄 Tümünde Ara", "all")
        self.filter_combo.addItem("👤 Sadece Hastalarda", "patients")
        self.filter_combo.addItem("📅 Sadece Randevularda", "appointments")
        self.filter_combo.addItem("📝 Sadece Görüşmelerde", "sessions")
        self.filter_combo.setMinimumWidth(200)
        self.filter_combo.setMinimumHeight(45)
        self.filter_combo.setStyleSheet("""
            QComboBox {
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                padding: 10px;
                font-size: 11pt;
                background-color: white;
            }
        """)
        search_layout.addWidget(self.filter_combo)
        
        # Ara butonu
        search_btn = QPushButton("🔍 Ara")
        search_btn.setMinimumHeight(45)
        search_btn.setMinimumWidth(120)
        search_btn.clicked.connect(self._perform_search)
        search_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 12pt;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        search_layout.addWidget(search_btn)
        
        layout.addLayout(search_layout)
        
        # Sonuç sayısı
        self.result_count_label = QLabel("Arama yapmak için yukarıdaki kutuya yazın")
        self.result_count_label.setStyleSheet("color: #757575; font-size: 10pt; margin-top: 10px;")
        layout.addWidget(self.result_count_label)
        
        # Sonuç listesi
        self.results_list = QListWidget()
        self.results_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #E0E0E0;
                background-color: white;
                border-radius: 8px;
            }
            QListWidget::item {
                padding: 15px;
                border-bottom: 1px solid #E0E0E0;
            }
            QListWidget::item:hover {
                background-color: #E8F5E9;
            }
        """)
        self.results_list.itemClicked.connect(self._on_result_clicked)
        layout.addWidget(self.results_list)
    
    def on_page_show(self):
        """Sayfa gösterildiğinde"""
        self.search_input.setFocus()
        logger.debug("Search page shown")
    
    def _perform_search(self):
        """Arama yap"""
        query = self.search_input.text().strip().lower()
        
        if not query or len(query) < 2:
            self.result_count_label.setText("En az 2 karakter girin")
            self.results_list.clear()
            return
        
        try:
            doctor_id = session_manager.get_current_user_id()
            filter_type = self.filter_combo.currentData()
            
            self.all_results = []
            
            # Hastalarda ara
            if filter_type in ["all", "patients"]:
                patients = self.patient_service.get_patients_by_doctor(doctor_id)
                
                for patient in patients:
                    matched = False
                    match_fields = []
                    
                    # Ad soyad
                    if patient.user and query in patient.user.full_name.lower():
                        matched = True
                        match_fields.append("Ad Soyad")
                    
                    # TC No
                    if patient.tc_no and query in patient.tc_no.lower():
                        matched = True
                        match_fields.append("TC No")
                    
                    # Telefon
                    if patient.phone and query in patient.phone.lower():
                        matched = True
                        match_fields.append("Telefon")
                    
                    # Tıbbi geçmiş
                    if patient.medical_history and query in patient.medical_history.lower():
                        matched = True
                        match_fields.append("Tıbbi Geçmiş")
                    
                    if matched:
                        patient_name = patient.user.full_name if patient.user else "N/A"
                        self.all_results.append({
                            'type': 'patient',
                            'title': f"👤 Hasta: {patient_name}",
                            'subtitle': f"Eşleşme: {', '.join(match_fields)}",
                            'data': {'patient_id': patient.id},
                            'color': '#4CAF50'
                        })
            
            # Randevularda ara
            if filter_type in ["all", "appointments"]:
                appointments = self.appointment_repo.find_by_doctor(doctor_id, limit=200)
                
                for apt in appointments:
                    patient = self.patient_service.get_patient_by_id(apt.patient_id)
                    patient_name = patient.user.full_name if patient and patient.user else "N/A"
                    
                    matched = False
                    
                    # Hasta adı
                    if query in patient_name.lower():
                        matched = True
                    
                    # Randevu notları
                    if apt.notes and query in apt.notes.lower():
                        matched = True
                    
                    if matched:
                        date_str = apt.appointment_date.strftime("%d.%m.%Y %H:%M")
                        status_map = {
                            'pending': '⏳ Beklemede',
                            'confirmed': '✅ Onaylandı',
                            'completed': '✔️ Tamamlandı',
                            'cancelled': '❌ İptal'
                        }
                        status = status_map.get(apt.status, apt.status)
                        
                        self.all_results.append({
                            'type': 'appointment',
                            'title': f"📅 Randevu: {patient_name} - {date_str}",
                            'subtitle': f"{status}",
                            'data': {'appointment_id': apt.id},
                            'color': '#2196F3'
                        })
            
            # Görüşmelerde ara
            if filter_type in ["all", "sessions"]:
                sessions = self.therapy_service.get_sessions_by_doctor(doctor_id, limit=200)
                
                for session in sessions:
                    patient = self.patient_service.get_patient_by_id(session.patient_id)
                    patient_name = patient.user.full_name if patient and patient.user else "N/A"
                    
                    matched = False
                    match_in = ""
                    
                    # Hasta adı
                    if query in patient_name.lower():
                        matched = True
                        match_in = "Hasta adı"
                    
                    # Görüşme notları
                    if session.therapist_notes and query in session.therapist_notes.lower():
                        matched = True
                        match_in = "Görüşme notları"
                    
                    # Tanı
                    if session.diagnosis and query in session.diagnosis.lower():
                        matched = True
                        match_in = "Tanı"
                    
                    if matched:
                        date_str = session.session_date.strftime("%d.%m.%Y") if session.session_date else "N/A"
                        
                        self.all_results.append({
                            'type': 'session',
                            'title': f"📝 Görüşme: {patient_name} - {date_str}",
                            'subtitle': f"Eşleşme: {match_in}",
                            'data': {'patient_id': session.patient_id},
                            'color': '#FF9800'
                        })
            
            # Sonuçları listele
            self._display_results()
            
        except Exception as e:
            logger.error(f"Arama hatasi: {e}")
            self.result_count_label.setText(f"Hata: {str(e)}")
    
    def _display_results(self):
        """Sonuçları göster"""
        self.results_list.clear()
        
        if not self.all_results:
            self.result_count_label.setText(f"'{self.search_input.text()}' için sonuç bulunamadı")
            
            item = QListWidgetItem("📭 Sonuç bulunamadı")
            item.setForeground(Qt.gray)
            self.results_list.addItem(item)
            return
        
        # Sonuç sayısını göster
        self.result_count_label.setText(f"{len(self.all_results)} sonuç bulundu")
        
        # Kategorilere göre grupla
        patients = [r for r in self.all_results if r['type'] == 'patient']
        appointments = [r for r in self.all_results if r['type'] == 'appointment']
        sessions = [r for r in self.all_results if r['type'] == 'session']
        
        # Hastalar
        if patients:
            header = QListWidgetItem(f"👤 HASTALAR ({len(patients)})")
            header_font = QFont()
            header_font.setBold(True)
            header.setFont(header_font)
            header.setBackground(QColor("#F5F5F5"))
            self.results_list.addItem(header)
            
            for result in patients:
                item = QListWidgetItem(f"{result['title']}\n   {result['subtitle']}")
                item.setForeground(QColor(result['color']))
                item.setData(Qt.UserRole, result['data'])
                self.results_list.addItem(item)
        
        # Randevular
        if appointments:
            header = QListWidgetItem(f"📅 RANDEVULAR ({len(appointments)})")
            header_font = QFont()
            header_font.setBold(True)
            header.setFont(header_font)
            header.setBackground(QColor("#F5F5F5"))
            self.results_list.addItem(header)
            
            for result in appointments:
                item = QListWidgetItem(f"{result['title']}\n   {result['subtitle']}")
                item.setForeground(QColor(result['color']))
                item.setData(Qt.UserRole, result['data'])
                self.results_list.addItem(item)
        
        # Görüşmeler
        if sessions:
            header = QListWidgetItem(f"📝 GÖRÜŞMELER ({len(sessions)})")
            header_font = QFont()
            header_font.setBold(True)
            header.setFont(header_font)
            header.setBackground(QColor("#F5F5F5"))
            self.results_list.addItem(header)
            
            for result in sessions:
                item = QListWidgetItem(f"{result['title']}\n   {result['subtitle']}")
                item.setForeground(QColor(result['color']))
                item.setData(Qt.UserRole, result['data'])
                self.results_list.addItem(item)
    
    def _on_result_clicked(self, item):
        """Sonuca tıklandığında"""
        try:
            data = item.data(Qt.UserRole)
            
            if not data:
                return
            
            # Hasta detayına git
            if 'patient_id' in data:
                patient_id = data['patient_id']
                self.page_changed.emit(PageID.PATIENT_DETAIL, patient_id)
                logger.info(f"Arama sonucundan hasta detayina gidildi: {patient_id}")
            
        except Exception as e:
            logger.error(f"Sonuc tiklama hatasi: {e}")