"""
Analytics Page
Gelişmiş analitik ve görselleştirme
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QPushButton, QScrollArea, QFrame,
    QGroupBox, QGridLayout
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from services.analytics_service import AnalyticsService
from database.repositories.patient_repository import PatientRepository
from utils.logger import setup_logger

logger = setup_logger(__name__)


class AnalyticsPage(QWidget):
    """Analytics sayfası"""

    page_changed = pyqtSignal(int, object)
    logout_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        
        self.analytics_service = AnalyticsService()
        self.patient_repo = PatientRepository()
        
        self.current_doctor_id = None
        self.current_patient_id = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """UI oluştur"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Başlık
        title = QLabel("📊 Analitik ve İstatistikler")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Hasta seçimi
        selection_layout = QHBoxLayout()
        
        patient_label = QLabel("Danışan:")
        patient_label.setStyleSheet("font-size: 12pt; font-weight: bold;")
        selection_layout.addWidget(patient_label)
        
        self.patient_combo = QComboBox()
        self.patient_combo.setMinimumWidth(300)
        self.patient_combo.setStyleSheet("font-size: 11pt; padding: 5px;")
        self.patient_combo.currentIndexChanged.connect(self._on_patient_changed)
        selection_layout.addWidget(self.patient_combo)
        
        selection_layout.addStretch()
        
        # Yenile butonu
        refresh_btn = QPushButton("🔄 Yenile")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 20px;
                font-size: 11pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        refresh_btn.clicked.connect(self._refresh_analytics)
        selection_layout.addWidget(refresh_btn)
        
        layout.addLayout(selection_layout)
        
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        scroll_content = QWidget()
        self.content_layout = QVBoxLayout(scroll_content)
        self.content_layout.setSpacing(15)
        
        # Genel istatistikler
        self.stats_group = self._create_stats_group()
        self.content_layout.addWidget(self.stats_group)
        
        # Grafikler container
        self.charts_container = QWidget()
        self.charts_layout = QVBoxLayout(self.charts_container)
        self.content_layout.addWidget(self.charts_container)
        
        self.content_layout.addStretch()
        
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
    
    def _create_stats_group(self) -> QGroupBox:
        """İstatistik kartları"""
        group = QGroupBox("📈 Genel İstatistikler")
        group_font = QFont()
        group_font.setPointSize(12)
        group_font.setBold(True)
        group.setFont(group_font)
        
        layout = QGridLayout(group)
        
        # Stat kartları
        self.total_sessions_label = self._create_stat_card("Toplam Görüşme", "0", "#2196F3")
        self.avg_duration_label = self._create_stat_card("Ortalama Süre", "0 dk", "#4CAF50")
        self.monthly_freq_label = self._create_stat_card("Aylık Sıklık", "0", "#FF9800")
        self.last_session_label = self._create_stat_card("Son Görüşme", "-", "#9C27B0")
        
        layout.addWidget(self.total_sessions_label, 0, 0)
        layout.addWidget(self.avg_duration_label, 0, 1)
        layout.addWidget(self.monthly_freq_label, 0, 2)
        layout.addWidget(self.last_session_label, 0, 3)
        
        return group
    
    def _create_stat_card(self, title: str, value: str, color: str) -> QFrame:
        """İstatistik kartı"""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 10px;
                padding: 15px;
            }}
        """)
        
        layout = QVBoxLayout(frame)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: white; font-size: 10pt; font-weight: bold;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setStyleSheet("color: white; font-size: 24pt; font-weight: bold;")
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setObjectName("value")
        layout.addWidget(value_label)
        
        return frame
    
    def _update_stat_card(self, card: QFrame, value: str):
        """Kart değerini güncelle"""
        value_label = card.findChild(QLabel, "value")
        if value_label:
            value_label.setText(value)
    
    def set_doctor(self, doctor_id: int):
        """Doktor ID ayarla"""
        self.current_doctor_id = doctor_id
        self._load_patients()
    
    def _load_patients(self):
        """Hastaları yükle"""
        if not self.current_doctor_id:
            return
        
        try:
            patients = self.patient_repo.find_all_by_doctor(self.current_doctor_id)
            
            self.patient_combo.clear()
            self.patient_combo.addItem("-- Tüm Hastalar --", None)
            
            for patient in patients:
                if patient.user:
                    self.patient_combo.addItem(patient.user.full_name, patient.id)
            
            logger.info(f"{len(patients)} hasta yüklendi")
            
        except Exception as e:
            logger.error(f"Hastalar yüklenemedi: {e}")
    
    def _on_patient_changed(self):
        """Hasta değiştiğinde"""
        self.current_patient_id = self.patient_combo.currentData()
        self._refresh_analytics()
    
    def _refresh_analytics(self):
        """Analitikleri yenile"""
        if self.current_patient_id:
            self._load_patient_analytics()
        else:
            self._load_doctor_analytics()
    
    def _load_patient_analytics(self):
        """Hasta analitikleri"""
        if not self.current_patient_id:
            return
        
        try:
            # İlerleme verileri
            progress = self.analytics_service.get_patient_progress(self.current_patient_id)
            
            # Grafikleri temizle
            self._clear_charts()
            
            if not progress.get('has_data'):
                logger.warning("Hasta için yeterli veri yok")
                # Kartları sıfırla
                self._update_stat_card(self.total_sessions_label, "0")
                self._update_stat_card(self.avg_duration_label, "0 dk")
                self._update_stat_card(self.monthly_freq_label, "0")
                self._update_stat_card(self.last_session_label, "-")
                
                # Bilgi mesajı ekle
                info_label = QLabel("Bu danışan için henüz görüşme verisi bulunmamaktadır.")
                info_label.setStyleSheet("""
                    QLabel {
                        background-color: #FFF9C4;
                        border: 2px solid #FBC02D;
                        border-radius: 8px;
                        padding: 20px;
                        font-size: 12pt;
                        color: #F57F17;
                    }
                """)
                info_label.setAlignment(Qt.AlignCenter)
                self.charts_layout.addWidget(info_label)
                return
            
            # Kartları güncelle
            self._update_stat_card(self.total_sessions_label, str(progress['total_sessions']))
            self._update_stat_card(self.avg_duration_label, f"{progress['avg_duration_minutes']:.0f} dk")
            self._update_stat_card(self.monthly_freq_label, f"{progress['monthly_frequency']}")
            
            if progress['last_session_date']:
                last_date = progress['last_session_date'].strftime('%d.%m.%Y')
                self._update_stat_card(self.last_session_label, last_date)
            
          
            
            # Görüşme timeline grafiği
            self._create_session_timeline_chart(progress['sessions_timeline'])
            
            # Duygu analizi
            emotion_data = self.analytics_service.get_emotion_trends(self.current_patient_id)
            if emotion_data.get('overall_distribution'):
                self._create_emotion_chart(emotion_data['overall_distribution'])
            
        except Exception as e:
            logger.error(f"Patient analytics error: {e}")
    
    def _load_doctor_analytics(self):
        """Doktor analitikleri (tüm hastalar)"""
        if not self.current_doctor_id:
            return
        
        try:
            # Session trends
            trends = self.analytics_service.get_session_trends(self.current_doctor_id, days=90)
            
            # Kartları güncelle
            self._update_stat_card(self.total_sessions_label, str(trends.get('total_sessions', 0)))
            self._update_stat_card(self.avg_duration_label, "-")
            self._update_stat_card(self.monthly_freq_label, f"{trends.get('weekly_average', 0)} / hafta")
            self._update_stat_card(self.last_session_label, "Son 90 gün")
            
            # Grafikleri temizle
            self._clear_charts()
            
            # Günlük görüşme grafiği
            if trends.get('daily_counts'):
                self._create_daily_sessions_chart(trends['daily_counts'])
            
            # Durum dağılımı
            if trends.get('status_distribution'):
                self._create_status_chart(trends['status_distribution'])
            
            # Tamamlama oranları
            completion = self.analytics_service.get_completion_rates(self.current_doctor_id, days=30)
            if completion.get('completion_rates'):
                self._create_completion_chart(completion['completion_rates'])
            
        except Exception as e:
            logger.error(f"Doctor analytics error: {e}")
    
    def _clear_charts(self):
        """Grafikleri temizle"""
        while self.charts_layout.count():
            child = self.charts_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def _create_session_timeline_chart(self, timeline: list):
        """Görüşme timeline grafiği"""
        if not timeline:
            return
        
        fig = Figure(figsize=(10, 4))
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        
        dates = [s['date'] for s in timeline]
        durations = [s['duration'] or 0 for s in timeline]
        
        ax.plot(dates, durations, marker='o', linestyle='-', linewidth=2, markersize=6)
        ax.set_xlabel('Tarih', fontsize=10)
        ax.set_ylabel('Süre (dakika)', fontsize=10)
        ax.set_title('Görüşme Süresi Trendi', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)
        fig.autofmt_xdate()
        fig.tight_layout()
        
        self.charts_layout.addWidget(canvas)
    
    def _create_emotion_chart(self, distribution: dict):
        """Duygu dağılımı grafiği"""
        if not distribution:
            return
        
        fig = Figure(figsize=(8, 4))
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        
        emotions = list(distribution.keys())
        counts = list(distribution.values())
        
        colors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40', '#FF6384']
        
        ax.bar(emotions, counts, color=colors[:len(emotions)])
        ax.set_xlabel('Duygu', fontsize=10)
        ax.set_ylabel('Görüşme Sayısı', fontsize=10)
        ax.set_title('Dominant Duygu Dağılımı', fontsize=12, fontweight='bold')
        ax.grid(True, axis='y', alpha=0.3)
        fig.tight_layout()
        
        self.charts_layout.addWidget(canvas)
    
    def _create_daily_sessions_chart(self, daily_counts: dict):
        """Günlük görüşme grafiği"""
        if not daily_counts:
            return
        
        fig = Figure(figsize=(10, 4))
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        
        dates = list(daily_counts.keys())
        counts = list(daily_counts.values())
        
        ax.bar(dates, counts, color='#2196F3', alpha=0.7)
        ax.set_xlabel('Tarih', fontsize=10)
        ax.set_ylabel('Görüşme Sayısı', fontsize=10)
        ax.set_title('Günlük Görüşme Dağılımı (Son 90 Gün)', fontsize=12, fontweight='bold')
        ax.grid(True, axis='y', alpha=0.3)
        fig.autofmt_xdate()
        fig.tight_layout()
        
        self.charts_layout.addWidget(canvas)
    
    def _create_status_chart(self, status_distribution: dict):
        """Durum dağılımı grafiği"""
        if not status_distribution:
            return
        
        fig = Figure(figsize=(6, 4))
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        
        statuses = list(status_distribution.keys())
        counts = list(status_distribution.values())
        
        colors = ['#4CAF50', '#FF9800', '#F44336', '#9E9E9E']
        ax.pie(counts, labels=statuses, autopct='%1.1f%%', colors=colors, startangle=90)
        ax.set_title('Görüşme Durum Dağılımı', fontsize=12, fontweight='bold')
        fig.tight_layout()
        
        self.charts_layout.addWidget(canvas)
    
    def _create_completion_chart(self, rates: dict):
        """Tamamlama oranları grafiği"""
        if not rates:
            return
        
        fig = Figure(figsize=(8, 4))
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        
        statuses = list(rates.keys())
        percentages = list(rates.values())
        
        colors = ['#4CAF50', '#FF9800', '#F44336', '#9E9E9E']
        ax.barh(statuses, percentages, color=colors[:len(statuses)])
        ax.set_xlabel('Oran (%)', fontsize=10)
        ax.set_title('Randevu Tamamlama Oranları (Son 30 Gün)', fontsize=12, fontweight='bold')
        ax.grid(True, axis='x', alpha=0.3)
        fig.tight_layout()
        
        self.charts_layout.addWidget(canvas)
    
    def on_page_show(self):
        """Sayfa gösterildiğinde"""
        logger.debug("Analytics page shown")
        self._load_patients()
        if self.patient_combo.count() > 1:
            self._refresh_analytics()