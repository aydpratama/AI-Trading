# MT5 Configuration - Simplified (Telegram + SQLite)

## 📋 Your MT5 Account Details

| Parameter | Value |
|-----------|-------|
| Account Number | **22622639** |
| Password | **gaIG763268~** |
| Server | **Dupoin Futures Indonesia • Demo** |

---

## 📝 .env Configuration File

Copy ini ke `backend/.env`:

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

# Database - SQLite (No installation needed!)
DATABASE_URL=sqlite:///./aitrading.db

# Telegram (Required for notifications)
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789

# Risk Management
MAX_POSITION_SIZE_PERCENT=2
MAX_TOTAL_EXPOSURE_PERCENT=10
MAX_DAILY_LOSS_PERCENT=5
MIN_RISK_REWARD=1.5
MAX_OPEN_POSITIONS=5
```

---

## ✅ Simplified Setup

### 1. Setup Telegram Bot (Required)

1. Buka Telegram → cari **@BotFather**
2. Kirim `/newbot`
3. Pilih nama bot (contoh: "AITradingBot")
4. Pilih username (contoh: "AITradingBot")
5. Dapatkan **Bot Token**

**Get Chat ID:**
- Buka: https://api.telegram.org/bot<TOKEN>/getUpdates
- Lihat `id` di JSON response

### 2. Install Dependencies

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Start Backend

```bash
python main.py
```

---

## 📚 Documentation

- **Setup Guide**: [`plans/MT5_Local_Setup_Guide.md`](plans/MT5_Local_Setup_Guide.md)
- **Architecture**: [`plans/MT5_Integration_Architecture.md`](plans/MT5_Integration_Architecture.md)
- **Detailed Design**: [`plans/MT5_Detailed_Design.md`](plans/MT5_Detailed_Design.md)
