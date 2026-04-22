"""
Camera Widget
OpenCV ile kamera goruntusu, video kayit ve duygu analizi
"""
import cv2
import os
import json
from typing import Optional
from datetime import datetime
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import QTimer, Qt, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap

from config import VIDEO_DIR, VIDEO_FPS, VIDEO_CODEC
from ml.emotion_detector import EmotionDetector
from utils.logger import setup_logger

logger = setup_logger(__name__)


class CameraWidget(QWidget):
    """Kamera widget - video gosterme, kayit ve duygu analizi"""
    
    # Signals
    recording_started = pyqtSignal()
    recording_stopped = pyqtSignal(str)  # Video dosya yolu
    error_occurred = pyqtSignal(str)  # Hata mesaji
    emotion_detected = pyqtSignal(str, float, str)  # (dominant_emotion, dominant_confidence, all_emotions_json)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.capture = None
        self.timer = QTimer()
        self.is_recording = False
        self.video_writer = None
        self.current_video_path = None
        
        self.emotion_detector = EmotionDetector()
        self.enable_emotion_analysis = False

        # Son tespit edilen duygu
        self.last_emotion = None
        
        self._setup_ui()
        self._connect_signals()
        
        # Model durumunu logla
        if self.emotion_detector.is_model_loaded():
            logger.info("Duygu analizi AKTIF - Model yuklendi")
        else:
            logger.warning("Duygu analizi KAPALI - Model bulunamadi")
    
    def _setup_ui(self):
        """UI olustur"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Video display label
        self.video_label = QLabel()
        self.video_label.setStyleSheet("""
            QLabel {
                background-color: #000000;
                border: 2px solid #2196F3;
                border-radius: 8px;
            }
        """)
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumSize(640, 480)
        self.video_label.setScaledContents(False)
        
        # Placeholder text
        self.video_label.setText("Kamera kapali\n\nBaslat butonuna tiklayin")
        self.video_label.setStyleSheet(self.video_label.styleSheet() + "color: white; font-size: 14pt;")
        
        layout.addWidget(self.video_label)
    
    def _connect_signals(self):
        """Signal baglantilari"""
        self.timer.timeout.connect(self._update_frame)
    
    def set_emotion_analysis(self, enabled: bool):
        """Duygu analizi acik/kapali"""
        self.enable_emotion_analysis = enabled
        logger.info(f"Duygu analizi: {'ACIK' if enabled else 'KAPALI'}")
    
    def start_camera(self) -> bool:
        """Kamerayi baslat"""
        try:
            logger.info("Kamera baslatiliyor...")
            
            self.capture = cv2.VideoCapture(0)
            
            if not self.capture.isOpened():
                logger.error("Kamera acilamadi!")
                self.error_occurred.emit("Kamera açılamadı!")
                return False
            
            # Kamera ayarlari
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            # Timer baslat (30 FPS)
            self.timer.start(33)  # ~30 FPS
            
            logger.info("Kamera baslatildi")
            return True
            
        except Exception as e:
            logger.error(f"Kamera baslatma hatasi: {e}")
            self.error_occurred.emit(f"Kamera hatası: {str(e)}")
            return False
    
    def stop_camera(self):
        """Kamerayi durdur"""
        try:
            logger.info("Kamera durduruluyor...")
            
            # Kayit varsa durdur
            if self.is_recording:
                self.stop_recording()
            
            # Timer durdur
            self.timer.stop()
            
            # Kamerayi kapat
            if self.capture:
                self.capture.release()
                self.capture = None
            
            # Placeholder goster
            self.video_label.setText("Kamera kapali")
            
            logger.info("Kamera durduruldu")
            
        except Exception as e:
            logger.error(f"Kamera durdurma hatasi: {e}")
    
    def start_recording(self, patient_id: int, doctor_id: int) -> bool:
        """Video kayit baslat"""
        try:
            if not self.capture or not self.capture.isOpened():
                logger.error("Kamera acik degil!")
                return False
            
            if self.is_recording:
                logger.warning("Kayit zaten devam ediyor!")
                return False
            
            # Video dosya adi olustur
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"session_p{patient_id}_d{doctor_id}_{timestamp}.avi"
            self.current_video_path = os.path.join(VIDEO_DIR, filename)
            
            # Video writer olustur
            fourcc = cv2.VideoWriter_fourcc(*VIDEO_CODEC)
            frame_width = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            frame_height = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            self.video_writer = cv2.VideoWriter(
                self.current_video_path,
                fourcc,
                VIDEO_FPS,
                (frame_width, frame_height)
            )
            
            if not self.video_writer.isOpened():
                logger.error("Video writer acilamadi!")
                return False
            
            self.is_recording = True
            
            # Duygu analizini ac (kayit basladiginda)
            self.set_emotion_analysis(True)
            
            self.recording_started.emit()
            
            logger.info(f"Video kayit basladi: {self.current_video_path}")
            return True
            
        except Exception as e:
            logger.error(f"Video kayit baslatma hatasi: {e}")
            return False
    
    def stop_recording(self) -> Optional[str]:
        """Video kayit durdur"""
        try:
            if not self.is_recording:
                logger.warning("Kayit devam etmiyor!")
                return None
            
            self.is_recording = False
            
            # Duygu analizini kapat
            self.set_emotion_analysis(False)
            
            if self.video_writer:
                self.video_writer.release()
                self.video_writer = None
            
            video_path = self.current_video_path
            self.current_video_path = None
            
            logger.info(f"Video kayit durduruldu: {video_path}")
            
            self.recording_stopped.emit(video_path)
            return video_path
            
        except Exception as e:
            logger.error(f"Video kayit durdurma hatasi: {e}")
            return None
    
    def _update_frame(self):
        """Frame guncelle (timer callback)"""
        if not self.capture or not self.capture.isOpened():
            return
        
        try:
            ret, frame = self.capture.read()
            
            if not ret:
                logger.warning("Frame okunamadi!")
                return
            
            if self.enable_emotion_analysis and self.emotion_detector.is_model_loaded():
                result = self.emotion_detector.detect_emotion(frame)
                if result['face_found']:
                    x, y, w, h = result['face_box']
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                    dominant_emotion = result['emotion']
                    dominant_confidence = result['confidence']
                    all_preds = result['all_predictions']

                    tr   = self.emotion_detector.get_emotion_turkish(dominant_emotion)
                    emoj = self.emotion_detector.get_emotion_emoji(dominant_emotion)
                    label = f"{emoj} {tr} ({dominant_confidence * 100:.0f}%)"
                    ty = max(y - 10, 20)
                    cv2.putText(frame, label, (x, ty),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

                    emotions_json = json.dumps(all_preds)
                    self.last_emotion = dominant_emotion
                    self.emotion_detected.emit(dominant_emotion, dominant_confidence, emotions_json)

            # Video kayit
            if self.is_recording and self.video_writer:
                self.video_writer.write(frame)

            # OpenCV BGR -> RGB donusumu
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # QImage'e donustur
            h, w, ch = frame_rgb.shape
            bytes_per_line = ch * w
            qt_image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
            
            # QPixmap'e donustur ve goster
            pixmap = QPixmap.fromImage(qt_image)
            
            # Label boyutuna gore olcekle
            scaled_pixmap = pixmap.scaled(
                self.video_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            self.video_label.setPixmap(scaled_pixmap)
            
        except Exception as e:
            logger.error(f"Frame guncelleme hatasi: {e}")
    
    def closeEvent(self, event):
        """Widget kapatilirken"""
        self.stop_camera()
        event.accept()