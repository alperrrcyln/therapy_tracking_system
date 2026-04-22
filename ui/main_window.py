"""
Main Window
Ana uygulama penceresi - StackedWidget ile sayfa yonetimi
"""
from PyQt5.QtWidgets import (
    QMainWindow, QStackedWidget, QHBoxLayout, QWidget, QVBoxLayout,
    QLineEdit, QListWidget, QListWidgetItem, QLabel, QFrame, QMessageBox
)
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCloseEvent

from ui.styles import get_stylesheet
from ui.widgets.sidebar_menu import SidebarMenu
from ui.pages.login_page import LoginPage
from core.constants import WINDOW_TITLE, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT, PageID
from core.session_manager import session_manager
from utils.logger import setup_logger
from database.models import User

logger = setup_logger(__name__)


class MainWindow(QMainWindow):
    """
    Ana pencere
    Tum sayfalari StackedWidget ile yonetir
    """
    
    def __init__(self):
        super().__init__()
        logger.info("MainWindow initialized")
        
        self.pages = {}
        self.current_page_id = None
        self.current_user = None  # Lazy loading için
        
        # Arama için repository'ler (lazy load edilecek)
        self.appointment_repo = None
        self.patient_service = None
        self.therapy_service = None
        
        self._setup_ui()
        self._apply_styles()
        self._show_login_page()
    
    def _setup_ui(self):
        """Ana pencere UI kurulumu"""
        self.setWindowTitle(WINDOW_TITLE)
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        
        # Tam ekran başlat
        self.showMaximized()
        
        # Ana widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Ana layout (yatay: Sidebar + Sağ Kısım)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar
        self.sidebar = SidebarMenu()
        self.sidebar.menu_item_clicked.connect(self._navigate_to_page)
        self.sidebar.logout_clicked.connect(self._handle_logout)
        self.sidebar.hide()  # Başlangıçta gizli
        main_layout.addWidget(self.sidebar)
        
        # Sağ taraf container (Header + İçerik)
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        
        # Header (arama çubuğu - başlangıçta gizli)
        self._create_header(right_layout)
        
        # Sayfa container
        self.stacked_widget = QStackedWidget()
        right_layout.addWidget(self.stacked_widget)
        
        main_layout.addWidget(right_container, 1)
        
        # Login sayfası ekle
        self.login_page = LoginPage()
        self.login_page.login_success.connect(self._on_login_success)
        self.login_page.page_changed.connect(self._navigate_to_page)
        self.pages[PageID.LOGIN] = self.login_page
        self.stacked_widget.addWidget(self.login_page)
        
        logger.info("Ana pencere kaydedildi")
    
    def _create_header(self, parent_layout):
        """Header oluştur (arama çubuğu)"""
        self.header = QFrame()
        self.header.setStyleSheet("""
            QFrame {
                background-color: white;
                border-bottom: 2px solid #E0E0E0;
            }
        """)
        self.header.setMinimumHeight(70)
        self.header.setMaximumHeight(70)
        self.header.hide()  # Başlangıçta gizli
        
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(30, 15, 30, 15)
        
        # Arama kutusu
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Hasta, randevu veya görüşme ara...")
        self.search_input.setMinimumWidth(400)
        self.search_input.setMaximumWidth(600)
        self.search_input.setMinimumHeight(40)
        self.search_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #E0E0E0;
                border-radius: 20px;
                padding: 8px 20px;
                font-size: 11pt;
                background-color: #F9F9F9;
            }
            QLineEdit:focus {
                border-color: #2196F3;
                background-color: white;
            }
        """)
        self.search_input.textChanged.connect(self._on_search_text_changed)
        header_layout.addWidget(self.search_input)
        
        header_layout.addStretch()
        
        # Kullanıcı bilgisi
        self.user_label = QLabel("")
        self.user_label.setStyleSheet("color: #757575; font-size: 10pt; font-weight: 600;")
        header_layout.addWidget(self.user_label)
        
        parent_layout.addWidget(self.header)
        
        # Arama sonuçları dropdown (başta gizli)
        self.search_results_widget = QListWidget()
        self.search_results_widget.setMaximumHeight(350)
        self.search_results_widget.setStyleSheet("""
            QListWidget {
                border: 2px solid #2196F3;
                border-radius: 8px;
                background-color: white;
                margin-left: 30px;
                margin-right: 30px;
            }
            QListWidget::item {
                padding: 12px 15px;
                border-bottom: 1px solid #E0E0E0;
            }
            QListWidget::item:hover {
                background-color: #E8F5E9;
            }
        """)
        self.search_results_widget.itemClicked.connect(self._on_search_result_clicked)
        self.search_results_widget.hide()
        
        parent_layout.addWidget(self.search_results_widget)
    
    def _apply_styles(self):
        """Stylesheet uygula"""
        self.setStyleSheet(get_stylesheet())
    
    def _show_login_page(self):
        """Login sayfasini goster"""
        self.sidebar.hide()
        self.header.hide()
        self.search_results_widget.hide()
        self.stacked_widget.setCurrentWidget(self.login_page)
        self.login_page.on_page_show()
    
    def _on_login_success(self, user):
        """Login basarili oldugunda"""
        logger.info(f"Login success handler: {user.email}")
        
        # Current user'ı kaydet (lazy loading için gerekli)
        self.current_user = user
        
        # Session'a user'i kaydet
        session_manager.login(user)
        
        # Sidebar'i goster ve kullaniciyi ayarla
        self.sidebar.set_user(user)
        self.sidebar.show()
        
        # Header'ı göster ve kullanıcı adını yaz
        self.header.show()
        if user.last_name:
            self.user_label.setText(f"👤 Dr. {user.last_name}")
        else:
            self.user_label.setText(f"👤 {user.email}")
        
        # Arama için repository'leri yükle
        self._load_search_repositories()
        
        # Doctor/Patient sayfalarini lazy load et
        self._load_role_pages(user)
    
    def _load_search_repositories(self):
        """Arama için repository'leri yükle"""
        try:
            from database.repositories.appointment_repository import AppointmentRepository
            from services.patient_service import PatientService
            from services.therapy_service import TherapyService
            
            self.appointment_repo = AppointmentRepository()
            self.patient_service = PatientService()
            self.therapy_service = TherapyService()
            
            logger.info("Search repositories loaded")
        except Exception as e:
            logger.error(f"Search repositories yukleme hatasi: {e}")
    
    def _load_role_pages(self, user: User):
        """Role gore sayfalari yukle"""
        if user.is_doctor:
            self._load_doctor_pages(user)  # user parametresi eklendi
        else:
            self._load_patient_pages()
    
    def _load_doctor_pages(self, user: User):
        """Danisman sayfalarini yukle - SADECE Dashboard (Lazy Loading)"""
        try:
            # SADECE Dashboard başta yüklenir
            # Diğer sayfalar (Patients List, Patient Detail, New Session, Appointments, Activities, Reports)
            # ilk tıklandığında lazy loading ile yüklenecek
            
            from ui.pages.doctor.dashboard_page import DoctorDashboardPage
            
            # Dashboard
            if PageID.DOCTOR_DASHBOARD not in self.pages:
                dashboard = DoctorDashboardPage()
                dashboard.page_changed.connect(self._navigate_to_page)
                dashboard.logout_requested.connect(self._handle_logout)
                self.pages[PageID.DOCTOR_DASHBOARD] = dashboard
                self.stacked_widget.addWidget(dashboard)
            
            logger.info("✅ Dashboard loaded - other pages will lazy load on first access")
            
            # Dashboard'a git
            self._navigate_to_page(PageID.DOCTOR_DASHBOARD)
            
        except Exception as e:
            logger.error(f"Dashboard yukleme hatasi: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Hata",
                f"Dashboard yuklenirken hata olustu:\n\n{str(e)}"
            )
            raise
    
    def _load_patient_pages(self):
        """Danisan sayfalarini yukle"""
        from ui.pages.patient.patient_dashboard_page import PatientDashboardPage
        
        if PageID.PATIENT_DASHBOARD not in self.pages:
            dashboard = PatientDashboardPage()
            dashboard.page_changed.connect(self._navigate_to_page)
            dashboard.logout_requested.connect(self._handle_logout)
            self.pages[PageID.PATIENT_DASHBOARD] = dashboard
            self.stacked_widget.addWidget(dashboard)
    
    def _navigate_to_page(self, page_id: int, *args):
        """Belirtilen sayfaya gec"""
        logger.debug(f"Navigate to page: {page_id}")
        
        # === LAZY LOADING - TÜM SAYFALAR ===
        if page_id not in self.pages and self.current_user and self.current_user.is_doctor:
            try:
                logger.info(f"🔄 Lazy loading page: {page_id}")
                
                # Patients List
                if page_id == PageID.PATIENTS_LIST:
                    from ui.pages.doctor.patients_list_page import PatientsListPage
                    page = PatientsListPage()
                    page.page_changed.connect(self._navigate_to_page)
                    page.logout_requested.connect(self._handle_logout)
                    page.patient_selected.connect(self._handle_patient_selected)
                    self.pages[page_id] = page
                    self.stacked_widget.addWidget(page)
                
                # Patient Detail
                elif page_id == PageID.PATIENT_DETAIL:
                    from ui.pages.doctor.patient_detail_page import PatientDetailPage
                    page = PatientDetailPage()
                    page.page_changed.connect(self._navigate_to_page)
                    page.logout_requested.connect(self._handle_logout)
                    self.pages[page_id] = page
                    self.stacked_widget.addWidget(page)
                
               # New Session -> Chat Page (Messenger benzeri)
                elif page_id == PageID.NEW_SESSION:
                    from ui.pages.doctor.chat_page import ChatPage
                    logger.info("📱 Chat sayfası yükleniyor...")
                    page = ChatPage()
                    page.page_changed.connect(self._navigate_to_page)
                    page.logout_requested.connect(self._handle_logout)
                    page.set_doctor(self.current_user.id)
                    self.pages[page_id] = page
                    self.stacked_widget.addWidget(page)
                
                # Appointments
                elif page_id == PageID.APPOINTMENTS:
                    from ui.pages.doctor.appointments_page import AppointmentsPage
                    page = AppointmentsPage()
                    page.page_changed.connect(self._navigate_to_page)
                    page.logout_requested.connect(self._handle_logout)
                    self.pages[page_id] = page
                    self.stacked_widget.addWidget(page)
                
                # Activities
                elif page_id == PageID.ACTIVITIES:
                    from ui.pages.doctor.activities_page import ActivitiesPage
                    page = ActivitiesPage()
                    page.page_changed.connect(self._navigate_to_page)
                    page.logout_requested.connect(self._handle_logout)
                    self.pages[page_id] = page
                    self.stacked_widget.addWidget(page)
                
                # Reports
                elif page_id == PageID.REPORTS:
                    from ui.pages.doctor.reports_page import ReportsPage
                    page = ReportsPage()
                    page.page_changed.connect(self._navigate_to_page)
                    page.logout_requested.connect(self._handle_logout)
                    page.set_doctor(self.current_user.id)
                    self.pages[page_id] = page
                    self.stacked_widget.addWidget(page)
                
                # Analytics
                elif page_id == PageID.ANALYTICS:
                    from ui.pages.doctor.analytics_page import AnalyticsPage
                    page = AnalyticsPage()
                    page.page_changed.connect(self._navigate_to_page)
                    page.logout_requested.connect(self._handle_logout)
                    page.set_doctor(self.current_user.id)
                    self.pages[page_id] = page
                    self.stacked_widget.addWidget(page)

                logger.info(f"✅ Page {page_id} loaded successfully")
                
            except Exception as e:
                logger.error(f"Lazy loading error for page {page_id}: {e}", exc_info=True)
                QMessageBox.critical(self, "Hata", f"Sayfa yüklenemedi:\n{str(e)}")
                return
        
        if page_id not in self.pages:
            logger.warning(f"Page not found: {page_id}")
            QMessageBox.warning(self, "Uyari", "Bu sayfa henuz hazir degil.")
            return
        
        # Mevcut sayfanin hide event'ini cagir
        current_page = self.stacked_widget.currentWidget()
        if hasattr(current_page, 'on_page_hide'):
            current_page.on_page_hide()
        
        # Yeni sayfayi goster
        target_page = self.pages[page_id]
        
        # Eger patient_id varsa (hasta detayı için)
        if args and page_id == PageID.PATIENT_DETAIL:
            if hasattr(target_page, 'set_patient'):
                target_page.set_patient(args[0])
        
        self.stacked_widget.setCurrentWidget(target_page)
        
        # Yeni sayfanin show event'ini cagir
        if hasattr(target_page, 'on_page_show'):
            target_page.on_page_show()
        
        # Sidebar'da aktif sayfayi isaretle
        if page_id != PageID.LOGIN:
            self.sidebar.set_active_page(page_id)
    
    def _handle_patient_selected(self, patient_id: int):
        """Danisan secildiginde detay sayfasina git"""
        logger.debug(f"Patient selected: {patient_id}")
        self._navigate_to_page(PageID.PATIENT_DETAIL, patient_id)
    
    def _handle_logout(self):
        """Logout islemi"""
        reply = QMessageBox.question(
            self, "Cikis", 
            "Cikis yapmak istediginizden emin misiniz?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            logger.info("User logging out")
            session_manager.logout()
            self.sidebar.hide()
            self.header.hide()
            self.search_results_widget.hide()
            self._show_login_page()
            self._clear_role_pages()
    
    def _clear_role_pages(self):
        """Role-specific sayfalari temizle"""
        pages_to_remove = [
            PageID.DOCTOR_DASHBOARD, PageID.PATIENTS_LIST,
            PageID.PATIENT_DETAIL, PageID.NEW_SESSION,
            PageID.APPOINTMENTS, PageID.ACTIVITIES,
            PageID.ANALYTICS, PageID.PATIENT_DASHBOARD
        ]
        
        for page_id in pages_to_remove:
            if page_id in self.pages:
                page = self.pages[page_id]
                self.stacked_widget.removeWidget(page)
                page.deleteLater()
                del self.pages[page_id]
        
        logger.debug("Role pages cleared")
    
    def _on_search_text_changed(self, text):
        """Arama metni değiştiğinde"""
        text = text.strip()

        if len(text) < 2:
            self.search_results_widget.hide()
            return

        self._perform_search(text.lower())

    def _perform_search(self, query):
        """Arama yap"""
        if not self.patient_service or not self.appointment_repo or not self.therapy_service:
            return
        
        try:
            doctor_id = session_manager.get_current_user_id()
            
            if not doctor_id:
                return
            
            self.search_results_widget.clear()
            results = []
            
            # Hastalarda ara
            patients = self.patient_service.get_patients_by_doctor(doctor_id)
            
            for patient in patients:
                matched = False
                match_fields = []
                
                # Ad soyad
                if patient.user and query in patient.user.full_name.lower():
                    matched = True
                    match_fields.append("Ad")
                
                # TC No
                if patient.tc_no and query in patient.tc_no.lower():
                    matched = True
                    match_fields.append("TC No")
                
                if matched:
                    patient_name = patient.user.full_name if patient.user else "N/A"
                    match_str = f" ({', '.join(match_fields)})" if match_fields else ""
                    results.append({
                        'text': f"👤 {patient_name}{match_str}",
                        'patient_id': patient.id,
                        'color': '#4CAF50'
                    })
            
            # Randevularda ara
            appointments = self.appointment_repo.find_by_doctor(doctor_id, limit=100)
            
            for apt in appointments:
                patient = self.patient_service.get_patient_by_id(apt.patient_id)
                patient_name = patient.user.full_name if patient and patient.user else "N/A"
                
                if query in patient_name.lower():
                    date_str = apt.appointment_date.strftime("%d.%m %H:%M")
                    results.append({
                        'text': f"📅 {patient_name} - {date_str}",
                        'patient_id': apt.patient_id,
                        'color': '#2196F3'
                    })
            
            # Görüşmelerde ara
            sessions = self.therapy_service.get_sessions_by_doctor(doctor_id, limit=100)
            
            for session in sessions:
                patient = self.patient_service.get_patient_by_id(session.patient_id)
                patient_name = patient.user.full_name if patient and patient.user else "N/A"
                
                if query in patient_name.lower():
                    date_str = session.session_date.strftime("%d.%m") if session.session_date else "N/A"
                    results.append({
                        'text': f"📝 {patient_name} - {date_str}",
                        'patient_id': session.patient_id,
                        'color': '#FF9800'
                    })
            
            # Sonuçları göster
            if not results:
                item = QListWidgetItem(f"📭 '{query}' için sonuç bulunamadı")
                item.setForeground(QColor("#757575"))
                self.search_results_widget.addItem(item)
            else:
                # İlk 8 sonucu göster
                for result in results[:8]:
                    item = QListWidgetItem(result['text'])
                    item.setForeground(QColor(result['color']))
                    item.setData(Qt.UserRole, result['patient_id'])
                    self.search_results_widget.addItem(item)
                
                if len(results) > 8:
                    item = QListWidgetItem(f"... ve {len(results) - 8} sonuç daha")
                    item.setForeground(QColor("#9E9E9E"))
                    self.search_results_widget.addItem(item)
            
            self.search_results_widget.show()
            
        except Exception as e:
            logger.error(f"Arama hatasi: {e}")
    
    def _on_search_result_clicked(self, item):
        """Arama sonucuna tıklandığında"""
        try:
            patient_id = item.data(Qt.UserRole)
            
            if patient_id:
                # Arama kutusunu temizle ve sonuçları gizle
                self.search_input.clear()
                self.search_results_widget.hide()
                
                # Hasta detayına git
                self._navigate_to_page(PageID.PATIENT_DETAIL, patient_id)
                logger.info(f"Aramadan hasta detayina gidildi: {patient_id}")
                
        except Exception as e:
            logger.error(f"Arama sonuc tiklama hatasi: {e}")
    
    def closeEvent(self, event: QCloseEvent):
        """Pencere kapatilirken"""
        reply = QMessageBox.question(
            self, "Cikis",
            "Uygulamayi kapatmak istediginizden emin misiniz?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            logger.info("Application closing")
            event.accept()
        else:
            event.ignore()