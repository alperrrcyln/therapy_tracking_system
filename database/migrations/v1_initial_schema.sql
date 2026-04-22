-- Therapy Tracking System Database Schema v1
-- Initial database structure

-- Users tablosu (Hem danışman hem danışan)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('doctor', 'patient')),
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    phone TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active INTEGER DEFAULT 1
);

-- Patients tablosu (Danışan detay bilgileri)
CREATE TABLE IF NOT EXISTS patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL,
    doctor_id INTEGER,
    tc_no TEXT,
    birth_date DATE,
    gender TEXT CHECK(gender IN ('male', 'female', 'other')),
    address TEXT,
    emergency_contact_name TEXT,
    emergency_contact_phone TEXT,
    photo_path TEXT,
    medical_history TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Therapy Sessions tablosu (Terapi görüşmeleri)
CREATE TABLE IF NOT EXISTS therapy_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    doctor_id INTEGER NOT NULL,
    session_date TIMESTAMP NOT NULL,
    duration_minutes INTEGER,
    status TEXT DEFAULT 'scheduled' CHECK(status IN ('scheduled', 'in_progress', 'completed', 'cancelled')),
    session_notes TEXT,
    therapist_notes TEXT,
    video_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Emotion Analysis Results tablosu (Duygu analiz sonuçları)
CREATE TABLE IF NOT EXISTS emotion_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    emotion_type TEXT NOT NULL CHECK(emotion_type IN ('happy', 'sad', 'angry', 'fear', 'surprise', 'neutral', 'disgust')),
    confidence REAL NOT NULL,
    frame_number INTEGER,
    additional_data TEXT,
    FOREIGN KEY (session_id) REFERENCES therapy_sessions(id) ON DELETE CASCADE
);

-- Appointments tablosu (Randevular)
CREATE TABLE IF NOT EXISTS appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    doctor_id INTEGER NOT NULL,
    appointment_date TIMESTAMP NOT NULL,
    duration_minutes INTEGER DEFAULT 60,
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'confirmed', 'completed', 'cancelled')),
    notes TEXT,
    reminder_sent INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Patient Diary tablosu (Danışan günlükleri)
CREATE TABLE IF NOT EXISTS patient_diary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    entry_date DATE NOT NULL,
    mood_rating INTEGER CHECK(mood_rating BETWEEN 1 AND 10),
    title TEXT,
    content TEXT NOT NULL,
    is_private INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
);

-- Session Notes tablosu (Görüşme notları - danışman tarafından)
CREATE TABLE IF NOT EXISTS session_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    note_type TEXT DEFAULT 'general' CHECK(note_type IN ('general', 'diagnosis', 'treatment_plan', 'observation')),
    content TEXT NOT NULL,
    created_by INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES therapy_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE
);

-- Indexler (Performans için)
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_patients_user_id ON patients(user_id);
CREATE INDEX IF NOT EXISTS idx_patients_doctor_id ON patients(doctor_id);
CREATE INDEX IF NOT EXISTS idx_therapy_sessions_patient_id ON therapy_sessions(patient_id);
CREATE INDEX IF NOT EXISTS idx_therapy_sessions_doctor_id ON therapy_sessions(doctor_id);
CREATE INDEX IF NOT EXISTS idx_therapy_sessions_date ON therapy_sessions(session_date);
CREATE INDEX IF NOT EXISTS idx_appointments_patient_id ON appointments(patient_id);
CREATE INDEX IF NOT EXISTS idx_appointments_doctor_id ON appointments(doctor_id);
CREATE INDEX IF NOT EXISTS idx_appointments_date ON appointments(appointment_date);
CREATE INDEX IF NOT EXISTS idx_emotion_analysis_session_id ON emotion_analysis(session_id);
CREATE INDEX IF NOT EXISTS idx_patient_diary_patient_id ON patient_diary(patient_id);

-- Varsayılan admin/doctor kullanıcısı (şifre: admin123)
-- Hash: pbkdf2_hmac ile oluşturulacak
-- Admin kullanici olustur
-- Sifre: admin123
-- Hash: pbkdf2_hmac SHA256
INSERT OR IGNORE INTO users (id, email, password_hash, role, first_name, last_name, is_active)
VALUES (
    1,
    'admin@therapy.com',
    'pbkdf2:sha256:600000$salt$5d9c68c6e45c8d7f9e4b3a2c1f8e7d6a5b4c3d2e1f0a9b8c7d6e5f4a3b2c1d0e',
    'doctor',
    'Admin',
    'Doctor',
    1
);