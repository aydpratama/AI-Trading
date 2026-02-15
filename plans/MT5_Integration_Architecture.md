# MT5 Integration Architecture - Option 1: Full Backend Integration

## 📋 Overview

Menghubungkan aplikasi Next.js frontend dengan MetaTrader 5 (MT5) melalui Python backend menggunakan MetaTrader5 API dan WebSocket untuk real-time data streaming.

---

## 🏗️ System Architecture

```mermaid
graph TB
    subgraph "Frontend (Next.js)"
        A1[TradingTerminal] -->|WebSocket| B1[WebSocket Client]
        A2[ChartArea] -->|WebSocket| B1
        A3[AiSidebar] -->|WebSocket| B1
        B1 -->|REST API| C[Python Backend]
    end
    
    subgraph "Python Backend"
        C --> D[MetaTrader5 API]
        C --> E[WebSocket Server]
        C --> F[REST API Server]
        C --> G[AI Signal Engine]
        C --> H[Risk Manager]
        C --> I[Database PostgreSQL]
    end
    
    subgraph "MT5"
        D --> J[MetaTrader 5 Terminal]
    end
    
    subgraph "External Services"
        K[OpenAI API]
        L[Telegram Bot]
    end
    
    G --> K
    C --> L
    I -.-> J
```

---

## 📁 Project Structure

```
aitrading_v1/
├── backend/                          # Python Backend
│   ├── main.py                      # Entry point
│   ├── config.py                    # Configuration
│   ├── requirements.txt             # Dependencies
│   │
│   ├── mt5/                         # MT5 Integration
│   │   ├── connector.py             # MT5 Connection Manager
│   │   ├── position_manager.py      # Position Operations
│   │   ├── order_manager.py         # Order Operations
│   │   └── price_streamer.py        # Real-time Price Stream
│   │
│   ├── api/                         # REST API
│   │   ├── routes/
│   │   │   ├── positions.py         # Position endpoints
│   │   │   ├── orders.py            # Order endpoints
│   │   │   ├── signals.py           # AI Signal endpoints
│   │   │   └── market.py            # Market data endpoints
│   │   └── middleware.py            # Auth, Error handling
│   │
│   ├── websocket/                   # WebSocket Server
│   │   ├── server.py                # WebSocket server
│   │   ├── handlers.py              # Message handlers
│   │   └── subscriptions.py         # Client subscriptions
│   │
│   ├── ai/                          # AI Signal Engine
│   │   ├── signal_generator.py      # Generate trading signals
│   │   ├── pattern_recognition.py   # Technical pattern detection
│   │   ├── rsi_calculator.py        # RSI calculation
│   │   └── risk_scanner.py          # Risk analysis
│   │
│   ├── risk/                        # Risk Management
│   │   ├── position_limiter.py      # Max position size
│   │   ├── drawdown_limiter.py      # Drawdown protection
│   │   ├── equity_limiter.py        # Equity risk
│   │   └── correlation_checker.py   # Correlation risk
│   │
│   ├── models/                      # Database Models
│   │   ├── position.py
│   │   ├── trade.py
│   │   ├── signal.py
│   │   └── account.py
│   │
│   └── utils/                       # Utilities
│       ├── logger.py
│       └── helpers.py
│
├── prisma/
│   └── schema.prisma                 # Database schema (shared)
│
└── src/
    ├── components/
    │   ├── TradingTerminal.tsx       # Update to use WebSocket
    │   ├── ChartArea.tsx             # Update to use WebSocket
    │   └── AiSidebar.tsx             # Update to use WebSocket
    │
    ├── lib/
    │   ├── websocket.ts              # WebSocket client
    │   └── api.ts                    # REST API client
```

---

## 🔌 MT5 Integration Design

### 1. MT5 Connector ([`backend/mt5/connector.py`](backend/mt5/connector.py))

```python
class MT5Connector:
    """Manages MT5 connection and authentication"""
    
    def connect(self, login: int, password: str, server: str) -> bool
    def disconnect(self)
    def is_connected(self) -> bool
    def get_account_info(self) -> dict
    def get_symbol_info(self, symbol: str) -> dict
```

### 2. Position Manager ([`backend/mt5/position_manager.py`](backend/mt5/position_manager.py))

```python
class PositionManager:
    """Handles all position operations"""
    
    def get_all_positions() -> List[Position]
    def get_position_by_ticket(ticket: int) -> Position
    def open_position(symbol: str, type: str, volume: float, 
                      sl: float, tp: float) -> OrderTicket
    def close_position(ticket: int) -> bool
    def modify_position(ticket: int, sl: float, tp: float) -> bool
    def get_open_orders() -> List[Order]
```

### 3. Order Manager ([`backend/mt5/order_manager.py`](backend/mt5/order_manager.py))

```python
class OrderManager:
    """Handles order placement and management"""
    
    def place_limit_order(symbol: str, type: str, volume: float,
                          price: float, sl: float, tp: float) -> OrderTicket
    def place_stop_order(symbol: str, type: str, volume: float,
                         price: float, sl: float, tp: float) -> OrderTicket
    def cancel_order(ticket: int) -> bool
    def modify_order(ticket: int, sl: float, tp: float) -> bool
```

