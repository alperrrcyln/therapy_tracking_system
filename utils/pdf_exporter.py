"""
PDF Exporter
ReportLab ile PDF rapor oluşturma
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
from typing import Dict, List
import os

from utils.logger import setup_logger

logger = setup_logger(__name__)

# Türkçe karakter destekli font kayıt
_FONT_NORMAL = 'Helvetica'
_FONT_BOLD   = 'Helvetica-Bold'

def _register_turkish_font():
    global _FONT_NORMAL, _FONT_BOLD
    candidates = [
        (r'C:\Windows\Fonts\arial.ttf',   r'C:\Windows\Fonts\arialbd.ttf'),
        (r'C:\Windows\Fonts\ARIAL.TTF',   r'C:\Windows\Fonts\ARIALBD.TTF'),
        ('/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
         '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf'),
    ]
    for reg, bold in candidates:
        if os.path.exists(reg):
            try:
                pdfmetrics.registerFont(TTFont('TurkishFont',     reg))
                pdfmetrics.registerFont(TTFont('TurkishFont-Bold', bold))
                _FONT_NORMAL = 'TurkishFont'
                _FONT_BOLD   = 'TurkishFont-Bold'
                logger.info(f"Türkçe font kaydedildi: {reg}")
                return
            except Exception as e:
                logger.warning(f"Font kayıt hatası: {e}")
    logger.warning("Türkçe font bulunamadı, varsayılan font kullanılıyor")

_register_turkish_font()


def _safe(text: str) -> str:
    """Türkçe karakterleri PDF-güvenli stringe çevirir (font yoksa ASCII)."""
    if _FONT_NORMAL == 'Helvetica':
        return (text
                .replace('ş', 's').replace('Ş', 'S')
                .replace('ğ', 'g').replace('Ğ', 'G')
                .replace('ü', 'u').replace('Ü', 'U')
                .replace('ö', 'o').replace('Ö', 'O')
                .replace('ç', 'c').replace('Ç', 'C')
                .replace('ı', 'i').replace('İ', 'I'))
    return text


class PDFExporter:
    """PDF export helper"""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Özel stiller"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontName=_FONT_BOLD,
            fontSize=18,
            textColor=colors.HexColor('#1976D2'),
            spaceAfter=30
        ))

        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontName=_FONT_BOLD,
            fontSize=14,
            textColor=colors.HexColor('#424242'),
            spaceAfter=12
        ))

        self.styles.add(ParagraphStyle(
            name='TurkishNormal',
            parent=self.styles['Normal'],
            fontName=_FONT_NORMAL,
            fontSize=10,
        ))
    
    def _ts(self, text: str) -> str:
        """_safe kısayolu — instance içinden çağrılır."""
        return _safe(text)

    def _cell(self, text: str):
        """Tablo hücresi için Türkçe-güvenli Paragraph."""
        return Paragraph(_safe(str(text)), self.styles['TurkishNormal'])

    def _table_style(self, header_color: str) -> TableStyle:
        return TableStyle([
            ('BACKGROUND',    (0, 0), (0, -1), colors.HexColor(header_color)),
            ('FONTNAME',      (0, 0), (-1, -1), _FONT_NORMAL),
            ('FONTNAME',      (0, 0), (0, -1),  _FONT_BOLD),
            ('TEXTCOLOR',     (0, 0), (-1, -1), colors.black),
            ('ALIGN',         (0, 0), (-1, -1), 'LEFT'),
            ('FONTSIZE',      (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING',    (0, 0), (-1, -1), 6),
            ('GRID',          (0, 0), (-1, -1), 0.5, colors.grey),
        ])

    def export_patient_summary(self, report_data: Dict, output_path: str) -> bool:
        """Hasta özet raporu PDF"""
        try:
            doc = SimpleDocTemplate(output_path, pagesize=A4,
                                    rightMargin=2*cm, leftMargin=2*cm,
                                    topMargin=2*cm, bottomMargin=2*cm)
            story = []

            patient = report_data['patient']
            user    = patient.user

            story.append(Paragraph(
                _safe(f"Danisan Ozet Raporu: {user.full_name if user else 'N/A'}"),
                self.styles['CustomTitle']
            ))
            story.append(Spacer(1, 0.5*cm))

            # Hasta bilgileri
            info_data = [
                [self._cell('E-posta:'),       self._cell(user.email if user else '-')],
                [self._cell('Yas:'),            self._cell(str(patient.age) if patient.age else '-')],
                [self._cell('Cinsiyet:'),       self._cell(_safe(patient.gender or '-'))],
                [self._cell('Rapor Tarihi:'),   self._cell(report_data['generated_at'].strftime('%d.%m.%Y %H:%M'))],
            ]
            info_table = Table(info_data, colWidths=[5*cm, 10*cm])
            info_table.setStyle(self._table_style('#E3F2FD'))
            story.append(info_table)
            story.append(Spacer(1, 1*cm))

            # İstatistikler
            story.append(Paragraph(_safe('Gorusme Istatistikleri'), self.styles['CustomHeading']))
            stats_data = [
                [self._cell('Toplam Gorusme:'),  self._cell(str(report_data['total_sessions']))],
                [self._cell('Tamamlanan:'),       self._cell(str(report_data['completed_sessions']))],
                [self._cell('Son 30 Gun:'),       self._cell(str(report_data['recent_sessions_count']))],
                [self._cell('Toplam Sure:'),      self._cell(f"{report_data['total_duration_hours']} saat")],
            ]
            stats_table = Table(stats_data, colWidths=[7*cm, 8*cm])
            stats_table.setStyle(self._table_style('#FFF9C4'))
            story.append(stats_table)
            story.append(Spacer(1, 1*cm))

            # Duygu analizi
            emo = report_data.get('emotion_summary', {})
            if emo.get('total_analyzed', 0) > 0:
                story.append(Paragraph(_safe('Duygu Analizi Ozeti'), self.styles['CustomHeading']))
                dom = emo.get('dominant_emotion', '')
                emo_text = _safe(
                    f"Toplam {emo['total_analyzed']} duygu analizi yapildi. "
                    f"Baskin duygu: {dom}" if dom else
                    f"Toplam {emo['total_analyzed']} duygu analizi yapildi."
                )
                story.append(Paragraph(emo_text, self.styles['TurkishNormal']))
                story.append(Spacer(1, 0.5*cm))

                if emo.get('percentages'):
                    story.append(Paragraph(_safe('Duygu Dagilimi (%)'), self.styles['CustomHeading']))
                    pct_data = [
                        [self._cell(k), self._cell(f"%{v}")]
                        for k, v in emo['percentages'].items()
                    ]
                    pct_table = Table(pct_data, colWidths=[7*cm, 8*cm])
                    pct_table.setStyle(self._table_style('#E8F5E9'))
                    story.append(pct_table)

            doc.build(story)
            logger.info(f"PDF olusturuldu: {output_path}")
            return True

        except Exception as e:
            logger.error(f"PDF export error: {e}", exc_info=True)
            return False

    def export_period_report(self, report_data: Dict, output_path: str) -> bool:
        """Dönem raporu PDF"""
        try:
            doc = SimpleDocTemplate(output_path, pagesize=A4,
                                    rightMargin=2*cm, leftMargin=2*cm,
                                    topMargin=2*cm, bottomMargin=2*cm)
            story = []

            period = report_data['period']
            story.append(Paragraph(
                _safe(f"Donem Raporu: {period['start'].strftime('%d.%m.%Y')} - "
                      f"{period['end'].strftime('%d.%m.%Y')}"),
                self.styles['CustomTitle']
            ))
            story.append(Spacer(1, 0.5*cm))

            stats = report_data['statistics']
            stats_data = [
                [self._cell('Toplam Danisan:'),        self._cell(str(stats['total_patients']))],
                [self._cell('Aktif Danisan:'),         self._cell(str(stats['active_patients']))],
                [self._cell('Toplam Gorusme:'),        self._cell(str(stats['total_sessions']))],
                [self._cell('Tamamlanan:'),            self._cell(str(stats['completed_sessions']))],
                [self._cell('Iptal Edilen:'),          self._cell(str(stats['cancelled_sessions']))],
                [self._cell('Toplam Sure:'),           self._cell(f"{stats['total_hours']} saat")],
                [self._cell('Ort. Gorusme Suresi:'),   self._cell(f"{stats['avg_session_duration']} dk")],
            ]
            stats_table = Table(stats_data, colWidths=[7*cm, 8*cm])
            stats_table.setStyle(self._table_style('#E8F5E9'))
            story.append(stats_table)
            story.append(Spacer(1, 1*cm))

            # Günlük dağılım varsa
            daily = report_data.get('daily_distribution', {})
            if daily:
                story.append(Paragraph(_safe('Gunluk Gorusme Dagilimi'), self.styles['CustomHeading']))
                daily_data = [
                    [self._cell(date), self._cell(f"{count} gorusme")]
                    for date, count in sorted(daily.items())
                ]
                daily_table = Table(daily_data, colWidths=[7*cm, 8*cm])
                daily_table.setStyle(self._table_style('#E3F2FD'))
                story.append(daily_table)

            doc.build(story)
            logger.info(f"Donem PDF olusturuldu: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Period PDF export error: {e}", exc_info=True)
            return False