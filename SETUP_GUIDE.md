# 📖 Panduan Setup Lengkap Gemini WhatsApp Bot

Panduan step-by-step untuk setup dan menjalankan Gemini WhatsApp Bot di lokal atau server.

## ✅ Prasyarat

Pastikan Anda sudah memiliki:
- Python 3.10 atau lebih tinggi
- PostgreSQL 12 atau lebih tinggi
- Git
- Akun Google Cloud dengan Gemini API aktif
- WhatsApp Business Account dengan akses Cloud API
- Meta Developer Account

## 🎯 Step 1: Clone dan Setup Project

### 1.1 Clone Repository
```bash
git clone <repository-url>
cd gemini-wa-bot
```

### 1.2 Setup Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 1.3 Install Dependencies
```bash
pip install -r requirements.txt
```

Untuk development (opsional):
```bash
pip install -r requirements-dev.txt
```

## 🗄️ Step 2: Setup Database PostgreSQL

### Opsi A: PostgreSQL Lokal

**Windows:**
1. Download PostgreSQL dari https://www.postgresql.org/download/windows/
2. Install dengan default settings
3. Buka pgAdmin atau Command Prompt
4. Buat database baru:

```sql
CREATE DATABASE gemini_wa_bot_db;
CREATE USER bot_user WITH PASSWORD 'bot_password_secure';
ALTER ROLE bot_user SET client_encoding TO 'utf8';
ALTER ROLE bot_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE bot_user SET default_transaction_deferrable TO on;
ALTER ROLE bot_user SET default_transaction_readonly TO off;
ALTER USER bot_user CREATEDB;
GRANT ALL PRIVILEGES ON DATABASE gemini_wa_bot_db TO bot_user;
```

5. Jalankan schema:
```bash
psql -U bot_user -d gemini_wa_bot_db -f schema.sql
```

**Linux/Mac:**
```bash
# Install PostgreSQL (Homebrew untuk Mac)
brew install postgresql

# Atau untuk Linux (Ubuntu/Debian)
sudo apt-get install postgresql postgresql-contrib

# Start PostgreSQL service
sudo systemctl start postgresql

# Connect sebagai superuser
sudo -u postgres psql

# Di dalam psql console, jalankan:
CREATE DATABASE gemini_wa_bot_db;
CREATE USER bot_user WITH PASSWORD 'bot_password_secure';
GRANT ALL PRIVILEGES ON DATABASE gemini_wa_bot_db TO bot_user;
\q

# Jalankan schema
psql -U bot_user -d gemini_wa_bot_db -f schema.sql
```

### Opsi B: Docker Compose (Recommended)

Jika Anda sudah install Docker dan Docker Compose:

```bash
# Start PostgreSQL container
docker-compose up -d

# Verify database container is running
docker-compose ps

# Check logs
docker-compose logs -f postgres
```

PostgreSQL akan berjalan di `localhost:5432` dengan credentials:
- Username: `bot_user`
- Password: `bot_password_secure`
- Database: `gemini_wa_bot_db`

## 🔑 Step 3: Setup Google Gemini API

### 3.1 Buat Google Cloud Project
1. Buka https://console.cloud.google.com
2. Klik "Create Project"
3. Masukkan nama project: `gemini-wa-bot`
4. Klik "Create"

### 3.2 Enable Generative Language API
1. Di sidebar, cari "Generative Language API"
2. Klik pada API tersebut
3. Klik "Enable"

### 3.3 Buat API Key
1. Di sidebar, buka "Credentials"
2. Klik "Create Credentials" → "API Key"
3. Copy API key yang ditampilkan
4. Simpan di file `.env` sebagai `GEMINI_API_KEY`

## 📱 Step 4: Setup WhatsApp Cloud API

### 4.1 Buat Meta App
1. Buka https://developers.facebook.com
2. Klik "My Apps" → "Create App"
3. Pilih "Business" sebagai app type
4. Isi detail app dan klik "Create"

### 4.2 Setup WhatsApp
1. Di app dashboard, klik "Add Product"
2. Cari "WhatsApp" dan klik "Add"
3. Pilih "WhatsApp Business Account" (buat atau gunakan existing)