### 4. Price Streamer ([`backend/mt5/price_streamer.py`](backend/mt5/price_streamer.py))

```python
class PriceStreamer:
    """Streams real-time prices from MT5 via WebSocket"""
    
    def start_streaming(symbols: List[str])
    def stop_streaming()
    def get_current_prices() -> dict
    def get_candles(symbol: str, timeframe: str, count: int) -> List[Candle]
```

---

## 📡 WebSocket Server Design

### Server Structure ([`backend/websocket/server.py`](backend/websocket/server.py))

```python
class WebSocketServer:
    """WebSocket server for real-time data streaming"""
    
    # Events
    CONNECTED
    DISCONNECTED
    ERROR
    
    # Subscriptions
    SUBSCRIBE_PRICES
    SUBSCRIBE_POSITIONS
    SUBSCRIBE_SIGNALS
    SUBSCRIBE_MARKET_DATA
    
    # Actions
    REQUEST_POSITIONS
    REQUEST_SIGNALS
    REQUEST_MARKET_DATA
```

### Message Format

```typescript
// Client → Server
{
  "action": "SUBSCRIBE_PRICES",
  "symbols": ["BTCUSD", "EURUSD"]
}

// Server → Client
{
  "type": "PRICE_UPDATE",
  "data": {
    "symbol": "BTCUSD",
    "bid": 96540.50,
    "ask": 96541.00,
    "time": "2026-02-12T12:45:00Z"
  }
}

{
  "type": "POSITION_UPDATE",
  "data": {
    "ticket": 12345,
    "symbol": "BTCUSD",
    "type": "BUY",
    "volume": 0.1,
    "entry": 96500.00,
    "current": 96540.50,
    "pnl": 40.50,
    "profit": 0.50,
    "margin": 965.00
  }
}
```

---

## 🤖 AI Signal Engine Design

### Signal Generator ([`backend/ai/signal_generator.py`](backend/ai/signal_generator.py))

```python
class SignalGenerator:
    """Generates trading signals based on AI analysis"""
    
    def analyze_market(symbol: str, timeframe: str) -> Signal
    def generate_signals(symbols: List[str]) -> List[Signal]
    def get_confidence_score(signal: Signal) -> float
    def get_risk_reward_ratio(signal: Signal) -> float
    
    # Technical Indicators
    def calculate_rsi(candles: List[Candle]) -> float
    def detect_patterns(candles: List[Candle]) -> List[Pattern]
    def calculate_moving_averages(candles: List[Candle]) -> dict
```

### Signal Structure

```typescript
interface Signal {
  id: string;
  symbol: string;
  type: 'BUY' | 'SELL';
  confidence: number; // 0-100
  entry: number;
  sl: number;
  tp: number;
  risk_reward: number;
  timeframe: string;
  reason: string[];
  timestamp: Date;
  status: 'PENDING' | 'EXECUTED' | 'REJECTED';
}
```

---

## ⚠️ Risk Management System

### Position Limiter ([`backend/risk/position_limiter.py`](backend/risk/position_limiter.py))

```python
class PositionLimiter:
    """Limits position size based on risk parameters"""
    
    def calculate_max_volume(symbol: str, risk_percent: float) -> float
    def check_drawdown_limit(current_equity: float) -> bool
    def check_correlation_risk(positions: List[Position]) -> bool
    def check_account_risk(total_exposure: float) -> bool
```

### Risk Parameters

```python
RISK_CONFIG = {
    "max_position_size_percent": 2,  # Max 2% per trade
    "max_total_exposure_percent": 10, # Max 10% total exposure
    "max_daily_loss_percent": 5,      # Max 5% daily loss
    "max_drawdown_percent": 20,       # Max 20% drawdown
    "min_risk_reward": 1.5,           # Min 1.5:1 RR
    "max_positions": 10,              # Max open positions
}
```

---

## 🗄️ Database Schema (Prisma)

### Positions

```prisma
model Position {
  id        String   @id @default(uuid())
  ticket    Int      @unique
  symbol    String
  type      String   // BUY, SELL
  volume    Float
  entry     Float
  sl        Float?
  tp        Float?
  current   Float
  pnl       Float
  margin    Float
  profit    Float
  status    String   // OPEN, CLOSED
  openTime  DateTime
  closeTime DateTime?
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
}

model Trade {
  id        String   @id @default(uuid())
  ticket    Int      @unique
  symbol    String
  type      String
  volume    Float
  entry     Float
  exit      Float
  sl        Float?
  tp        Float?
  pnl       Float
  commission Float
  status    String   // CLOSED
  openTime  DateTime
  closeTime DateTime
  createdAt DateTime @default(now())
}

model Signal {
  id        String   @id @default(uuid())
  symbol    String
  type      String
  confidence Float
  entry     Float
  sl        Float
  tp        Float
  timeframe String
  reason    String[]
  status    String   // PENDING, EXECUTED, REJECTED
  executedAt DateTime?
  createdAt DateTime @default(now())
}

model Account {
  id        String   @id @default(uuid())
  login     Int      @unique
  balance   Float
  equity    Float
  margin    Float
  freeMargin Float
  profit    Float
  leverage  Int
  server    String
  lastUpdate DateTime @default(now())
}
```

