# Terapi Takip Sistemi

Terapist ve hastalar için geliştirilmiş kapsamlı bir terapi yönetim uygulaması. Gerçek zamanlı yüz ifadesi analizi, seans takibi, randevu yönetimi ve detaylı raporlama özellikleri sunar.

---

## Özellikler

### Terapist Paneli
- Hasta yönetimi (ekleme, düzenleme, arama)
- Terapi seansı planlama ve takibi
- Gerçek zamanlı video görüşmesi ve duygu analizi
- Randevu yönetim sistemi
- Hasta ilerleme analizleri ve dashboard
- Mesajlaşma / chat modülü
- PDF ve Excel rapor dışa aktarma

### Hasta Paneli
- Atanmış terapist ve randevu bilgileri
- Randevu oluşturma ve yönetimi
- Geçmiş seans görüntüleme
- Kişisel günlük / not defteri
- Seanslardaki duygu analizi sonuçlarını görüntüleme

### Makine Öğrenmesi & Bilgisayarlı Görü
- Gerçek zamanlı yüz ifadesi tespiti (7 duygu: mutlu, üzgün, kızgın, korku, şaşkın, iğrenme, nötr)
- MediaPipe ile yüz tespiti
- FER2013 veri setiyle eğitilmiş TensorFlow modeli
- Video seansları sırasında otomatik duygu kaydı

---

## Teknoloji Yığını

| Katman | Teknoloji |
|--------|-----------|
| GUI | PyQt5 5.15.10 |
| Veritabanı | SQLite3 |
| Bilgisayarlı Görü | OpenCV 4.8.1 + MediaPipe 0.10.8 |
| Derin Öğrenme | TensorFlow 2.15.0 |
| Görselleştirme | Matplotlib 3.8.2 |
| Görüntü İşleme | NumPy 1.26.2, Pillow 10.1.0 |

---

## Gereksinimler

- Python **3.9 – 3.11** (TensorFlow 2.15 ile uyumlu)
- Windows 10/11 (64-bit)
- Webcam (video seans ve duygu analizi için)
- En az 4 GB RAM (TensorFlow modeli için 8 GB önerilir)

---

## Kurulum

### 1. Depoyu Klonlayın

```bash
git clone https://github.com/kullanici-adi/therapy_tracking_system.git
cd therapy_tracking_system
```

### 2. Sanal Ortam Oluşturun

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Bağımlılıkları Yükleyin

```bash
pip install -r requirements.txt
```

### 4. Uygulamayı Çalıştırın

```bash
python main.py
```

İlk çalıştırmada SQLite veritabanı ve gerekli klasörler otomatik oluşturulur.

---

## Varsayılan Giriş Bilgileri

İlk çalıştırmada veritabanı sıfırdan oluşturulur ve aşağıdaki yönetici hesabı otomatik eklenir:

| Alan | Değer |
|------|-------|
| E-posta | `admin@therapy.com` |
| Şifre | `admin123` |

> Uygulama her klonlamada **tamamen temiz** başlar — hiçbir danışan verisi içermez. Danışanlarınızı kendiniz ekleyin.
>
> Güvenlik için ilk girişten sonra şifrenizi değiştirmeniz önerilir.

---

## Proje Yapısı

```
therapy_tracking_system/
├── core/               # Uygulama yaşam döngüsü, oturum, sabitler
├── database/           # Veritabanı yöneticisi, modeller, repository'ler
├── ml/                 # Duygu ve yüz tespit modülleri, eğitilmiş model
├── services/           # İş mantığı katmanı (auth, randevu, video, chat...)
├── ui/                 # PyQt5 arayüzü (sayfalar, widget'lar, dialog'lar)
├── utils/              # Şifreleme, doğrulama, loglama, dışa aktarma
├── data/               # Çalışma zamanı verisi (DB, loglar, video kayıtları)
├── resources/          # İkonlar ve stil dosyaları
├── config.py           # Genel yapılandırma
├── main.py             # Uygulama giriş noktası
└── requirements.txt    # Python bağımlılıkları
```

---



---

## Lisans

Bu proje [MIT Lisansı](LICENSE) altında lisanslanmıştır.
