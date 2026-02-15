# MT5 Local Development Setup Guide

## 📋 Overview

Setup MT5 integration untuk **Local Development** - Backend Python terhubung ke MT5 terminal yang berjalan di komputer Anda.

---

## 🎯 Prerequisites

### 1. MT5 Terminal
- **Download**: https://www.metatrader5.com/en/download
- **Install**: Windows, macOS, or Linux
- **Register**: Buat akun MetaQuotes (gratis)

### 2. Python 3.10+
- Download: https://www.python.org/downloads/
- Install dengan pilih "Add to PATH"

### 3. Database (PostgreSQL)
- Download: https://www.postgresql.org/download/
- Atau gunakan SQLite untuk testing

### 4. Email Account
- Gmail dengan App Password
- Atau email lain dengan SMTP

---

## 📦 Step-by-Step Setup

### Step 1: Install MT5 Terminal

1. Download MT5 dari website resmi
2. Install di komputer Anda
3. Buka MT5 terminal
4. Login dengan akun MetaQuotes Anda (atau broker)

**Demo Account Recommended:**
- Login: 100000
- Password: demo
- Server: MetaQuotes-Demo

---

### Step 2: Install Python Dependencies

Buka terminal/command prompt:

```bash
# Create backend directory
mkdir backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install metaTrader5==5.0.34523
pip install fastapi==0.104.1
pip install uvicorn==0.24.0
pip install websockets==12.0
pip install pydantic==2.5.0
pip install psycopg2-binary==2.9.9
pip install sqlalchemy==2.0.23
pip install python-dotenv==1.0.0
pip install numpy==1.26.2
pip install pandas==2.1.1
pip install python-telegram-bot==20.7
pip install python-multipart==0.0.6
pip install python-jose[cryptography]==3.3.0
pip install passlib[bcrypt]==1.7.4
```

---

### Step 3: Setup PostgreSQL Database

**Option A: Using PostgreSQL**

```bash
# Install PostgreSQL
# Windows: https://www.postgresql.org/download/windows/
# Download installer dan follow wizard

# Create database
# 1. Buka pgAdmin 4
# 2. Connect ke server
# 3. Right-click Databases → Create → Database
# 4. Name: aitrading_eurusd
# 5. Click Create

# Create user (optional)
# 1. Right-click Login/Role → Create → Login Role
# 2. Name: aitrading
# 3. Password: your_password
# 4. Set privileges
```

**Option B: Using SQLite (Easier)**

```bash
# SQLite already included in Python
# No installation needed!
```

---

### Step 4: Setup Telegram Bot

1. Buka Telegram dan cari **@BotFather**
2. Klik **Start**
3. Kirim `/newbot`
4. Pilih nama bot (contoh: "AITradingBot")
5. Pilih username (contoh: "AITradingBot")
6. Bot akan memberikan **Bot Token**
7. Chat dengan bot Anda untuk dapat **Chat ID**

**Get Chat ID:**
- Buka: https://api.telegram.org/bot<TOKEN>/getUpdates
- Lihat `id` di JSON response

---

### Step 5: Setup Email (Gmail)

1. Buka Google Account Settings
2. Security → 2-Step Verification → ON
3. Apps → Password → Generate
4. Copy **App Password** (contoh: `abcd efgh ijkl mnop`)
5. Gunakan app password ini di backend config

**Other Email Options:**
- Outlook: smtp.office365.com:587
- Yahoo: smtp.mail.yahoo.com:587
- SendGrid: smtp.sendgrid.net:587

---

### Step 6: Create Backend Files

Buat struktur directory:

```
backend/
├── main.py
├── config.py
├── requirements.txt
├── .env
├── mt5/
│   ├── connector.py
│   ├── position_manager.py
│   ├── order_manager.py
│   └── price_streamer.py
├── api/
│   ├── routes/
│   │   ├── positions.py
│   │   ├── orders.py
│   │   ├── signals.py
│   │   └── market.py
│   └── middleware.py
├── websocket/
│   ├── server.py
│   ├── handlers.py
│   └── subscriptions.py
├── ai/
│   ├── signal_generator.py
│   ├── rsi_calculator.py
│   ├── macd_calculator.py
│   ├── ma_calculator.py
│   ├── sr_detector.py
│   └── pattern_analyzer.py
├── risk/
│   ├── position_limiter.py
│   ├── drawdown_limiter.py
│   ├── exposure_limiter.py
│   └── eur_risk_manager.py
├── notification/
│   ├── telegram.py
│   ├── email.py
│   └── notification_manager.py
├── models/
│   ├── position.py
│   ├── trade.py
│   ├── signal.py
│   ├── account.py
│   └── performance.py
└── utils/
    ├── logger.py
    └── helpers.py
```

