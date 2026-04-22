"""
Modern QSS Styles
Profesyonel tema tasarımı
"""

# Terapötik Renkler - Sakinleştirici ve Profesyonel
COLORS = {
    # Primary - Sakin Mavi (Güven ve Huzur)
    'primary': '#4A90E2',
    'primary_dark': '#357ABD',
    'primary_light': '#E3F2FD',
    
    # Accent - Yumuşak Yeşil (Doğa ve Şifa)
    'accent': '#66BB6A',
    'accent_light': '#A5D6A7',
    
    # Neutral - Yumuşak Gri Tonları
    'background': '#F7F9FC',
    'surface': '#FFFFFF',
    'border': '#E0E4E8',
    'divider': '#CFD8DC',
    
    # Text - Yüksek Kontrast
    'text_primary': '#2C3E50',
    'text_secondary': '#5D6D7E',
    'text_disabled': '#95A5A6',
    'text_on_primary': '#FFFFFF',
    
    # Status - Yumuşak Tonlar
    'success': '#66BB6A',
    'warning': '#FFA726',
    'error': '#EF5350',
    'info': '#42A5F5',
    
    # Sidebar - Koyu Ama Sakinleştirici
    'sidebar_bg': '#34495E',
    'sidebar_text': '#ECF0F1',
    'sidebar_hover': '#415B76',
    'sidebar_active': '#4A90E2',
}


