"""
Emotion Analysis Dialog
Duygu analizi: yatay zaman grafigi + pasta grafik + video — tam senkronizasyon
"""
import os
import json
import numpy as np
from scipy.interpolate import make_interp_spline
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QMessageBox, QSlider, QSizePolicy, QFrame
)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtGui import QFont

from database.repositories.emotion_repository import EmotionAnalysisRepository
from utils.logger import setup_logger

logger = setup_logger(__name__)

# ── Duygu paleti ─────────────────────────────────────────────────────────────
EMOTION_CONFIG = {
    'angry':    {'turkish': 'Kizgin',   'color': '#E74C3C'},
    'disgusted':{'turkish': 'Igrenmis', 'color': '#27AE60'},
    'disgust':  {'turkish': 'Igrenmis', 'color': '#27AE60'},
    'fearful':  {'turkish': 'Korkmus',  'color': '#9B59B6'},
    'fear':     {'turkish': 'Korkmus',  'color': '#9B59B6'},
    'happy':    {'turkish': 'Mutlu',    'color': '#F39C12'},
    'neutral':  {'turkish': 'Notr',     'color': '#95A5A6'},
    'sad':      {'turkish': 'Uzgun',    'color': '#3498DB'},
    'surprised':{'turkish': 'Sasirmis', 'color': '#E67E22'},
    'surprise': {'turkish': 'Sasirmis', 'color': '#E67E22'},
}

def _label(key):
    c = EMOTION_CONFIG.get(key, {})
    return c.get('turkish', key)

def _color(key):
    return EMOTION_CONFIG.get(key, {}).get('color', '#333333')