---

### Step 7: Create .env File

```env
# MT5 Connection
MT5_LOGIN=100000
MT5_PASSWORD=demo
MT5_SERVER=MetaQuotes-Demo
MT5_PATH=C:\Program Files\MetaTrader 5

# WebSocket
WS_HOST=0.0.0.0
WS_PORT=8765

# REST API
API_HOST=0.0.0.0
API_PORT=8000

# Database
DATABASE_URL=postgresql://aitrading:password@localhost:5432/aitrading_eurusd

# Telegram
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789

# Email
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

### Step 8: Create Basic MT5 Connector

**File: `backend/mt5/connector.py`**

```python
import MetaTrader5 as mt5
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class MT5Connector:
    """Manages MT5 connection"""

    def __init__(self):
        self.connected = False

    def connect(self, login: int, password: str, server: str, path: str) -> bool:
        """Connect to MT5 terminal"""
        try:
            # Initialize MT5
            if not mt5.initialize(path=path):
                logger.error(f"MT5 initialize failed: {mt5.last_error()}")
                return False

            # Login
            authorized = mt5.login(login, password, server)
            if not authorized:
                logger.error(f"MT5 login failed: {mt5.last_error()}")
                mt5.shutdown()
                return False

            self.connected = True
            logger.info(f"Connected to MT5: {login}@{server}")
            return True

        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False

    def disconnect(self):
        """Disconnect from MT5"""
        mt5.shutdown()
        self.connected = False
        logger.info("Disconnected from MT5")

    def is_connected(self) -> bool:
        """Check connection status"""
        return self.connected

    def get_account_info(self) -> dict:
        """Get account information"""
        if not self.connected:
            return {}

        account = mt5.account_info()
        if account is None:
            return {}

        return {
            "login": account.login,
            "balance": account.balance,
            "equity": account.equity,
            "margin": account.margin,
            "free_margin": account.margin_free,
            "profit": account.profit,
            "leverage": account.leverage,
            "server": account.server,
            "currency": account.currency
        }

    def get_symbol_info(self, symbol: str) -> dict:
        """Get symbol information"""
        if not self.connected:
            return {}

        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            return {}

        return {
            "name": symbol_info.name,
            "description": symbol_info.description,
            "digits": symbol_info.digits,
            "point": symbol_info.point,
            "trade_tick_size": symbol_info.trade_tick_size,
            "trade_tick_value": symbol_info.trade_tick_value,
            "trade_contract_size": symbol_info.trade_contract_size,
            "volume_min": symbol_info.volume_min,
            "volume_max": symbol_info.volume_max,
            "volume_step": symbol_info.volume_step,
            "spread": symbol_info.spread,
            "currency_base": symbol_info.currency_base,
            "currency_profit": symbol_info.currency_profit,
            "currency_margin": symbol_info.currency_margin,
            "price_precision": symbol_info.price_precision,
            "digits": symbol_info.digits
        }

# Singleton instance
connector = MT5Connector()
```

---

### Step 9: Create Main Entry Point

**File: `backend/main.py`**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv
import logging

from config import settings
from mt5.connector import connector

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AI Trading Backend",
    description="Backend untuk MT5 trading dengan AI signals",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/")
async def root():
    return {
        "status": "ok",
        "mt5_connected": connector.is_connected(),
        "version": "1.0.0"
    }

# Import and include routers
from api.routes import positions, orders, signals, market

app.include_router(positions.router, prefix="/api/positions", tags=["Positions"])
app.include_router(orders.router, prefix="/api/orders", tags=["Orders"])
app.include_router(signals.router, prefix="/api/signals", tags=["Signals"])
app.include_router(market.router, prefix="/api/market", tags=["Market"])

if __name__ == "__main__":
    # Connect to MT5 on startup
    if connector.connect(
        login=int(settings.MT5_LOGIN),
        password=settings.MT5_PASSWORD,
        server=settings.MT5_SERVER,
        path=settings.MT5_PATH
    ):
        logger.info("✅ Connected to MT5 successfully!")
    else:
        logger.error("❌ Failed to connect to MT5")

    # Start server
    uvicorn.run(
        "main:app",
        host=settings.WS_HOST,
        port=settings.API_PORT,
        reload=True
    )
```