---

## 🔐 API Endpoints

### Positions API

```
GET    /api/positions          - Get all positions
GET    /api/positions/:ticket  - Get specific position
POST   /api/positions/close    - Close position
POST   /api/positions/modify   - Modify position (SL/TP)
```

### Orders API

```
POST   /api/orders              - Place new order
POST   /api/orders/cancel      - Cancel order
POST   /api/orders/modify      - Modify order
```

### Signals API

```
GET    /api/signals            - Get all signals
GET    /api/signals/latest     - Get latest signals
GET    /api/signals/:symbol    - Get signals for symbol
POST   /api/signals/execute    - Execute signal
```

### Market API

```
GET    /api/market/prices      - Get current prices
GET    /api/market/candles     - Get historical candles
GET    /api/market/account     - Get account info
```

---

## 🚀 Implementation Roadmap

### Phase 1: Backend Setup (Week 1)
- [ ] Setup Python backend structure
- [ ] Install and configure MetaTrader5 library
- [ ] Create MT5 connection manager
- [ ] Create basic REST API endpoints

### Phase 2: Real-time Data (Week 2)
- [ ] Implement WebSocket server
- [ ] Implement price streaming from MT5
- [ ] Implement position updates
- [ ] Update frontend to use WebSocket

### Phase 3: Trade Management (Week 3)
- [ ] Implement position manager
- [ ] Implement order manager
- [ ] Add trade execution endpoints
- [ ] Add position modification endpoints

### Phase 4: AI Integration (Week 4)
- [ ] Implement signal generator
- [ ] Add technical indicators (RSI, MACD)
- [ ] Add pattern recognition
- [ ] Connect AI signals to UI

### Phase 5: Risk Management (Week 5)
- [ ] Implement position limiter
- [ ] Implement drawdown limiter
- [ ] Add risk checks before execution
- [ ] Add notification system

### Phase 6: Testing & Deployment (Week 6)
- [ ] Unit testing
- [ ] Integration testing
- [ ] Deploy backend server
- [ ] Deploy frontend

---

## 📦 Dependencies

### Python Dependencies ([`backend/requirements.txt`](backend/requirements.txt))

```
metaTrader5==5.0.34523
fastapi==0.104.1
uvicorn==0.24.0
websockets==12.0
pydantic==2.5.0
psycopg2-binary==2.9.9
sqlalchemy==2.0.23
python-dotenv==1.0.0
numpy==1.26.2
pandas==2.1.1
```

---

## 🔧 Configuration

### MT5 Connection ([`.env`](backend/.env))

```
MT5_LOGIN=123456
MT5_PASSWORD=your_password
MT5_SERVER=MetaQuotes-Demo
MT5_PATH=C:\Program Files\MetaTrader 5

# WebSocket
WS_HOST=0.0.0.0
WS_PORT=8765

# API
API_HOST=0.0.0.0
API_PORT=8000

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/aitrading
```

---

## 🎯 Key Features

1. **Real-time Data**: WebSocket streaming from MT5
2. **Auto-execution**: AI signals can auto-execute
3. **Trade Management**: Open, close, modify positions
4. **Risk Management**: Position size limits, drawdown protection
5. **AI Analysis**: Pattern recognition, RSI, MACD
6. **Multi-instrument**: Support for Forex, Crypto, Indices
7. **Multi-timeframe**: 1M, 5M, 15M, 1H, 4H, Daily

---

## 🔄 Data Flow

```mermaid
sequenceDiagram
    participant UI as Next.js Frontend
    participant WS as WebSocket Server
    participant MT5 as MT5 API
    participant AI as AI Signal Engine
    participant DB as Database

    UI->>WS: Subscribe to prices
    MT5->>WS: Push price updates
    WS->>UI: Send price updates
    
    UI->>WS: Request signals
    AI->>WS: Generate signals
    WS->>UI: Send signals
    
    UI->>WS: Execute signal
    WS->>MT5: Place order
    MT5->>WS: Order confirmation
    WS->>UI: Update position
```

---

## 📊 Comparison: Current vs Proposed

| Feature | Current | Proposed |
|---------|---------|----------|
| Price Data | Mock/TradingView | Real-time from MT5 |
| Positions | Mock | Real from MT5 |
| Signals | Mock | AI-generated from MT5 |
| Order Execution | UI only | Direct to MT5 |
| Risk Management | None | Full implementation |
| Database | None | PostgreSQL |

---

## 🚨 Important Notes

1. **MT5 Terminal Must Be Running**: The Python backend needs MT5 terminal open
2. **Account Credentials**: Store MT5 credentials securely (env variables)
3. **Risk Warning**: Always implement proper risk management
4. **Testing**: Test on demo account first before live trading
5. **Error Handling**: Implement robust error handling for MT5 disconnections
