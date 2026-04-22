"""
Chat Page - Modern WhatsApp Benzeri Tasarım
Tamamen yeniden tasarlandı - Orantılı ve profesyonel
"""
import os
import wave
import struct
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QFrame, QListWidget, QListWidgetItem,
    QTextEdit, QMessageBox, QStackedWidget
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QBuffer, QIODevice
from PyQt5.QtMultimedia import QAudioInput, QAudioFormat, QAudioDeviceInfo

from services.chat_service import ChatService
from services.therapy_service import TherapyService
from database.models import Message
from utils.logger import setup_logger
from ui.pages.doctor.video_call_page import VideoCallPage
from config import VIDEO_DIR

logger = setup_logger(__name__)


class ChatPage(QWidget):
    """Modern 2-aşamalı chat sistemi"""
    
    page_changed = pyqtSignal(int, object)
    logout_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        
        self.chat_service = ChatService()
        self.therapy_service = TherapyService()
        self.current_doctor_id = None
        self.current_patient_id = None
        self.current_patient_user_id = None
        self.current_patient_name = None
        self.video_call_page = None

        # Ses kaydı durumu
        self._audio_input = None
        self._audio_buffer = None
        self._audio_recording = False
        self._audio_timer = QTimer()
        self._audio_timer.timeout.connect(self._update_audio_label)
        self._audio_elapsed = 0
        
        self._setup_ui()
        
        # Auto-refresh (3 saniyede bir)
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._auto_refresh)
        self.refresh_timer.start(3000)
    
    def _setup_ui(self):
        """Ana UI kurulumu"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 2 sayfalı yapı
        self.stacked = QStackedWidget()
        self.stacked.addWidget(self._build_contacts_page())
        self.stacked.addWidget(self._build_chat_page())
        
        main_layout.addWidget(self.stacked)
    
    # ==================== SAYFA 1: KİŞİLER LİSTESİ ====================
    
    def _build_contacts_page(self) -> QWidget:
        """Kişiler listesi sayfası"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = QFrame()
        header.setFixedHeight(65)
        header.setStyleSheet("background-color: #2196F3;")
        
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(20, 0, 20, 0)
        
        title = QLabel("💬 Mesajlar")
        title.setStyleSheet("color: white; font-size: 20pt; font-weight: bold;")
        h_layout.addWidget(title)
        
        layout.addWidget(header)
        
        # Kişi listesi
        self.contact_list = QListWidget()
        self.contact_list.setStyleSheet("""
            QListWidget {
                background-color: #FFFFFF;
                border: none;
                font-size: 12pt;
            }
            QListWidget::item {
                border-bottom: 1px solid #E8E8E8;
                padding: 0px;
                min-height: 80px;
            }
            QListWidget::item:hover {
                background-color: #F5F5F5;
            }
            QListWidget::item:selected {
                background-color: #DCFCE7;
                border-left: 4px solid #25D366;
            }
        """)
        self.contact_list.itemClicked.connect(self._on_contact_click)
        
        layout.addWidget(self.contact_list)
        
        return page
    
    def _create_contact_widget(self, user, last_msg: Message = None) -> QWidget:
        """Tek bir kişi kartı - SADECE İSİM"""
        card = QWidget()
        card.setFixedHeight(75)
        
        layout = QHBoxLayout(card)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)
        
        # İsim - TAM ORTALANMIŞ
        name = QLabel(user.full_name)
        name.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        name.setStyleSheet("font-size: 15pt; font-weight: bold; color: #000000;")
        name.setWordWrap(False)
        layout.addWidget(name, 1)
        
        # Saat - SAĞ TARAFTA
        if last_msg:
            time = QLabel(self._format_time(last_msg.sent_at))
            time.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
            time.setStyleSheet("font-size: 11pt; color: #667781;")
            time.setFixedWidth(60)
            layout.addWidget(time, 0)
        
        return card
    
    # ==================== SAYFA 2: CHAT EKRANI ====================
    
    def _build_chat_page(self) -> QWidget:
        """Chat ekranı"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header (sabit 65px)
        layout.addWidget(self._build_chat_header())
        
        # Mesajlar (flexible)
        layout.addWidget(self._build_message_area(), 1)
        
        # Input (sabit 95px)
        layout.addWidget(self._build_input_area())
        
        return page
    
    def _build_chat_header(self) -> QFrame:
        """Chat üst bar"""
        header = QFrame()
        header.setFixedHeight(65)
        header.setStyleSheet("background-color: #2196F3;")
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(10, 0, 15, 0)
        layout.setSpacing(12)
        
        # Geri butonu - NET
        back = QPushButton("◀")
        back.setFixedSize(50, 50)
        back.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.2);
                color: white;
                border: 2px solid white;
                border-radius: 25px;
                font-size: 22pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.35);
                border: 3px solid white;
            }
        """)
        back.clicked.connect(self._go_back)
        layout.addWidget(back)
        
        # Hasta adı
        self.chat_title = QLabel("")
        self.chat_title.setStyleSheet("""
            color: white;
            font-size: 17pt;
            font-weight: bold;
            padding-left: 8px;
        """)
        layout.addWidget(self.chat_title, 1)
        
        # Video butonu - KAMERA
        video = QPushButton("📷")
        video.setFixedSize(45, 45)
        video.setStyleSheet("""
            QPushButton {
                background: white;
                border: none;
                border-radius: 22px;
                font-size: 22pt;
            }
            QPushButton:hover {
                background: #E3F2FD;
            }
        """)
        video.setToolTip("Görüntülü Görüşme")
        video.clicked.connect(self._start_video_call)
        layout.addWidget(video)
        
        # Audio butonu - MİKROFON
        self.audio_btn = QPushButton("🎤")
        self.audio_btn.setFixedSize(45, 45)
        self.audio_btn.setStyleSheet("""
            QPushButton {
                background: white;
                border: none;
                border-radius: 22px;
                font-size: 22pt;
            }
            QPushButton:hover { background: #E3F2FD; }
        """)
        self.audio_btn.setToolTip("Ses Kaydı Başlat")
        self.audio_btn.clicked.connect(self._toggle_audio_recording)
        layout.addWidget(self.audio_btn)
        
        return header
    
    def _build_message_area(self) -> QScrollArea:
        """Mesaj alanı"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { background: #E5DDD5; border: none; }")
        
        container = QWidget()
        container.setStyleSheet("background: #E5DDD5;")
        
        self.msg_layout = QVBoxLayout(container)
        self.msg_layout.addStretch(1)
        self.msg_layout.setSpacing(6)
        self.msg_layout.setContentsMargins(12, 12, 12, 12)
        
        scroll.setWidget(container)
        self.message_scroll = scroll
        
        return scroll
    
    def _build_input_area(self) -> QFrame:
        """Mesaj yazma alanı"""
        panel = QFrame()
        panel.setFixedHeight(80)
        panel.setStyleSheet("background: #F0F0F0; border-top: 1px solid #D1D1D1;")
        
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)
        
        # QLineEdit - TİTREMEZ!
        from PyQt5.QtWidgets import QLineEdit
        self.msg_input = QLineEdit()
        self.msg_input.setPlaceholderText("Mesaj yazın...")
        self.msg_input.setFixedHeight(50)
        self.msg_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #25D366;
                border-radius: 25px;
                padding: 0px 20px;
                font-size: 13pt;
                background: white;
                color: #000000;
            }
            QLineEdit:focus {
                border: 3px solid #25D366;
            }
        """)
        self.msg_input.returnPressed.connect(self._send_msg)
        layout.addWidget(self.msg_input, 1)
        
        # Gönder butonu
        send = QPushButton("➤")
        send.setFixedSize(50, 50)
        send.setStyleSheet("""
            QPushButton {
                background: #25D366;
                border: none;
                border-radius: 25px;
                color: white;
                font-size: 22pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #20BD5F;
            }
            QPushButton:pressed {
                background: #1DA851;
            }
        """)
        send.clicked.connect(self._send_msg)
        layout.addWidget(send)
        
        return panel
    
    # ==================== MESAJ BALONU ====================
    
    def _create_bubble(self, text: str, is_me: bool, time: datetime) -> QFrame:
        """Mesaj balonu oluştur"""
        container = QFrame()
        container.setStyleSheet("background: transparent;")
        
        h_layout = QHBoxLayout(container)
        h_layout.setContentsMargins(0, 3, 0, 3)
        
        if is_me:
            h_layout.addStretch(1)
        
        # Balon
        bubble = QFrame()
        bubble.setMaximumWidth(500)
        
        v_layout = QVBoxLayout(bubble)
        v_layout.setContentsMargins(14, 10, 14, 10)
        v_layout.setSpacing(4)
        
        if is_me:
            bubble.setStyleSheet("""
                QFrame {
                    background: #DCF8C6;
                    border-radius: 12px;
                    border-top-right-radius: 2px;
                }
            """)
        else:
            bubble.setStyleSheet("""
                QFrame {
                    background: #FFFFFF;
                    border-radius: 12px;
                    border-top-left-radius: 2px;
                }
            """)
        
        # Mesaj
        msg_label = QLabel(text)
        msg_label.setWordWrap(True)
        msg_label.setStyleSheet("font-size: 12pt; color: #000000; background: transparent;")
        v_layout.addWidget(msg_label)
        
        # Saat
        time_label = QLabel(time.strftime("%H:%M"))
        time_label.setStyleSheet("font-size: 10pt; color: #667781; background: transparent;")
        time_label.setAlignment(Qt.AlignRight)
        v_layout.addWidget(time_label)
        
        h_layout.addWidget(bubble)
        
        if not is_me:
            h_layout.addStretch(1)
        
        return container
    
    # ==================== İŞLEVLER ====================
    
    def set_doctor(self, doctor_id: int):
        """Doktor ata"""
        self.current_doctor_id = doctor_id
        self._load_contacts()
    
    def _load_contacts(self):
        """Kişileri yükle"""
        if not self.current_doctor_id:
            return
        
        try:
            self.contact_list.clear()
            patients = self.chat_service.get_doctor_patients_with_last_message(self.current_doctor_id)
            
            for p in patients:
                item = QListWidgetItem()
                widget = self._create_contact_widget(p['user'], p['last_message'])
                
                item.setSizeHint(widget.sizeHint())
                item.setData(Qt.UserRole, p['patient'].id)
                item.setData(Qt.UserRole + 1, p['user'].id)
                item.setData(Qt.UserRole + 2, p['user'].full_name)
                
                self.contact_list.addItem(item)
                self.contact_list.setItemWidget(item, widget)
            
            logger.info(f"{len(patients)} kişi yüklendi")
        except Exception as e:
            logger.error(f"Kişiler yüklenemedi: {e}")
    
    def _on_contact_click(self, item: QListWidgetItem):
        """Kişiye tıklandı"""
        self.current_patient_id = item.data(Qt.UserRole)
        self.current_patient_user_id = item.data(Qt.UserRole + 1)
        self.current_patient_name = item.data(Qt.UserRole + 2)
        
        self.chat_title.setText(self.current_patient_name)
        self.stacked.setCurrentIndex(1)
        self._load_messages()
    
    def _go_back(self):
        """Geri dön"""
        self.stacked.setCurrentIndex(0)
        self.current_patient_id = None
        self.current_patient_user_id = None
    
    def _load_messages(self):
        """Mesajları yükle"""
        if not self.current_doctor_id or not self.current_patient_user_id:
            return
        
        try:
            # Temizle
            while self.msg_layout.count() > 1:
                item = self.msg_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            # Yükle
            messages = self.chat_service.get_conversation(
                self.current_doctor_id,
                self.current_patient_user_id,
                limit=200
            )
            
            for msg in messages:
                is_me = (msg.sender_id == self.current_doctor_id)
                bubble = self._create_bubble(msg.message_text, is_me, msg.sent_at)
                self.msg_layout.insertWidget(self.msg_layout.count() - 1, bubble)
            
            QTimer.singleShot(50, self._scroll_down)
            
        except Exception as e:
            logger.error(f"Mesajlar yüklenemedi: {e}")
    
    def _send_msg(self):
        """Mesaj gönder"""
        if not self.current_doctor_id or not self.current_patient_user_id:
            return
        
        text = self.msg_input.text().strip()
        if not text:
            return
        
        try:
            msg_id = self.chat_service.send_message(
                self.current_doctor_id,
                self.current_patient_user_id,
                text
            )
            
            if msg_id:
                self.msg_input.clear()
                self._load_messages()
            else:
                QMessageBox.warning(self, "Hata", "Mesaj gönderilemedi!")
                
        except Exception as e:
            logger.error(f"Gönderme hatası: {e}")
            QMessageBox.critical(self, "Hata", str(e))
    
    def _auto_refresh(self):
        """Otomatik yenileme"""
        if self.current_patient_user_id and self.stacked.currentIndex() == 1:
            self._load_messages()
    
    def _scroll_down(self):
        """Aşağı kaydır"""
        bar = self.message_scroll.verticalScrollBar()
        bar.setValue(bar.maximum())
    
    def _format_time(self, dt: datetime) -> str:
        """Zaman formatla"""
        now = datetime.now()
        diff = (now - dt).days
        
        if diff == 0:
            return dt.strftime("%H:%M")
        elif diff == 1:
            return "Dün"
        elif diff < 7:
            days = ["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"]
            return days[dt.weekday()]
        else:
            return dt.strftime("%d/%m/%y")
    
    def on_page_show(self):
        """Sayfa açıldı"""
        self._load_contacts()
        self.stacked.setCurrentIndex(0)

    def _start_video_call(self):
        """Görüntülü görüşme başlat"""
        if not self.current_patient_name:
            QMessageBox.warning(self, "Hata", "Lütfen bir danışan seçin!")
            return
        
        # Video call page oluştur
        self.video_call_page = VideoCallPage()
        self.video_call_page.call_ended.connect(self._on_call_ended)
        self.video_call_page.start_call(
            self.current_patient_name, 
            self.current_doctor_id,
            self.current_patient_id
        )
        
        # Tam ekran
        self.video_call_page.showFullScreen()
    
    def _on_call_ended(self):
        """Görüşme bittiğinde chat'e dön"""
        if self.video_call_page:
            self.video_call_page.close()
            self.video_call_page = None
        logger.info("Chat sayfası yenileniyor...")
        self._load_contacts()

    # ── Ses Kaydı ─────────────────────────────────────────────────────────────

    def _toggle_audio_recording(self):
        if not self.current_patient_id:
            QMessageBox.warning(self, "Uyarı", "Lütfen önce bir danışan seçin!")
            return
        if self._audio_recording:
            self._stop_audio_recording()
        else:
            self._start_audio_recording()

    def _start_audio_recording(self):
        fmt = QAudioFormat()
        fmt.setSampleRate(44100)
        fmt.setChannelCount(1)
        fmt.setSampleSize(16)
        fmt.setCodec("audio/pcm")
        fmt.setByteOrder(QAudioFormat.LittleEndian)
        fmt.setSampleType(QAudioFormat.SignedInt)

        info = QAudioDeviceInfo.defaultInputDevice()
        if info.isNull():
            QMessageBox.critical(self, "Hata", "Mikrofon bulunamadı!")
            return
        if not info.isFormatSupported(fmt):
            fmt = info.nearestFormat(fmt)

        self._audio_buffer = QBuffer()
        self._audio_buffer.open(QIODevice.ReadWrite)

        self._audio_input = QAudioInput(fmt)
        self._audio_input.start(self._audio_buffer)

        self._audio_recording = True
        self._audio_elapsed = 0
        self._audio_timer.start(1000)

        self.audio_btn.setText("⏹")
        self.audio_btn.setStyleSheet("""
            QPushButton {
                background: #F44336;
                border: none;
                border-radius: 22px;
                font-size: 22pt;
                color: white;
            }
            QPushButton:hover { background: #D32F2F; }
        """)
        self.audio_btn.setToolTip("Kaydı Durdur")

    def _stop_audio_recording(self):
        if not self._audio_input:
            return

        self._audio_input.stop()
        self._audio_timer.stop()
        self._audio_recording = False

        # PCM verisini al
        self._audio_buffer.seek(0)
        pcm_data = bytes(self._audio_buffer.readAll())
        self._audio_buffer.close()

        self.audio_btn.setText("🎤")
        self.audio_btn.setStyleSheet("""
            QPushButton {
                background: white;
                border: none;
                border-radius: 22px;
                font-size: 22pt;
            }
            QPushButton:hover { background: #E3F2FD; }
        """)
        self.audio_btn.setToolTip("Ses Kaydı Başlat")

        if len(pcm_data) < 1000:
            QMessageBox.warning(self, "Uyarı", "Kayıt çok kısa, kaydedilmedi.")
            return

        # WAV dosyası kaydet
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        audio_filename = f"audio_p{self.current_patient_id}_{ts}.wav"
        audio_path = os.path.join(str(VIDEO_DIR), audio_filename)

        try:
            with wave.open(audio_path, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(44100)
                wf.writeframes(pcm_data)
        except Exception as e:
            logger.error(f"WAV kaydetme hatası: {e}")
            QMessageBox.critical(self, "Hata", f"Ses dosyası kaydedilemedi:\n{e}")
            return

        # Terapi seansı oluştur
        duration_min = max(1, self._audio_elapsed // 60)
        success, msg, session = self.therapy_service.create_session(
            patient_id=self.current_patient_id,
            doctor_id=self.current_doctor_id,
            session_notes="Sesli görüşme kaydı",
            video_path=audio_path
        )
        if success:
            self.therapy_service.complete_session(
                session_id=session.id,
                duration_minutes=duration_min,
                video_path=audio_path
            )
            QMessageBox.information(
                self, "Kayıt Tamamlandı",
                f"Ses kaydı başarıyla kaydedildi.\nSüre: {duration_min} dakika"
            )
        else:
            QMessageBox.warning(self, "Uyarı", f"Ses kaydedildi ancak seans oluşturulamadı:\n{msg}")

    def _update_audio_label(self):
        self._audio_elapsed += 1
        m, s = divmod(self._audio_elapsed, 60)
        self.audio_btn.setToolTip(f"Kaydediliyor — {m:02d}:{s:02d} — Durdurmak için tıkla")