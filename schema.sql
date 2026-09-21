-- =====================================================
-- DATABASE SCHEMA untuk Gemini WhatsApp Bot
-- =====================================================

-- Tabel Pengguna
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabel Riwayat Percakapan
CREATE TABLE IF NOT EXISTS chat_history (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(20) NOT NULL REFERENCES users(phone_number) ON DELETE CASCADE,
    role VARCHAR(10) NOT NULL CHECK (role IN ('user', 'model')),
    message TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index untuk mempercepat query history percakapan berdasarkan nomor HP
CREATE INDEX IF NOT EXISTS idx_chat_history_phone ON chat_history(phone_number, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone_number);

-- Tabel Custom Responses (untuk append text khusus per nomor)
CREATE TABLE IF NOT EXISTS custom_responses (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index untuk mempercepat lookup berdasarkan nomor HP
CREATE INDEX IF NOT EXISTS idx_custom_responses_phone ON custom_responses(phone_number);

-- =====================================================
-- SAMPLE DATA (opsional, untuk testing)
-- =====================================================
-- INSERT INTO users (phone_number, name) VALUES ('62812345678', 'Test User');
-- INSERT INTO custom_responses (phone_number, message) VALUES ('62812345678', 'Info khusus user ini');