### 4.3 Dapatkan Credentials

**Phone Number ID:**
1. Di sidebar WhatsApp, buka "Getting Started"
2. Copy "Phone Number ID"

**Access Token:**
1. Di WhatsApp settings, buka "API Setup"
2. Generate system user access token
3. Pastikan token punya permission: `whatsapp_business_messaging`
4. Copy token

**Verify Token:**
1. Buat token custom sendiri (bisa any string, misal: `your_secure_verify_token_12345`)

### 4.4 Configure Webhook
Kita akan setup webhook setelah bot berjalan di langkah 6.

## 🌍 Step 5: Setup Environment Variables

### 5.1 Buat .env file
```bash
cp .env.example .env
```

### 5.2 Edit .env dengan credentials Anda
```env
# Gemini Configuration
GEMINI_API_KEY=your_actual_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash

# WhatsApp Cloud API Configuration
WA_PHONE_NUMBER_ID=your_actual_phone_number_id_here
WA_ACCESS_TOKEN=your_actual_access_token_here
WA_VERIFY_TOKEN=your_custom_verify_token_here

# PostgreSQL Database Configuration
DATABASE_URL=postgresql://bot_user:bot_password_secure@localhost:5432/gemini_wa_bot_db

# App Configuration
PORT=8000
LOG_LEVEL=INFO
```

**⚠️ PENTING:** Jangan commit `.env` file! File ini berisi secrets.

## 🚀 Step 6: Jalankan Bot

### 6.1 Test Database Connection
```bash
python -c "from database import engine; engine.connect(); print('Database connection successful!')"
```

Jika berhasil, Anda akan melihat: `Database connection successful!`

### 6.2 Jalankan Bot

**Development Mode (dengan auto-reload):**
```bash
python main.py
```

atau

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Bot akan berjalan di: `http://localhost:8000`

Anda akan melihat output seperti:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started server process [1234]
```

### 6.3 Test Health Endpoint
Di terminal lain, jalankan:
```bash
curl http://localhost:8000/health
```

Response yang diharapkan:
```json
{"status":"ok","service":"Gemini WhatsApp Bot","version":"1.0.0"}
```

## 🔗 Step 7: Setup Webhook WhatsApp

### 7.1 Expose Lokal URL dengan ngrok

Di terminal baru, download dan jalankan ngrok:

```bash
# Download dari https://ngrok.com/download
# Atau jika sudah install:
ngrok http 8000
```

Anda akan melihat output:
```
Forwarding  https://xxxx-xx-xxx-xxx-xx.ngrok.io -> http://localhost:8000
```

Copy URL tersebut (misal: `https://xxxx-xx-xxx-xxx-xx.ngrok.io`)

### 7.2 Configure Webhook di Meta Dashboard

1. Buka https://developers.facebook.com
2. Pilih app Anda
3. Di sidebar, buka "WhatsApp" → "Configuration"
4. Di bagian "Webhook URL", masukkan:
   ```
   https://xxxx-xx-xxx-xxx-xx.ngrok.io/webhook
   ```
5. Di "Verify Token", masukkan `WA_VERIFY_TOKEN` dari `.env` Anda
6. Klik "Verify and Save"

Jika berhasil, Anda akan melihat ✅ checkmark dan status "Active"

### 7.3 Subscribe ke Message Events

1. Di Meta Dashboard, buka "Webhook Fields"
2. Cari dan checklist:
   - ✅ `messages`
3. Klik "Save"

## ✅ Step 8: Test Bot

### 8.1 Test via WhatsApp

1. Buka WhatsApp di phone Anda
2. Cari Business Account yang sudah dikonfigurasi
3. Kirim pesan test
4. Bot akan reply dengan respons dari Gemini AI

### 8.2 Test via API Endpoint

**Send Message:**
```bash
curl -X POST "http://localhost:8000/test/send-message?phone_number=62812345678&message=Hello%20World"
```

Response:
```json
{"success":true,"message_id":"wamid.xxx","phone_number":"62812345678"}
```

