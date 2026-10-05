# Gemini WhatsApp Bot - Multi-Client SaaS

Production-ready WhatsApp chatbot dengan AI (Gemini, Groq, NVIDIA) untuk bisnis. Multi-client architecture, admin panel, dan lead tracking.

## 🚀 Quick Start

### Setup (5 menit)

**Pilih script sesuai OS Anda:**

```bash
# Linux/Mac
bash scripts/run.sh

# Windows PowerShell
.\scripts\run.ps1

# Atau Python
python scripts/quickstart.py
```

Script akan:
1. ✅ Create virtual environment
2. ✅ Install dependencies
3. ✅ Setup `.env` dari `.env.example`
4. ✅ Verify database connection

### Jalankan Bot

```bash
python main.py
# atau
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Bot berjalan di `http://localhost:8000`

---

## 📋 Fitur Utama

### ✅ Multi-Client Architecture
- Setiap bisnis memiliki namespace sendiri (FAQ, conversations, leads)
- Admin login terpisah per bisnis
- Scalable ke ratusan bisnis

### ✅ AI Fallback System
- Primary: Groq (fast, free)
- Fallback 1: NVIDIA NIM
- Fallback 2: OpenAI

### ✅ Admin Panel
- JWT-based authentication
- Manage FAQ & business settings
- Track conversations & leads
- Manual override (handoff mode)
- Test bot sebelum go-live

### ✅ Smart Message Handling
- Conversation history (10 pesan terakhir)
- Auto-detect order intent → create Lead
- Handoff mode (skip LLM, admin handle manual)
- Rate limiting (20 msgs/min per customer)

### ✅ Database Support
- **Development**: SQLite (file-based)
- **Production**: PostgreSQL (cloud-ready)

---

## 🔧 Konfigurasi

### Environment Variables

Copy `.env.example` → `.env` dan update:

```bash
# =====================================================
# Gemini AI
# =====================================================
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-1.5-flash

# =====================================================
# WhatsApp
# =====================================================
WA_PHONE_NUMBER_ID=your_phone_id
WA_ACCESS_TOKEN=your_access_token
WA_VERIFY_TOKEN=your_verify_token

# =====================================================
# Database (development = SQLite, production = PostgreSQL)
# =====================================================
DATABASE_URL=sqlite:///./chatbot.db
# atau
DATABASE_URL=postgresql://user:password@localhost/dbname

# =====================================================
# JWT & Auth
# =====================================================
JWT_SECRET_KEY=your_secret_key_change_in_production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# =====================================================
# Frontend
# =====================================================
FRONTEND_ORIGIN=http://localhost:3000

# =====================================================
# LLM Fallbacks (opsional)
# =====================================================
GROQ_API_KEY=your_groq_key
NVIDIA_API_KEY=your_nvidia_key
OPENAI_API_KEY=your_openai_key
```

### Generate JWT Secret

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 📡 API Endpoints

### Authentication

```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "admin@business.com",
  "password": "password123"
}

Response:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "business_id": 1
}
```

**Semua endpoint berikut require header:**
```http
Authorization: Bearer <access_token>
```

### Business Settings

```http
GET /api/business
→ Dapatkan data bisnis

PUT /api/business
{
  "name": "Toko Kopi Asik",
  "tone": "ramah",
  "opening_hours": "08:00 - 17:00",
  "address": "Jl. Sudirman 123",
  "order_flow": "Pesan via WA..."
}
```

### FAQ Management

```http
GET /api/faqs
→ Dapatkan semua FAQ

POST /api/faqs
{
  "question": "Apa saja menu?",
  "answer": "Kopi, teh, smoothie...",
  "order": 1
}

PUT /api/faqs/{faq_id}
DELETE /api/faqs/{faq_id}
```

### Conversations

```http
GET /api/conversations?limit=50&offset=0
→ Daftar percakapan (with pagination)

GET /api/conversations/{conversation_id}
→ Detail percakapan + message history

GET /api/conversations/{conversation_id}/messages
→ Hanya messages (paging)

POST /api/conversations/{conversation_id}/handoff
{
  "handoff": true
}
→ Set admin mode (skip LLM)

POST /api/conversations/{conversation_id}/reply
{
  "message": "Terima kasih, akan kami proses..."
}
→ Admin balas manual via WhatsApp
```

