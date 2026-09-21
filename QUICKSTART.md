# ⚡ Quick Start Guide

Panduan cepat untuk setup dan menjalankan Gemini WhatsApp Bot dalam 5 menit.

## 🔧 Prerequisites
- Python 3.10+
- PostgreSQL running (atau Docker)
- Google Gemini API key
- WhatsApp Business Account credentials

## ⚙️ Setup (5 menit)

### 1️⃣ Clone & Setup
```bash
cd gemini-wa-bot
python -m venv venv
venv\Scripts\activate  # Windows
# atau: source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### 2️⃣ Database
**Option A - Docker (Recommended):**
```bash
docker-compose up -d
```

**Option B - PostgreSQL lokal:**
```bash
psql -U postgres -f schema.sql
```

### 3️⃣ Environment Variables
```bash
cp .env.example .env
# Edit .env dengan credentials Anda
```

Minimal credentials diperlukan:
```env
GEMINI_API_KEY=sk-...
WA_PHONE_NUMBER_ID=123456789
WA_ACCESS_TOKEN=EAAB...
WA_VERIFY_TOKEN=verify_token_123
DATABASE_URL=postgresql://bot_user:bot_password_secure@localhost:5432/gemini_wa_bot_db
```

### 4️⃣ Run Bot
```bash
python main.py
```

Bot running di: `http://localhost:8000`

## 🌐 Setup Webhook

### 1️⃣ Expose Lokal dengan ngrok
```bash
ngrok http 8000
```

Copy URL: `https://xxxx-xx-xxx-xxx-xx.ngrok.io`

### 2️⃣ Configure di Meta Dashboard
1. WhatsApp → Configuration
2. Webhook URL: `https://xxxx-xx-xxx-xxx-xx.ngrok.io/webhook`
3. Verify Token: `verify_token_123` (dari `.env`)
4. Subscribe: `messages` event

### 3️⃣ Test
Kirim pesan dari WhatsApp, bot akan reply dengan Gemini response!

## 📡 API Endpoints

| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| GET | `/health` | Health check |
| GET | `/webhook` | Webhook verification |
| POST | `/webhook` | Receive messages |
| POST | `/test/send-message` | Send test message |
| GET | `/test/chat-history/{phone}` | View chat history |

## 🧪 Test Commands

### Health Check
```bash
curl http://localhost:8000/health
```

### Send Message
```bash
curl -X POST "http://localhost:8000/test/send-message?phone_number=62812345678&message=Hello"
```

### Get History
```bash
curl http://localhost:8000/test/chat-history/62812345678
```

## 🐛 Troubleshooting

| Error | Solution |
|-------|----------|
| Database connection refused | Pastikan PostgreSQL running atau docker-compose up -d |
| Invalid verify token | Check `.env` WA_VERIFY_TOKEN |
| Bot not receiving messages | Check webhook URL di Meta Dashboard (harus green ✅) |
| GEMINI_API_KEY is required | Copy `.env.example` ke `.env` dan isi values |

## 📚 Full Documentation
- Setup lengkap: [SETUP_GUIDE.md](SETUP_GUIDE.md)
- Dokumentasi lengkap: [README.md](README.md)
- Available commands: `make help`

## 🚀 Useful Commands

```bash
# Development dengan auto-reload
make dev

# Run tests
make test

# Format code
make format

# Database reset
make db-reset

# Docker
docker-compose up -d    # Start
docker-compose down     # Stop
docker-compose logs -f  # View logs
```

## 📊 Folder Structure
```
gemini-wa-bot/
├── main.py              # FastAPI app
├── config.py            # Configuration
├── database.py          # Database models
├── models.py            # Pydantic models
├── services/            # Business logic
│   ├── gemini.py       # Gemini API
│   ├── whatsapp.py     # WhatsApp API
│   └── message_handler.py
├── schema.sql          # Database schema
├── requirements.txt    # Dependencies
└── .env               # Configuration (create from .env.example)
```

---

**Need help?** Check [SETUP_GUIDE.md](SETUP_GUIDE.md) untuk instruksi lengkap step-by-step.

**Happy botting! 🤖**
