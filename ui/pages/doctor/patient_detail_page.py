"""
Patient Detail Page
Danisan detay sayfasi
"""
import os
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QTextEdit, QGroupBox, QFormLayout, QScrollArea,
    QWidget, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor

from ui.pages.base_page import BasePage
from services.patient_service import PatientService
from services.therapy_service import TherapyService
from database.models import Patient
from database.repositories.patient_note_repository import PatientNoteRepository
from core.constants import PageID
from utils.logger import setup_logger
from ui.dialogs.emotion_analysis_dialog import EmotionAnalysisDialog
from database.repositories.emotion_repository import EmotionAnalysisRepository
from ui.dialogs.edit_patient_dialog import EditPatientDialog
from database.repositories.session_repository import TherapySessionRepository

logger = setup_logger(__name__)


class PatientDetailPage(BasePage):
    """Danisan detay sayfasi"""
    
    patient_loaded = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.patient_service = PatientService()
        self.therapy_service = TherapyService()
        self.therapy_repo = TherapySessionRepository()
        self.emotion_repo = EmotionAnalysisRepository()
        self.patient_note_repo = PatientNoteRepository()
        self.current_patient: Patient = None
        self.current_patient_id: int = None
        self.current_editing_note_id: int = None
        
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """UI olustur"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        self.layout.addWidget(scroll)
        
        content_widget = QWidget()
        scroll.setWidget(content_widget)
        
        main_layout = QVBoxLayout(content_widget)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(20)
        
        # Header
        header_layout = QHBoxLayout()
        
        self.back_btn = QPushButton("← Geri")
        self.back_btn.setMaximumWidth(100)
        header_layout.addWidget(self.back_btn)
        
        header_layout.addStretch()
        
        self.edit_btn = QPushButton("✏️ Duzenle")
        self.edit_btn.setProperty("class", "secondary")
        self.edit_btn.setMaximumWidth(120)
        header_layout.addWidget(self.edit_btn)
        
        main_layout.addLayout(header_layout)
        
        # Title
        self.title_label = QLabel("Danisan Detayi")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        main_layout.addWidget(self.title_label)
        
        # Info Card
        self.info_card = self._create_info_card()
        main_layout.addWidget(self.info_card)
        
        # Two column layout
        columns_layout = QHBoxLayout()
        columns_layout.setSpacing(20)
        
        # Left column
        left_column = QVBoxLayout()
        
        self.contact_group = self._create_contact_group()
        left_column.addWidget(self.contact_group)
        
        self.medical_group = self._create_medical_group()
        left_column.addWidget(self.medical_group)
        
        self.patient_notes_group = self._create_patient_notes_history_group()
        left_column.addWidget(self.patient_notes_group)
        
        left_column.addStretch()
        columns_layout.addLayout(left_column, 1)
        
        # Right column
        right_column = QVBoxLayout()
        
        self.stats_group = self._create_stats_group()
        right_column.addWidget(self.stats_group)
        
        self.sessions_group = self._create_sessions_group()
        right_column.addWidget(self.sessions_group)
        
        right_column.addStretch()
        columns_layout.addLayout(right_column, 1)
        
        main_layout.addLayout(columns_layout)
        
        self.notes_group = self._create_notes_group()
        main_layout.addWidget(self.notes_group)
        
        main_layout.addStretch()
    
    def _create_info_card(self) -> QFrame:
        """Ana bilgi karti"""
        card = QFrame()
        card.setProperty("class", "card")
        card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2196F3, stop:1 #1976D2);
                border-radius: 12px;
                padding: 30px;
            }
        """)
        
        layout = QHBoxLayout(card)
        
        avatar = QLabel("👤")
        avatar.setStyleSheet("font-size: 64pt; color: white;")
        layout.addWidget(avatar)
        
        info_layout = QVBoxLayout()
        
        self.name_label = QLabel()
        self.name_label.setStyleSheet("color: white; font-size: 22pt; font-weight: bold;")
        info_layout.addWidget(self.name_label)
        
        self.age_gender_label = QLabel()
        self.age_gender_label.setStyleSheet("color: #E3F2FD; font-size: 12pt;")
        info_layout.addWidget(self.age_gender_label)
        
        self.email_label = QLabel()
        self.email_label.setStyleSheet("color: #BBDEFB; font-size: 10pt;")
        info_layout.addWidget(self.email_label)
        
        info_layout.addStretch()
        layout.addLayout(info_layout)
        
        layout.addStretch()
        
        return card
    
    def _create_contact_group(self) -> QGroupBox:
        """Iletisim bilgileri grubu"""
        group = QGroupBox("Iletisim Bilgileri")
        group_font = QFont()
        group_font.setPointSize(11)
        group_font.setBold(True)
        group.setFont(group_font)
        
        layout = QFormLayout(group)
        layout.setSpacing(10)
        
        self.phone_label = QLabel()
        layout.addRow("Telefon:", self.phone_label)
        
        self.email_info_label = QLabel()
        layout.addRow("Email:", self.email_info_label)
        
        self.address_label = QLabel()
        self.address_label.setWordWrap(True)
        layout.addRow("Adres:", self.address_label)
        
        emergency_title = QLabel("Acil Durum Iletisim")
        emergency_title.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addRow(emergency_title)
        
        self.emergency_name_label = QLabel()
        layout.addRow("Isim:", self.emergency_name_label)
        
        self.emergency_phone_label = QLabel()
        layout.addRow("Telefon:", self.emergency_phone_label)
        
        return group
    
    def _create_medical_group(self) -> QGroupBox:
        """Tibbi bilgiler grubu"""
        group = QGroupBox("Tibbi Bilgiler")
        group_font = QFont()
        group_font.setPointSize(11)
        group_font.setBold(True)
        group.setFont(group_font)
        
        layout = QVBoxLayout(group)
        
        self.tc_label = QLabel()
        layout.addWidget(self.tc_label)
        
        self.birth_date_label = QLabel()
        layout.addWidget(self.birth_date_label)
        
        medical_title = QLabel("Tibbi Gecmis:")
        medical_title.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(medical_title)
        
        self.medical_history_label = QLabel()
        self.medical_history_label.setWordWrap(True)
        self.medical_history_label.setStyleSheet("background-color: #F5F5F5; padding: 10px; border-radius: 4px;")
        layout.addWidget(self.medical_history_label)
        
        return group
    
    def _create_patient_notes_history_group(self) -> QGroupBox:
        """Danışan notları geçmişi grubu"""
        group = QGroupBox("📋 Danışan Notları")
        group_font = QFont()
        group_font.setPointSize(11)
        group_font.setBold(True)
        group.setFont(group_font)
        
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        
        self.patient_notes_container = QVBoxLayout()
        self.patient_notes_container.setSpacing(8)
        layout.addLayout(self.patient_notes_container)
        
        self.no_notes_label = QLabel("📭 Henüz not yok")
        self.no_notes_label.setStyleSheet("color: #757575; font-style: italic; padding: 20px;")
        self.no_notes_label.setAlignment(Qt.AlignCenter)
        self.patient_notes_container.addWidget(self.no_notes_label)
        
        return group
    
    def _create_stats_group(self) -> QGroupBox:
        """Istatistikler grubu"""
        group = QGroupBox("Istatistikler")
        group_font = QFont()
        group_font.setPointSize(11)
        group_font.setBold(True)
        group.setFont(group_font)
        
        layout = QVBoxLayout(group)
        
        stats_layout = QVBoxLayout()
        
        self.total_sessions_card, self.total_sessions_value = self._create_stat_card("0", "Toplam Gorusme")
        stats_layout.addWidget(self.total_sessions_card)
        
        self.upcoming_appointments_card, self.upcoming_appointments_value = self._create_stat_card("0", "Yaklasan Randevu")
        stats_layout.addWidget(self.upcoming_appointments_card)
        
        self.last_session_card, self.last_session_value = self._create_stat_card("-", "Son Gorusme")
        stats_layout.addWidget(self.last_session_card)
        
        layout.addLayout(stats_layout)
        
        return group
    
    def _create_stat_card(self, value: str, label: str):
        """Istatistik karti"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #E3F2FD;
                border-radius: 8px;
                padding: 15px;
                margin: 5px;
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(5)
        
        value_label = QLabel(value)
        value_label.setStyleSheet("font-size: 20pt; font-weight: bold; color: #1976D2;")
        value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(value_label)
        
        text_label = QLabel(label)
        text_label.setStyleSheet("font-size: 9pt; color: #757575;")
        text_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(text_label)
        
        return card, value_label
    
    def _create_sessions_group(self) -> QGroupBox:
        """Son gorusmeler grubu"""
        group = QGroupBox("Son Gorusmeler")
        group_font = QFont()
        group_font.setPointSize(11)
        group_font.setBold(True)
        group.setFont(group_font)
        
        layout = QVBoxLayout(group)
        
        self.sessions_container = QVBoxLayout()
        self.sessions_container.setSpacing(10)
        layout.addLayout(self.sessions_container)
        
        self.no_sessions_label = QLabel("Henuz gorusme kaydi yok")
        self.no_sessions_label.setStyleSheet("color: #757575; font-style: italic; padding: 20px;")
        self.no_sessions_label.setAlignment(Qt.AlignCenter)
        self.sessions_container.addWidget(self.no_sessions_label)
        
        return group
    
    def _create_notes_group(self) -> QGroupBox:
        """Notlar grubu"""
        group = QGroupBox("Danisan Notu Ekle/Duzenle")
        group_font = QFont()
        group_font.setPointSize(11)
        group_font.setBold(True)
        group.setFont(group_font)
        
        layout = QVBoxLayout(group)
        
        self.notes_text = QTextEdit()
        self.notes_text.setReadOnly(False)
        self.notes_text.setMinimumHeight(120)
        self.notes_text.setPlaceholderText("Danisan hakkinda yeni not ekleyin...")
        layout.addWidget(self.notes_text)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.clear_note_btn = QPushButton("🗑️ Temizle")
        self.clear_note_btn.setMaximumWidth(120)
        btn_layout.addWidget(self.clear_note_btn)
        
        self.save_notes_btn = QPushButton("💾 Kaydet")
        self.save_notes_btn.setMaximumWidth(150)
        self.save_notes_btn.setProperty("class", "success")
        btn_layout.addWidget(self.save_notes_btn)
        
        layout.addLayout(btn_layout)
        
        return group
    
    def _connect_signals(self):
        """Signal baglantilari"""
        self.back_btn.clicked.connect(self._handle_back)
        self.save_notes_btn.clicked.connect(self._handle_save_note)
        self.clear_note_btn.clicked.connect(self._handle_clear_note)
        self.edit_btn.clicked.connect(self._handle_edit_patient)
    
    def set_patient(self, patient_id: int):
        """Danisan bilgilerini yukle ve goster"""
        try:
            logger.info(f"Loading patient detail: {patient_id}")
            
            self.current_patient_id = patient_id
            self.current_patient = self.patient_service.get_patient_by_id(patient_id)
            
            if not self.current_patient:
                QMessageBox.warning(self, "Hata", "Danisan bilgileri yuklenemedi!")
                return
            
            self._populate_ui()
            self.patient_loaded.emit(patient_id)
            
        except Exception as e:
            logger.error(f"Patient detail yukleme hatasi: {e}")
            QMessageBox.critical(self, "Hata", f"Danisan bilgileri yuklenirken hata olustu:\n{str(e)}")
    
    def _populate_ui(self):
        """UI'i danisan bilgileriyle doldur"""
        if not self.current_patient:
            return
        
        patient = self.current_patient
        user = patient.user
        
        self.title_label.setText(f"Danisan: {user.full_name if user else 'N/A'}")
        self.name_label.setText(user.full_name if user else "N/A")
        
        gender_map = {"male": "Erkek", "female": "Kadin", "other": "Diger"}
        gender_text = gender_map.get(patient.gender, "Belirtilmemis")
        age_text = f"{patient.age} yas" if patient.age else "Yas belirtilmemis"
        self.age_gender_label.setText(f"{age_text} • {gender_text}")
        
        self.email_label.setText(user.email if user else "Email yok")
        self.phone_label.setText(user.phone if user and user.phone else "-")
        self.email_info_label.setText(user.email if user else "-")
        self.address_label.setText(patient.address if patient.address else "-")
        self.emergency_name_label.setText(patient.emergency_contact_name if patient.emergency_contact_name else "-")
        self.emergency_phone_label.setText(patient.emergency_contact_phone if patient.emergency_contact_phone else "-")
        
        self.tc_label.setText(f"TC No: {patient.tc_no if patient.tc_no else '-'}")
        
        if patient.birth_date:
            self.birth_date_label.setText(f"Dogum Tarihi: {patient.birth_date.strftime('%d.%m.%Y')}")
        else:
            self.birth_date_label.setText("Dogum Tarihi: -")
        
        self.medical_history_label.setText(patient.medical_history if patient.medical_history else "Tibbi gecmis kaydi yok")
        
        self._load_sessions()
        self._load_patient_notes_history()
        
        logger.debug(f"UI populated for patient: {patient.id}")
    
    def _handle_back(self):
        """Geri butonu"""
        self.navigate_to(PageID.PATIENTS_LIST)
    
    def _handle_clear_note(self):
        """Not temizle"""
        self.notes_text.clear()
        self.current_editing_note_id = None
        self.save_notes_btn.setText("💾 Kaydet")
    
    def _handle_save_note(self):
        """Notu kaydet veya güncelle"""
        if not self.current_patient:
            return
        
        note_text = self.notes_text.toPlainText().strip()
        
        if not note_text:
            QMessageBox.warning(self, "Uyarı", "Not boş olamaz!")
            return
        
        try:
            if self.current_editing_note_id:
                success = self.patient_note_repo.update(self.current_editing_note_id, note_text)
                
                if success:
                    QMessageBox.information(self, "Başarılı", "Not başarıyla güncellendi!")
                    self.notes_text.clear()
                    self.current_editing_note_id = None
                    self.save_notes_btn.setText("💾 Kaydet")
                    self._load_patient_notes_history()
                else:
                    QMessageBox.critical(self, "Hata", "Not güncellenemedi!")
            else:
                note = self.patient_note_repo.create(self.current_patient.id, note_text)
                
                if note:
                    QMessageBox.information(self, "Başarılı", "Not başarıyla kaydedildi!")
                    self.notes_text.clear()
                    self._load_patient_notes_history()
                else:
                    QMessageBox.critical(self, "Hata", "Not kaydedilemedi!")
        
        except Exception as e:
            logger.error(f"Not kaydetme hatasi: {e}")
            QMessageBox.critical(self, "Hata", f"Not kaydedilirken hata olustu:\n{str(e)}")
    
    def _load_patient_notes_history(self):
        """Danışan notlarını yükle"""
        if not self.current_patient:
            return
        
        try:
            self._clear_patient_notes_container()
            
            notes = self.patient_note_repo.find_by_patient(self.current_patient.id)
            
            if not notes:
                self.no_notes_label.setVisible(True)
            else:
                self.no_notes_label.setVisible(False)
                
                for note in notes:
                    card = self._create_patient_note_card(note)
                    self.patient_notes_container.addWidget(card)
            
            logger.info(f"{len(notes)} danışan notu listelendi")
            
        except Exception as e:
            logger.error(f"Notlar yükleme hatası: {e}")
    
    def _clear_patient_notes_container(self):
        """Patient notes container'ı temizle"""
        items_to_remove = []
        for i in range(self.patient_notes_container.count()):
            item = self.patient_notes_container.itemAt(i)
            if item and item.widget() and item.widget() != self.no_notes_label:
                items_to_remove.append(item.widget())
        
        for widget in items_to_remove:
            self.patient_notes_container.removeWidget(widget)
            widget.deleteLater()
    
    def _create_patient_note_card(self, note) -> QFrame:
        """Tek bir danışan notu kartı"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #FFF9C4;
                border: 2px solid #FBC02D;
                border-radius: 8px;
                padding: 12px;
                margin: 2px;
            }
            QFrame:hover {
                background-color: #FFF59D;
                border-color: #F9A825;
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        
        header_layout = QHBoxLayout()
        
        date_str = note.created_at.strftime("%d.%m.%Y %H:%M") if note.created_at else "N/A"
        
        if note.updated_at and note.updated_at != note.created_at:
            date_label = QLabel(f"📝 {date_str} (Güncellendi)")
        else:
            date_label = QLabel(f"📝 {date_str}")
        
        date_label.setStyleSheet("font-weight: bold; font-size: 9pt; color: #F57F17;")
        header_layout.addWidget(date_label)
        
        header_layout.addStretch()
        
        edit_btn = QPushButton("✏️")
        edit_btn.setMaximumWidth(30)
        edit_btn.setMaximumHeight(25)
        edit_btn.setProperty("note_id", note.id)
        edit_btn.setProperty("note_text", note.note_text)
        edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #FBC02D;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F9A825;
            }
        """)
        edit_btn.clicked.connect(self._handle_edit_note)
        header_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("🗑️")
        delete_btn.setMaximumWidth(30)
        delete_btn.setMaximumHeight(25)
        delete_btn.setProperty("note_id", note.id)
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #E57373;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #EF5350;
            }
        """)
        delete_btn.clicked.connect(self._handle_delete_note)
        header_layout.addWidget(delete_btn)
        
        layout.addLayout(header_layout)
        
        note_label = QLabel(note.note_text)
        note_label.setWordWrap(True)
        note_label.setStyleSheet("color: #424242; font-size: 9pt; line-height: 1.4; padding: 5px;")
        layout.addWidget(note_label)
        
        return card
    
    def _handle_edit_note(self):
        """Nota tıklayınca düzenleme moduna geç"""
        button = self.sender()
        note_id = button.property("note_id")
        note_text = button.property("note_text")
        
        self.notes_text.setPlainText(note_text)
        self.current_editing_note_id = note_id
        self.save_notes_btn.setText("💾 Güncelle")
        self.notes_text.setFocus()
    
    def _handle_delete_note(self):
        """Notu sil"""
        button = self.sender()
        note_id = button.property("note_id")
        
        reply = QMessageBox.question(
            self, "Notu Sil",
            "Bu notu silmek istediğinizden emin misiniz?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success = self.patient_note_repo.delete(note_id)
            
            if success:
                QMessageBox.information(self, "Başarılı", "Not silindi!")
                
                if self.current_editing_note_id == note_id:
                    self.notes_text.clear()
                    self.current_editing_note_id = None
                    self.save_notes_btn.setText("💾 Kaydet")
                
                self._load_patient_notes_history()
            else:
                QMessageBox.critical(self, "Hata", "Not silinemedi!")
    
    def on_page_show(self):
        """Sayfa gosterildiginde"""
        logger.debug("Patient detail page shown")
        
        if self.current_patient_id:
            self.set_patient(self.current_patient_id)
    
    def _load_sessions(self):
        """Danisanin gorusmelerini yukle"""
        if not self.current_patient:
            return
        
        try:
            sessions = self.therapy_repo.find_by_patient(self.current_patient.id, limit=10)
            
            logger.info(f"📊 {len(sessions)} session yüklendi")
            
            self._clear_sessions_container()
            
            total_count = self.therapy_repo.count_by_patient(self.current_patient.id)
            
            if total_count == 0:
                self.no_sessions_label.setVisible(True)
            else:
                self.no_sessions_label.setVisible(False)
                
                for session in sessions:
                    card = self._create_session_card(session)
                    self.sessions_container.addWidget(card)
                
                all_dates = [s.session_date for s in sessions if s.session_date]
                self._update_stats_combined(total_count, all_dates)
            
            logger.info(f"✅ Toplam {total_count} görüşme yüklendi")
            
        except Exception as e:
            logger.error(f"Oturum yukleme hatasi: {e}")
    
    def _clear_sessions_container(self):
        """Sessions container'i temizle"""
        items_to_remove = []
        for i in range(self.sessions_container.count()):
            item = self.sessions_container.itemAt(i)
            if item and item.widget() and item.widget() != self.no_sessions_label:
                items_to_remove.append(item.widget())
        
        for widget in items_to_remove:
            self.sessions_container.removeWidget(widget)
            widget.deleteLater()
    
    def _create_session_card(self, session) -> QFrame:
        """Session kartı"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #FAFAFA;
                border: 1px solid #E0E0E0;
                border-radius: 10px;
                padding: 4px;
                margin: 2px;
            }
            QFrame:hover { border-color: #2196F3; background-color: #F3F8FF; }
        """)

        layout = QHBoxLayout(card)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(12)

        # Durum ikonu
        status_icons = {
            "completed": ("✅", "#4CAF50"),
            "scheduled": ("📝", "#2196F3"),
            "in_progress": ("🔄", "#FF9800"),
            "cancelled": ("❌", "#F44336"),
        }
        icon, color = status_icons.get(session.status, ("📝", "#9E9E9E"))
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"font-size: 18pt; color: {color};")
        icon_label.setFixedWidth(30)
        layout.addWidget(icon_label)

        # Bilgiler
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        date_str = session.session_date.strftime('%d.%m.%Y %H:%M') if session.session_date else "Tarih yok"
        date_label = QLabel(f"📅  {date_str}")
        date_label.setStyleSheet("font-weight: bold; font-size: 10pt; color: #2C3E50;")
        info_layout.addWidget(date_label)

        duration_text = f"{session.duration_minutes} dk" if session.duration_minutes else "—"
        status_map = {"completed": "Tamamlandı", "scheduled": "Planlandı",
                      "in_progress": "Devam Ediyor", "cancelled": "İptal"}
        status_text = status_map.get(session.status, session.status)
        is_audio_session = bool(
            session.video_path and
            session.video_path.lower().endswith(('.wav', '.mp3', '.ogg', '.m4a'))
        )
        type_icon = "🔊 Ses  •  " if is_audio_session else ""
        detail_label = QLabel(f"⏱  {duration_text}   •   {type_icon}{status_text}")
        detail_label.setStyleSheet("color: #757575; font-size: 9pt;")
        info_layout.addWidget(detail_label)

        layout.addLayout(info_layout)
        layout.addStretch()

        # Ses mi video mu?
        is_audio = bool(
            session.video_path and
            session.video_path.lower().endswith(('.wav', '.mp3', '.ogg', '.m4a'))
        )

        if is_audio:
            # ── Ses çal butonu ──
            play_btn = QPushButton("🔊 Dinle")
            play_btn.setFixedSize(90, 34)
            btn_font = QFont()
            btn_font.setPointSize(10)
            btn_font.setBold(True)
            play_btn.setFont(btn_font)
            play_btn.setStyleSheet(
                "QPushButton {"
                "  background-color: #2196F3;"
                "  color: white; border: none; border-radius: 6px;"
                "}"
                "QPushButton:hover { background-color: #1976D2; }"
            )
            play_btn.setToolTip("Ses kaydını oynat")
            play_btn.clicked.connect(lambda _=False, p=session.video_path, s=session: self._play_audio(p, s))
            layout.addWidget(play_btn)
        else:
            # ── Analiz butonu ──
            has_emotion = False
            try:
                has_emotion = self.emotion_repo.count_by_session(session.id) > 0
            except Exception:
                pass

            analysis_btn = QPushButton("Analiz")
            analysis_btn.setFixedSize(80, 34)
            analysis_font = QFont()
            analysis_font.setPointSize(10)
            analysis_font.setBold(True)
            analysis_btn.setFont(analysis_font)
            if has_emotion:
                analysis_btn.setStyleSheet(
                    "QPushButton {"
                    "  background-color: #FF9800; color: white;"
                    "  border: none; border-radius: 6px;"
                    "}"
                    "QPushButton:hover { background-color: #F57C00; }"
                )
                analysis_btn.setToolTip("Duygu analizini görüntüle")
            else:
                analysis_btn.setStyleSheet(
                    "QPushButton {"
                    "  background-color: #BDBDBD; color: white;"
                    "  border: none; border-radius: 6px;"
                    "}"
                    "QPushButton:hover { background-color: #9E9E9E; }"
                )
                analysis_btn.setToolTip("Bu gorusme icin duygu analizi verisi yok")
            analysis_btn.clicked.connect(lambda _=False, s=session: self._open_analysis(s))
            layout.addWidget(analysis_btn)

        # ── Sil butonu ──
        delete_btn = QPushButton("Sil")
        delete_btn.setFixedSize(60, 34)
        delete_font = QFont()
        delete_font.setPointSize(10)
        delete_font.setBold(True)
        delete_btn.setFont(delete_font)
        delete_btn.setStyleSheet(
            "QPushButton {"
            "  background-color: #F44336;"
            "  color: white;"
            "  border: none;"
            "  border-radius: 6px;"
            "}"
            "QPushButton:hover { background-color: #D32F2F; }"
        )
        delete_btn.clicked.connect(lambda _=False, sid=session.id: self._delete_session(sid))
        layout.addWidget(delete_btn)

        return card

    def _open_analysis(self, session):
        """Duygu analizi dialog'unu aç"""
        try:
            from ui.dialogs.emotion_analysis_dialog import EmotionAnalysisDialog
            video_path = session.video_path if session.video_path else None
            dialog = EmotionAnalysisDialog(session, video_path, self)
            dialog.exec_()
        except Exception as e:
            logger.error(f"Analiz dialogu hatasi: {e}")
            QMessageBox.critical(self, "Hata", f"Analiz açılamadı:\n{str(e)}")

    def _play_audio(self, audio_path: str, session=None):
        """Ses kaydını AudioPlayerDialog ile oynat"""
        import os
        if not audio_path or not os.path.exists(audio_path):
            QMessageBox.warning(self, "Hata", "Ses dosyası bulunamadı!")
            return
        try:
            from ui.dialogs.audio_player_dialog import AudioPlayerDialog
            dlg = AudioPlayerDialog(audio_path, session=session, parent=self)
            dlg.exec_()
        except Exception as e:
            logger.error(f"Ses oynatma hatası: {e}")
            QMessageBox.critical(self, "Hata", f"Ses oynatılamadı:\n{str(e)}")

    def _delete_session(self, session_id: int):
        """Görüşmeyi sil"""
        reply = QMessageBox.question(
            self, "Görüşmeyi Sil",
            "Bu görüşmeyi silmek istediğinizden emin misiniz?\nBu işlem geri alınamaz!",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                success = self.therapy_repo.delete(session_id)
                if success:
                    QMessageBox.information(self, "Başarılı", "Görüşme silindi!")
                    self._load_sessions()
                else:
                    QMessageBox.critical(self, "Hata", "Görüşme silinemedi!")
            except Exception as e:
                logger.error(f"Görüşme silme hatası: {e}")
                QMessageBox.critical(self, "Hata", f"Hata: {str(e)}")
    
    def _handle_edit_patient(self):
        """Danışan bilgilerini düzenle"""
        try:
            from PyQt5.QtWidgets import QDialog
            
            dialog = EditPatientDialog(self.current_patient_id, self)
            
            if dialog.exec_() == QDialog.Accepted:
                self.set_patient(self.current_patient_id)
                logger.info("Danışan bilgileri güncellendi")
        
        except Exception as e:
            logger.error(f"Edit patient dialog hatası: {e}")
            QMessageBox.critical(self, "Hata", f"Dialog açılırken hata oluştu:\n{str(e)}")
    
    def _update_stats_combined(self, total_count: int, all_dates: list):
        """İstatistikleri guncelle"""
        self.total_sessions_value.setText(str(total_count))
        
        if all_dates:
            all_dates.sort(reverse=True)
            last_date = all_dates[0].strftime("%d.%m.%Y")
            self.last_session_value.setText(last_date)
        else:
            self.last_session_value.setText("-")
        
        self.upcoming_appointments_value.setText("0")