### Leads

```http
GET /api/leads?status=baru&limit=100
→ Daftar leads (filter by status: baru, follow-up, selesai)

PATCH /api/leads/{lead_id}
{
  "status": "follow-up",
  "need": "updated need..."
}
```

### Test Bot

```http
POST /api/chat/test
{
  "message": "Berapa harga kopi?"
}
→ Test bot response tanpa WhatsApp (untuk admin panel)
```

### Health Check

```http
GET /health
→ {"status": "ok", "service": "Gemini WhatsApp Bot", "version": "2.0.0"}
```

---

## 🧪 Testing

Run pytest untuk semua tests:

```bash
pytest tests/
```

Atau specific test:

```bash
pytest tests/test_prompt_builder.py -v
pytest tests/test_auth.py::TestLoginEndpoint -v
pytest tests/test_message_handler.py::TestHandoffLogic -v
```

**Test coverage:**
- ✅ Prompt building (no placeholders, tone guidance)
- ✅ JWT authentication & token expiration
- ✅ Handoff logic (skip LLM when handoff=True)
- ✅ Lead creation & detection
- ✅ Message validation & rate limiting
- ✅ Protected endpoints

---

## 🗄️ Database Migrations

### Initialize Alembic

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Existing Initial Migration

Direktori `alembic/versions/` sudah ada migration:
- `001_initial_setup.py` — Create all tables (businesses, FAQs, conversations, leads, admin_users)

Jalankan:
```bash
alembic upgrade head
```

---

## 🌐 Deployment

### Docker

```bash
docker build -t wa-bot .
docker run -p 8000:8000 --env-file .env wa-bot
```

### Render.com (Recommended)

1. Push ke GitHub
2. Create new Web Service di Render
3. Connect repository
4. Set environment variables di Render dashboard
5. Deploy! 🚀

**Database**: Gunakan Render PostgreSQL (included)

```yaml
# render.yaml (auto-detected)
services:
  - type: web
    name: wa-bot
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: python main.py
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: wa-bot-db
          property: connectionString
databases:
  - name: wa-bot-db
    plan: starter
```

### Manual VPS (DigitalOcean, AWS, etc)

```bash
# SSH ke server
ssh user@server

# Clone & setup
git clone your-repo
cd wa-bot
python -m venv venv
source venv/bin/activate  # atau venv\Scripts\activate di Windows
pip install -r requirements.txt

# Edit .env dengan production values
nano .env

# Setup PostgreSQL (optional)
sudo apt install postgresql
createdb chatbot
createuser botuser -P

# Run dengan production server
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Atau use systemd
sudo vim /etc/systemd/system/wa-bot.service
[Unit]
Description=WhatsApp Bot
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/var/wa-bot
Environment="PATH=/var/wa-bot/venv/bin"
ExecStart=/var/wa-bot/venv/bin/gunicorn main:app --bind 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target

sudo systemctl start wa-bot
sudo systemctl enable wa-bot
```

---

## 📱 WhatsApp Integration

### Setup WhatsApp Business Account

