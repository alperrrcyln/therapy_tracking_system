"""
Reports Page
Raporlar ve analiz sayfası
"""
import os
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGroupBox,
    QComboBox, QDateEdit, QFrame, QScrollArea, QWidget, QMessageBox,
    QProgressDialog, QFileDialog
)
from PyQt5.QtCore import Qt, QDate, QThread, pyqtSignal
from PyQt5.QtGui import QFont

from ui.pages.base_page import BasePage
from services.report_service import ReportService
from services.patient_service import PatientService
from utils.pdf_exporter import PDFExporter
from utils.excel_exporter import ExcelExporter
from utils.logger import setup_logger

logger = setup_logger(__name__)


class ReportGeneratorThread(QThread):
    """Rapor oluşturma thread'i"""
    finished = pyqtSignal(bool, str)
    
    def __init__(self, export_func, *args):
        super().__init__()
        self.export_func = export_func
        self.args = args
    
    def run(self):
        try:
            success = self.export_func(*self.args)
            self.finished.emit(success, "Rapor başarıyla oluşturuldu!" if success else "Rapor oluşturulamadı!")
        except Exception as e:
            logger.error(f"Report generation error: {e}")
            self.finished.emit(False, f"Hata: {str(e)}")


class ReportsPage(BasePage):
    """Raporlar sayfası"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.report_service = ReportService()
        self.patient_service = PatientService()
        self.pdf_exporter = PDFExporter()
        self.excel_exporter = ExcelExporter()
        
        self.current_doctor_id = None
        self.report_thread = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """UI oluştur"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        self.layout.addWidget(scroll)
        
        content = QWidget()
        scroll.setWidget(content)
        
        main_layout = QVBoxLayout(content)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(20)
        
        # Başlık
        title = QLabel("📊 Raporlar ve Analiz")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title.setFont(title_font)
        main_layout.addWidget(title)
        
        # Rapor tipleri
        reports_layout = QHBoxLayout()
        
        # Hasta Özet Raporu
        patient_report_group = self._create_patient_report_group()
        reports_layout.addWidget(patient_report_group)
        
        # Dönem Raporu
        period_report_group = self._create_period_report_group()
        reports_layout.addWidget(period_report_group)
        
        main_layout.addLayout(reports_layout)
        
        # Hızlı raporlar
        quick_reports_group = self._create_quick_reports_group()
        main_layout.addWidget(quick_reports_group)
        
        main_layout.addStretch()
    
    def _create_patient_report_group(self) -> QGroupBox:
        """Hasta raporu grubu"""
        group = QGroupBox("🏥 Danışan Özet Raporu")
        group_font = QFont()
        group_font.setPointSize(12)
        group_font.setBold(True)
        group.setFont(group_font)
        
        layout = QVBoxLayout(group)
        
        desc = QLabel("Tek bir danışan için detaylı özet rapor oluşturun")
        desc.setStyleSheet("color: #757575; font-size: 10pt;")
        layout.addWidget(desc)
        
        # Hasta seçimi
        patient_layout = QHBoxLayout()
        patient_label = QLabel("Danışan:")
        patient_layout.addWidget(patient_label)
        
        self.patient_combo = QComboBox()
        self.patient_combo.setMinimumWidth(300)
        patient_layout.addWidget(self.patient_combo)
        patient_layout.addStretch()
        
        layout.addLayout(patient_layout)
        
        # Export butonları
        btn_layout = QHBoxLayout()
        
        self.patient_pdf_btn = QPushButton("📄 PDF Oluştur")
        self.patient_pdf_btn.setProperty("class", "primary")
        self.patient_pdf_btn.setMinimumHeight(40)
        self.patient_pdf_btn.clicked.connect(self._export_patient_pdf)
        btn_layout.addWidget(self.patient_pdf_btn)
        
        self.patient_excel_btn = QPushButton("📊 Excel Oluştur")
        self.patient_excel_btn.setProperty("class", "success")
        self.patient_excel_btn.setMinimumHeight(40)
        self.patient_excel_btn.clicked.connect(self._export_patient_excel)
        btn_layout.addWidget(self.patient_excel_btn)
        
        layout.addLayout(btn_layout)
        
        return group
    
    def _create_period_report_group(self) -> QGroupBox:
        """Dönem raporu grubu"""
        group = QGroupBox("📅 Dönem Raporu")
        group_font = QFont()
        group_font.setPointSize(12)
        group_font.setBold(True)
        group.setFont(group_font)
        
        layout = QVBoxLayout(group)
        
        desc = QLabel("Belirli bir tarih aralığı için genel rapor oluşturun")
        desc.setStyleSheet("color: #757575; font-size: 10pt;")
        layout.addWidget(desc)
        
        # Tarih seçimi
        date_layout = QHBoxLayout()
        
        date_layout.addWidget(QLabel("Başlangıç:"))
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        date_layout.addWidget(self.start_date)
        
        date_layout.addWidget(QLabel("Bitiş:"))
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        date_layout.addWidget(self.end_date)
        
        date_layout.addStretch()
        
        layout.addLayout(date_layout)
        
        # Export butonları
        btn_layout = QHBoxLayout()
        
        self.period_pdf_btn = QPushButton("📄 PDF Oluştur")
        self.period_pdf_btn.setProperty("class", "primary")
        self.period_pdf_btn.setMinimumHeight(40)
        self.period_pdf_btn.clicked.connect(self._export_period_pdf)
        btn_layout.addWidget(self.period_pdf_btn)
        
        self.period_excel_btn = QPushButton("📊 Excel Oluştur")
        self.period_excel_btn.setProperty("class", "success")
        self.period_excel_btn.setMinimumHeight(40)
        self.period_excel_btn.clicked.connect(self._export_period_excel)
        btn_layout.addWidget(self.period_excel_btn)
        
        layout.addLayout(btn_layout)
        
        return group
    
    def _create_quick_reports_group(self) -> QGroupBox:
        """Hızlı raporlar"""
        group = QGroupBox("⚡ Hızlı Raporlar")
        group_font = QFont()
        group_font.setPointSize(12)
        group_font.setBold(True)
        group.setFont(group_font)
        
        layout = QHBoxLayout(group)
        
        # Bu hafta
        week_btn = QPushButton("📆 Bu Hafta")
        week_btn.setMinimumHeight(70)
        week_btn.setStyleSheet("""
            QPushButton {
                background-color: #E3F2FD;
                border: 2px solid #2196F3;
                border-radius: 8px;
                font-size: 12pt;
                font-weight: bold;
                color: #1976D2;
            }
            QPushButton:hover {
                background-color: #BBDEFB;
            }
        """)
        week_btn.clicked.connect(self._export_week_report)
        layout.addWidget(week_btn)
        
        # Bu ay
        month_btn = QPushButton("📅 Bu Ay")
        month_btn.setMinimumHeight(70)
        month_btn.setStyleSheet("""
            QPushButton {
                background-color: #E8F5E9;
                border: 2px solid #4CAF50;
                border-radius: 8px;
                font-size: 12pt;
                font-weight: bold;
                color: #388E3C;
            }
            QPushButton:hover {
                background-color: #C8E6C9;
            }
        """)
        month_btn.clicked.connect(self._export_month_report)
        layout.addWidget(month_btn)
        
        # Son 3 ay
        quarter_btn = QPushButton("📊 Son 3 Ay")
        quarter_btn.setMinimumHeight(70)
        quarter_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFF9C4;
                border: 2px solid #FBC02D;
                border-radius: 8px;
                font-size: 12pt;
                font-weight: bold;
                color: #F57F17;
            }
            QPushButton:hover {
                background-color: #FFF59D;
            }
        """)
        quarter_btn.clicked.connect(self._export_quarter_report)
        layout.addWidget(quarter_btn)
        
        return group
    
    def set_doctor(self, doctor_id: int):
        """Doktor bilgilerini ayarla"""
        self.current_doctor_id = doctor_id
        self._load_patients()
    
    def _load_patients(self):
        """Hastaları yükle"""
        if not self.current_doctor_id:
            logger.warning("Doctor ID yok, hastalar yüklenemedi")
            return
        
        try:
            from database.repositories.patient_repository import PatientRepository
            patient_repo = PatientRepository()
            patients = patient_repo.find_all_by_doctor(self.current_doctor_id)
            
            self.patient_combo.clear()
            self.patient_combo.addItem("-- Danışan Seçin --", None)
            
            for patient in patients:
                if patient.user:
                    self.patient_combo.addItem(patient.user.full_name, patient.id)
            
            logger.info(f"{len(patients)} hasta combobox'a yüklendi")
            
        except Exception as e:
            logger.error(f"Hastalar yüklenemedi: {e}", exc_info=True)
    
    def _export_patient_pdf(self):
        """Hasta raporu PDF"""
        patient_id = self.patient_combo.currentData()
        if not patient_id:
            QMessageBox.warning(self, "Uyarı", "Lütfen danışan seçin!")
            return
        
        # Rapor verisi
        report_data = self.report_service.get_patient_summary_report(patient_id)
        if not report_data:
            QMessageBox.critical(self, "Hata", "Rapor verileri alınamadı!")
            return
        
        # Dosya yolu
        patient_name = self.patient_combo.currentText().replace(' ', '_')
        filename = f"Danisan_Raporu_{patient_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "PDF Kaydet", 
            os.path.join(os.path.expanduser("~"), "Desktop", filename),
            "PDF Files (*.pdf)"
        )
        
        if not file_path:
            return
        
        # Thread ile export
        self._show_progress("PDF oluşturuluyor...")
        self.report_thread = ReportGeneratorThread(
            self.pdf_exporter.export_patient_summary,
            report_data,
            file_path
        )
        self.report_thread.finished.connect(self._on_export_finished)
        self.report_thread.start()
    
    def _export_patient_excel(self):
        """Hasta raporu Excel"""
        patient_id = self.patient_combo.currentData()
        if not patient_id:
            QMessageBox.warning(self, "Uyarı", "Lütfen danışan seçin!")
            return
        
        report_data = self.report_service.get_patient_summary_report(patient_id)
        if not report_data:
            QMessageBox.critical(self, "Hata", "Rapor verileri alınamadı!")
            return
        
        patient_name = self.patient_combo.currentText().replace(' ', '_')
        filename = f"Danisan_Raporu_{patient_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Excel Kaydet",
            os.path.join(os.path.expanduser("~"), "Desktop", filename),
            "Excel Files (*.xlsx)"
        )
        
        if not file_path:
            return
        
        self._show_progress("Excel oluşturuluyor...")
        self.report_thread = ReportGeneratorThread(
            self.excel_exporter.export_patient_summary,
            report_data,
            file_path
        )
        self.report_thread.finished.connect(self._on_export_finished)
        self.report_thread.start()
    
    def _export_period_pdf(self):
        """Dönem raporu PDF"""
        if not self.current_doctor_id:
            return
        
        start = datetime(
            self.start_date.date().year(),
            self.start_date.date().month(),
            self.start_date.date().day()
        )
        end = datetime(
            self.end_date.date().year(),
            self.end_date.date().month(),
            self.end_date.date().day(),
            23, 59, 59
        )
        
        report_data = self.report_service.get_period_report(self.current_doctor_id, start, end)
        if not report_data:
            QMessageBox.critical(self, "Hata", "Rapor verileri alınamadı!")
            return
        
        filename = f"Donem_Raporu_{start.strftime('%Y%m%d')}_{end.strftime('%Y%m%d')}.pdf"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "PDF Kaydet",
            os.path.join(os.path.expanduser("~"), "Desktop", filename),
            "PDF Files (*.pdf)"
        )
        
        if not file_path:
            return
        
        self._show_progress("PDF oluşturuluyor...")
        self.report_thread = ReportGeneratorThread(
            self.pdf_exporter.export_period_report,
            report_data,
            file_path
        )
        self.report_thread.finished.connect(self._on_export_finished)
        self.report_thread.start()
    
    def _export_period_excel(self):
        """Dönem raporu Excel"""
        if not self.current_doctor_id:
            return
        
        start = datetime(
            self.start_date.date().year(),
            self.start_date.date().month(),
            self.start_date.date().day()
        )
        end = datetime(
            self.end_date.date().year(),
            self.end_date.date().month(),
            self.end_date.date().day(),
            23, 59, 59
        )
        
        report_data = self.report_service.get_period_report(self.current_doctor_id, start, end)
        if not report_data:
            QMessageBox.critical(self, "Hata", "Rapor verileri alınamadı!")
            return
        
        filename = f"Donem_Raporu_{start.strftime('%Y%m%d')}_{end.strftime('%Y%m%d')}.xlsx"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Excel Kaydet",
            os.path.join(os.path.expanduser("~"), "Desktop", filename),
            "Excel Files (*.xlsx)"
        )
        
        if not file_path:
            return
        
        self._show_progress("Excel oluşturuluyor...")
        self.report_thread = ReportGeneratorThread(
            self.excel_exporter.export_period_report,
            report_data,
            file_path
        )
        self.report_thread.finished.connect(self._on_export_finished)
        self.report_thread.start()
    
    def _export_week_report(self):
        """Bu hafta raporu"""
        today = datetime.now()
        start = today - timedelta(days=today.weekday())
        end = today
        
        self.start_date.setDate(QDate(start.year, start.month, start.day))
        self.end_date.setDate(QDate(end.year, end.month, end.day))
        
        self._export_period_pdf()
    
    def _export_month_report(self):
        """Bu ay raporu"""
        today = datetime.now()
        start = datetime(today.year, today.month, 1)
        end = today
        
        self.start_date.setDate(QDate(start.year, start.month, start.day))
        self.end_date.setDate(QDate(end.year, end.month, end.day))
        
        self._export_period_excel()
    
    def _export_quarter_report(self):
        """Son 3 ay raporu"""
        today = datetime.now()
        start = today - timedelta(days=90)
        end = today
        
        self.start_date.setDate(QDate(start.year, start.month, start.day))
        self.end_date.setDate(QDate(end.year, end.month, end.day))
        
        self._export_period_pdf()
    
    def _show_progress(self, message: str):
        """Progress dialog göster"""
        self.progress = QProgressDialog(message, None, 0, 0, self)
        self.progress.setWindowTitle("Rapor Oluşturuluyor")
        self.progress.setWindowModality(Qt.WindowModal)
        self.progress.show()
    
    def _on_export_finished(self, success: bool, message: str):
        """Export tamamlandı"""
        if hasattr(self, 'progress'):
            self.progress.close()
        
        if success:
            QMessageBox.information(self, "Başarılı", message)
        else:
            QMessageBox.critical(self, "Hata", message)
    
    def on_page_show(self):
        """Sayfa gösterildiğinde"""
        logger.debug("Reports page shown")
        self._load_patients()