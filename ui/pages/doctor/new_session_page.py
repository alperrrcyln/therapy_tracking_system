"""
New Session Page
Yeni gorusme sayfasi - kamera, video kayit, notlar
"""
import json as _json
from datetime import datetime

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QComboBox, QGroupBox, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer, QTime
from PyQt5.QtGui import QFont

from ui.pages.base_page import BasePage
from ui.widgets.camera_widget import CameraWidget
from services.patient_service import PatientService
from services.therapy_service import TherapyService
from core.session_manager import session_manager
from core.constants import PageID
from utils.logger import setup_logger
from database.repositories.emotion_repository import EmotionAnalysisRepository
from database.models import EmotionAnalysis

logger = setup_logger(__name__)

_EMOTION_ORDER = ['angry', 'disgust', 'fear', 'happy', 'sad', 'surprise', 'neutral']
_EMOTION_TR    = {
    'angry': 'Kizgin', 'disgust': 'Igrenmis', 'fear': 'Korkmus',
    'happy': 'Mutlu',  'neutral': 'Notr',      'sad': 'Uzgun', 'surprise': 'Saskin'
}
_EMOTION_COLORS = {
    'angry': '#E74C3C', 'disgust': '#27AE60', 'fear': '#9B59B6',
    'happy': '#F39C12', 'neutral': '#95A5A6',  'sad': '#3498DB', 'surprise': '#E67E22'
}


