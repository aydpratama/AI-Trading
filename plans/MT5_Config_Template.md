# MT5 Configuration Template - Your Credentials

## 📋 Your MT5 Account Details

| Parameter | Value |
|-----------|-------|
| Account Number | **22622639** |
| Password | **gaIG763268~** |
| Server | **Dupoin Futures Indonesia • Demo** |

---

## 📝 .env Configuration File

Copy this file ke `backend/.env`:

```env
# MT5 Connection
MT5_LOGIN=22622639
MT5_PASSWORD=gaIG763268~
MT5_SERVER=Dupoin Futures Indonesia • Demo
MT5_PATH=C:\Program Files\MetaTrader 5

# WebSocket
WS_HOST=0.0.0.0
WS_PORT=8765

# REST API
API_HOST=0.0.0.0
API_PORT=8000

# Database
DATABASE_URL=postgresql://aitrading:password@localhost:5432/aitrading_eurusd

# Telegram (Setelah buat bot)
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789

# Email (Setelah setup Gmail)
EMAIL_ENABLED=true
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_FROM=your_email@gmail.com
EMAIL_PASSWORD=abcd efgh ijkl mnop
EMAIL_FROM_NAME=AI Trading System

# Risk Management
MAX_POSITION_SIZE_PERCENT=2
MAX_TOTAL_EXPOSURE_PERCENT=10
MAX_DAILY_LOSS_PERCENT=5
MIN_RISK_REWARD=1.5
MAX_OPEN_POSITIONS=5
```

---

## 🔧 Next Steps

### 1. Setup Telegram Bot (Required for Notifications)

1. Buka Telegram → cari **@BotFather**
2. Kirim `/newbot`
3. Pilih nama bot (contoh: "AITradingBot")
4. Pilih username (contoh: "AITradingBot")
5. Dapatkan **Bot Token**

**Get Chat ID:**
- Buka: https://api.telegram.org/bot<TOKEN>/getUpdates
- Lihat `id` di JSON response

### 2. Setup Email (Optional but Recommended)

1. Google Account → Security → 2-Step Verification
2. Apps → Password → Generate
3. Copy **App Password**
4. Gunakan di .env

### 3. Create Database

**Option A: PostgreSQL**
```
1. Install PostgreSQL
2. Buka pgAdmin
3. Create database: aitrading_eurusd
4. Create user: aitrading
5. Set password
```

**Option B: SQLite (Easier)**
```
1. No installation needed!
2. Database akan otomatis created
```

### 4. Install Dependencies

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 5. Start Backend

```bash
python main.py
```

---

## ✅ Verification

Setelah setup selesai, test connection:

1. Buka MT5 terminal
2. Login dengan akun demo Anda
3. Pastikan EURUSD ada di chart
4. Start backend
5. Buka browser: http://localhost:8000/

**Expected Response:**
```json
{
  "status": "ok",
  "mt5_connected": true,
  "version": "1.0.0"
}
```

---

## 📚 Resources

- Setup Guide: [`plans/MT5_Local_Setup_Guide.md`](plans/MT5_Local_Setup_Guide.md)
- Architecture: [`plans/MT5_Integration_Architecture.md`](plans/MT5_Integration_Architecture.md)
- Detailed Design: [`plans/MT5_Detailed_Design.md`](plans/MT5_Detailed_Design.md)
