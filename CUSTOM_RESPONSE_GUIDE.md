# 📋 Custom Response Feature Guide

Dokumentasi lengkap untuk fitur Custom Response yang baru.

---

## 🎯 Apa Itu Custom Response?

**Custom Response** adalah fitur untuk menambahkan pesan khusus yang akan di-append ke respons AI berdasarkan nomor telepon pengirim.

### Skenario Penggunaan:
- User `62812345678` chat ke bot
- Bot respond dengan AI answer
- Bot cek database → ada custom data untuk nomor ini
- Bot append custom message dengan formatting kreatif
- Response gabungan dikirim ke user

---

## 🔧 Setup

### 1️⃣ Update Database
Custom response table sudah ditambahkan ke `schema.sql`. Jika menggunakan database baru, jalankan:

```bash
# Option A - Docker
docker-compose up -d
python main.py

# Option B - PostgreSQL lokal
psql -U postgres -f schema.sql
python main.py
```

Aplikasi akan auto-create table saat startup.

---

## 📡 API Endpoints

### 1️⃣ **GET** - Lihat Custom Response
```bash
curl http://localhost:8000/custom-response/62812345678
```

**Response:**
```json
{
  "phone_number": "62812345678",
  "found": true,
  "message": "Info khusus untuk user ini",
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:00"
}
```

---

### 2️⃣ **POST** - Tambah/Update Custom Response
```bash
curl -X POST "http://localhost:8000/custom-response?phone_number=62812345678&message=Halo+Budi!+Terima+kasih+sudah+berlangganan"
```

**Response:**
```json
{
  "success": true,
  "phone_number": "62812345678",
  "message": "Halo Budi! Terima kasih sudah berlangganan",
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:00"
}
```

---

### 3️⃣ **DELETE** - Hapus Custom Response
```bash
curl -X DELETE "http://localhost:8000/custom-response/62812345678"
```

**Response:**
```json
{
  "success": true,
  "message": "Custom response deleted successfully",
  "phone_number": "62812345678"
}
```

---

## 💬 Contoh Output di WhatsApp

### Tanpa Custom Response:
```
Halo! Apa yang bisa saya bantu?
Saya adalah asisten virtual berbasis AI...
```

### Dengan Custom Response:
```
🤖 *Respons AI*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Halo! Apa yang bisa saya bantu?
Saya adalah asisten virtual berbasis AI...

✨ *Info Khusus Untuk Anda* ✨
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Halo Budi! Selamat datang di program premium kami 🎉
Saldo kamu: Rp 500.000
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
```

---

## 🧪 Testing dengan cURL

### Test 1: Add Custom Response
```bash
curl -X POST "http://localhost:8000/custom-response?phone_number=62812345678&message=Info+khusus+untuk+user+premium"
```

### Test 2: Get Custom Response
```bash
curl http://localhost:8000/custom-response/62812345678
```

### Test 3: Send Message yang Trigger Custom Response
```bash
curl -X POST "http://localhost:8000/test/send-message?phone_number=62812345678&message=Halo+bot"
```

Bot akan:
1. Generate AI response
2. Lookup custom response dari `62812345678`
3. Format dengan emoji dan garis
4. Kirim gabungan response ke WhatsApp

### Test 4: Delete Custom Response
```bash
curl -X DELETE "http://localhost:8000/custom-response/62812345678"
```

---

## 📊 Database Schema

```sql
CREATE TABLE custom_responses (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🎨 Format Styling

Custom response di-format dengan creative elements:

```
🤖 = Bot indicator
━━━━ = Top separator (horizontal line)
✨ = Info section indicator
~~~~~~~~~~~~~~~~ = Bottom separator (tildes)
```

Bisa dikustomisasi di method `_format_with_custom_response()` di `services/message_handler.py`

---

## 🚀 Contoh Use Cases

### 1️⃣ VIP Member Welcome
```bash
curl -X POST "http://localhost:8000/custom-response?phone_number=62812345678&message=🎁+Status+VIP+Anda+Aktif%0ASaldo+Premium:+Rp+1.000.000%0ADiskon+Khusus:+30%25"
```

### 2️⃣ Business Info
```bash
curl -X POST "http://localhost:8000/custom-response?phone_number=62898765432&message=📱+Agen+Resmi+Toko+Elektronik%0AJam+Operasional:+09:00-21:00%0ALokasi:+Mall+Central+Lt+2"
```

### 3️⃣ Support Info
```bash
curl -X POST "http://localhost:8000/custom-response?phone_number=62811111111&message=💼+Tim+Support%0AWhatsApp+Support:+0812-9999-9999%0AEmail:+support@toko.com"
```

---

## ✅ Checklist Setup

- [ ] Database schema updated (auto-saat startup)
- [ ] Endpoints di main.py sudah ditambahkan
- [ ] DatabaseService methods sudah ada
- [ ] message_handler.py sudah include custom response lookup
- [ ] Bot running: `python main.py`
- [ ] Test POST endpoint untuk add custom response
- [ ] Test GET endpoint untuk verify data
- [ ] Kirim pesan dari WhatsApp dan lihat output dengan custom response

---

## 🔄 Flow Diagram

```
User Send Message (WhatsApp)
        ↓
Webhook menerima pesan
        ↓
message_handler.handle_incoming_message()
        ↓
Generate AI response (Gemini)
        ↓
Check: Ada custom response untuk nomor ini?
        ↓
    YES ←→ Format dengan emoji + lines + tildes
    NO  ←→ Use AI response only
        ↓
Kirim ke WhatsApp
```

---

## 📝 Notes

- Phone number format: tanpa `+` di depan (misal: `62812345678`, bukan `+62812345678`)
- Custom message bisa multiple line (gunakan `%0A` untuk line break di cURL)
- Satu phone number = satu custom response (UNIQUE constraint)
- Data disimpan di PostgreSQL, tidak di memory

---

**Need help?** Baca file dokumentasi lainnya atau cek logs dengan `docker-compose logs -f`