class NewSessionPage(BasePage):
    """Yeni gorusme sayfasi"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.patient_service  = PatientService()
        self.therapy_service  = TherapyService()
        self.emotion_repo     = EmotionAnalysisRepository()

        self.session_timer        = QTimer()
        self.session_start_time   = None
        self.current_video_path   = None
        self.current_patient_id   = None
        self.current_session_id   = None
        self.last_emotion_save_time = None
        self._emotion_tick        = 0

        self._live_bars = None

        self._setup_ui()
        self._connect_signals()

    # ── UI ────────────────────────────────────────────────────────────────────
    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        self.layout.addLayout(layout)

        title = QLabel("Yeni Gorusme")
        f = QFont(); f.setPointSize(24); f.setBold(True)
        title.setFont(f)
        layout.addWidget(title)

        # Danisan secimi
        patient_layout = QHBoxLayout()
        pl = QLabel("Danisan:")
        pl.setStyleSheet("font-weight: 600; font-size: 11pt;")
        patient_layout.addWidget(pl)
        self.patient_combo = QComboBox()
        self.patient_combo.setMinimumHeight(40)
        patient_layout.addWidget(self.patient_combo)
        patient_layout.addStretch()
        layout.addLayout(patient_layout)

        # Kamera grubu
        camera_group = QGroupBox("Kamera")
        camera_layout = QVBoxLayout(camera_group)

        self.camera_widget = CameraWidget()
        camera_layout.addWidget(self.camera_widget)

        # Kamera kontrolleri
        controls_layout = QHBoxLayout()
        self.start_camera_btn = QPushButton("Kamerayi Baslat")
        self.start_camera_btn.setMinimumHeight(40)
        controls_layout.addWidget(self.start_camera_btn)

        self.stop_camera_btn = QPushButton("Kamerayi Durdur")
        self.stop_camera_btn.setMinimumHeight(40)
        self.stop_camera_btn.setEnabled(False)
        controls_layout.addWidget(self.stop_camera_btn)

        self.start_record_btn = QPushButton("Kayit Baslat")
        self.start_record_btn.setProperty("class", "success")
        self.start_record_btn.setMinimumHeight(40)
        self.start_record_btn.setEnabled(False)
        controls_layout.addWidget(self.start_record_btn)

        self.stop_record_btn = QPushButton("Kayit Durdur")
        self.stop_record_btn.setProperty("class", "danger")
        self.stop_record_btn.setMinimumHeight(40)
        self.stop_record_btn.setEnabled(False)
        controls_layout.addWidget(self.stop_record_btn)
        camera_layout.addLayout(controls_layout)

        # Sure
        self.timer_label = QLabel("Sure: 00:00:00")
        self.timer_label.setStyleSheet("font-size: 16pt; font-weight: bold; color: #2196F3;")
        self.timer_label.setAlignment(Qt.AlignCenter)
        camera_layout.addWidget(self.timer_label)

        # Canli duygu grafigi
        self.live_fig = Figure(figsize=(8, 1.8), facecolor='#FAFAFA', tight_layout=True)
        self.live_canvas = FigureCanvas(self.live_fig)
        self.live_canvas.setFixedHeight(140)
        self._live_ax = self.live_fig.add_subplot(111)
        self._init_live_chart()
        camera_layout.addWidget(self.live_canvas)

        layout.addWidget(camera_group)

        # Notlar
        notes_layout = QHBoxLayout()

        session_notes_group = QGroupBox("Oturum Notlari")
        sn_layout = QVBoxLayout(session_notes_group)
        self.session_notes = QTextEdit()
        self.session_notes.setPlaceholderText("Gorusme sirasinda notlar...")
        sn_layout.addWidget(self.session_notes)
        notes_layout.addWidget(session_notes_group)

        therapist_notes_group = QGroupBox("Terapist Notlari")
        tn_layout = QVBoxLayout(therapist_notes_group)
        self.therapist_notes = QTextEdit()
        self.therapist_notes.setPlaceholderText("Terapist degerlendirme notlari...")
        tn_layout.addWidget(self.therapist_notes)
        notes_layout.addWidget(therapist_notes_group)

        layout.addLayout(notes_layout)

        # Kaydet butonu
        save_layout = QHBoxLayout()
        save_layout.addStretch()
        self.save_btn = QPushButton("Gorusmeyi Kaydet ve Bitir")
        self.save_btn.setMinimumHeight(50)
        self.save_btn.setMinimumWidth(250)
        sf = QFont(); sf.setPointSize(11); sf.setBold(True)
        self.save_btn.setFont(sf)
        self.save_btn.setEnabled(False)
        save_layout.addWidget(self.save_btn)
        layout.addLayout(save_layout)

    def _init_live_chart(self):
        """Canli duygu grafigini sifirla"""
        ax = self._live_ax
        ax.clear()
        labels = [_EMOTION_TR[e] for e in _EMOTION_ORDER]
        colors = [_EMOTION_COLORS[e] for e in _EMOTION_ORDER]
        vals   = [0.0] * len(_EMOTION_ORDER)
        self._live_bars = ax.barh(labels, vals, color=colors, height=0.65)
        ax.set_xlim(0, 1)
        ax.set_xlabel('Olasilik', fontsize=7)
        ax.tick_params(labelsize=7)
        ax.grid(axis='x', alpha=0.25)
        self.live_canvas.draw()

    def _update_live_chart(self, all_emotions_json: str):
        """Canli grafigi guncelle"""
        try:
            scores = _json.loads(all_emotions_json)
            vals   = [scores.get(e, 0.0) for e in _EMOTION_ORDER]
            if self._live_bars is not None:
                for bar, val in zip(self._live_bars, vals):
                    bar.set_width(val)
                self.live_canvas.draw_idle()
        except Exception:
            pass

    # ── Sinyaller ─────────────────────────────────────────────────────────────
    def _connect_signals(self):
        self.camera_widget.emotion_detected.connect(self._on_emotion_detected)
        self.start_camera_btn.clicked.connect(self._handle_start_camera)
        self.stop_camera_btn.clicked.connect(self._handle_stop_camera)
        self.start_record_btn.clicked.connect(self._handle_start_recording)
        self.stop_record_btn.clicked.connect(self._handle_stop_recording)
        self.save_btn.clicked.connect(self._handle_save_session)
        self.camera_widget.recording_stopped.connect(self._on_recording_stopped)
        self.camera_widget.error_occurred.connect(self._on_camera_error)
        self.session_timer.timeout.connect(self._update_timer)

    # ── Sayfa acilisi ─────────────────────────────────────────────────────────
    def on_page_show(self):
        logger.debug("New session page shown")
        self._load_patients()

    def _load_patients(self):
        try:
            doctor_id = session_manager.get_current_user_id()
            patients  = self.patient_service.get_patients_by_doctor(doctor_id)
            self.patient_combo.clear()
            for patient in patients:
                name = patient.user.full_name if patient.user else "N/A"
                self.patient_combo.addItem(name, patient.id)
            logger.info(f"{len(patients)} danisan yuklendi")
        except Exception as e:
            logger.error(f"Danisan yukleme hatasi: {e}")

    # ── Kamera kontrolleri ────────────────────────────────────────────────────
    def _handle_start_camera(self):
        if self.camera_widget.start_camera():
            self.start_camera_btn.setEnabled(False)
            self.stop_camera_btn.setEnabled(True)
            self.start_record_btn.setEnabled(True)

    def _handle_stop_camera(self):
        self.camera_widget.stop_camera()
        self.start_camera_btn.setEnabled(True)
        self.stop_camera_btn.setEnabled(False)
        self.start_record_btn.setEnabled(False)
        self.stop_record_btn.setEnabled(False)

    def _handle_start_recording(self):
        if self.patient_combo.currentIndex() == -1:
            QMessageBox.warning(self, "Uyari", "Lutfen danisan secin!")
            return

        patient_id = self.patient_combo.currentData()
        doctor_id  = session_manager.get_current_user_id()

        success, message, session = self.therapy_service.create_session(
            patient_id=patient_id, doctor_id=doctor_id,
            session_notes=None, therapist_notes=None, video_path=None
        )
        if not success:
            QMessageBox.critical(self, "Hata", f"Session olusturulamadi:\n{message}")
            return

        self.current_session_id = session.id
        logger.info(f"Session olusturuldu: {session.id}")

        if self.camera_widget.start_recording(patient_id, doctor_id):
            self.current_patient_id     = patient_id
            self.session_start_time     = QTime.currentTime()
            self.last_emotion_save_time = None
            self._emotion_tick          = 0
            self.session_timer.start(1000)
            self.start_record_btn.setEnabled(False)
            self.stop_record_btn.setEnabled(True)
            self.patient_combo.setEnabled(False)

    def _handle_stop_recording(self):
        video_path = self.camera_widget.stop_recording()
        self.session_timer.stop()
        self.start_record_btn.setEnabled(True)
        self.stop_record_btn.setEnabled(False)
        self.save_btn.setEnabled(True)

    def _on_recording_stopped(self, video_path):
        self.current_video_path = video_path
        logger.info(f"Video kaydedildi: {video_path}")

    def _on_camera_error(self, error_msg):
        QMessageBox.critical(self, "Kamera Hatasi", error_msg)

    def _update_timer(self):
        if self.session_start_time:
            elapsed = self.session_start_time.secsTo(QTime.currentTime())
            h = elapsed // 3600
            m = (elapsed % 3600) // 60
            s = elapsed % 60
            self.timer_label.setText(f"Sure: {h:02d}:{m:02d}:{s:02d}")

    # ── Duygu tespiti ─────────────────────────────────────────────────────────
    def _on_emotion_detected(self, emotion: str, confidence: float, all_emotions_json: str):
        """Her frame'de: canli grafigi guncelle + 250ms throttle ile DB'ye kaydet"""
        # Canli grafik her zaman guncellenir
        self._update_live_chart(all_emotions_json)

        # DB kaydi: saniyede 4 kez (250ms arayla)
        if not self.current_session_id:
            return
        now = datetime.now()
        if (self.last_emotion_save_time is None or
                (now - self.last_emotion_save_time).total_seconds() >= 0.25):
            self.last_emotion_save_time = now
            self._emotion_tick += 1
            frame_time = self._emotion_tick * 0.25
            self.emotion_repo.create(EmotionAnalysis(
                session_id=self.current_session_id,
                emotion_type=emotion,
                confidence=confidence,
                frame_number=frame_time,
                additional_data=all_emotions_json,
                timestamp=now
            ))

    # ── Kaydet ve bitir ───────────────────────────────────────────────────────
    def _handle_save_session(self):
        try:
            if not self.current_session_id:
                QMessageBox.warning(self, "Uyari", "Aktif gorusme yok!")
                return

            duration = (self.session_start_time.secsTo(QTime.currentTime()) // 60
                        if self.session_start_time else 0)

            success = self.therapy_service.complete_session(
                session_id=self.current_session_id,
                duration_minutes=duration,
                session_notes=self.session_notes.toPlainText().strip() or None,
                therapist_notes=self.therapist_notes.toPlainText().strip() or None,
                video_path=self.current_video_path
            )

            if success:
                QMessageBox.information(
                    self, "Basarili",
                    f"Gorusme basariyla kaydedildi!\nSure: {duration} dakika"
                )
                logger.info(f"Session tamamlandi: {self.current_session_id}")
                self._reset_form()
            else:
                QMessageBox.critical(self, "Hata", "Gorusme kaydedilemedi!")

        except Exception as e:
            logger.error(f"Session kaydetme hatasi: {e}")
            QMessageBox.critical(self, "Hata", f"Hata olustu:\n{str(e)}")

    def _reset_form(self):
        self.session_notes.clear()
        self.therapist_notes.clear()
        self.timer_label.setText("Sure: 00:00:00")
        self.current_video_path     = None
        self.current_patient_id     = None
        self.current_session_id     = None
        self.session_start_time     = None
        self.last_emotion_save_time = None
        self._emotion_tick          = 0
        self.patient_combo.setEnabled(True)
        self.save_btn.setEnabled(False)
        self._init_live_chart()
        if self.camera_widget.capture:
            self._handle_stop_camera()
