"""
Activities Page
Aktivite geçmişi sayfası
"""
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QComboBox, QPushButton, QFrame,
    QScrollArea, QWidget, QStackedWidget
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor

from ui.pages.base_page import BasePage
from core.session_manager import session_manager
from database.repositories.appointment_repository import AppointmentRepository
from database.repositories.emotion_repository import EmotionAnalysisRepository
from services.patient_service import PatientService
from services.therapy_service import TherapyService
from utils.logger import setup_logger
from datetime import datetime, timedelta

logger = setup_logger(__name__)


class ActivitiesPage(BasePage):
    """Aktivite geçmişi sayfası"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.appointment_repo = AppointmentRepository()
        self.patient_service = PatientService()
        self.therapy_service = TherapyService()
        self.emotion_repo = EmotionAnalysisRepository()

        self.all_activities = []
        self.all_sessions = []  # TherapySession nesneleri (kart için)

        self._setup_ui()

    def _setup_ui(self):
        """UI oluştur"""
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        self.layout.addLayout(layout)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("Aktivite Geçmişi")
        title.setStyleSheet("color: #2C3E50; font-size: 24pt; font-weight: bold;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        filter_label = QLabel("Filtre:")
        filter_label.setStyleSheet("font-weight: 600; font-size: 11pt;")
        header_layout.addWidget(filter_label)

        self.filter_combo = QComboBox()
        self.filter_combo.addItem("🔄 Tümü", "all")
        self.filter_combo.addItem("📅 Randevular", "appointments")
        self.filter_combo.addItem("📝 Görüşmeler", "sessions")
        self.filter_combo.addItem("👤 Hastalar", "patients")
        self.filter_combo.setMinimumWidth(150)
        self.filter_combo.currentIndexChanged.connect(self._apply_filter)
        header_layout.addWidget(self.filter_combo)

        refresh_btn = QPushButton("🔄 Yenile")
        refresh_btn.setMaximumWidth(100)
        refresh_btn.clicked.connect(self.load_activities)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #1976D2; }
        """)
        header_layout.addWidget(refresh_btn)

        layout.addLayout(header_layout)

        # İstatistik kartları
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(15)

        self.today_card = self._create_stat_card("0", "Bugün", "#4CAF50")
        stats_layout.addWidget(self.today_card)

        self.week_card = self._create_stat_card("0", "Bu Hafta", "#2196F3")
        stats_layout.addWidget(self.week_card)

        self.month_card = self._create_stat_card("0", "Bu Ay", "#FF9800")
        stats_layout.addWidget(self.month_card)

        layout.addLayout(stats_layout)

        # Stacked widget: liste (all/appointments/patients) veya session kartları
        self.stack = QStackedWidget()

        # Stack 0: QListWidget (genel aktiviteler)
        self.activities_list = QListWidget()
        self.activities_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #E0E0E0;
                background-color: white;
                border-radius: 8px;
            }
            QListWidget::item {
                padding: 15px;
                border-bottom: 1px solid #E0E0E0;
            }
            QListWidget::item:hover { background-color: #E8F5E9; }
        """)
        self.stack.addWidget(self.activities_list)

        # Stack 1: Session kartları (scroll area)
        self.sessions_scroll = QScrollArea()
        self.sessions_scroll.setWidgetResizable(True)
        self.sessions_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.sessions_container = QWidget()
        self.sessions_container.setStyleSheet("background: transparent;")
        self.sessions_layout = QVBoxLayout(self.sessions_container)
        self.sessions_layout.setSpacing(12)
        self.sessions_layout.setContentsMargins(0, 0, 0, 0)
        self.sessions_layout.addStretch()

        self.sessions_scroll.setWidget(self.sessions_container)
        self.stack.addWidget(self.sessions_scroll)

        layout.addWidget(self.stack)

    def _create_stat_card(self, value: str, label: str, color: str):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 12px;
                padding: 20px;
            }}
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(8)

        value_label = QLabel(value)
        value_label.setStyleSheet("color: white; font-size: 28pt; font-weight: bold;")
        value_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(value_label)

        text_label = QLabel(label)
        text_label.setStyleSheet("color: white; font-size: 10pt;")
        text_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(text_label)

        card.value_label = value_label
        return card

    def on_page_show(self):
        self.load_activities()

    def load_activities(self):
        try:
            doctor_id = session_manager.get_current_user_id()
            if not doctor_id:
                return

            self.all_activities = []
            self.all_sessions = []

            # Randevular
            appointments = self.appointment_repo.find_by_doctor(doctor_id, limit=100)
            for apt in appointments:
                if not apt.created_at:
                    continue
                patient = self.patient_service.get_patient_by_id(apt.patient_id)
                patient_name = patient.user.full_name if patient and patient.user else "N/A"
                time_ago = self._time_ago(apt.created_at)
                status_icons = {
                    'pending': '⏳', 'confirmed': '✅',
                    'completed': '✔️', 'cancelled': '❌'
                }
                icon = status_icons.get(apt.status, '📅')
                self.all_activities.append({
                    'time': apt.created_at,
                    'text': f"{icon} Randevu: {patient_name} - {apt.appointment_date.strftime('%d.%m.%Y %H:%M')} ({time_ago})",
                    'type': 'appointments',
                    'color': '#2196F3'
                })

            # Hastalar
            patients = self.patient_service.get_patients_by_doctor(doctor_id)
            for patient in patients:
                if patient.created_at:
                    time_ago = self._time_ago(patient.created_at)
                    self.all_activities.append({
                        'time': patient.created_at,
                        'text': f"👤 Yeni hasta eklendi: {patient.user.full_name if patient.user else 'N/A'} ({time_ago})",
                        'type': 'patients',
                        'color': '#4CAF50'
                    })

            # Görüşmeler — hem activities listesi hem de session kartları için sakla
            sessions = self.therapy_service.get_sessions_by_doctor(doctor_id, limit=100)
            for session in sessions:
                if session.created_at:
                    patient = self.patient_service.get_patient_by_id(session.patient_id)
                    patient_name = patient.user.full_name if patient and patient.user else "N/A"
                    time_ago = self._time_ago(session.created_at)
                    status_map = {
                        'scheduled': '📝', 'in_progress': '🔄',
                        'completed': '✅', 'cancelled': '❌'
                    }
                    icon = status_map.get(session.status, '📝')
                    self.all_activities.append({
                        'time': session.created_at,
                        'text': f"{icon} Görüşme: {patient_name} ({time_ago})",
                        'type': 'sessions',
                        'color': '#FF9800'
                    })
                    self.all_sessions.append({
                        'session': session,
                        'patient_name': patient_name,
                        'time_ago': time_ago
                    })

            self.all_activities.sort(key=lambda x: x['time'] or datetime.min, reverse=True)

            self._update_stats()
            self._apply_filter()

            logger.info(f"{len(self.all_activities)} aktivite yuklendi")

        except Exception as e:
            logger.error(f"Aktivite yukleme hatasi: {e}")

    def _apply_filter(self):
        filter_type = self.filter_combo.currentData()

        if filter_type == "sessions":
            self.stack.setCurrentIndex(1)
            self._populate_session_cards()
        else:
            self.stack.setCurrentIndex(0)
            self._populate_list(filter_type)

    def _populate_list(self, filter_type: str):
        self.activities_list.clear()

        if filter_type == "all":
            activities = self.all_activities
        else:
            activities = [a for a in self.all_activities if a['type'] == filter_type]

        if not activities:
            item = QListWidgetItem("📭 Aktivite bulunamadı")
            item.setForeground(Qt.gray)
            self.activities_list.addItem(item)
            return

        for activity in activities:
            item = QListWidgetItem(activity['text'])
            item.setForeground(QColor(activity['color']))
            self.activities_list.addItem(item)

    def _populate_session_cards(self):
        # Mevcut kartları temizle (stretch hariç)
        while self.sessions_layout.count() > 1:
            item = self.sessions_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self.all_sessions:
            empty_label = QLabel("📭 Görüşme bulunamadı")
            empty_label.setStyleSheet("color: #9E9E9E; font-size: 13pt; padding: 20px;")
            empty_label.setAlignment(Qt.AlignCenter)
            self.sessions_layout.insertWidget(0, empty_label)
            return

        for idx, entry in enumerate(self.all_sessions):
            card = self._create_session_card(entry)
            self.sessions_layout.insertWidget(idx, card)

    def _create_session_card(self, entry: dict) -> QFrame:
        session = entry['session']
        patient_name = entry['patient_name']
        time_ago = entry['time_ago']

        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #E0E0E0;
                border-radius: 10px;
                padding: 4px;
            }
            QFrame:hover { border-color: #FF9800; }
        """)

        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(16, 12, 16, 12)
        card_layout.setSpacing(16)

        # Sol: durum ikonu
        status_map = {
            'scheduled': ('📝', '#2196F3'),
            'in_progress': ('🔄', '#FF9800'),
            'completed': ('✅', '#4CAF50'),
            'cancelled': ('❌', '#F44336')
        }
        icon, color = status_map.get(session.status, ('📝', '#9E9E9E'))

        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"font-size: 22pt; color: {color};")
        icon_label.setFixedWidth(36)
        card_layout.addWidget(icon_label)

        # Orta: bilgiler
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)

        name_label = QLabel(f"👤 {patient_name}")
        name_label.setStyleSheet("font-size: 12pt; font-weight: bold; color: #2C3E50;")
        info_layout.addWidget(name_label)

        date_str = session.session_date.strftime("%d.%m.%Y %H:%M") if session.session_date else "—"
        duration_str = f"{session.duration_minutes} dk" if session.duration_minutes else "—"
        detail_label = QLabel(f"📅 {date_str}   ⏱ {duration_str}   ({time_ago})")
        detail_label.setStyleSheet("font-size: 10pt; color: #757575;")
        info_layout.addWidget(detail_label)

        card_layout.addLayout(info_layout, 1)

        # Sağ: butonlar
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        # Analiz butonu — emotion verisi varsa aktif
        has_emotion = False
        try:
            has_emotion = self.emotion_repo.count_by_session(session.id) > 0
        except Exception:
            pass

        analysis_btn = QPushButton("📊 Analiz")
        analysis_btn.setMinimumWidth(100)
        analysis_btn.setEnabled(has_emotion)
        if has_emotion:
            analysis_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FF9800;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 14px;
                    font-weight: bold;
                    font-size: 10pt;
                }
                QPushButton:hover { background-color: #F57C00; }
            """)
        else:
            analysis_btn.setStyleSheet("""
                QPushButton {
                    background-color: #E0E0E0;
                    color: #9E9E9E;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 14px;
                    font-size: 10pt;
                }
            """)
            analysis_btn.setToolTip("Bu görüşme için duygu analizi verisi yok")

        # Butona session referansı bağla
        analysis_btn.clicked.connect(lambda checked, s=session: self._open_analysis(s))
        btn_layout.addWidget(analysis_btn)

        card_layout.addLayout(btn_layout)

        return card

    def _open_analysis(self, session):
        """Duygu analizi dialogunu aç"""
        try:
            from ui.dialogs.emotion_analysis_dialog import EmotionAnalysisDialog
            video_path = session.video_path if session.video_path else None
            dialog = EmotionAnalysisDialog(session, video_path, self)
            dialog.exec_()
        except Exception as e:
            logger.error(f"Analiz dialogu acma hatasi: {e}")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Hata", f"Analiz açılamadı:\n{str(e)}")

    def _update_stats(self):
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0)
        week_start = now - timedelta(days=7)
        month_start = now - timedelta(days=30)

        today_count = sum(1 for a in self.all_activities if a['time'] >= today_start)
        week_count = sum(1 for a in self.all_activities if a['time'] >= week_start)
        month_count = sum(1 for a in self.all_activities if a['time'] >= month_start)

        self.today_card.value_label.setText(str(today_count))
        self.week_card.value_label.setText(str(week_count))
        self.month_card.value_label.setText(str(month_count))

    def _time_ago(self, dt: datetime) -> str:
        if not dt:
            return "bilinmiyor"
        now = datetime.now()
        seconds = (now - dt).total_seconds()
        if seconds < 60:
            return "az önce"
        elif seconds < 3600:
            return f"{int(seconds / 60)} dakika önce"
        elif seconds < 86400:
            return f"{int(seconds / 3600)} saat önce"
        elif seconds < 172800:
            return "dün"
        elif seconds < 604800:
            return f"{int(seconds / 86400)} gün önce"
        else:
            return dt.strftime("%d.%m.%Y")
