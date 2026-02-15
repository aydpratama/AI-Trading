# AI Trading Backend - MT5 Integration

Backend untuk trading dengan MetaTrader 5 (MT5) dan AI signals via Telegram.

## 🎯 Features

- **Real-time MT5 Connection** - Connect ke MT5 terminal
- **AI Signal Generation** - RSI, MACD, EMA, Support/Resistance
- **Telegram Notifications** - Signal alerts, position updates
- **REST API** - API endpoints untuk frontend
- **SQLite Database** - Trade history dan signals

## 📋 Requirements

- Python 3.10+
- MT5 Terminal installed
- Telegram Bot Token

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Setup Environment

Copy `.env.example` ke `.env` dan edit:

```bash
cp .env.example .env
```

Edit `.env` dengan credentials MT5 dan Telegram bot token.

### 3. Start Backend

```bash
python main.py
```

## 📁 Structure

```
backend/
├── main.py                      # Entry point
├── config.py                    # Configuration
├── requirements.txt             # Dependencies
├── .env.example                 # Environment template
├── .env                         # Environment variables
│
├── mt5/                         # MT5 Integration
│   ├── connector.py             # MT5 Connection Manager
│   ├── position_manager.py      # Position Operations
│   └── order_manager.py         # Order Operations
│
├── api/                         # REST API
│   ├── routes/
│   │   ├── market.py            # Market data endpoints
│   │   ├── positions.py         # Position endpoints
│   │   ├── orders.py            # Order endpoints
│   │   └── signals.py           # Signal endpoints
│   └── __init__.py
│
├── ai/                          # AI Signal Engine
│   ├── signal_generator.py      # Generate signals
│   ├── rsi_calculator.py        # RSI calculation
│   ├── macd_calculator.py       # MACD calculation
│   ├── ma_calculator.py         # MA calculation
│   └── sr_detector.py           # Support/Resistance detection
│
├── notification/                # Telegram Notifications
│   └── telegram.py              # Telegram notifier
│
├── models/                      # Database Models
│   ├── base.py                  # Base model
│   ├── position.py              # Position model
│   ├── trade.py                 # Trade history model
│   ├── signal.py                # Signal model
│   └── account.py               # Account model
│
└── database.py                  # Database connection
```

## 🔌 API Endpoints

### Market
- `GET /api/market/health` - Health check
- `GET /api/market/prices` - Get current prices
- `GET /api/market/candles` - Get historical candles
- `GET /api/market/symbols` - Get available symbols
- `GET /api/market/account` - Get account info
- `GET /api/market/signals` - Get AI signals

### Positions
- `GET /api/positions` - Get all positions
- `GET /api/positions/{ticket}` - Get position by ticket
- `POST /api/positions/open` - Open new position
- `POST /api/positions/close/{ticket}` - Close position
- `POST /api/positions/modify/{ticket}` - Modify SL/TP

### Orders
- `POST /api/orders/limit` - Place limit order
- `POST /api/orders/stop` - Place stop order
- `DELETE /api/orders/{ticket}` - Cancel order
- `GET /api/orders` - Get open orders

### Signals
- `GET /api/signals` - Get AI signals

## 📊 Technical Indicators

- **RSI (14)** - Overbought/Oversold detection
- **MACD (12, 26, 9)** - Trend & momentum
- **EMA (9, 21, 50)** - Trend direction
- **Support/Resistance** - Key levels

## ⚠️ Risk Management

- Max 2% per trade
- Max 10% total exposure
- Max 5% daily loss
- Min 1.5:1 Risk/Reward
- Max 5 open positions

## 📝 Configuration

### MT5 Connection
```
MT5_LOGIN=22622639
MT5_PASSWORD=your_password
MT5_SERVER=Dupoin Futures Indonesia • Demo
MT5_PATH=C:\Program Files\MetaTrader 5
```

### Telegram
```
TELEGRAM_BOT_TOKEN=123456789:ABCdef...
TELEGRAM_CHAT_ID=123456789
```

## 🚀 Usage

### Generate Signals
```bash
curl http://localhost:8000/api/signals?symbol=EURUSD&timeframe=1H
```

### Get Positions
```bash
curl http://localhost:8000/api/positions
```

### Open Position
```bash
curl -X POST http://localhost:8000/api/positions/open \
  -d "symbol=EURUSD" \
  -d "trade_type=BUY" \
  -d "volume=0.1"
```

## 📚 Documentation

- Architecture: [`plans/MT5_Integration_Architecture.md`](../plans/MT5_Integration_Architecture.md)
- Detailed Design: [`plans/MT5_Detailed_Design.md`](../plans/MT5_Detailed_Design.md)
- Setup Guide: [`plans/MT5_Local_Setup_Guide.md`](../plans/MT5_Local_Setup_Guide.md)
- Configuration: [`plans/MT5_Config_Simple.md`](../plans/MT5_Config_Simple.md)

## 📞 Support

Jika ada masalah:
1. Cek log di terminal
2. Pastikan MT5 terminal sudah running
3. Cek .env file configuration
4. Restart backend dan MT5