1. Daftar di [Meta Business](https://business.facebook.com)
2. Create WhatsApp Business App
3. Get credentials:
   - `WA_PHONE_NUMBER_ID` — dari App Settings
   - `WA_ACCESS_TOKEN` — dari System User
   - `WA_VERIFY_TOKEN` — buat random string (security)
4. Setup webhook:
   - Callback URL: `https://your-domain.com/webhook`
   - Verify Token: input `WA_VERIFY_TOKEN` Anda
   - Subscribe to messages

### Testing Webhook

```bash
# Test webhook verification
curl -X GET "http://localhost:8000/webhook?hub.mode=subscribe&hub.challenge=12345&hub.verify_token=YOUR_TOKEN"

# Send test message
curl -X POST http://localhost:8000/test/send-message \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "628123456789",
    "message": "Test message"
  }'
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│         WhatsApp Cloud API                  │
└────────────────────┬────────────────────────┘
                     │
                     ↓
        ┌─────────────────────────────┐
        │   FastAPI Webhook Handler   │
        │   (Rate Limiting)           │
        └────────────┬────────────────┘
                     │
        ┌────────────┴───────────────┐
        ↓                            ↓
   ┌─────────────┐         ┌──────────────────┐
   │  Message    │         │  Admin Routes    │
   │  Handler    │         │  (JWT Protected) │
   └──────┬──────┘         └──────────────────┘
          │
    ┌─────┴──────────┬───────────┐
    ↓                ↓           ↓
┌────────────┐ ┌──────────┐ ┌─────────┐
│ Prompt     │ │LLM Router│ │Database │
│ Builder    │ │(Fallback)│ │ (SQLite/│
└────────────┘ └──────────┘ │ PostgreSQL)
                             └─────────┘
```

**Components:**
- **main.py** — FastAPI app, webhooks, CORS, rate limiting
- **services/** — Business logic (message handling, prompts, LLM routing)
- **routers/admin.py** — Admin API endpoints with JWT auth
- **models.py** — Database models (Business, FAQ, Conversation, Lead, AdminUser)
- **database.py** — ORM & database service layer
- **config.py** — Configuration from environment
- **schemas.py** — Pydantic request/response validation

---

## 📊 Database Schema

```sql
Business
├── FAQ (many-to-one)
├── Conversation (many-to-one)
│   └── ChatMessage (many-to-one)
├── Lead (many-to-one)
└── AdminUser (many-to-one)
```

**Key Features:**
- Foreign keys dengan `CASCADE` delete
- Indexes pada frequently-queried columns
- Timezone-aware timestamps
- Legacy tables untuk backward compatibility

---

## 🔐 Security

✅ **Implemented:**
- JWT tokens (HS256, 24-hour expiry)
- bcrypt password hashing
- Rate limiting (20 msgs/min per phone)
- WhatsApp webhook signature verification
- CORS middleware
- SQLAlchemy ORM (SQL injection prevention)
- Message length validation (4096 chars max)

⚠️ **Best Practices:**
- Always use HTTPS in production
- Rotate JWT secret regularly
- Monitor API logs for abuse
- Use strong passwords for admin accounts
- Enable database backups

---

## 🐛 Troubleshooting

### Bot tidak menerima pesan dari WhatsApp

1. Check webhook URL publik & HTTPS
2. Verify `WA_VERIFY_TOKEN` di Meta Business
3. Check WhatsApp app notifications allowed
4. Review logs: `python main.py` (development)

### Database connection error

```
ERROR: could not connect to database
```

✅ Solutions:
- Verify `DATABASE_URL` di `.env`
- Untuk PostgreSQL: `psql -U user -d dbname` (test connection)
- Create tables: `alembic upgrade head`

### Rate limit: "429 Too Many Requests"

- Bot receive >20 messages/min dari 1 nomor
- Check customer tidak spam
- Adjust `RATE_LIMIT_PER_MINUTE` di config jika perlu

### LLM response timeout

- Primary provider (Groq) down → fallback to NVIDIA
- Check API keys di `.env`
- Verify internet connection
- Logs show: "Provider X gagal dengan error: ..."

---

## 📚 Next Steps

1. **Setup Admin Panel** — Deploy Next.js frontend (separate repo)
2. **Monitor & Analytics** — Setup logging, error tracking (Sentry)
3. **Scale to Production** — Use Render/AWS + PostgreSQL
4. **Custom Integrations** — Add SMS, Telegram, LINE bots

---

## 📞 Support

- GitHub Issues: [Report bugs](https://github.com/your-repo/issues)
- Docs: [Full API docs](https://api.your-domain.com/docs)
- WhatsApp Group: [Komunitas](https://chat.whatsapp.com/xxx)

---

## 📄 License

MIT License - Gunakan dengan bebas untuk project komersial

---

**Last Updated:** 2024  
**Status:** ✅ Production Ready  
**Version:** 2.0.0 (Multi-Client SaaS)
