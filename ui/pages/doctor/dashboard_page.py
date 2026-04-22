"""
Doctor Dashboard Page
Danışman ana sayfası - Gelişmiş Tasarım
"""
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton,
    QCalendarWidget, QListWidget, QListWidgetItem, QGroupBox, QWidget
)
from PyQt5.QtCore import Qt, QDate, pyqtSignal
from PyQt5.QtGui import QFont

from ui.pages.base_page import BasePage
from core.session_manager import session_manager
from database.repositories.appointment_repository import AppointmentRepository
from services.patient_service import PatientService
from services.therapy_service import TherapyService
from utils.logger import setup_logger
from datetime import datetime, timedelta
from PyQt5.QtWidgets import QGroupBox
from core.constants import PageID
from PyQt5.QtGui import QTextCharFormat, QColor
from PyQt5.QtWidgets import QMessageBox


logger = setup_logger(__name__)


class DoctorDashboardPage(BasePage):
    """Danışman dashboard"""

    page_changed = pyqtSignal(int, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.appointment_repo = AppointmentRepository()
        self.patient_service = PatientService()
        self.therapy_service = TherapyService()
        
        self.appointment_dates = {}  # {date: [appointments]}
        
        self._setup_ui()
    
    def _setup_ui(self):
        """UI oluştur"""
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        self.layout.addLayout(layout)
        
        # Header
        header_layout = QHBoxLayout()
        
        # Title & Welcome
        title_layout = QVBoxLayout()
        
        title = QLabel("Danışman Ana Sayfası")
        title.setStyleSheet("color: #2C3E50; font-size: 24pt; font-weight: bold;")
        title_layout.addWidget(title)
        
        self.welcome_label = QLabel()
        self.welcome_label.setStyleSheet("font-size: 13pt; color: #5D6D7E;")
        title_layout.addWidget(self.welcome_label)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # İki sütunlu layout
        main_content = QHBoxLayout()
        main_content.setSpacing(20)
        
        # SOL SÜTUN - Takvim
        left_column = QVBoxLayout()
        
        calendar_group = self._create_calendar_group()
        left_column.addWidget(calendar_group)
        
        # İstatistik kartları
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(15)
        
        self.total_patients_card = self._create_stat_card("0", "Toplam Danışan", "#4CAF50")
        stats_layout.addWidget(self.total_patients_card)
        
        self.today_appointments_card = self._create_stat_card("0", "Bugünkü Randevular", "#2196F3")
        stats_layout.addWidget(self.today_appointments_card)
        
        self.week_sessions_card = self._create_stat_card("0", "Bu Hafta Görüşme", "#FF9800")
        stats_layout.addWidget(self.week_sessions_card)
        
        # Hızlı işlemler
        quick_actions = self._create_quick_actions()
        left_column.addWidget(quick_actions)
        
        left_column.addStretch()

        left_column.addLayout(stats_layout)
        
        main_content.addLayout(left_column, 3)
        
        # SAĞ SÜTUN - Yaklaşan Randevular & Bildirimler
        right_column = QVBoxLayout()
        
        upcoming_group = self._create_upcoming_appointments_group()
        right_column.addWidget(upcoming_group)
        
        # Uyarılar
        warnings_group = self._create_warnings_group()
        right_column.addWidget(warnings_group)

        notifications_group = self._create_notifications_group()
        right_column.addWidget(notifications_group)
        
        # Bildirimlere tıklama event'i bağla
        self.notifications_list.itemClicked.connect(self._on_notification_clicked)
        
        # Uyarılara tıklama event'i bağla
        self.warnings_list.itemClicked.connect(self._on_notification_clicked)
        
        # Sağ sütun boşluğunu doldur
        right_column.addStretch()
        
        main_content.addLayout(right_column, 2)
        
        layout.addLayout(main_content)
    
    def _create_calendar_group(self) -> QGroupBox:
        """Takvim widget'ı"""
        group = QGroupBox("Takvim")
        group_font = QFont()
        group_font.setPointSize(12)
        group_font.setBold(True)
        group.setFont(group_font)
        
        layout = QVBoxLayout(group)
        
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.setMinimumHeight(300)
        # Takvim tıklama event'i
        self.calendar.clicked.connect(self._on_date_clicked)
        
        # Takvim stili
        self.calendar.setStyleSheet("""
            QCalendarWidget QWidget {
                alternate-background-color: #E3F2FD;
            }
            QCalendarWidget QAbstractItemView:enabled {
                font-size: 11pt;
                selection-background-color: #2196F3;
                selection-color: white;
            }
        """)
        
        layout.addWidget(self.calendar)
        
        # Bugüne git butonu
        today_btn = QPushButton("📅 Bugüne Git")
        today_btn.setMaximumWidth(150)
        today_btn.clicked.connect(lambda: self.calendar.setSelectedDate(QDate.currentDate()))
        today_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        layout.addWidget(today_btn, 0, Qt.AlignRight)
        
        return group
    
    def _create_stat_card(self, value: str, label: str, color: str) -> QFrame:
        """İstatistik kartı"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 12px;
                padding: 20px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        
        value_label = QLabel(value)
        value_label.setStyleSheet("color: white; font-size: 28pt; font-weight: bold;")
        value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(value_label)
        
        text_label = QLabel(label)
        text_label.setStyleSheet("color: white; font-size: 10pt;")
        text_label.setAlignment(Qt.AlignCenter)
        text_label.setWordWrap(True)
        layout.addWidget(text_label)
        
        # Değeri güncellemek için referans tut
        card.value_label = value_label
        
        return card
    
    def _create_upcoming_appointments_group(self) -> QGroupBox:
        """Bugünün Ajandası + Yaklaşan Randevular"""
        group = QGroupBox("Bugünün Ajandası & Yaklaşan Randevular")
        group_font = QFont()
        group_font.setPointSize(12)
        group_font.setBold(True)
        group.setFont(group_font)
        
        layout = QVBoxLayout(group)
        
        # Bugünün ajandası başlığı
        today_header = QLabel("📋 Bugün")
        today_header.setStyleSheet("font-weight: bold; font-size: 11pt; color: #2196F3; margin-top: 5px;")
        layout.addWidget(today_header)
        
        self.today_agenda_list = QListWidget()
        self.today_agenda_list.setMaximumHeight(200)
        self.today_agenda_list.setStyleSheet("""
            QListWidget {
                border: none;
                background-color: #E8F5E9;
                border-radius: 8px;
            }
            QListWidget::item {
                padding: 12px;
                border-bottom: 1px solid #C8E6C9;
            }
            QListWidget::item:hover {
                background-color: #C8E6C9;
            }
        """)
        layout.addWidget(self.today_agenda_list)
        
        # Yaklaşan randevular başlığı
        upcoming_header = QLabel("📅 Yaklaşan")
        upcoming_header.setStyleSheet("font-weight: bold; font-size: 11pt; color: #FF9800; margin-top: 15px;")
        layout.addWidget(upcoming_header)
        
        self.appointments_list = QListWidget()
        self.appointments_list.setStyleSheet("""
            QListWidget {
                border: none;
                background-color: #FFF3E0;
                border-radius: 8px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #FFE0B2;
            }
            QListWidget::item:hover {
                background-color: #FFE0B2;
            }
        """)
        layout.addWidget(self.appointments_list)
        
        return group
    
    def _create_warnings_group(self) -> QGroupBox:
        """Önemli notlar ve uyarılar"""
        group = QGroupBox("⚠️ Önemli Uyarılar")
        group_font = QFont()
        group_font.setPointSize(12)
        group_font.setBold(True)
        group.setFont(group_font)
        
        layout = QVBoxLayout(group)
        
        self.warnings_list = QListWidget()
        self.warnings_list.setMaximumHeight(250)
        self.warnings_list.setStyleSheet("""
            QListWidget {
                border: none;
                background-color: #FFEBEE;
                border-radius: 8px;
            }
            QListWidget::item {
                padding: 12px;
                border-bottom: 1px solid #FFCDD2;
            }
            QListWidget::item:hover {
                background-color: #FFCDD2;
            }
        """)
        layout.addWidget(self.warnings_list)
        
        return group
    
    def _create_notifications_group(self) -> QGroupBox:
        """Bildirimler & Hatırlatıcılar"""
        group = QGroupBox("Bildirimler")
        group_font = QFont()
        group_font.setPointSize(12)
        group_font.setBold(True)
        group.setFont(group_font)
        
        layout = QVBoxLayout(group)
        
        self.notifications_list = QListWidget()
        self.notifications_list.setStyleSheet("""
            QListWidget {
                border: none;
                background-color: #FFF3E0;
                border-radius: 8px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #FFE0B2;
            }
        """)
        layout.addWidget(self.notifications_list)
        
        return group
    
    def on_page_show(self):
        """Sayfa gösterildiğinde"""
        user = session_manager.get_current_user()
        if user:
            self.welcome_label.setText(f"Hoş geldiniz, Dr. {user.last_name} 👋")

        self._load_dashboard_data()

        logger.debug("Doctor dashboard shown")
    
    def _load_dashboard_data(self):
        """Dashboard verilerini yükle"""
        try:
            doctor_id = session_manager.get_current_user_id()

            if not doctor_id:
                return

            patients = self.patient_service.get_patients_by_doctor(doctor_id)
            self.total_patients_card.value_label.setText(str(len(patients)))

            today_start = datetime.now().replace(hour=0, minute=0, second=0)
            today_end = datetime.now().replace(hour=23, minute=59, second=59)

            all_appointments = self.appointment_repo.find_by_doctor(doctor_id, limit=100)
            today_count = sum(1 for apt in all_appointments
                            if today_start <= apt.appointment_date <= today_end)
            self.today_appointments_card.value_label.setText(str(today_count))

            # Bu hafta görüşme sayısı
            week_start = datetime.now().replace(hour=0, minute=0, second=0) - timedelta(days=datetime.now().weekday())
            sessions = self.therapy_service.get_sessions_by_doctor(doctor_id, limit=100)
            week_sessions = sum(1 for s in sessions if s.session_date and s.session_date >= week_start)
            self.week_sessions_card.value_label.setText(str(week_sessions))

            self._populate_upcoming_appointments()
            self._populate_warnings()
            self._populate_notifications()
            self._highlight_appointment_dates()

        except Exception as e:
            logger.error(f"Dashboard veri yukleme hatasi: {e}")
    
    def _populate_upcoming_appointments(self):
        """Bugünün ajandası ve yaklaşan randevuları listele"""
        try:
            doctor_id = session_manager.get_current_user_id()
            upcoming = self.appointment_repo.find_upcoming(doctor_id)
            
            # Bugün ve ileri randevuları ayır
            today = datetime.now().date()
            today_appointments = [apt for apt in upcoming if apt.appointment_date.date() == today]
            future_appointments = [apt for apt in upcoming if apt.appointment_date.date() > today]
            
            # BUGÜNÜN AJANDASI
            self.today_agenda_list.clear()
            
            if not today_appointments:
                item = QListWidgetItem("🎉 Bugün randevu yok - serbest gün!")
                item.setForeground(Qt.gray)
                self.today_agenda_list.addItem(item)
            else:
                # Saate göre sırala
                today_appointments.sort(key=lambda x: x.appointment_date)
                current_time = datetime.now()
                
                for apt in today_appointments:
                    patient = self.patient_service.get_patient_by_id(apt.patient_id)
                    patient_name = patient.user.full_name if patient and patient.user else "N/A"
                    
                    time_str = apt.appointment_date.strftime("%H:%M")
                    
                    # Geçmiş, şimdi, gelecek kontrolü
                    if apt.appointment_date < current_time:
                        # Geçmiş randevu
                        item_text = f"✅ {time_str} - {patient_name} ({apt.duration_minutes} dk)"
                        item = QListWidgetItem(item_text)
                        item.setForeground(Qt.gray)
                    elif apt.appointment_date <= current_time.replace(microsecond=0) + timedelta(hours=1):
                        # Yakın/şimdiki randevu (1 saat içinde)
                        item_text = f"🔴 {time_str} - {patient_name} ({apt.duration_minutes} dk)\n   ⚠️ ŞİMDİ / YAKIN!"
                        item = QListWidgetItem(item_text)
                        item.setBackground(QColor("#FFCDD2"))
                        item.setForeground(QColor("#C62828"))
                    else:
                        # Gelecek randevu
                        item_text = f"🕐 {time_str} - {patient_name} ({apt.duration_minutes} dk)"
                        item = QListWidgetItem(item_text)
                    
                    self.today_agenda_list.addItem(item)
            
            # YAKLASAN RANDEVULAR (Bugün hariç)
            self.appointments_list.clear()
            
            if not future_appointments:
                item = QListWidgetItem("📭 Yaklaşan randevu yok")
                item.setForeground(Qt.gray)
                self.appointments_list.addItem(item)
            else:
                for apt in future_appointments[:5]:  # İlk 5 tanesi
                    patient = self.patient_service.get_patient_by_id(apt.patient_id)
                    patient_name = patient.user.full_name if patient and patient.user else "N/A"
                    
                    date_str = apt.appointment_date.strftime("%d.%m.%Y %H:%M")
                    
                    item_text = f"📅 {date_str}\n👤 {patient_name}"
                    item = QListWidgetItem(item_text)
                    
                    self.appointments_list.addItem(item)
                
        except Exception as e:
            logger.error(f"Yaklasan randevu yukleme hatasi: {e}")
    
    def _populate_notifications(self):
        """Bildirimleri gerçek verilerden doldur"""
        self.notifications_list.clear()
        
        try:
            doctor_id = session_manager.get_current_user_id()
            
            # Bugünkü randevu sayısı
            today = datetime.now().date()
            all_appointments = self.appointment_repo.find_by_doctor(doctor_id, limit=100)
            today_count = sum(1 for apt in all_appointments 
                            if apt.appointment_date.date() == today and apt.status in ['pending', 'confirmed'])
            
            if today_count > 0:
                item = QListWidgetItem(f"🔔 Bugün {today_count} randevunuz var")
                item.setData(Qt.UserRole, {'action': 'goto_appointments'})
                self.notifications_list.addItem(item)
            
            # Yakın randevular (1 saat içinde)
            current_time = datetime.now()
            near_appointments = [apt for apt in all_appointments 
                               if current_time <= apt.appointment_date <= current_time + timedelta(hours=1)
                               and apt.status in ['pending', 'confirmed']]
            
            for apt in near_appointments[:2]:  # İlk 2 tanesi
                patient = self.patient_service.get_patient_by_id(apt.patient_id)
                patient_name = patient.user.full_name if patient and patient.user else "N/A"
                time_str = apt.appointment_date.strftime("%H:%M")
                
                item = QListWidgetItem(f"⏰ {time_str}'de {patient_name} ile görüşme")
                item.setData(Qt.UserRole, {'action': 'goto_appointments'})
                item.setBackground(QColor("#FFEBEE"))
                self.notifications_list.addItem(item)
            
            # Pending randevular (onay bekleyenler)
            pending_count = sum(1 for apt in all_appointments if apt.status == 'pending')
            if pending_count > 0:
                item = QListWidgetItem(f"📝 {pending_count} randevu onay bekliyor")
                item.setData(Qt.UserRole, {'action': 'goto_appointments'})
                self.notifications_list.addItem(item)
            
            # Yeni hastalar (son 7 gün)
            recent_patients = [p for p in self.patient_service.get_patients_by_doctor(doctor_id)
                             if p.created_at and (datetime.now() - p.created_at).days <= 7]
            
            if recent_patients:
                for patient in recent_patients[:2]:  # İlk 2 tanesi
                    item = QListWidgetItem(f"👤 Yeni hasta: {patient.user.full_name if patient.user else 'N/A'}")
                    item.setData(Qt.UserRole, {'action': 'goto_patients', 'patient_id': patient.id})
                    self.notifications_list.addItem(item)
            
            # Boş durum
            if self.notifications_list.count() == 0:
                item = QListWidgetItem("✅ Tüm bildirimler okundu")
                item.setForeground(Qt.gray)
                self.notifications_list.addItem(item)
            
        except Exception as e:
            logger.error(f"Bildirim yukleme hatasi: {e}")
            item = QListWidgetItem("⚠️ Bildirimler yüklenemedi")
            item.setForeground(Qt.red)
            self.notifications_list.addItem(item)

    def _create_quick_actions(self) -> QGroupBox:
        """Hızlı erişim butonları"""
        group = QGroupBox("Hızlı İşlemler")
        group_font = QFont()
        group_font.setPointSize(12)
        group_font.setBold(True)
        group.setFont(group_font)
        
        layout = QHBoxLayout(group)
        layout.setSpacing(10)
        
        # Yeni Randevu
        apt_btn = QPushButton("📅\nYeni Randevu")
        apt_btn.setMinimumHeight(80)
        apt_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        apt_btn.clicked.connect(lambda: self.navigate_to(PageID.APPOINTMENTS))
        layout.addWidget(apt_btn)
        
        # Yeni Görüşme
        session_btn = QPushButton("📝\nYeni Görüşme")
        session_btn.setMinimumHeight(80)
        session_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        session_btn.clicked.connect(lambda: self.navigate_to(PageID.NEW_SESSION))
        layout.addWidget(session_btn)
        
        # Danışanlar
        patients_btn = QPushButton("👥\nDanışanlar")
        patients_btn.setMinimumHeight(80)
        patients_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        patients_btn.clicked.connect(lambda: self.navigate_to(PageID.PATIENTS_LIST))
        layout.addWidget(patients_btn)
        
        return group        
    
    def _highlight_appointment_dates(self):
        """Randevu olan günleri takvimde renklendir"""
        try:
            doctor_id = session_manager.get_current_user_id()
            if not doctor_id:
                return
            
            # Önce tüm günlerin formatını sıfırla (hafta sonu kırmızısını kaldır)
            default_format = QTextCharFormat()
            default_format.setBackground(QColor("#FFFFFF"))  # Beyaz
            
            # Takvimin tüm günlerini beyaz yap
            current_date = QDate.currentDate()
            for month_offset in range(-2, 3):  # 2 ay öncesi - 2 ay sonrası
                year = current_date.addMonths(month_offset).year()
                month = current_date.addMonths(month_offset).month()
                days_in_month = QDate(year, month, 1).daysInMonth()
                
                for day in range(1, days_in_month + 1):
                    qdate = QDate(year, month, day)
                    self.calendar.setDateTextFormat(qdate, default_format)
            
            # Tüm randevuları al
            appointments = self.appointment_repo.find_by_doctor(doctor_id, limit=200)

            # Tarihlere göre grupla
            self.appointment_dates = {}
            for apt in appointments:
                date = apt.appointment_date.date()
                if date not in self.appointment_dates:
                    self.appointment_dates[date] = []
                self.appointment_dates[date].append(apt)
            
            # Renklendirme formatları (daha belirgin renkler + kalın yazı)
            pending_format = QTextCharFormat()
            pending_format.setBackground(QColor("#FFD54F"))  # Koyu Sarı
            pending_format.setForeground(QColor("#000000"))  # Siyah yazı
            pending_format.setFontWeight(QFont.Bold)
            
            confirmed_format = QTextCharFormat()
            confirmed_format.setBackground(QColor("#81C784"))  # Koyu Yeşil
            confirmed_format.setForeground(QColor("#FFFFFF"))  # Beyaz yazı
            confirmed_format.setFontWeight(QFont.Bold)
            
            completed_format = QTextCharFormat()
            completed_format.setBackground(QColor("#BDBDBD"))  # Koyu Gri
            completed_format.setForeground(QColor("#FFFFFF"))  # Beyaz yazı
            completed_format.setFontWeight(QFont.Bold)
            
            cancelled_format = QTextCharFormat()
            cancelled_format.setBackground(QColor("#E57373"))  # Koyu Kırmızı
            cancelled_format.setForeground(QColor("#FFFFFF"))  # Beyaz yazı
            cancelled_format.setFontWeight(QFont.Bold)
            
            # Tarihleri renklendir
            for date, apts in self.appointment_dates.items():
                qdate = QDate(date.year, date.month, date.day)
                
                # Statuslere göre öncelik belirle (en önemli status kazanır)
                statuses = [apt.status for apt in apts]
                
                if 'confirmed' in statuses:
                    self.calendar.setDateTextFormat(qdate, confirmed_format)
                elif 'pending' in statuses:
                    self.calendar.setDateTextFormat(qdate, pending_format)
                elif 'cancelled' in statuses:
                    self.calendar.setDateTextFormat(qdate, cancelled_format)
                elif 'completed' in statuses:
                    self.calendar.setDateTextFormat(qdate, completed_format)
            
            logger.info(f"{len(self.appointment_dates)} gun randevu renkleri ayarlandi")
            
        except Exception as e:
            logger.error(f"Takvim renklendirme hatasi: {e}")
    
    def _on_date_clicked(self, qdate: QDate):
        """Takvimde bir güne tıklandığında"""
        try:
            # QDate -> Python date
            clicked_date = qdate.toPyDate()
            
            # Bu günün randevuları var mı?
            if clicked_date in self.appointment_dates:
                appointments = self.appointment_dates[clicked_date]
                
                # Randevu detaylarını göster
                message = f"📅 {clicked_date.strftime('%d.%m.%Y')} - {len(appointments)} Randevu\n\n"
                
                for apt in appointments:
                    patient = self.patient_service.get_patient_by_id(apt.patient_id)
                    patient_name = patient.user.full_name if patient and patient.user else "N/A"
                    
                    time_str = apt.appointment_date.strftime("%H:%M")
                    status_map = {
                        'pending': '⏳ Beklemede',
                        'confirmed': '✅ Onaylandı',
                        'completed': '✔️ Tamamlandı',
                        'cancelled': '❌ İptal'
                    }
                    status = status_map.get(apt.status, apt.status)
                    
                    message += f"🕐 {time_str} - {patient_name}\n"
                    message += f"   {status} ({apt.duration_minutes} dk)\n\n"
                
                QMessageBox.information(self, "Günlük Randevular", message)
            else:
                # Randevu yok
                QMessageBox.information(
                    self, 
                    "Randevu Yok",
                    f"{clicked_date.strftime('%d.%m.%Y')} tarihinde randevu bulunmuyor.\n\n"
                    "Yeni randevu eklemek için 'Hızlı İşlemler' bölümündeki\n"
                    "'📅 Yeni Randevu' butonunu kullanabilirsiniz."
                )
        
        except Exception as e:
            logger.error(f"Tarih tiklama hatasi: {e}")

    def _on_notification_clicked(self, item):
        """Bildirime/uyarıya tıklandığında"""
        try:
            data = item.data(Qt.UserRole)
            
            if not data:
                return
            
            action = data.get('action')
            
            if action == 'goto_appointments':
                # Randevular sayfasına git
                self.navigate_to(PageID.APPOINTMENTS)
                logger.info("Bildirimden randevular sayfasına gidildi")
                
            elif action == 'goto_patients':
                # Danışanlar sayfasına git
                self.navigate_to(PageID.PATIENTS_LIST)
                logger.info("Bildirimden danışanlar sayfasına gidildi")
                
            elif action == 'goto_patient_detail':
                # Direkt hasta detayına git
                patient_id = data.get('patient_id')
                if patient_id:
                    self.page_changed.emit(PageID.PATIENT_DETAIL, patient_id)
                    logger.info(f"Uyarıdan hasta detayına gidildi: {patient_id}")
                
        except Exception as e:
            logger.error(f"Bildirim/uyari tiklama hatasi: {e}")

    def _create_activities_group(self) -> QGroupBox:
        """Son aktiviteler widget'ı"""
        group = QGroupBox("Son Aktiviteler")
        group_font = QFont()
        group_font.setPointSize(12)
        group_font.setBold(True)
        group.setFont(group_font)
        
        layout = QVBoxLayout(group)
        
        self.activities_list = QListWidget()
        self.activities_list.setMaximumHeight(250)
        self.activities_list.setStyleSheet("""
            QListWidget {
                border: none;
                background-color: #F9F9F9;
                border-radius: 8px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #E0E0E0;
            }
            QListWidget::item:hover {
                background-color: #E8F5E9;
            }
        """)
        layout.addWidget(self.activities_list)
        
        return group
    
    def _populate_activities(self):
        """Son aktiviteleri doldur"""
        self.activities_list.clear()
        
        try:
            doctor_id = session_manager.get_current_user_id()
            activities = []
            
            # Son randevular
            appointments = self.appointment_repo.find_by_doctor(doctor_id, limit=50)
            for apt in appointments[:10]:
                patient = self.patient_service.get_patient_by_id(apt.patient_id)
                patient_name = patient.user.full_name if patient and patient.user else "N/A"
                
                time_ago = self._time_ago(apt.created_at)
                
                status_icons = {
                    'pending': '⏳',
                    'confirmed': '✅',
                    'completed': '✔️',
                    'cancelled': '❌'
                }
                icon = status_icons.get(apt.status, '📅')
                
                activities.append({
                    'time': apt.created_at,
                    'text': f"{icon} Randevu: {patient_name} ({time_ago})",
                    'type': 'appointment'
                })
            
            # Son eklenen hastalar
            patients = self.patient_service.get_patients_by_doctor(doctor_id)
            for patient in patients[:5]:
                if patient.created_at:
                    time_ago = self._time_ago(patient.created_at)
                    activities.append({
                        'time': patient.created_at,
                        'text': f"👤 Yeni hasta: {patient.user.full_name if patient.user else 'N/A'} ({time_ago})",
                        'type': 'patient'
                    })
            
            # Son görüşmeler
            from services.therapy_service import TherapyService
            therapy_service = TherapyService()
            sessions = therapy_service.get_sessions_by_doctor(doctor_id, limit=10)
            
            for session in sessions[:5]:
                if session.created_at:
                    patient = self.patient_service.get_patient_by_id(session.patient_id)
                    patient_name = patient.user.full_name if patient and patient.user else "N/A"
                    time_ago = self._time_ago(session.created_at)
                    
                    status_map = {
                        'scheduled': '📝',
                        'in_progress': '🔄',
                        'completed': '✅',
                        'cancelled': '❌'
                    }
                    icon = status_map.get(session.status, '📝')
                    
                    activities.append({
                        'time': session.created_at,
                        'text': f"{icon} Görüşme: {patient_name} ({time_ago})",
                        'type': 'session'
                    })
            
            # Zamana göre sırala (en yeni en üstte)
            activities.sort(key=lambda x: x['time'], reverse=True)
            
            # İlk 10 aktiviteyi göster
            for activity in activities[:10]:
                item = QListWidgetItem(activity['text'])
                
                # Tip'e göre renklendirme
                if activity['type'] == 'appointment':
                    item.setForeground(QColor("#2196F3"))
                elif activity['type'] == 'patient':
                    item.setForeground(QColor("#4CAF50"))
                elif activity['type'] == 'session':
                    item.setForeground(QColor("#FF9800"))
                
                self.activities_list.addItem(item)
            
            # Boş durum
            if self.activities_list.count() == 0:
                item = QListWidgetItem("📭 Henüz aktivite yok")
                item.setForeground(Qt.gray)
                self.activities_list.addItem(item)
                
        except Exception as e:
            logger.error(f"Aktivite yukleme hatasi: {e}")
            item = QListWidgetItem("⚠️ Aktiviteler yüklenemedi")
            item.setForeground(Qt.red)
            self.activities_list.addItem(item)
    
    def _time_ago(self, dt: datetime) -> str:
        """Zaman farkını insan okunabilir formata çevir"""
        if not dt:
            return "bilinmiyor"
        
        now = datetime.now()
        diff = now - dt
        
        seconds = diff.total_seconds()
        
        if seconds < 60:
            return "az önce"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f"{minutes} dakika önce"
        elif seconds < 86400:
            hours = int(seconds / 3600)
            return f"{hours} saat önce"
        elif seconds < 172800:
            return "dün"
        elif seconds < 604800:
            days = int(seconds / 86400)
            return f"{days} gün önce"
        else:
            return dt.strftime("%d.%m.%Y") 

    def _populate_warnings(self):
        """Önemli uyarıları doldur - hasta bazlı"""
        self.warnings_list.clear()
        warnings_found = False
        
        try:
            doctor_id = session_manager.get_current_user_id()
            
            # Eksik tıbbi geçmiş kontrolü - HASTA BAZLI
            patients = self.patient_service.get_patients_by_doctor(doctor_id)
            
            for patient in patients:
                if not patient.medical_history or not patient.medical_history.strip():
                    patient_name = patient.user.full_name if patient and patient.user else "N/A"
                    item = QListWidgetItem(f"📋 {patient_name}: Tıbbi geçmiş eksik")
                    item.setData(Qt.UserRole, {'action': 'goto_patient_detail', 'patient_id': patient.id})
                    item.setBackground(QColor("#FFF9C4"))
                    self.warnings_list.addItem(item)
                    warnings_found = True
            
            # Eksik acil iletişim kontrolü - HASTA BAZLI
            for patient in patients:
                if not patient.emergency_contact_phone or not patient.emergency_contact_name:
                    patient_name = patient.user.full_name if patient and patient.user else "N/A"
                    item = QListWidgetItem(f"🚨 {patient_name}: Acil iletişim eksik")
                    item.setData(Qt.UserRole, {'action': 'goto_patient_detail', 'patient_id': patient.id})
                    item.setBackground(QColor("#FFE0B2"))
                    self.warnings_list.addItem(item)
                    warnings_found = True
            
            # Görüşme notu girilmemiş oturumlar - HASTA BAZLI
            sessions = self.therapy_service.get_sessions_by_doctor(doctor_id, limit=50)
            
            for session in sessions:
                if session.status == 'completed' and (not session.therapist_notes or not session.therapist_notes.strip()):
                    patient = self.patient_service.get_patient_by_id(session.patient_id)
                    patient_name = patient.user.full_name if patient and patient.user else "N/A"
                    date_str = session.session_date.strftime("%d.%m.%Y") if session.session_date else "N/A"
                    
                    item = QListWidgetItem(f"📝 {patient_name}: {date_str} görüşme notu eksik")
                    item.setData(Qt.UserRole, {'action': 'goto_patient_detail', 'patient_id': session.patient_id})
                    item.setBackground(QColor("#FFCDD2"))
                    self.warnings_list.addItem(item)
                    warnings_found = True
            
            # Onay bekleyen randevular - HASTA BAZLI
            appointments = self.appointment_repo.find_by_doctor(doctor_id, limit=100)
            
            for apt in appointments:
                if apt.status == 'pending' and (datetime.now() - apt.created_at).days > 2:
                    patient = self.patient_service.get_patient_by_id(apt.patient_id)
                    patient_name = patient.user.full_name if patient and patient.user else "N/A"
                    days = (datetime.now() - apt.created_at).days
                    
                    item = QListWidgetItem(f"⏰ {patient_name}: {days} gündür onay bekliyor")
                    item.setData(Qt.UserRole, {'action': 'goto_appointments'})
                    item.setBackground(QColor("#FFCDD2"))
                    self.warnings_list.addItem(item)
                    warnings_found = True
            
            # Yarın randevusu olan hastalar (hazırlık hatırlatıcısı) - HASTA BAZLI
            tomorrow = (datetime.now() + timedelta(days=1)).date()
            
            for apt in appointments:
                if apt.appointment_date.date() == tomorrow and apt.status in ['pending', 'confirmed']:
                    patient = self.patient_service.get_patient_by_id(apt.patient_id)
                    patient_name = patient.user.full_name if patient and patient.user else "N/A"
                    time_str = apt.appointment_date.strftime("%H:%M")
                    
                    item = QListWidgetItem(f"📅 Yarın {time_str}: {patient_name} - hazırlık yapın")
                    item.setData(Qt.UserRole, {'action': 'goto_appointments'})
                    item.setBackground(QColor("#E1F5FE"))
                    self.warnings_list.addItem(item)
                    warnings_found = True
            
            # Boş durum
            if not warnings_found:
                item = QListWidgetItem("✅ Tüm işler tamamlanmış!")
                item.setForeground(Qt.gray)
                self.warnings_list.addItem(item)
            
        except Exception as e:
            logger.error(f"Uyari yukleme hatasi: {e}")
            item = QListWidgetItem(f"⚠️ Hata: {str(e)}")
            item.setForeground(Qt.red)
            self.warnings_list.addItem(item)