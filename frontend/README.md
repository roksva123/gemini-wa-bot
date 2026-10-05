# Admin Panel - WhatsApp Bot Frontend

Production-ready Next.js admin panel untuk manajemen bot WhatsApp multi-klien.

## 🚀 Quick Start

```bash
# 1. Install dependencies
npm install

# 2. Setup environment
cp .env.example .env.local
# Edit .env.local dengan backend API URL

# 3. Run development server
npm run dev

# Admin panel akan berjalan di http://localhost:3000
```

## 📁 Project Structure

```
src/
├── app/                    # Next.js App Router pages
│   ├── (auth)/
│   │   └── login/         # Login page
│   ├── layout.tsx         # Root layout dengan sidebar
│   ├── page.tsx           # Dashboard
│   ├── pengaturan/        # Business settings
│   ├── percakapan/        # Conversations
│   ├── lead/              # Leads tracking
│   └── coba-bot/          # Test bot
├── components/            # Reusable components
│   ├── Sidebar.tsx        # Navigation sidebar
│   ├── ChatBubble.tsx     # Chat message bubble
│   ├── LoadingSkeleton.tsx # Loading state
│   └── Toast.tsx          # Notifications
├── lib/
│   ├── api.ts            # API client wrapper
│   └── store.ts          # Zustand state management
└── app/
    └── globals.css       # Global styles (Tailwind + dark mode)
```

## 🎨 Features

- ✅ **Dark Mode Support** — Automatic theme switching
- ✅ **Responsive Design** — Works on mobile (360px+) to desktop
- ✅ **JWT Authentication** — Secure login dengan token management
- ✅ **Real-time Updates** — Chat, leads, conversations live
- ✅ **Admin Panel Features:**
  - Business settings management
  - FAQ editor (add/edit/delete)
  - Conversation tracking + handoff mode
  - Lead management dengan status tracking
  - Test bot simulator
  - CSV export untuk leads

## 📦 Tech Stack

- **Next.js 14** — React framework dengan App Router
- **TypeScript** — Type safety
- **Tailwind CSS** — Styling + dark mode
- **Zustand** — Lightweight state management
- **js-cookie** — Secure token storage
- **Papa Parse** — CSV export

## 🔧 Environment Variables

```env
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
# atau production:
# NEXT_PUBLIC_API_URL=https://api.your-domain.com
```

## 📄 Pages

### 🔓 Login (`/login`)
- Email + password authentication
- Token stored securely dalam cookies
- Error messages yang jelas

### 📊 Dashboard (`/`)
- 3 metrics: Percakapan hari ini, Lead baru, Perlu admin
- Quick access links
- Links ke setup dan test bot

### ⚙️ Pengaturan (`/pengaturan`)
- Edit nama bisnis, kategori, gaya bahasa
- Manage jam operasional, alamat
- Konfigurasi alur pemesanan
- FAQ editor (add/edit/delete)

### 💬 Percakapan (`/percakapan`)
- Daftar percakapan dengan customer
- Detail chat dengan riwayat pesan
- Admin handoff mode
- Manual reply via WhatsApp

### 👥 Lead (`/lead`)
- Tabel calon customer
- Filter status (Baru, Follow-up, Selesai)
- Update status per lead
- CSV export

### 🤖 Coba Bot (`/coba-bot`)
- Simulasi chat dengan bot
- Test response sebelum go-live
- Berdasarkan FAQ & pengaturan yang sudah dibuat

## 🚀 Deployment

### Vercel (Recommended)

```bash
# 1. Push ke GitHub
git push origin main

# 2. Connect di Vercel
# - Buat project baru di vercel.com
# - Connect repository
# - Add environment variables: NEXT_PUBLIC_API_URL

# 3. Deploy!
# Otomatis deploy setiap push ke main
```

### Docker

```bash
# Build
docker build -t wa-bot-admin .

# Run
docker run -p 3000:3000 \
  -e NEXT_PUBLIC_API_URL=http://api:8000 \
  wa-bot-admin
```

### Manual VPS

```bash
# SSH ke server
ssh user@server

# Clone dan setup
git clone your-repo
cd wa-bot-admin
npm install
npm run build

# Run dengan PM2
npm install -g pm2
pm2 start npm --name "admin" -- start
pm2 save
pm2 startup
```

## 🧪 Testing

```bash
# Development dengan hot reload
npm run dev

# Type checking
npm run type-check

# Production build
npm run build

# Production server
npm start
```

## 🔐 Security

✅ **Implemented:**
- JWT token stored in secure httpOnly cookies
- CORS configured untuk backend API
- Input validation pada semua forms
- No sensitive data di localStorage

⚠️ **Best Practices:**
- Always use HTTPS di production
- Rotate JWT secret regularly
- Enable CSRF protection di Vercel/server
- Monitor API calls untuk abuse

## 🌐 API Integration

Frontend terhubung ke backend via `src/lib/api.ts`:

```typescript
// Auto-token management
api.setToken(token) // Store token
api.getToken()      // Retrieve token
api.clearToken()    // Logout

// API methods
await api.login(email, password)
await api.getBusiness()
await api.updateBusiness(data)
await api.getConversations()
await api.testChat(message)
// ... dan banyak lagi
```

Token automatically included di setiap request.

## 📱 Responsive Design

- **Mobile (360px+):** Full-width pages, collapsible sidebar
- **Tablet (768px+):** 2-column layouts
- **Desktop (1024px+):** Full sidebar + content
- **Dark Mode:** Automatic berdasarkan system preference

## 🐛 Troubleshooting

### API Connection Error
```
Error: Failed to connect to backend
```
✅ Solutions:
- Check `NEXT_PUBLIC_API_URL` di .env.local
- Verify backend running: `curl http://localhost:8000/health`
- Check CORS settings di backend

### Login Failed
- Verify email & password benar
- Check backend auth endpoint: `POST /api/auth/login`
- Clear cookies dan coba lagi

### Dark Mode Not Working
- Check browser support untuk `prefers-color-scheme`
- Manual toggle di sidebar (icon 🌙)

## 📚 Next Steps

1. **Connect Backend** — Update `NEXT_PUBLIC_API_URL`
2. **Test Login** — Create admin user via backend
3. **Setup Ngrok** — Expose local backend untuk WhatsApp webhook
4. **Go Live** — Deploy ke Vercel/Docker
5. **Monitor** — Setup error tracking (Sentry, etc)

## 📞 Support

- Backend API Docs: `http://localhost:8000/docs`
- Frontend Issues: Check console (F12)
- WhatsApp Integration: See backend README

---

**Status:** ✅ Production Ready  
**Version:** 1.0.0  
**Last Updated:** 2024
