"""
Video Call Page - Yüz Analizi ile Görüşme
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
import cv2
from datetime import datetime
import os

from utils.logger import setup_logger
from database.repositories.emotion_repository import EmotionAnalysisRepository
from database.models import EmotionAnalysis
import json

logger = setup_logger(__name__)


class VideoCallPage(QWidget):
    """Video görüşme sayfası - Yüz analizi ile"""
    
    call_ended = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        
        self.camera = None
        self.face_cascade = None
        self.video_writer = None
        self.is_recording = False
        self.patient_name = ""
        self.doctor_id = None
        self.current_patient_id = None
        self.call_start_time = None
        self.call_duration = 0
        self.emotion_history = []
        self.emotion_repo = EmotionAnalysisRepository()
        self.emotion_detector = None  # start_call'da lazy yukle
        self.emotion_buffer = []   # session bitmeden önce toplanır
        self.current_session_id = None
        self.frame_count = 0
        
        self._setup_ui()
        self._load_face_detector()
    
    def _setup_ui(self):
        """UI oluştur"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header = QFrame()
        header.setFixedHeight(80)
        header.setStyleSheet("background-color: #2196F3;")
        
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(25, 0, 25, 0)
        h_layout.setSpacing(15)
        
        self.patient_label = QLabel("Görüşme")
        self.patient_label.setStyleSheet("color: white; font-size: 20pt; font-weight: bold;")
        h_layout.addWidget(self.patient_label)
        
        # Süre sayacı
        self.timer_label = QLabel("00:00:00")
        self.timer_label.setStyleSheet("color: white; font-size: 18pt; font-weight: bold; background: rgba(0,0,0,0.3); padding: 10px 20px; border-radius: 8px;")
        h_layout.addWidget(self.timer_label)
        
        h_layout.addStretch()
        
        # Kayıt butonu
        self.record_btn = QPushButton("Kayit Devam Ediyor")
        self.record_btn.setFixedHeight(55)
        self.record_btn.setMinimumWidth(150)
        self.record_btn.setEnabled(False)
        self.record_btn.setStyleSheet("""
            QPushButton {
                background: #F44336;
                border: 2px solid white;
                border-radius: 12px;
                font-size: 14pt;
                font-weight: bold;
                color: white;
                padding: 10px 20px;
            }
        """)
        h_layout.addWidget(self.record_btn)
        
        # Kapat butonu
        end_btn = QPushButton("☎")
        end_btn.setFixedSize(70, 70)
        end_btn.setStyleSheet("""
            QPushButton {
                background: #F44336;
                border: 3px solid white;
                border-radius: 35px;
                font-size: 32pt;
                color: white;
            }
            QPushButton:hover {
                background: #D32F2F;
                border: 4px solid white;
            }
        """)
        end_btn.clicked.connect(self._end_call)
        h_layout.addWidget(end_btn)
        
        layout.addWidget(header)
        
        # Video alanı
        video_container = QFrame()
        video_layout = QVBoxLayout(video_container)
        video_layout.setContentsMargins(0, 0, 0, 0)
        
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("background-color: #000000;")
        self.video_label.setMinimumHeight(400)
        video_layout.addWidget(self.video_label)
        
        layout.addWidget(video_container, 1)
        
        # Analiz paneli - DÜZGÜN
        analysis_panel = QFrame()
        analysis_panel.setFixedHeight(90)
        analysis_panel.setStyleSheet("background-color: #1A1A1A;")
        
        a_layout = QVBoxLayout(analysis_panel)
        a_layout.setContentsMargins(20, 10, 20, 10)
        a_layout.setSpacing(10)
        
        # Yüz durumu
        self.face_status = QLabel("Yuz araniyor...")
        self.face_status.setWordWrap(False)
        self.face_status.setStyleSheet("color: #FFFFFF; font-size: 12pt;")
        a_layout.addWidget(self.face_status)
        
        # Duygu durumu
        self.emotion_label = QLabel("Analiz bekleniyor...")
        self.emotion_label.setWordWrap(False)
        self.emotion_label.setStyleSheet("color: #FFC107; font-size: 12pt;")
        a_layout.addWidget(self.emotion_label)
        
        layout.addWidget(analysis_panel)
        
        # Timer - 30 FPS
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_frame)
    
    def _load_face_detector(self):
        pass  # MediaPipe is now inside EmotionDetector
    
    def start_call(self, patient_name: str, doctor_id: int, patient_id: int = None):
        """Görüşmeyi başlat"""
        self.patient_name = patient_name
        self.doctor_id = doctor_id
        self.current_patient_id = patient_id
        self.patient_label.setText(f"{patient_name}")
        
        # EmotionDetector'ı burada lazy yükle (import chat page'i yavaşlatmasın)
        if self.emotion_detector is None:
            from ml.emotion_detector import EmotionDetector
            self.emotion_detector = EmotionDetector()

        logger.info(f"🎥 Görüşme başlıyor - Patient: {patient_name} (ID:{patient_id}), Doctor ID: {doctor_id}")
        
        # Kamerayı aç
        self.camera = cv2.VideoCapture(0)
        
        if not self.camera.isOpened():
            self.face_status.setText("Kamera acilamadi!")
            logger.error("Kamera açılamadı!")
            return
        
        # Timer başlat
        self.timer.start(33)  # ~30 FPS
        
        # Süre sayacı başlat
        self.call_start_time = datetime.now()
        self.call_duration = 0
        self.emotion_history = []
        
        # OTOMATİK KAYIT BAŞLAT
        self._start_recording()
        
        logger.info(f"✅ Görüşme başladı: {patient_name}")
    
    def _update_frame(self):
        """Frame güncelle - Yüz algıla ve analiz et"""
        if not self.camera or not self.camera.isOpened():
            return
        
        self.frame_count += 1
        
        # Süre güncelle
        if self.call_start_time:
            self.call_duration = int((datetime.now() - self.call_start_time).total_seconds())
            hours = self.call_duration // 3600
            minutes = (self.call_duration % 3600) // 60
            seconds = self.call_duration % 60
            self.timer_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
        
        ret, frame = self.camera.read()
        
        if not ret:
            return
        
        if self.emotion_detector and self.emotion_detector.is_model_loaded():
            result = self.emotion_detector.detect_emotion(frame)
            if result['face_found']:
                x, y, w, h = result['face_box']
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

                emotion_en = result['emotion']
                confidence = result['confidence']
                all_preds  = result['all_predictions']
                emotion_tr = self.emotion_detector.get_emotion_turkish(emotion_en)

                cv2.putText(frame, f"{emotion_en} ({confidence*100:.0f}%)", (x, max(y-10, 20)),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                self.face_status.setText("Yuz algilandi")
                self.emotion_label.setText(f"Duygu: {emotion_tr}")

                if not self.emotion_history or self.emotion_history[-1] != emotion_tr:
                    self.emotion_history.append(emotion_tr)

                if self.frame_count % 30 == 0:
                    self.emotion_buffer.append({
                        'dominant': emotion_en,
                        'confidence': confidence,
                        'all_json': json.dumps(all_preds),
                        'frame_time': self.call_duration,
                    })
            else:
                self.face_status.setText("Yuz araniyor...")
                self.emotion_label.setText("Analiz bekleniyor...")
        
        # Kayıt (orijinal, aynasız)
        if self.is_recording and self.video_writer:
            self.video_writer.write(frame)

        # Frame'i göster
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        
        self.video_label.setPixmap(QPixmap.fromImage(qt_image).scaled(
            self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        ))
    
    def _bulk_save_emotions(self, session_id: int):
        """Görüşme sonunda tüm bufferdaki emotion kayitlarini DB'ye yaz"""
        if not self.emotion_buffer:
            logger.warning("Emotion buffer bos, kaydedilecek veri yok")
            return
        saved = 0
        for em in self.emotion_buffer:
            try:
                record = EmotionAnalysis(
                    session_id=session_id,
                    emotion_type=em['dominant'],
                    confidence=em['confidence'],
                    timestamp=datetime.now(),
                    frame_number=em['frame_time'],
                    additional_data=em['all_json'],
                )
                self.emotion_repo.create(record)
                saved += 1
            except Exception as e:
                logger.error(f"Emotion buffer kayit hatasi: {e}")
        logger.info(f"{saved}/{len(self.emotion_buffer)} emotion kaydi yazildi (session={session_id})")
        self.emotion_buffer = []
    
    def _start_recording(self):
        """Video kaydını başlat"""
        try:
            # Kayıt dizini
            save_dir = "recordings"
            os.makedirs(save_dir, exist_ok=True)
            
            # Dosya adı
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            patient_safe = self.patient_name.replace(" ", "_")
            filename = f"{save_dir}/call_{patient_safe}_{timestamp}.avi"
            
            # Video writer
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            fps = 30.0
            frame_size = (640, 480)
            
            self.video_writer = cv2.VideoWriter(filename, fourcc, fps, frame_size)
            self.is_recording = True
            
            logger.info(f"📹 Kayıt başladı: {filename}")
            
        except Exception as e:
            logger.error(f"❌ Kayıt başlatılamadı: {e}")
            QMessageBox.warning(self, "Hata", f"Kayıt başlatılamadı:\n{str(e)}")
    
    def _end_call(self):
        """Görüşmeyi sonlandır"""
        # Timer durdur
        self.timer.stop()
        
        # Kayıt dosyası yolu
        self.final_recording_path = None
        
        # Kayıt durdur
        if self.video_writer:
            self.video_writer.release()
            
            # Son kaydedilen dosyayı bul
            save_dir = "recordings"
            timestamp = self.call_start_time.strftime("%Y%m%d")
            patient_safe = self.patient_name.replace(" ", "_")
            
            import glob
            pattern = f"{save_dir}/call_{patient_safe}_{timestamp}*.avi"
            files = glob.glob(pattern)
            if files:
                self.final_recording_path = max(files, key=os.path.getctime)
            
            self.is_recording = False
        
        # Kamera kapat
        if self.camera:
            self.camera.release()
        
        logger.info(f"⏹️ Görüşme sonlandı - Süre: {self.call_duration}s")
        
        # Veritabanına kaydet
        if self.final_recording_path and self.doctor_id and self.current_patient_id:
            logger.info(f"💾 Veritabanına kaydediliyor...")
            logger.info(f"   Path: {self.final_recording_path}")
            logger.info(f"   Doctor: {self.doctor_id}")
            logger.info(f"   Patient: {self.current_patient_id}")
            self._save_to_database(self.final_recording_path)
        else:
            logger.error(f"❌ KAYIT EKSİK!")
            logger.error(f"   Path: {self.final_recording_path}")
            logger.error(f"   Doctor: {self.doctor_id}")
            logger.error(f"   Patient: {self.current_patient_id}")
            QMessageBox.warning(self, "Hata", "Görüşme kaydedilemedi - eksik bilgi!")
        
        # Chat sayfasına dön
        self.call_ended.emit()
    
    def _save_to_database(self, recording_path: str):
        """Görüşme kaydını therapy_sessions tablosuna kaydet"""
        try:
            from database.repositories.session_repository import TherapySessionRepository
            from database.models import TherapySession
            
            logger.info("📝 Therapy session oluşturuluyor...")
            
            # Duygu analizi özeti
            emotion_summary = self._create_emotion_summary()
            
            # Session oluştur
            session = TherapySession(
                patient_id=self.current_patient_id,
                doctor_id=self.doctor_id,
                session_date=self.call_start_time,
                duration_minutes=max(1, self.call_duration // 60),
                status="completed",
                session_notes=emotion_summary,
                therapist_notes="",
                video_path=recording_path
            )
            
            logger.info(f"   Patient ID: {session.patient_id}")
            logger.info(f"   Doctor ID: {session.doctor_id}")
            logger.info(f"   Duration: {session.duration_minutes} min")
            logger.info(f"   Video: {recording_path}")
            
            repo = TherapySessionRepository()
            session_id = repo.create(session)
            self.current_session_id = session_id

            # Buffer'daki emotion kayitlarini toplu kaydet
            self._bulk_save_emotions(session_id)

            logger.info(f"✅ Therapy session kaydedildi: session_id={session_id}")
            
            # Başarı mesajı göster
            QMessageBox.information(self, "Basarili", 
                f"Gorusme kaydedildi!\n\nSure: {self.call_duration // 60} dakika\n{emotion_summary.split(chr(10))[0]}")
            
        except Exception as e:
            logger.error(f"❌ Görüşme kaydedilemedi: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.warning(self, "Hata", f"Gorusme kaydedilemedi:\n{str(e)}")
    
    def _create_emotion_summary(self) -> str:
        """Duygu analizi özeti oluştur"""
        if not self.emotion_history:
            return "Duygu analizi yapilamadi."
        
        # Duygu frekansları
        from collections import Counter
        emotion_counts = Counter(self.emotion_history)
        
        summary = "Duygu Analizi:\n"
        for emotion, count in emotion_counts.most_common():
            percentage = (count / len(self.emotion_history)) * 100
            summary += f"- {emotion}: %{percentage:.1f}\n"
        
        # Baskın duygu
        dominant = emotion_counts.most_common(1)[0][0]
        summary += f"\nBaskin Duygu: {dominant}"
        
        return summary