**Get Chat History:**
```bash
curl "http://localhost:8000/test/chat-history/62812345678"
```

Response:
```json
{
  "phone_number":"62812345678",
  "message_count":2,
  "messages":[...]
}
```

## 🐛 Troubleshooting

### ❌ Error: "Database connection refused"

**Solusi:**
- Pastikan PostgreSQL berjalan: `pg_isready -h localhost`
- Cek `DATABASE_URL` di `.env`
- Reset PostgreSQL service jika perlu

### ❌ Error: "Invalid verify token"

**Solusi:**
- Pastikan `WA_VERIFY_TOKEN` di `.env` sama dengan di Meta Dashboard
- Klik "Save" lagi di Meta Dashboard untuk confirm

### ❌ Bot tidak menerima pesan

**Solusi:**
1. Cek ngrok masih berjalan
2. Cek webhook URL di Meta Dashboard (harus "Active" dengan ✅)
3. Lihat logs di console untuk error messages
4. Test dengan curl: `curl http://localhost:8000/health`

### ❌ Error: "GEMINI_API_KEY is required"

**Solusi:**
- Pastikan `.env` file ada di root directory
- Pastikan `GEMINI_API_KEY` diisi dengan benar
- Restart bot setelah mengubah `.env`

## 📊 Monitoring & Logs

### View Logs Real-time
Logs akan ditampilkan di console saat bot berjalan:

```
2024-01-15 10:30:00,123 - main - INFO - Webhook request received
2024-01-15 10:30:01,456 - services.gemini - INFO - Gemini response generated
2024-01-15 10:30:02,789 - services.whatsapp - INFO - Message sent successfully
```

### Change Log Level

Edit `LOG_LEVEL` di `.env`:
- `DEBUG`: Detail info (for troubleshooting)
- `INFO`: General info (default)
- `WARNING`: Warnings only
- `ERROR`: Errors only

## 🚀 Production Deployment

Untuk deploy ke production server:

### 1. Setup di Server
```bash
# Clone repo
git clone <repository-url>
cd gemini-wa-bot

# Setup virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy dan edit .env
cp .env.example .env
# Edit .env dengan production credentials
```

### 2. Setup PostgreSQL di Server
```bash
# Install PostgreSQL
sudo apt-get install postgresql postgresql-contrib

# Create database dan user (lihat langkah 2)
```

### 3. Run dengan Systemd (Linux)

Buat file `/etc/systemd/system/gemini-wa-bot.service`:
```ini
[Unit]
Description=Gemini WhatsApp Bot
After=network.target

[Service]
Type=simple
User=bot
WorkingDirectory=/home/bot/gemini-wa-bot
ExecStart=/home/bot/gemini-wa-bot/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Jalankan:
```bash
sudo systemctl enable gemini-wa-bot
sudo systemctl start gemini-wa-bot
sudo systemctl status gemini-wa-bot
```

### 4. Setup Reverse Proxy (Nginx)

Edit `/etc/nginx/sites-available/default`:
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Reload nginx:
```bash
sudo systemctl reload nginx
```

### 5. Update Webhook URL di Meta Dashboard
Ubah webhook URL dari ngrok ke production URL:
```
https://yourdomain.com/webhook
```

## 📝 Checklist Setup

- [ ] Python 3.10+ terinstall
- [ ] PostgreSQL terinstall dan running
- [ ] Project di-clone dan dependencies terinstall
- [ ] Database dibuat dan schema diterapkan
- [ ] Google Gemini API key didapat
- [ ] WhatsApp Business Account credentials didapat
- [ ] `.env` file dikonfigurasi dengan benar
- [ ] Bot berjalan tanpa error di `localhost:8000`
- [ ] ngrok berjalan dan expose port 8000
- [ ] Webhook URL dikonfigurasi di Meta Dashboard
- [ ] Webhook verified dengan ✅ status
- [ ] Message events di-subscribe
- [ ] Test pesan berhasil dikirim dan dijawab oleh bot

---

Jika ada pertanyaan atau masalah, silakan check bagian **Troubleshooting** di README.md atau buka issue di repository.

**Happy botting! 🤖**
