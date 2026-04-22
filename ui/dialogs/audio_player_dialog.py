"""
Audio Player Dialog
Ses kaydi oynatici - slider, sure, oynat/durdur
"""
import os
from datetime import datetime

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QSlider, QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt, QUrl, QTimer
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtGui import QFont

from utils.logger import setup_logger

logger = setup_logger(__name__)


class AudioPlayerDialog(QDialog):
    """Ses kaydi oynatici dialog"""

    def __init__(self, audio_path: str, session=None, parent=None):
        super().__init__(parent)
        self.audio_path = audio_path
        self.session = session
        self.dur_ms = 0
        self._user_dragging = False

        self._build_ui()
        self._connect_signals()
        self._load_audio()

    # ── UI ───────────────────────────────────────────────────────────────────
    def _build_ui(self):
        fname = os.path.basename(self.audio_path)
        self.setWindowTitle(f"Ses Kaydı  —  {fname}")
        self.setMinimumSize(560, 320)
        self.resize(620, 340)
        self.setStyleSheet("background-color: #F5F5F5;")

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 20)
        root.setSpacing(16)

        # ── Başlık ──────────────────────────────────────────────────────────
        title = QLabel("🔊  Ses Kaydı Oynatıcı")
        tf = QFont(); tf.setPointSize(14); tf.setBold(True)
        title.setFont(tf)
        title.setStyleSheet("color: #1565C0;")
        root.addWidget(title)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #BDBDBD;")
        root.addWidget(sep)

        # ── Dosya bilgisi ────────────────────────────────────────────────────
        info_box = QFrame()
        info_box.setStyleSheet(
            "QFrame { background: #E3F2FD; border-radius: 8px; padding: 4px; }"
        )
        info_layout = QVBoxLayout(info_box)
        info_layout.setContentsMargins(14, 10, 14, 10)
        info_layout.setSpacing(4)

        fname_label = QLabel(f"📄  {fname}")
        fname_label.setStyleSheet("font-size: 11pt; font-weight: bold; color: #0D47A1;")
        info_layout.addWidget(fname_label)

        if self.session:
            date_str = (self.session.session_date.strftime('%d.%m.%Y %H:%M')
                        if self.session.session_date else '—')
            dur_str = (f"{self.session.duration_minutes} dakika"
                       if self.session.duration_minutes else '—')
            meta = QLabel(f"📅  {date_str}    ⏱  {dur_str}")
            meta.setStyleSheet("font-size: 10pt; color: #1565C0;")
            info_layout.addWidget(meta)

        root.addWidget(info_box)

        # ── Süre etiketi ─────────────────────────────────────────────────────
        self.pos_label = QLabel("00:00 / 00:00")
        self.pos_label.setAlignment(Qt.AlignCenter)
        pf = QFont(); pf.setPointSize(20); pf.setBold(True)
        self.pos_label.setFont(pf)
        self.pos_label.setStyleSheet("color: #1565C0; letter-spacing: 2px;")
        root.addWidget(self.pos_label)

        # ── İlerleme çubuğu ──────────────────────────────────────────────────
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 0)
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 8px; background: #BBDEFB; border-radius: 4px;
            }
            QSlider::handle:horizontal {
                width: 20px; height: 20px; margin: -6px 0;
                background: #1976D2; border-radius: 10px;
            }
            QSlider::sub-page:horizontal {
                background: #1976D2; border-radius: 4px;
            }
        """)
        root.addWidget(self.slider)

        # ── Kontrol butonları ─────────────────────────────────────────────────
        ctrl = QHBoxLayout()
        ctrl.setSpacing(12)
        ctrl.addStretch()

        btn_style = lambda bg, hover: (
            f"QPushButton {{ background: {bg}; color: white; border: none; "
            f"border-radius: 8px; padding: 10px 24px; font-size: 12pt; font-weight: bold; }}"
            f"QPushButton:hover {{ background: {hover}; }}"
            f"QPushButton:disabled {{ background: #B0BEC5; }}"
        )

        self.play_btn = QPushButton("▶  Oynat")
        self.play_btn.setMinimumWidth(130)
        self.play_btn.setStyleSheet(btn_style("#1976D2", "#1565C0"))
        ctrl.addWidget(self.play_btn)

        self.stop_btn = QPushButton("⏹  Durdur")
        self.stop_btn.setMinimumWidth(130)
        self.stop_btn.setStyleSheet(btn_style("#546E7A", "#37474F"))
        ctrl.addWidget(self.stop_btn)

        ctrl.addStretch()
        root.addLayout(ctrl)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet("color: #BDBDBD;")
        root.addWidget(sep2)

        # ── Kapat ────────────────────────────────────────────────────────────
        bot = QHBoxLayout()
        bot.addStretch()
        close_btn = QPushButton("Kapat")
        cf = QFont(); cf.setPointSize(10); cf.setBold(True)
        close_btn.setFont(cf)
        close_btn.setFixedSize(110, 36)
        close_btn.setStyleSheet(
            "QPushButton { background: #546E7A; color: white; border: none; border-radius: 6px; }"
            "QPushButton:hover { background: #37474F; }"
        )
        close_btn.clicked.connect(self.accept)
        bot.addWidget(close_btn)
        root.addLayout(bot)

        # ── Media player ─────────────────────────────────────────────────────
        self.player = QMediaPlayer()

    # ── Sinyal bağlantıları ──────────────────────────────────────────────────
    def _connect_signals(self):
        self.player.durationChanged.connect(self._on_duration)
        self.player.positionChanged.connect(self._on_position)
        self.player.stateChanged.connect(self._on_state)

        self.play_btn.clicked.connect(self._toggle_play)
        self.stop_btn.clicked.connect(self._stop)

        self.slider.sliderPressed.connect(lambda: setattr(self, '_user_dragging', True))
        self.slider.sliderReleased.connect(self._on_slider_released)
        self.slider.sliderMoved.connect(
            lambda v: self.pos_label.setText(f"{self._fmt(v)} / {self._fmt(self.dur_ms)}")
        )

    # ── Ses yükleme ──────────────────────────────────────────────────────────
    def _load_audio(self):
        if not os.path.exists(self.audio_path):
            self.pos_label.setText("Dosya bulunamadı!")
            self.play_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)
            return
        self.player.setMedia(QMediaContent(QUrl.fromLocalFile(self.audio_path)))

    # ── Sinyal işleyicileri ──────────────────────────────────────────────────
    def _on_duration(self, ms: int):
        self.dur_ms = ms
        self.slider.setRange(0, ms)
        self.pos_label.setText(f"00:00 / {self._fmt(ms)}")

    def _on_position(self, ms: int):
        if self._user_dragging:
            return
        self.slider.blockSignals(True)
        self.slider.setValue(ms)
        self.slider.blockSignals(False)
        self.pos_label.setText(f"{self._fmt(ms)} / {self._fmt(self.dur_ms)}")

    def _on_state(self, state):
        if state == QMediaPlayer.PlayingState:
            self.play_btn.setText("⏸  Duraklat")
        else:
            self.play_btn.setText("▶  Oynat")

    def _on_slider_released(self):
        self._user_dragging = False
        self.player.setPosition(self.slider.value())

    def _toggle_play(self):
        if self.player.state() == QMediaPlayer.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def _stop(self):
        self.player.stop()

    @staticmethod
    def _fmt(ms: int) -> str:
        s = int(ms / 1000)
        return f"{s // 60:02d}:{s % 60:02d}"

    def closeEvent(self, event):
        self.player.stop()
        event.accept()
