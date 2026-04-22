"""
Patients List Page
Danisan listesi sayfasi
"""
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, 
    QPushButton, QLineEdit, QTableWidgetItem, QHeaderView, QMessageBox, QDialog
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from ui.pages.base_page import BasePage
from ui.dialogs.add_patient_dialog import AddPatientDialog
from services.patient_service import PatientService
from core.session_manager import session_manager
from core.constants import PageID
from utils.logger import setup_logger

logger = setup_logger(__name__)


class PatientsListPage(BasePage):
    """Danisan listesi sayfasi"""
    
    # Custom signal - danisan secildiginde
    patient_selected = pyqtSignal(int)  # Patient ID
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.patient_service = PatientService()
        self.patients = []
        
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
        title = QLabel("Danisanlarim")
        title.setProperty("class", "title")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title.setFont(title_font)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Add button
        self.add_btn = QPushButton("+ Yeni Danisan Ekle")
        self.add_btn.setMinimumHeight(40)
        add_btn_font = QFont()
        add_btn_font.setPointSize(10)
        add_btn_font.setBold(True)
        self.add_btn.setFont(add_btn_font)
        header_layout.addWidget(self.add_btn)
        
        layout.addLayout(header_layout)
        
        # Search bar
        search_layout = QHBoxLayout()
        
        search_label = QLabel("Ara:")
        search_label.setStyleSheet("font-weight: 600;")
        search_layout.addWidget(search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Isim, email, TC No ile ara...")
        self.search_input.setMinimumWidth(300)
        search_layout.addWidget(self.search_input)
        
        search_layout.addStretch()
        
        # Patient count label
        self.count_label = QLabel()
        self.count_label.setStyleSheet("color: #757575; font-size: 11pt;")
        search_layout.addWidget(self.count_label)
        
        layout.addLayout(search_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "#",
            "Ad Soyad", 
            "Email", 
            "Telefon", 
            "Yas",
            "TC No",
            "Islemler"
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
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.table)
    
    def _connect_signals(self):
        """Signal baglantilari"""
        self.add_btn.clicked.connect(self._show_add_patient_dialog)
        self.search_input.textChanged.connect(self._filter_patients)
        self.table.cellDoubleClicked.connect(self._handle_row_double_click)
    
    def on_page_show(self):
        """Sayfa gosterildiginde"""
        logger.debug("Patients list shown")
        self.load_patients()
    
    def load_patients(self):
        """Danisanlari yukle"""
        try:
            doctor_id = session_manager.get_current_user_id()
            
            if not doctor_id:
                logger.error("Doctor ID bulunamadi!")
                return
            
            self.patients = self.patient_service.get_patients_by_doctor(doctor_id)
            self._populate_table(self.patients)
            
            self.count_label.setText(f"Toplam: {len(self.patients)} danisan")
            
            logger.info(f"{len(self.patients)} danisan yuklendi")
            
        except Exception as e:
            logger.error(f"Danisan yukleme hatasi: {e}")
            QMessageBox.critical(
                self,
                "Hata",
                f"Danisanlar yuklenirken hata olustu:\n{str(e)}"
            )
    
    def _populate_table(self, patients):
        """Tabloyu doldur"""
        self.table.setRowCount(0)
        
        for idx, patient in enumerate(patients):
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # Numara
            num_item = QTableWidgetItem(str(idx + 1))
            num_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, num_item)
            
            # Ad Soyad
            name_item = QTableWidgetItem(patient.user.full_name if patient.user else "N/A")
            self.table.setItem(row, 1, name_item)
            
            # Email
            email_item = QTableWidgetItem(patient.user.email if patient.user else "N/A")
            self.table.setItem(row, 2, email_item)
            
            # Telefon
            phone_item = QTableWidgetItem(patient.user.phone if patient.user and patient.user.phone else "-")
            self.table.setItem(row, 3, phone_item)
            
            # Yas
            age_text = str(patient.age) if patient.age else "-"
            age_item = QTableWidgetItem(age_text)
            age_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 4, age_item)
            
            # TC No
            tc_item = QTableWidgetItem(patient.tc_no if patient.tc_no else "-")
            self.table.setItem(row, 5, tc_item)
            
            # Islemler butonu
            view_btn = QPushButton("Detay")
            view_btn.setProperty("patient_id", patient.id)
            view_btn.clicked.connect(self._handle_view_patient)
            self.table.setCellWidget(row, 6, view_btn)
    
    def _filter_patients(self):
        """Danisanlari filtrele"""
        search_term = self.search_input.text().strip()
        
        if not search_term:
            self._populate_table(self.patients)
            return
        
        # Danisman ID
        doctor_id = session_manager.get_current_user_id()
        
        # Arama yap
        filtered = self.patient_service.search_patients(doctor_id, search_term)
        self._populate_table(filtered)
        
        # Count guncelle
        self.count_label.setText(f"{len(filtered)} / {len(self.patients)} danisan")
    
    def _show_add_patient_dialog(self):
        """Yeni danisan ekleme dialog'unu ac"""
        try:
            dialog = AddPatientDialog(self)
            
            if dialog.exec_() == QDialog.Accepted:
                # Dialog basariyla kapatildi, listeyi yenile
                self.load_patients()
                logger.info("Yeni danisan eklendi, liste yenilendi")
        
        except Exception as e:
            logger.error(f"Add patient dialog hatasi: {e}")
            QMessageBox.critical(
                self,
                "Hata",
                f"Dialog acilirken hata olustu:\n{str(e)}"
            )
    
    def _handle_view_patient(self):
        """Danisan detayini goster"""
        button = self.sender()
        patient_id = button.property("patient_id")
        
        logger.debug(f"View patient: {patient_id}")
        
        # Signal emit et - MainWindow handle edecek
        self.patient_selected.emit(patient_id)
    
    def _handle_row_double_click(self, row, column):
        """Satira cift tiklandiginda"""
        if row < len(self.patients):
            patient = self.patients[row]
            logger.debug(f"Double click on patient: {patient.id}")
            
            # Signal emit et
            self.patient_selected.emit(patient.id)