class EmotionAnalysisDialog(QDialog):
    """Duygu analizi: grafik + pasta + video + senkronizasyon"""

    def __init__(self, session, video_path: str = None, parent=None):
        super().__init__(parent)
        self.session      = session
        self.video_path   = video_path
        self.emotion_repo = EmotionAnalysisRepository()
        self.emotions     = []

        # senkronizasyon
        self._time_line   = None   # axvline nesnesi
        self.video_dur_ms = 0
        self.line_ax      = None
        self._user_dragging = False

        self._build_ui()
        self._load_data()
        self._connect_signals()

    # ── UI ───────────────────────────────────────────────────────────────────
    def _build_ui(self):
        date_str = (self.session.session_date.strftime('%d.%m.%Y %H:%M')
                    if self.session.session_date else '—')
        self.setWindowTitle(f"Duygu Analizi  —  {date_str}")
        self.setMinimumSize(1300, 820)
        self.resize(1400, 860)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(14)

        # ── Başlık ──
        title = QLabel(f"Duygu Analizi  —  Gorusme #{self.session.id}  |  {date_str}")
        f = QFont(); f.setPointSize(14); f.setBold(True)
        title.setFont(f)
        title.setStyleSheet("color: #2C3E50;")
        root.addWidget(title)

        sep = QFrame(); sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #E0E0E0;")
        root.addWidget(sep)

        # ── İçerik: sol (grafikler) + sağ (video) ──
        body = QHBoxLayout()
        body.setSpacing(18)

        # Sol: yatay grafik + pasta grafik
        left = QVBoxLayout()
        left.setSpacing(10)

        # Yatay zaman grafigi
        self.line_fig    = Figure(figsize=(7, 3.6), tight_layout=True)
        self.line_canvas = FigureCanvas(self.line_fig)
        self.line_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.line_canvas.mpl_connect('button_press_event', self._on_graph_click)
        left.addWidget(self.line_canvas, 55)

        # Pasta grafigi
        self.pie_fig    = Figure(figsize=(7, 3.0), tight_layout=True)
        self.pie_canvas = FigureCanvas(self.pie_fig)
        self.pie_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        left.addWidget(self.pie_canvas, 45)

        body.addLayout(left, 58)

        # Sag: video player
        right = QVBoxLayout()
        right.setSpacing(8)

        self._video_title = QLabel("Video Kaydi")
        vf = QFont(); vf.setPointSize(11); vf.setBold(True)
        self._video_title.setFont(vf)
        self._video_title.setStyleSheet("color: #2C3E50;")
        right.addWidget(self._video_title)

        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumHeight(340)
        self.video_widget.setStyleSheet("background: #000;")
        self.video_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        right.addWidget(self.video_widget, 1)

        # Zaman etiketi
        self.pos_label = QLabel("00:00 / 00:00")
        self.pos_label.setAlignment(Qt.AlignCenter)
        pf = QFont(); pf.setPointSize(13); pf.setBold(True)
        self.pos_label.setFont(pf)
        self.pos_label.setStyleSheet("color: #1565C0;")
        right.addWidget(self.pos_label)

        # Ilerleme cubugu
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 0)
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 6px; background: #CFD8DC; border-radius: 3px;
            }
            QSlider::handle:horizontal {
                width: 16px; height: 16px; margin: -5px 0;
                background: #1976D2; border-radius: 8px;
            }
            QSlider::sub-page:horizontal {
                background: #1976D2; border-radius: 3px;
            }
        """)
        self.slider.sliderMoved.connect(self._seek)
        right.addWidget(self.slider)

        # Kontrol butonlari
        ctrl = QHBoxLayout()
        ctrl.setSpacing(10)

        btn_style_play = (
            "QPushButton {"
            "  background-color: #1976D2; color: white;"
            "  border: none; border-radius: 6px;"
            "  padding: 8px 18px; font-size: 11pt; font-weight: bold;"
            "}"
            "QPushButton:hover { background-color: #1565C0; }"
            "QPushButton:disabled { background-color: #B0BEC5; color: #78909C; }"
        )
        btn_style_stop = (
            "QPushButton {"
            "  background-color: #546E7A; color: white;"
            "  border: none; border-radius: 6px;"
            "  padding: 8px 18px; font-size: 11pt; font-weight: bold;"
            "}"
            "QPushButton:hover { background-color: #37474F; }"
            "QPushButton:disabled { background-color: #B0BEC5; color: #78909C; }"
        )

        self.play_btn = QPushButton("Oynat")
        self.play_btn.setStyleSheet(btn_style_play)
        self.play_btn.clicked.connect(self._toggle_play)
        ctrl.addWidget(self.play_btn)

        self.stop_btn = QPushButton("Durdur")
        self.stop_btn.setStyleSheet(btn_style_stop)
        self.stop_btn.clicked.connect(self._stop_video)
        ctrl.addWidget(self.stop_btn)

        right.addLayout(ctrl)

        body.addLayout(right, 42)
        root.addLayout(body, 1)

        # ── Alt: kapat ──
        bot = QHBoxLayout()
        bot.addStretch()
        close_btn = QPushButton("Kapat")
        cf = QFont(); cf.setPointSize(10); cf.setBold(True)
        close_btn.setFont(cf)
        close_btn.setFixedSize(110, 36)
        close_btn.setStyleSheet(
            "QPushButton { background-color: #546E7A; color: white;"
            " border: none; border-radius: 6px; }"
            "QPushButton:hover { background-color: #37474F; }"
        )
        close_btn.clicked.connect(self.accept)
        bot.addWidget(close_btn)
        root.addLayout(bot)

        # ── Media player ──
        self.media_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.media_player.setVideoOutput(self.video_widget)

        if self.video_path and os.path.exists(self.video_path):
            self.media_player.setMedia(
                QMediaContent(QUrl.fromLocalFile(self.video_path))
            )
        else:
            self._video_title.setText("Video Kaydi Yok")
            self.play_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)
            self.slider.setEnabled(False)

    # ── Sinyaller ────────────────────────────────────────────────────────────
    def _connect_signals(self):
        self.media_player.durationChanged.connect(self._on_duration)
        self.media_player.positionChanged.connect(self._on_position)
        self.slider.sliderPressed.connect(self._on_slider_pressed)
        self.slider.sliderReleased.connect(self._on_slider_released)
        self.slider.sliderMoved.connect(self._on_slider_moved)

    def _on_duration(self, dur_ms: int):
        self.video_dur_ms = dur_ms
        self.slider.setRange(0, dur_ms)
        if self.line_ax is not None:
            self.line_ax.set_xlim(0, dur_ms / 1000.0)
            self.line_canvas.draw_idle()

    def _on_position(self, pos_ms: int):
        if self._user_dragging:
            return
        self.slider.blockSignals(True)
        self.slider.setValue(pos_ms)
        self.slider.blockSignals(False)
        self.pos_label.setText(
            f"{self._fmt(pos_ms)} / {self._fmt(self.video_dur_ms)}"
        )
        self._move_time_line(pos_ms / 1000.0)

    def _on_slider_pressed(self):
        self._user_dragging = True

    def _on_slider_moved(self, pos_ms: int):
        self.pos_label.setText(
            f"{self._fmt(pos_ms)} / {self._fmt(self.video_dur_ms)}"
        )

    def _on_slider_released(self):
        self._user_dragging = False
        self.media_player.setPosition(self.slider.value())

    @staticmethod
    def _fmt(ms: int) -> str:
        s = int(ms / 1000)
        return f"{s // 60:02d}:{s % 60:02d}"

    def _seek(self, pos_ms: int):
        self.media_player.setPosition(pos_ms)

    # ── Grafik cizgisi ───────────────────────────────────────────────────────
    def _move_time_line(self, sec: float):
        if self.line_ax is None:
            return
        if self._time_line is not None:
            try:
                self._time_line.remove()
            except Exception:
                pass
        self._time_line = self.line_ax.axvline(
            x=sec, color='#E53935', linewidth=2.5, linestyle='--', zorder=10
        )
        self.line_canvas.draw_idle()

    def _on_graph_click(self, event):
        if event.inaxes != self.line_ax or event.xdata is None:
            return
        self.media_player.setPosition(int(event.xdata * 1000))

    # ── Veri yükleme ─────────────────────────────────────────────────────────
    def _load_data(self):
        try:
            self.emotions = self.emotion_repo.find_by_session(self.session.id)
            if not self.emotions:
                QMessageBox.warning(
                    self, "Veri Yok",
                    "Bu gorusme icin duygu analizi verisi bulunamadi.\n"
                    "Sadece kayit sirasinda kamera aktifken veri toplanir."
                )
                return
            # Hemen ciz, video yuklenince x ekseni guncellenir
            self._draw_all()
        except Exception as e:
            logger.error(f"Emotion data hatasi: {e}")
            QMessageBox.critical(self, "Hata", f"Veriler yuklenemedi:\n{e}")

    def _draw_all(self):
        self._draw_line()
        self._draw_pie()

    # ── Yatay zaman grafigi ──────────────────────────────────────────────────
    def _draw_line(self):
        self.line_fig.clear()
        ax = self.line_fig.add_subplot(111)
        self.line_ax = ax

        types = ['angry', 'disgust', 'fear', 'happy', 'sad', 'surprise', 'neutral']

        # 0.5s hassasiyetle grupla (duplicate x sorununu çözer)
        from collections import defaultdict
        raw = defaultdict(lambda: defaultdict(list))
        for rec in self.emotions:
            if not rec.additional_data:
                continue
            try:
                scores = json.loads(rec.additional_data)
                # En yakın 0.25 saniyeye yuvarla (saniyede 4 nokta)
                t = round(float(rec.frame_number) * 4) / 4
                for etype in types:
                    raw[t][etype].append(scores.get(etype, 0.0))
            except Exception:
                continue

        # Gruplandırılmış veriyi diziye çevir
        sorted_times = sorted(raw.keys())
        grouped = {etype: {'times': [], 'vals': []} for etype in types}
        for t in sorted_times:
            for etype in types:
                if raw[t][etype]:
                    grouped[etype]['times'].append(t)
                    grouped[etype]['vals'].append(float(np.mean(raw[t][etype])))

        # Her duygu çizgisi 0. saniyeden başlasın
        for etype in types:
            d = grouped[etype]
            if d['times'] and d['times'][0] > 0:
                d['times'].insert(0, 0.0)
                d['vals'].insert(0, d['vals'][0])

        plotted = False
        for etype, d in grouped.items():
            if not d['times']:
                continue
            times = np.array(d['times'], dtype=float)
            vals  = np.array(d['vals'],  dtype=float)
            lbl   = _label(etype)
            col   = _color(etype)
            plotted = True
            if len(times) >= 4:
                try:
                    ts  = np.linspace(0, times[-1], 300)
                    spl = make_interp_spline(times, vals, k=3)
                    ax.plot(ts, np.clip(spl(ts), 0, 1),
                            label=lbl, color=col, linewidth=2.0)
                    continue
                except Exception:
                    pass
            ax.plot(times, vals, 'o-', markersize=4,
                    label=lbl, color=col, linewidth=1.5)

        if not plotted:
            ax.text(0.5, 0.5, 'Grafik verisi yok', transform=ax.transAxes,
                    ha='center', va='center', fontsize=11, color='gray')

        max_t = (self.video_dur_ms / 1000.0 if self.video_dur_ms > 0
                 else (sorted_times[-1] if sorted_times else 60))
        ax.set_xlim(0, max_t)
        ax.set_ylim(0, 1)
        ax.set_xlabel('Zaman (saniye)', fontsize=9)
        ax.set_ylabel('Olasilik', fontsize=9)
        ax.set_title('Duygu Degisimi — Grafige tiklayarak videoya atla',
                     fontsize=9, pad=6)
        if plotted:
            ax.legend(fontsize=7, loc='upper right', ncol=2, framealpha=0.7)
        ax.grid(True, alpha=0.25)
        ax.tick_params(labelsize=8)

        self.line_canvas.draw()
        self.line_canvas.flush_events()

    # ── Pasta grafigi ─────────────────────────────────────────────────────────
    def _draw_pie(self):
        self.pie_fig.clear()
        ax = self.pie_fig.add_subplot(111)

        counts = {}
        for rec in self.emotions:
            counts[rec.emotion_type] = counts.get(rec.emotion_type, 0) + 1

        if not counts:
            return

        labels = [_label(e) for e in counts]
        sizes  = list(counts.values())
        colors = [_color(e) for e in counts]

        _, _, autotexts = ax.pie(
            sizes, labels=labels, autopct='%1.0f%%',
            startangle=90, colors=colors,
            textprops={'fontsize': 8}
        )
        for at in autotexts:
            at.set_fontsize(8)
        ax.set_title('Genel Duygu Dagilimi', fontsize=9, pad=6)

        self.pie_canvas.draw()

    # ── Video kontrolleri ─────────────────────────────────────────────────────
    def _toggle_play(self):
        if self.media_player.state() == QMediaPlayer.PlayingState:
            self.media_player.pause()
            self.play_btn.setText("Oynat")
        else:
            self.media_player.play()
            self.play_btn.setText("Duraklat")

    def _stop_video(self):
        self.media_player.stop()
        self.play_btn.setText("Oynat")

    def closeEvent(self, event):
        self.media_player.stop()
        event.accept()