def get_stylesheet() -> str:
    """
    Ana QSS stylesheet'i döndür
    
    Returns:
        QSS string
    """
    return f"""
    /* ==================== GLOBAL ==================== */
    QWidget {{
        font-family: 'Segoe UI', Arial, sans-serif;
        font-size: 10pt;
        color: {COLORS['text_primary']};
    }}
    
    QMainWindow {{
        background-color: {COLORS['background']};
    }}
    
    /* ==================== BUTTONS ==================== */
    QPushButton {{
        background-color: {COLORS['primary']};
        color: white;
        border: none;
        border-radius: 4px;
        padding: 8px 16px;
        font-weight: 500;
        min-height: 32px;
    }}
    
    QPushButton:hover {{
        background-color: {COLORS['primary_dark']};
    }}
    
    QPushButton:pressed {{
        background-color: {COLORS['primary_dark']};
        padding-top: 9px;
        padding-bottom: 7px;
    }}
    
    QPushButton:disabled {{
        background-color: {COLORS['border']};
        color: {COLORS['text_disabled']};
    }}
    
    QPushButton.secondary {{
        background-color: transparent;
        color: {COLORS['primary']};
        border: 2px solid {COLORS['primary']};
    }}
    
    QPushButton.secondary:hover {{
        background-color: {COLORS['primary_light']};
    }}
    
    QPushButton.danger {{
        background-color: {COLORS['error']};
    }}
    
    QPushButton.danger:hover {{
        background-color: #D32F2F;
    }}
    
    QPushButton.success {{
        background-color: {COLORS['success']};
    }}
    
    QPushButton.success:hover {{
        background-color: #388E3C;
    }}
    
    /* ==================== LINE EDIT ==================== */
    QLineEdit {{
        background-color: white;
        border: 2px solid {COLORS['border']};
        border-radius: 4px;
        padding: 8px 12px;
        min-height: 32px;
    }}
    
    QLineEdit:focus {{
        border: 2px solid {COLORS['primary']};
    }}
    
    QLineEdit:disabled {{
        background-color: {COLORS['background']};
        color: {COLORS['text_disabled']};
    }}
    
    /* ==================== TEXT EDIT ==================== */
    QTextEdit, QPlainTextEdit {{
        background-color: white;
        border: 2px solid {COLORS['border']};
        border-radius: 4px;
        padding: 8px;
    }}
    
    QTextEdit:focus, QPlainTextEdit:focus {{
        border: 2px solid {COLORS['primary']};
    }}
    
    /* ==================== COMBO BOX ==================== */
    QComboBox {{
        background-color: white;
        border: 2px solid {COLORS['border']};
        border-radius: 4px;
        padding: 8px 12px;
        min-height: 32px;
    }}
    
    QComboBox:focus {{
        border: 2px solid {COLORS['primary']};
    }}
    
    QComboBox::drop-down {{
        border: none;
        width: 30px;
    }}
    
    QComboBox::down-arrow {{
        image: url(down_arrow.png);
        width: 12px;
        height: 12px;
    }}
    
    /* ==================== LABELS ==================== */
    QLabel {{
        color: {COLORS['text_primary']};
        background-color: transparent;
    }}
    
    QLabel.title {{
        font-size: 24pt;
        font-weight: bold;
        color: {COLORS['text_primary']};
    }}
    
    QLabel.subtitle {{
        font-size: 16pt;
        font-weight: 600;
        color: {COLORS['text_primary']};
    }}
    
    QLabel.section-title {{
        font-size: 14pt;
        font-weight: 600;
        color: {COLORS['text_primary']};
        padding: 8px 0px;
    }}
    
    QLabel.hint {{
        color: {COLORS['text_secondary']};
        font-size: 9pt;
    }}
    
    /* ==================== TABLE ==================== */
    QTableWidget {{
        background-color: white;
        border: 1px solid {COLORS['border']};
        border-radius: 4px;
        gridline-color: {COLORS['border']};
    }}
    
    QTableWidget::item {{
        padding: 8px;
    }}
    
    QTableWidget::item:selected {{
        background-color: {COLORS['primary_light']};
        color: {COLORS['text_primary']};
    }}
    
    QHeaderView::section {{
        background-color: {COLORS['background']};
        color: {COLORS['text_primary']};
        padding: 8px;
        border: none;
        border-bottom: 2px solid {COLORS['primary']};
        font-weight: 600;
    }}
    
    /* ==================== SCROLL BAR ==================== */
    QScrollBar:vertical {{
        background-color: {COLORS['background']};
        width: 12px;
        border-radius: 6px;
    }}
    
    QScrollBar::handle:vertical {{
        background-color: {COLORS['divider']};
        border-radius: 6px;
        min-height: 30px;
    }}
    
    QScrollBar::handle:vertical:hover {{
        background-color: {COLORS['text_secondary']};
    }}
    
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    
    QScrollBar:horizontal {{
        background-color: {COLORS['background']};
        height: 12px;
        border-radius: 6px;
    }}
    
    QScrollBar::handle:horizontal {{
        background-color: {COLORS['divider']};
        border-radius: 6px;
        min-width: 30px;
    }}
    
    QScrollBar::handle:horizontal:hover {{
        background-color: {COLORS['text_secondary']};
    }}
    
    /* ==================== FRAME ==================== */
    QFrame.card {{
        background-color: white;
        border: 1px solid {COLORS['border']};
        border-radius: 8px;
        padding: 16px;
    }}
    
    QFrame.sidebar {{
        background-color: {COLORS['sidebar_bg']};
        border: none;
    }}
    
    /* ==================== TAB WIDGET ==================== */
    QTabWidget::pane {{
        border: 1px solid {COLORS['border']};
        border-radius: 4px;
        background-color: white;
    }}
    
    QTabBar::tab {{
        background-color: {COLORS['background']};
        color: {COLORS['text_secondary']};
        padding: 10px 20px;
        border: 1px solid {COLORS['border']};
        border-bottom: none;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
    }}
    
    QTabBar::tab:selected {{
        background-color: white;
        color: {COLORS['primary']};
        font-weight: 600;
        border-bottom: 2px solid {COLORS['primary']};
    }}
    
    QTabBar::tab:hover {{
        background-color: {COLORS['primary_light']};
    }}
    
    /* ==================== PROGRESS BAR ==================== */
    QProgressBar {{
        border: 2px solid {COLORS['border']};
        border-radius: 4px;
        text-align: center;
        height: 20px;
    }}
    
    QProgressBar::chunk {{
        background-color: {COLORS['primary']};
        border-radius: 2px;
    }}
    
    /* ==================== CHECKBOX & RADIO ==================== */
    QCheckBox, QRadioButton {{
        spacing: 8px;
    }}
    
    QCheckBox::indicator, QRadioButton::indicator {{
        width: 20px;
        height: 20px;
    }}
    
    QCheckBox::indicator:unchecked {{
        border: 2px solid {COLORS['border']};
        border-radius: 4px;
        background-color: white;
    }}
    
    QCheckBox::indicator:checked {{
        border: 2px solid {COLORS['primary']};
        border-radius: 4px;
        background-color: {COLORS['primary']};
    }}
    
    /* ==================== DATE EDIT ==================== */
    QDateEdit {{
        background-color: white;
        border: 2px solid {COLORS['border']};
        border-radius: 4px;
        padding: 8px 12px;
        min-height: 32px;
    }}
    
    QDateEdit:focus {{
        border: 2px solid {COLORS['primary']};
    }}
    
    /* ==================== SPIN BOX ==================== */
    QSpinBox, QDoubleSpinBox {{
        background-color: white;
        border: 2px solid {COLORS['border']};
        border-radius: 4px;
        padding: 8px 12px;
        min-height: 32px;
    }}
    
    QSpinBox:focus, QDoubleSpinBox:focus {{
        border: 2px solid {COLORS['primary']};
    }}
    
    /* ==================== MENU BAR ==================== */
    QMenuBar {{
        background-color: white;
        border-bottom: 1px solid {COLORS['border']};
    }}
    
    QMenuBar::item {{
        padding: 8px 16px;
        background-color: transparent;
    }}
    
    QMenuBar::item:selected {{
        background-color: {COLORS['primary_light']};
    }}
    
    QMenu {{
        background-color: white;
        border: 1px solid {COLORS['border']};
        padding: 4px;
    }}
    
    QMenu::item {{
        padding: 8px 24px;
        border-radius: 4px;
    }}
    
    QMenu::item:selected {{
        background-color: {COLORS['primary_light']};
    }}
    
    /* ==================== TOOL TIP ==================== */
    QToolTip {{
        background-color: {COLORS['sidebar_bg']};
        color: white;
        border: none;
        padding: 6px 12px;
        border-radius: 4px;
    }}
    """