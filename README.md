# WarungTech

Platform digital terintegrasi untuk pemilik warung dan UMKM Indonesia. Menggabungkan manajemen toko, pembayaran digital, e-kupon berbasis blockchain, investasi kripto, dan asisten AI dalam satu ekosistem.

---

## Struktur Proyek

```
WarungTechFix/
├── WarTechUIRevision1/     # Aplikasi mobile (React Native / Expo)
├── WarungTechAPI/          # Backend REST API (Node.js / Express)
├── WarungTechAI/           # AI Chatbot Server (Python / LangChain)
├── WartechAPI2/            # API versi alternatif
├── smart-contract-wartech/ # Smart contract (Solidity / Hardhat ZKsync)
└── wartechweb3/            # Smart contract Web3 (Hardhat ZKsync)
```

---

## Fitur Utama

### Mobile App (WarTechUIRevision1)
- Autentikasi pengguna (login & registrasi)
- Dashboard wallet & riwayat transaksi
- **Bayar** — pembayaran via Midtrans (QRIS, transfer, kartu) dan on-chain (MetaMask)
- **Promo** — e-kupon berbasis smart contract, generate & share QR/barcode via WhatsApp
- **Invest** — analisis harga kripto real-time
- **Aktivitas** — log semua transaksi dan aktivitas
- **Profil** — manajemen akun pengguna
- AI Chatbot terintegrasi untuk bantuan pengguna

### Backend API (WarungTechAPI)
- REST API dengan Express.js + PostgreSQL (Supabase)
- JWT Authentication
- Manajemen toko, produk, dan pesanan
- Integrasi Midtrans payment gateway
- Wallet & saldo pengguna
- Business analytics dashboard
- Deploy ke Vercel

### AI Assistant (WarungTechAI)
- Chatbot berbasis LangChain + LangGraph
- Menggunakan OpenRouter API (LLM)
- Konteks bisnis warung & UMKM
- REST API dengan Flask
- Riwayat percakapan per pengguna

### Smart Contract
- Solidity contract untuk e-kupon (ERC-based)
- Deploy di jaringan ZKsync
- Integrasi dengan MetaMask di mobile app

---

## Tech Stack

| Layer | Teknologi |
|---|---|
| Mobile | React Native, Expo, NativeWind (Tailwind), TypeScript |
| Backend | Node.js, Express.js, PostgreSQL, JWT, Midtrans |
| AI | Python, Flask, LangChain, LangGraph, OpenRouter |
| Blockchain | Solidity, Hardhat, ZKsync, ethers.js, MetaMask |
| Deploy | Vercel (API), Expo (Mobile) |

---

## Setup

### Mobile App
```bash
cd WarTechUIRevision1
npm install
npx expo start
```

### Backend API
```bash
cd WarungTechAPI
cp src/.env.example .env
# isi nilai di .env
npm install
node src/server.js
```

### AI Server
```bash
cd WarungTechAI
cp .env.example .env
# isi OPENROUTER_API_KEY di .env
pip install -r requirements.txt
python start_ai_server.py
```

---

## Environment Variables

### WarungTechAPI `.env`
```env
DB_HOST=
DB_PORT=5432
DB_NAME=postgres
DB_USER=
DB_PASSWORD=
JWT_SECRET=
MIDTRANS_SERVER_KEY=
MIDTRANS_CLIENT_KEY=
MIDTRANS_IS_PRODUCTION=false
PORT=3001
```

### WarungTechAI `.env`
```env
OPENROUTER_API_KEY=
INFURA_PROJECT_ID=
FLASK_ENV=development
```

### WarTechUIRevision1 `.env`
```env
EXPO_PUBLIC_THIRDWEB_CLIENT_ID=
THIRDWEB_SECRET_KEY=
```

---

## API Base URL

Production: `https://war-tech-backend-k6hg.vercel.app/api`

---

## Lisensi

Private — WarungTech © 2025
