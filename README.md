# QR Attendance / QR Yoklama

> [English](#english) | [Turkce](#turkce)

---

## English

### Overview

QR Attendance is a web-based student attendance tracking system for university courses. Instructors generate a unique QR code per course; students scan it to record attendance. The system includes a student self-service portal, an instructor dashboard with analytics, and a Django admin backend.

### Features

**Instructor Dashboard**
- Course overview with student count, session count, and average attendance
- At-risk student alerts (below 60% attendance)
- Attendance matrix (students x sessions) with CSV export
- Printable QR code page per course
- Bulk grade import via CSV (midterm/final)
- Course materials management (URL and file upload)

**Student Portal**
- Passwordless login via magic link (`.edu.tr` email only)
- Per-course attendance breakdown (present / excused / absent per week)
- Course materials and grade viewing
- Attendance threshold warnings

**Attendance Recording**
- Students scan the course QR code and enter their student ID
- IP and user-agent logging for audit
- Duplicate detection per session
- Excused absence support with reason tracking

**Admin**
- Full Django admin with inline editing for schedules, sessions, materials
- UBYS student list importer (Excel via pandas/openpyxl)
- Holiday calendar for auto-skipping sessions
- Auto-generation of 14-week session schedules from semester start date

### Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 5.1, Django REST Framework |
| Database | SQLite (dev) / PostgreSQL via Supabase (prod) |
| Hosting | Railway (Nixpacks) |
| Static files | WhiteNoise |
| Frontend | Django templates + Tailwind CSS |
| Auth | Django admin (instructors), magic link (students) |
| Email | Gmail SMTP |

### Project Structure

```
qr_attendence/
  apps/
    core/           # TimeStampedModel base, shared utilities
    attendance/     # Course, Student, Session, Enrollment, QR, Materials
    portal/         # Student self-service portal (magic link auth)
    api/            # REST API endpoints
  qr_attendance/
    settings/
      base.py         # Common settings
      development.py  # SQLite, DEBUG=True
      production.py   # PostgreSQL, WhiteNoise, security
  templates/
    instructor/     # Instructor dashboard templates
    portal/         # Student portal templates
  requirements/
    base.txt        # Core dependencies
    prod.txt        # Production (base + gunicorn)
```

### Local Development

```bash
# Clone
git clone https://github.com/fatihbozdag/QRattendance.git
cd QRattendance

# Virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements/base.txt

# Environment variables (.env)
DJANGO_SETTINGS_MODULE=qr_attendance.settings.development
SECRET_KEY=your-secret-key
DEBUG=True

# Migrate and run
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Deployment

The project is deployed on **Railway** with **Supabase** PostgreSQL.

- Auto-deploys on push to `master`
- Procfile runs migrate + collectstatic + gunicorn at start
- Session Pooler is used for IPv4 compatibility with Supabase

### License

This project is developed for academic use.

---

## Turkce

### Genel Bakis

QR Yoklama, universite dersleri icin web tabanli bir ogrenci yoklama takip sistemidir. Ogretim uyeleri her ders icin benzersiz bir QR kod olusturur; ogrenciler bu kodu tarayarak yoklamaya katilir. Sistem, ogrenci self-servis portali, analitik iceren ogretim uyesi paneli ve Django admin arayuzu icerir.

### Ozellikler

**Ogretim Uyesi Paneli**
- Ogrenci sayisi, oturum sayisi ve ortalama devamlilik ile ders ozeti
- Risk altindaki ogrenci uyarilari (%60 alti devamlilik)
- Devamlilik matrisi (ogrenciler x oturumlar) ve CSV disari aktarimi
- Ders bazinda yazdirilabilir QR kod sayfasi
- CSV ile toplu not yukleme (vize/final)
- Ders materyalleri yonetimi (URL ve dosya yukleme)

**Ogrenci Portali**
- Sihirli baglanti ile sifresiz giris (yalnizca `.edu.tr` e-posta)
- Ders bazinda devamlilik dokumu (haftalik katilim / mazeret / devamsizlik)
- Ders materyalleri ve not goruntuleme
- Devamlilik esik degeri uyarilari

**Yoklama Kaydi**
- Ogrenciler ders QR kodunu tarayip ogrenci numaralarini girer
- Denetim icin IP ve kullanici ajani kaydedilir
- Oturum basina tekrar algilama
- Aciklamali mazeretli devamsizlik destegi

**Yonetim**
- Program, oturum ve materyal icin satirici duzenleme ile tam Django admin
- UBYS ogrenci listesi icerik aktarimi (pandas/openpyxl ile Excel)
- Otomatik oturum atlamasi icin resmi tatil takvimi
- Doneme baslangic tarihinden 14 haftalik oturum otomatik olusturma

### Teknoloji Yigini

| Katman | Teknoloji |
|---|---|
| Backend | Django 5.1, Django REST Framework |
| Veritabani | SQLite (gelistirme) / PostgreSQL - Supabase (uretim) |
| Barindirma | Railway (Nixpacks) |
| Statik dosyalar | WhiteNoise |
| On yuz | Django sablonlari + Tailwind CSS |
| Kimlik dogrulama | Django admin (ogretim uyeleri), sihirli baglanti (ogrenciler) |
| E-posta | Gmail SMTP |

### Proje Yapisi

```
qr_attendence/
  apps/
    core/           # TimeStampedModel temeli, ortak araclar
    attendance/     # Ders, Ogrenci, Oturum, Kayit, QR, Materyaller
    portal/         # Ogrenci self-servis portali (sihirli baglanti)
    api/            # REST API uclari
  qr_attendance/
    settings/
      base.py         # Ortak ayarlar
      development.py  # SQLite, DEBUG=True
      production.py   # PostgreSQL, WhiteNoise, guvenlik
  templates/
    instructor/     # Ogretim uyesi paneli sablonlari
    portal/         # Ogrenci portali sablonlari
  requirements/
    base.txt        # Temel bagimliliklar
    prod.txt        # Uretim (temel + gunicorn)
```

### Yerel Gelistirme

```bash
# Klonlama
git clone https://github.com/fatihbozdag/QRattendance.git
cd QRattendance

# Sanal ortam
python -m venv .venv
source .venv/bin/activate

# Bagimliliklari yukleme
pip install -r requirements/base.txt

# Ortam degiskenleri (.env)
DJANGO_SETTINGS_MODULE=qr_attendance.settings.development
SECRET_KEY=gizli-anahtariniz
DEBUG=True

# Migrasyon ve calistirma
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Dagitim

Proje **Railway** uzerinde **Supabase** PostgreSQL ile calistirilmaktadir.

- `master` dalina push yapildiginda otomatik dagitim
- Procfile baslatma asamasinda migrate + collectstatic + gunicorn calistirir
- Supabase ile IPv4 uyumlulugu icin Session Pooler kullanilir

### Lisans

Bu proje akademik kullanim icin gelistirilmistir.
