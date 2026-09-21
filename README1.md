# Gemini WhatsApp Bot 🤖

Bot WhatsApp berbasis AI menggunakan Google Gemini API dengan memory percakapan yang disimpan di PostgreSQL.

## 🎯 Fitur Utama

- ✅ **AI-Powered Responses**: Menggunakan Google Gemini 2.0 Flash untuk generate respons yang cerdas dan natural
- ✅ **Chat History Memory**: Menyimpan riwayat percakapan untuk memberikan konteks yang lebih baik
- ✅ **Real-time Processing**: Memproses pesan masuk secara real-time menggunakan FastAPI webhook
- ✅ **User Management**: Menyimpan data pengguna dan riwayat percakapan
- ✅ **Error Handling**: Penanganan error yang baik dengan logging lengkap

## 📋 Requirement

- **Python 3.10+**
- **PostgreSQL 12+** (database)
- **Google Gemini API Key** (dari [console.cloud.google.com](https://console.cloud.google.com))
- **WhatsApp Business Account** dengan akses ke Cloud API
- **Meta App Credentials** (dari [developers.facebook.com](https://developers.facebook.com))

## 🚀 Setup & Installation

### 1. Clone Repository
```bash
cd gemini-wa-bot
```

### 2. Buat Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Setup Database PostgreSQL

#### Opsi A: Menggunakan psql CLI
```bash
# Koneksi ke PostgreSQL
psql -U postgres

# Buat database baru
CREATE DATABASE gemini_wa_bot_db;

# Keluar dari psql
\q

# Jalankan schema
psql -U postgres -d gemini_wa_bot_db -f schema.sql
```

#### Opsi B: Menggunakan pgAdmin atau Database Management Tool Lainnya
1. Buat database baru bernama `gemini_wa_bot_db`
2. Jalankan script `schema.sql` di database tersebut

### 5. Setup Environment Variables

Copy `.env.example` ke `.env` dan isi dengan credential Anda:

```bash
cp .env.example .env
```

Edit `.env`:
```env
# Gemini Configuration
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash

# WhatsApp Cloud API Configuration
WA_PHONE_NUMBER_ID=your_whatsapp_phone_number_id
WA_ACCESS_TOKEN=your_whatsapp_system_user_access_token
WA_VERIFY_TOKEN=your_custom_webhook_verify_token

# PostgreSQL Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/gemini_wa_bot_db

# App Configuration
PORT=8000
LOG_LEVEL=INFO
```

### 6. Dapatkan Credentials

#### Google Gemini API Key
1. Buka [console.cloud.google.com](https://console.cloud.google.com)
2. Buat project baru
3. Enable "Generative Language API"
4. Buat API key di "Credentials" section
5. Copy API key ke `.env`

#### WhatsApp Credentials
1. Buka [developers.facebook.com](https://developers.facebook.com)
2. Buat app WhatsApp Business
3. Setup webhook dan dapatkan:
   - `WA_PHONE_NUMBER_ID`: Phone number ID dari WhatsApp Business Account
   - `WA_ACCESS_TOKEN`: System User access token dengan permission `whatsapp_business_messaging`
   - `WA_VERIFY_TOKEN`: Token custom yang Anda set sendiri (untuk verifikasi webhook)

## 🏃 Menjalankan Bot

### Development Mode (dengan auto-reload)
```bash
python main.py
```

atau

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Bot akan berjalan di `http://localhost:8000`

### Production Mode
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 🌐 Setup Webhook WhatsApp

### 1. Menggunakan ngrok untuk Tunnel Lokal (Development)

```bash
# Download dan install ngrok dari https://ngrok.com/download
# Jalankan ngrok (di terminal lain)
ngrok http 8000
```

Anda akan mendapat URL seperti: `https://xxxx-xx-xxx-xxx-xx.ngrok.io`

### 2. Configure Webhook di Meta Dashboard

1. Buka [developers.facebook.com](https://developers.facebook.com)
2. Pilih app Anda
3. Pilih "WhatsApp" → "Configuration"
4. Di "Webhook URL", masukkan: `https://xxxx-xx-xxx-xxx-xx.ngrok.io/webhook`
5. Di "Verify Token", masukkan `WA_VERIFY_TOKEN` dari `.env`
6. Klik "Verify and Save"

### 3. Subscribe ke Message Events

1. Di Meta Dashboard, pilih "Webhook Fields"
2. Pilih event yang ingin di-subscribe:
   - `messages` (untuk menerima pesan masuk)
3. Save

## 📡 API Endpoints

### Health Check
```http
GET /health
```

### WhatsApp Webhook (Verification)
```http
GET /webhook?hub.mode=subscribe&hub.challenge=<challenge>&hub.verify_token=<token>
```

### WhatsApp Webhook (Receive Messages)
```http
POST /webhook
Content-Type: application/json

{
  "object": "whatsapp_business_account",
  "entry": [...]
}
```

### Testing Endpoints (Development Only)

#### Send Message Manually
```http
POST /test/send-message?phone_number=62812345678&message=Hello%20World
```

**Response:**
```json
{
  "success": true,
  "message_id": "wamid.xxx",
  "phone_number": "62812345678"
}
```

#### Get Chat History
```http
GET /test/chat-history/62812345678
```

**Response:**
```json
{
  "phone_number": "62812345678",
  "message_count": 5,
  "messages": [
    {
      "role": "user",
      "message": "Halo",
      "timestamp": "2024-01-15T10:30:00"
    },
    {
      "role": "model",
      "message": "Halo! Ada yang bisa saya bantu?",
      "timestamp": "2024-01-15T10:30:05"
    }
  ]
}
```

## 📊 Database Schema

### Tabel `users`
Menyimpan data pengguna WhatsApp

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| phone_number | VARCHAR(20) | Nomor WhatsApp (unique) |
| name | VARCHAR(100) | Nama pengguna |
| created_at | TIMESTAMP | Waktu pembuatan user |
| updated_at | TIMESTAMP | Waktu update terakhir |

### Tabel `chat_history`
Menyimpan riwayat percakapan

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| phone_number | VARCHAR(20) | Nomor WhatsApp (FK ke users) |
| role | VARCHAR(10) | 'user' atau 'model' |
| message | TEXT | Konten pesan |
| created_at | TIMESTAMP | Waktu pesan dikirim |

## 🏗️ Project Structure

```
gemini-wa-bot/
├── main.py                    # FastAPI aplikasi utama
├── config.py                  # Konfigurasi dari environment variables
├── database.py                # Database models & SQLAlchemy setup
├── models.py                  # Pydantic models untuk request/response
├── schema.sql                 # SQL schema untuk PostgreSQL
├── requirements.txt           # Python dependencies
├── .env.example              # Template environment variables
├── .gitignore                # Git ignore patterns
├── README.md                 # Dokumentasi ini
└── services/
    ├── __init__.py
    ├── gemini.py             # Integrasi Google Gemini API
    ├── whatsapp.py           # Integrasi WhatsApp Cloud API
    └── message_handler.py    # Business logic untuk handle pesan
```

## 🧪 Testing

### Test Endpoint Health Check
```bash
curl http://localhost:8000/health
```

### Test Send Message
```bash
curl -X POST "http://localhost:8000/test/send-message?phone_number=62812345678&message=Halo%20dunia"
```

### Test Get Chat History
```bash
curl http://localhost:8000/test/chat-history/62812345678
```

### Check Logs

Lihat log real-time di console untuk debugging:
```
2024-01-15 10:30:00,123 - main - INFO - Webhook request received: {...}
2024-01-15 10:30:01,456 - services.gemini - INFO - Gemini response generated successfully
2024-01-15 10:30:02,789 - services.whatsapp - INFO - Message sent successfully
```

## 🔐 Security Best Practices

1. **Environment Variables**: Jangan commit `.env` file, gunakan `.env.example` sebagai template
2. **API Keys**: Simpan semua API keys di environment variables, tidak di code
3. **HTTPS**: Selalu gunakan HTTPS untuk webhook URL di production
4. **Token Verification**: Selalu verifikasi webhook token dari WhatsApp
5. **Input Validation**: Validate semua input dari user
6. **Rate Limiting**: Pertimbangkan menambahkan rate limiting di production
7. **Database**: Gunakan prepared statements (SQLAlchemy sudah handle ini)

## 📝 Logging

Bot menggunakan Python logging dengan format:
```
%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

Level logging bisa diset via environment variable `LOG_LEVEL`:
- `DEBUG`: Informasi detail untuk debugging
- `INFO`: Informasi umum (default)
- `WARNING`: Peringatan
- `ERROR`: Kesalahan

## 🚨 Troubleshooting

### Error: "Invalid verify token"
- Pastikan `WA_VERIFY_TOKEN` di `.env` sama dengan yang di Meta Dashboard
- Pastikan Anda melakukan Save setelah mengubah verify token

### Error: "Database connection refused"
- Pastikan PostgreSQL sedang berjalan
- Pastikan `DATABASE_URL` di `.env` benar (format: `postgresql://user:password@host:port/database`)
- Cek username dan password PostgreSQL

### Error: "GEMINI_API_KEY is required"
- Pastikan `.env` file ada dan berisi `GEMINI_API_KEY`
- Pastikan API key valid dan aktif di Google Cloud Console

### Bot tidak menerima pesan
- Cek apakah webhook URL benar di Meta Dashboard
- Cek apakah webhook ber-status "Active" (green checkmark)
- Cek logs di console untuk error messages
- Test webhook dengan endpoint `/test/send-message`

### Pesan terkirim tapi tidak dikonfirmasi
- Cek apakah WhatsApp number ID benar
- Cek apakah access token masih valid
- Verifikasi di dashboard bahwa phone number sudah di-assign ke app

## 🤝 Contributing

Contributions welcome! Silakan buat pull request atau buka issue untuk bugs/features.

## 📄 License

MIT License - Lihat LICENSE file

## 📞 Support

Jika ada masalah atau pertanyaan, buka issue di repository ini.

---

**Made with ❤️ using FastAPI, Google Gemini, dan WhatsApp Cloud API**
