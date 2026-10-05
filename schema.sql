-- =====================================================
-- Gemini WhatsApp Bot - Multi-Client Database Schema
-- =====================================================
-- Database: gemini_wa_bot_db
-- Created: 2024-01-01
-- Version: 2.0.0 (Multi-Client)
-- =====================================================

-- =====================================================
-- BUSINESSES TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS businesses (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    tone VARCHAR(50) NOT NULL DEFAULT 'ramah',
    opening_hours TEXT,
    address TEXT,
    order_flow TEXT,
    whatsapp_number VARCHAR(20) NOT NULL UNIQUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX idx_businesses_name ON businesses(name);
CREATE INDEX idx_businesses_whatsapp_number ON businesses(whatsapp_number);
CREATE INDEX idx_businesses_is_active ON businesses(is_active);

-- =====================================================
-- FAQ TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS faqs (
    id SERIAL PRIMARY KEY,
    business_id INTEGER NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    question VARCHAR(500) NOT NULL,
    answer TEXT NOT NULL,
    "order" INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX idx_faqs_business_id ON faqs(business_id);

-- =====================================================
-- CONVERSATIONS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS conversations (
    id SERIAL PRIMARY KEY,
    business_id INTEGER NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    customer_phone VARCHAR(20) NOT NULL,
    customer_name VARCHAR(100),
    handoff BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX idx_conversations_business_id ON conversations(business_id);
CREATE INDEX idx_conversations_customer_phone ON conversations(customer_phone);
CREATE INDEX idx_conversations_updated_at ON conversations(updated_at);

-- =====================================================
-- CHAT MESSAGES TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS chat_messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX idx_chat_messages_conversation_id ON chat_messages(conversation_id);
CREATE INDEX idx_chat_messages_created_at ON chat_messages(created_at);

-- =====================================================
-- LEADS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS leads (
    id SERIAL PRIMARY KEY,
    business_id INTEGER NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    customer_name VARCHAR(100) NOT NULL,
    customer_phone VARCHAR(20) NOT NULL,
    need TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'baru',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX idx_leads_business_id ON leads(business_id);
CREATE INDEX idx_leads_customer_phone ON leads(customer_phone);
CREATE INDEX idx_leads_created_at ON leads(created_at);

-- =====================================================
-- ADMIN USERS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS admin_users (
    id SERIAL PRIMARY KEY,
    business_id INTEGER NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX idx_admin_users_email ON admin_users(email);
CREATE INDEX idx_admin_users_business_id ON admin_users(business_id);
CREATE INDEX idx_admin_users_is_active ON admin_users(is_active);

-- =====================================================
-- LEGACY TABLES (Backward Compatibility)
-- =====================================================

-- =====================================================
-- USERS TABLE (Legacy)
-- =====================================================
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX idx_users_phone_number ON users(phone_number);

-- =====================================================
-- CHAT HISTORY TABLE (Legacy)
-- =====================================================
CREATE TABLE IF NOT EXISTS chat_history (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(20) NOT NULL REFERENCES users(phone_number) ON DELETE CASCADE,
    role VARCHAR(10) NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX idx_chat_history_phone_number ON chat_history(phone_number);
CREATE INDEX idx_chat_history_created_at ON chat_history(created_at);

-- =====================================================
-- CUSTOM RESPONSES TABLE (Legacy)
-- =====================================================
CREATE TABLE IF NOT EXISTS custom_responses (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(20) NOT NULL UNIQUE,
    message TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX idx_custom_responses_phone_number ON custom_responses(phone_number);

-- =====================================================
-- ALEMBIC VERSION TABLE (For Migrations)
-- =====================================================
CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) PRIMARY KEY
);

-- =====================================================
-- VIEWS (Optional - untuk analytics)
-- =====================================================

-- View untuk summary per bisnis
CREATE OR REPLACE VIEW v_business_summary AS
SELECT
    b.id,
    b.name,
    b.whatsapp_number,
    COUNT(DISTINCT c.id) as total_conversations,
    COUNT(DISTINCT l.id) as total_leads,
    COUNT(DISTINCT CASE WHEN c.handoff = true THEN c.id END) as conversations_in_handoff,
    COUNT(DISTINCT l.id) FILTER (WHERE l.status = 'baru') as new_leads,
    MAX(c.updated_at) as last_conversation_at
FROM businesses b
LEFT JOIN conversations c ON b.id = c.business_id
LEFT JOIN leads l ON b.id = l.business_id
WHERE b.is_active = true
GROUP BY b.id, b.name, b.whatsapp_number;

-- View untuk recent conversations
CREATE OR REPLACE VIEW v_recent_conversations AS
SELECT
    c.id,
    c.business_id,
    c.customer_phone,
    c.customer_name,
    c.handoff,
    COUNT(cm.id) as message_count,
    MAX(cm.created_at) as last_message_at
FROM conversations c
LEFT JOIN chat_messages cm ON c.id = cm.conversation_id
GROUP BY c.id
ORDER BY c.updated_at DESC;

-- =====================================================
-- CONSTRAINTS & RULES
-- =====================================================
-- Foreign Keys:
-- - faqs.business_id -> businesses.id (CASCADE)
-- - conversations.business_id -> businesses.id (CASCADE)
-- - chat_messages.conversation_id -> conversations.id (CASCADE)
-- - leads.business_id -> businesses.id (CASCADE)
-- - admin_users.business_id -> businesses.id (CASCADE)
-- - chat_history.phone_number -> users.phone_number (CASCADE)

-- Unique Constraints:
-- - businesses.whatsapp_number
-- - admin_users.email
-- - custom_responses.phone_number
-- - users.phone_number

-- Check Constraints:
-- - conversations.handoff: BOOLEAN (true/false)
-- - admin_users.is_active: BOOLEAN (true/false)
-- - businesses.is_active: BOOLEAN (true/false)
-- - leads.status: IN ('baru', 'follow-up', 'selesai')
-- - chat_messages.role: IN ('user', 'assistant')
-- - chat_history.role: IN ('user', 'model')

-- Default Values:
-- - businesses.tone: 'ramah'
-- - businesses.is_active: TRUE
-- - conversations.handoff: FALSE
-- - leads.status: 'baru'
-- - admin_users.is_active: TRUE
-- - All created_at/updated_at: CURRENT_TIMESTAMP

-- =====================================================
-- INDEXES SUMMARY
-- =====================================================
-- Total Indexes: 18

-- Performance Indexes:
-- 1. idx_businesses_is_active - Filter active businesses
-- 2. idx_conversations_business_id - Join conversations by business
-- 3. idx_conversations_updated_at - Sort conversations by recent
-- 4. idx_chat_messages_created_at - Sort messages by timestamp
-- 5. idx_leads_created_at - Sort leads by date
-- 6. idx_chat_history_created_at - Sort history by timestamp
-- 7. idx_admin_users_is_active - Filter active admins

-- Lookup Indexes:
-- 8. idx_businesses_name - Search by business name
-- 9. idx_businesses_whatsapp_number - Lookup by WhatsApp number
-- 10. idx_faqs_business_id - Get FAQ for business
-- 11. idx_conversations_customer_phone - Find conversations by phone
-- 12. idx_leads_customer_phone - Find leads by phone
-- 13. idx_leads_business_id - Get leads for business
-- 14. idx_admin_users_email - Login by email
-- 15. idx_admin_users_business_id - Get admins for business
-- 16. idx_users_phone_number - Lookup user (legacy)
-- 17. idx_chat_history_phone_number - Get chat history (legacy)
-- 18. idx_custom_responses_phone_number - Get custom response (legacy)

-- =====================================================
-- DATA TYPES REFERENCE
-- =====================================================
-- VARCHAR(n) - Text with max length n
-- TEXT - Unlimited text
-- INTEGER - Whole numbers (-2147483648 to 2147483647)
-- SERIAL - Auto-incrementing integer (1, 2, 3, ...)
-- BOOLEAN - TRUE or FALSE
-- TIMESTAMP WITH TIME ZONE - Date and time with timezone
-- PRIMARY KEY - Unique identifier for each row
-- FOREIGN KEY - Reference to another table
-- ON DELETE CASCADE - Delete child rows when parent is deleted
-- UNIQUE - Value must be unique in this column
-- NOT NULL - Value must exist
-- DEFAULT - Default value if not provided
-- INDEX - Speed up queries on this column

-- =====================================================
-- MIGRATION INFO
-- =====================================================
-- Initial Migration: 001_initial_setup
-- Status: Ready for production
-- Backup recommended before first use
-- Test on development database first