---

### Step 10: Run Backend

```bash
# Activate virtual environment
venv\Scripts\activate

# Start backend
python main.py
```

**Expected Output:**
```
2026-02-12 14:00:00 - __main__ - INFO - Connected to MT5: 100000@MetaQuotes-Demo
2026-02-12 14:00:00 - __main__ - INFO - ✅ Connected to MT5 successfully!
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

### Step 11: Test Connection

1. Buka MT5 terminal
2. Login dengan akun demo
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

## 🔍 Troubleshooting

### Issue 1: MT5 Connection Failed

**Error:** `MT5 initialize failed`

**Solution:**
1. Pastikan MT5 terminal sudah terinstall
2. Pastikan path MT5 benar: `C:\Program Files\MetaTrader 5`
3. Cek MT5 sudah running atau tidak
4. Cek login/password/server benar

---

### Issue 2: Python Module Not Found

**Error:** `ModuleNotFoundError: No module named 'metaTrader5'`

**Solution:**
```bash
pip install metaTrader5
```

---

### Issue 3: Port Already in Use

**Error:** `Address already in use`

**Solution:**
```bash
# Windows: Cari dan matikan proses yang pakai port 8000
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Atau ganti port di .env
API_PORT=8001
```

---

### Issue 4: PostgreSQL Connection Failed

**Error:** `connection refused`

**Solution:**
1. Pastikan PostgreSQL sudah running
2. Cek DATABASE_URL di .env
3. Pastikan database sudah created

---

### Issue 5: Telegram Bot Not Working

**Error:** `Unauthorized`

**Solution:**
1. Cek bot token benar
2. Cek chat ID benar
3. Chat dengan bot dulu sebelum menggunakan

---

### Issue 6: Email Not Sending

**Error:** `SMTP authentication failed`

**Solution:**
1. Gunakan App Password (bukan password akun)
2. Cek SMTP server/port benar
3. Cek 2-Step Verification ON

---

## 📝 Checklist

- [ ] MT5 terminal installed dan running
- [ ] Python 3.10+ installed
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] PostgreSQL installed (atau SQLite)
- [ ] Database created
- [ ] Telegram bot created
- [ ] Email account setup
- [ ] .env file created
- [ ] Backend started successfully
- [ ] MT5 connection successful
- [ ] Health check endpoint working

---

## 🎯 Next Steps

Setelah setup selesai:

1. **Test MT5 Connection** - Verify data streaming works
2. **Test WebSocket** - Verify real-time updates
3. **Test AI Signals** - Generate dan test signals
4. **Test Manual Execution** - Execute order manual
5. **Test Notifications** - Verify Telegram/Email
6. **Test Database** - Verify data persistence

---

## 📞 Support

Jika ada masalah:
1. Cek log di terminal
2. Cek MT5 terminal status
3. Cek .env file configuration
4. Restart backend dan MT5

---

## 🔄 Reconnecting to MT5

Jika MT5 terputus:

```python
# Di backend
connector.disconnect()
connector.connect(
    login=int(settings.MT5_LOGIN),
    password=settings.MT5_PASSWORD,
    server=settings.MT5_SERVER,
    path=settings.MT5_PATH
)
```

---

## 💡 Tips

1. **Always keep MT5 running** - Backend butuh MT5 terkoneksi
2. **Use demo account first** - Test sebelum live trading
3. **Monitor logs** - Cek error di terminal
4. **Backup .env** - Jangan commit ke git
5. **Test frequently** - Test setiap fitur sebelum production

---

## 📚 Additional Resources

- MT5 API Docs: https://www.mql5.com/en/docs/metatrader5
- Python MetaTrader5: https://github.com/kjlotus/MetaTrader5-connector
- FastAPI Docs: https://fastapi.tiangolo.com/
- PostgreSQL: https://www.postgresql.org/docs/

---

## ✅ Success Criteria

Setelah setup selesai, Anda harus bisa:
- ✅ Connect ke MT5 dari backend
- ✅ Get real-time prices
- ✅ Get account info
- ✅ Get symbol info
- ✅ WebSocket connection successful
- ✅ Health check passing

Selamat! Backend sudah siap untuk development.
