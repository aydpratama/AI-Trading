# MT5 Integration - Detailed Design (EURUSD + 15M-1H + Day Trading)

## 🎯 Requirements Summary

| Parameter | Value |
|-----------|-------|
| Instrument | EURUSD (Forex) |
| Timeframe | 15M, 30M, 1H |
| Trading Style | Day Trading (4 jam sehari) |
| Risk Management | 2% per trade |
| Execution | Manual confirmation |
| Deployment | Local development |
| AI Indicators | RSI, MACD, MA, Support/Resistance |
| Notifications | Telegram + Email |
| Database | History trade storage |

---

## 📊 Technical Indicators Specification

### 1. RSI (Relative Strength Index)
```python
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
RSI_DIVERGENCE_THRESHOLD = 0.05
```

### 2. MACD (Moving Average Convergence Divergence)
```python
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
MACD_HISTOGRAM_THRESHOLD = 0.0001
```

### 3. Moving Averages
```python
EMA_9 = 9
EMA_21 = 21
EMA_50 = 50
MA_CROSSOVER_THRESHOLD = 0.0001
```

### 4. Support/Resistance
```python
SR_LEVELS_COUNT = 5
SR_REFRESH_RATE = 50  # Candles
```

---

## 🗄️ Database Schema (EURUSD Specific)

### Position Model
```prisma
model Position {
  id        String   @id @default(uuid())
  ticket    Int      @unique
  symbol    String   @default("EURUSD")
  type      String   // BUY, SELL
  volume    Float    // Lot size (min 0.01)
  entry     Float    // Entry price
  sl        Float?   // Stop loss
  tp        Float?   // Take profit
  current   Float    // Current price
  pnl       Float    // Profit/Loss
  margin    Float    // Margin used
  profit    Float    // Realized profit
  status    String   // OPEN, CLOSED
  openTime  DateTime
  closeTime DateTime?
  timeframe String   // 15M, 30M, 1H
  reason    String?  // Reason for entry
  confidence Float?  // Signal confidence
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
}
```

### Trade History Model
```prisma
model Trade {
  id        String   @id @default(uuid())
  ticket    Int      @unique
  symbol    String   @default("EURUSD")
  type      String
  volume    Float
  entry     Float
  exit      Float
  sl        Float?
  tp        Float?
  pnl       Float
  commission Float
  fees      Float
  status    String   // CLOSED
  openTime  DateTime
  closeTime DateTime
  timeframe String
  reason    String?
  confidence Float?
  notes     String?
  createdAt DateTime @default(now())
}
```

### Signal Model
```prisma
model Signal {
  id        String   @id @default(uuid())
  symbol    String   @default("EURUSD")
  type      String   // BUY, SELL
  timeframe String   // 15M, 30M, 1H
  entry     Float
  sl        Float
  tp        Float
  risk_reward Float
  confidence Float  // 0-100
  indicators {
    rsi        Float?
    macd       Float?
    ema_9      Float?
    ema_21     Float?
    ema_50     Float?
    macd_hist  Float?
  }
  support_resistance {
    resistance_1 Float?
    resistance_2 Float?
    support_1    Float?
    support_2    Float?
  }
  reason        String[]
  status        String   // PENDING, EXECUTED, REJECTED
  executedAt    DateTime?
  rejectedAt    DateTime?
  rejectionReason String?
  createdAt     DateTime @default(now())
}
```

### Account Model
```prisma
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

### Daily Performance Model
```prisma
model DailyPerformance {
  id        String   @id @default(uuid())
  date      DateTime @unique
  totalTrades   Int
  winTrades     Int
  lossTrades    Int
  winRate       Float
  totalPnl      Float
  maxDrawdown   Float
  maxProfit     Float
  avgRiskReward Float
  createdAt     DateTime @default(now())
}
```

---

## 🔔 Notification System Design

### Telegram Notification
```python
class TelegramNotifier:
    """Send notifications via Telegram Bot API"""

    def send_signal_notification(signal: Signal)
    def send_position_update(position: Position)
    def send_trade_closed(trade: Trade)
    def send_risk_alert(risk_type: str, message: str)
    def send_daily_summary(performance: DailyPerformance)

    # Signal Format
    """
    📊 EURUSD Signal (1H)
    ━━━━━━━━━━━━━━━━━━━
    Type: BUY
    Confidence: 85%
    Entry: 1.0850
    SL: 1.0820 | TP: 1.0890
    RR: 1:2.0
    ━━━━━━━━━━━━━━━━━━━
    RSI: 32.5 (Oversold)
    MACD: Bullish crossover
    EMA: EMA9 > EMA21
    """
```

### Email Notification
```python
class EmailNotifier:
    """Send notifications via SMTP"""

    def send_signal_email(signal: Signal)
    def send_position_update_email(position: Position)
    def send_trade_closed_email(trade: Trade)
    def send_daily_report_email(performance: DailyPerformance)
    def send_risk_alert_email(risk_type: str, message: str)

    # Email Format
    """
    Subject: EURUSD Signal - BUY @ 1.0850

    Dear Trader,

    New trading signal detected for EURUSD (1H):
    - Type: BUY
    - Entry: 1.0850
    - Stop Loss: 1.0820
    - Take Profit: 1.0890
    - Risk/Reward: 1:2.0
    - Confidence: 85%

    Technical Analysis:
    • RSI: 32.5 (Oversold)
    • MACD: Bullish crossover
    • EMA: EMA9 > EMA21

    Best regards,
    AI Trading System
    """
```

### Notification Configuration
```python
NOTIFICATION_CONFIG = {
    "telegram": {
        "enabled": True,
        "bot_token": "YOUR_BOT_TOKEN",
        "chat_id": "YOUR_CHAT_ID"
    },
    "email": {
        "enabled": True,
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "email": "your_email@gmail.com",
        "password": "your_app_password",
        "from_name": "AI Trading System"
    },
    "notifications": {
        "signal_new": True,        # New signal detected
        "signal_confirmed": True,  # Signal executed
        "position_update": True,   # Position PnL changes
        "trade_closed": True,      # Trade closed
        "daily_summary": True,     # Daily performance
        "risk_alert": True,        # Risk warnings
        "error_alert": True        # System errors
    }
}
```

---

## 🤖 AI Signal Generator (EURUSD Specific)

### Signal Generation Logic
```python
class EURUSDSignalGenerator:
    """Generate trading signals for EURUSD"""

    def generate_signals(timeframe: str) -> List[Signal]:
        # 1. Fetch latest candles
        candles = self.get_candles(timeframe, count=100)

        # 2. Calculate indicators
        rsi = self.calculate_rsi(candles)
        macd = self.calculate_macd(candles)
        ema_9 = self.calculate_ema(candles, 9)
        ema_21 = self.calculate_ema(candles, 21)
        ema_50 = self.calculate_ema(candles, 50)

        # 3. Detect support/resistance
        sr_levels = self.detect_support_resistance(candles)

        # 4. Analyze patterns
        patterns = self.analyze_patterns(candles)

        # 5. Generate signals
        signals = []

        # BUY Signal Conditions
        if (rsi < 30 and macd > 0 and
            ema_9 > ema_21 and
            ema_21 > ema_50 and
            sr_levels['support_1'] is not None):
            signal = self.create_signal(
                type='BUY',
                entry=calculate_entry(sr_levels['support_1']),
                sl=calculate_sl(signal.entry, 'BUY'),
                tp=calculate_tp(signal.entry, 'BUY'),
                indicators={...},
                support_resistance={...},
                reason=['RSI oversold', 'MACD bullish', 'EMA bullish']
            )
            signals.append(signal)

        # SELL Signal Conditions
        if (rsi > 70 and macd < 0 and
            ema_9 < ema_21 and
            ema_21 < ema_50 and
            sr_levels['resistance_1'] is not None):
            signal = self.create_signal(
                type='SELL',
                entry=calculate_entry(sr_levels['resistance_1']),
                sl=calculate_sl(signal.entry, 'SELL'),
                tp=calculate_tp(signal.entry, 'SELL'),
                indicators={...},
                support_resistance={...},
                reason=['RSI overbought', 'MACD bearish', 'EMA bearish']
            )
            signals.append(signal)

        return signals
```

### Signal Confidence Scoring
```python
def calculate_confidence(signal: Signal) -> float:
    """
    Confidence score based on indicator alignment
    Max: 100
    """
    score = 0

    # RSI alignment (0-30 points)
    if signal.indicators['rsi'] < 30:
        score += 15  # Strong oversold
    elif signal.indicators['rsi'] < 35:
        score += 10  # Moderate oversold
    elif signal.indicators['rsi'] > 70:
        score += 15  # Strong overbought
    elif signal.indicators['rsi'] > 65:
        score += 10  # Moderate overbought

    # MACD alignment (0-25 points)
    if signal.indicators['macd'] > 0:
        score += 12  # Bullish
    else:
        score += 12  # Bearish

    # EMA alignment (0-25 points)
    if signal.indicators['ema_9'] > signal.indicators['ema_21']:
        score += 12  # Bullish crossover
    elif signal.indicators['ema_9'] < signal.indicators['ema_21']:
        score += 12  # Bearish crossover

    # EMA trend (0-15 points)
    if signal.indicators['ema_21'] > signal.indicators['ema_50']:
        score += 15  # Uptrend
    elif signal.indicators['ema_21'] < signal.indicators['ema_50']:
        score += 15  # Downtrend

    # Support/Resistance alignment (0-15 points)
    if signal.support_resistance['support_1'] is not None:
        score += 15  # Near support
    if signal.support_resistance['resistance_1'] is not None:
        score += 15  # Near resistance

    return min(score, 100)
```

---

## ⚠️ Risk Management (EURUSD Specific)

### Position Sizing
```python
class EURUSDRiskManager:
    """Risk management for EURUSD trading"""

    # Configuration
    MAX_POSITION_SIZE_PERCENT = 2  # Max 2% per trade
    MAX_TOTAL_EXPOSURE_PERCENT = 10  # Max 10% total exposure
    MAX_DAILY_LOSS_PERCENT = 5  # Max 5% daily loss
    MIN_RISK_REWARD = 1.5  # Min 1.5:1 RR
    MAX_OPEN_POSITIONS = 5

    def calculate_max_volume(self, entry: float, sl: float) -> float:
        """
        Calculate max lot size based on account balance
        Formula: (Balance * RiskPercent) / (SL in pips * ContractSize)
        """
        balance = self.get_account_balance()
        risk_amount = balance * self.MAX_POSITION_SIZE_PERCENT / 100
        sl_pips = abs(entry - sl) * 100000  # EURUSD 5 decimal places
        contract_size = 100000

        max_volume = risk_amount / (sl_pips * contract_size)
        return round(max_volume, 2)  # Min 0.01 lot

    def check_daily_loss_limit(self, current_pnl: float) -> bool:
        """Check if daily loss limit is exceeded"""
        daily_pnl = self.get_daily_pnl()
        return (daily_pnl + current_pnl) < (self.MAX_DAILY_LOSS_PERCENT / 100 * self.get_account_balance())

    def check_total_exposure(self, new_position: Position) -> bool:
        """Check if total exposure limit is exceeded"""
        total_exposure = self.get_total_exposure()
        new_exposure = new_position.volume * new_position.entry
        return (total_exposure + new_exposure) < (self.MAX_TOTAL_EXPOSURE_PERCENT / 100 * self.get_account_balance())

    def validate_signal(self, signal: Signal) -> bool:
        """Validate signal before execution"""
        # Check RR ratio
        if signal.risk_reward < self.MIN_RISK_REWARD:
            return False

        # Check position size
        max_volume = self.calculate_max_volume(signal.entry, signal.sl)
        if signal.volume > max_volume:
            return False

        # Check daily loss limit
        if not self.check_daily_loss_limit(0):
            return False

        # Check total exposure
        if not self.check_total_exposure(signal):
            return False

        # Check open positions limit
        if len(self.get_open_positions()) >= self.MAX_OPEN_POSITIONS:
            return False

        return True
```

### Risk Parameters (Config)
```python
EURUSD_RISK_CONFIG = {
    "symbol": "EURUSD",
    "max_position_size_percent": 2,
    "max_total_exposure_percent": 10,
    "max_daily_loss_percent": 5,
    "min_risk_reward": 1.5,
    "max_open_positions": 5,
    "stop_loss_percent": 0.003,  # 0.3% SL
    "take_profit_percent": 0.006,  # 0.6% TP (1:2 RR)
    "max_slippage": 0.0002,  # Max 0.2 pips slippage
}
```

---

## 📡 WebSocket Message Format (EURUSD)

### Client → Server
```typescript
// Subscribe to EURUSD prices
{
  "action": "SUBSCRIBE_PRICES",
  "symbols": ["EURUSD"],
  "timeframes": ["15M", "30M", "1H"]
}

// Request signals
{
  "action": "REQUEST_SIGNALS",
  "symbol": "EURUSD",
  "timeframe": "1H"
}

// Execute signal manually
{
  "action": "EXECUTE_SIGNAL",
  "signal_id": "uuid",
  "volume": 0.1,
  "sl": 1.0820,
  "tp": 1.0890
}
```

### Server → Client
```typescript
// Price update
{
  "type": "PRICE_UPDATE",
  "data": {
    "symbol": "EURUSD",
    "bid": 1.08542,
    "ask": 1.08545,
    "spread": 3,
    "time": "2026-02-12T13:30:00Z"
  }
}

// Signal generated
{
  "type": "SIGNAL_NEW",
  "data": {
    "id": "uuid",
    "symbol": "EURUSD",
    "type": "BUY",
    "timeframe": "1H",
    "entry": 1.0850,
    "sl": 1.0820,
    "tp": 1.0890,
    "risk_reward": 2.0,
    "confidence": 85,
    "indicators": {
      "rsi": 32.5,
      "macd": 0.00015,
      "ema_9": 1.0848,
      "ema_21": 1.0845,
      "ema_50": 1.0830
    },
    "support_resistance": {
      "resistance_1": 1.0890,
      "resistance_2": 1.0920,
      "support_1": 1.0820,
      "support_2": 1.0790
    },
    "reason": ["RSI oversold (32.5)", "MACD bullish crossover", "EMA bullish alignment"],
    "timestamp": "2026-02-12T13:30:00Z"
  }
}

// Position update
{
  "type": "POSITION_UPDATE",
  "data": {
    "ticket": 123456,
    "symbol": "EURUSD",
    "type": "BUY",
    "volume": 0.1,
    "entry": 1.0850,
    "current": 1.08542,
    "sl": 1.0820,
    "tp": 1.0890,
    "pnl": 42.00,
    "profit": 0.42,
    "margin": 108.50,
    "status": "OPEN",
    "timeframe": "1H",
    "confidence": 85,
    "reason": ["RSI oversold", "MACD bullish", "EMA bullish"]
  }
}
```

---

## 🔄 Data Flow Diagram

```mermaid
sequenceDiagram
    participant MT5 as MT5 Terminal
    participant Backend as Python Backend
    participant WS as WebSocket Server
    participant DB as Database
    participant TG as Telegram
    participant Email as Email Service
    participant UI as Next.js UI

    Note over MT5,UI: EURUSD Trading (15M-1H)

    MT5->>Backend: Real-time price updates
    Backend->>WS: Push prices to clients
    WS->>UI: Send price updates

    Backend->>DB: Save account info
    Backend->>TG: Send signal notification
    Backend->>Email: Send signal email
    UI->>WS: Request signals (1H)
    Backend->>WS: Generate EURUSD signals
    WS->>UI: Send signals with indicators

    UI->>WS: Execute signal (manual)
    WS->>Backend: Execute order
    Backend->>MT5: Place order
    MT5->>Backend: Order confirmation
    Backend->>DB: Save position
    Backend->>TG: Send position update
    Backend->>Email: Send position update
    WS->>UI: Send position update

    MT5->>Backend: Position closed
    Backend->>DB: Save trade history
    Backend->>TG: Send trade closed
    Backend->>Email: Send trade closed
    WS->>UI: Send trade closed
```

---

## 📦 Python Backend Structure (EURUSD)

```
backend/
├── main.py                      # Entry point
├── config.py                    # Configuration
├── requirements.txt             # Dependencies
│
├── mt5/                         # MT5 Integration
│   ├── connector.py             # MT5 Connection
│   ├── position_manager.py      # Position Operations
│   ├── order_manager.py         # Order Operations
│   └── price_streamer.py        # Real-time Prices
│
├── api/                         # REST API
│   ├── routes/
│   │   ├── positions.py         # Position endpoints
│   │   ├── orders.py            # Order endpoints
│   │   ├── signals.py           # Signal endpoints
│   │   └── market.py            # Market data
│   └── middleware.py            # Auth, Error
│
├── websocket/                   # WebSocket Server
│   ├── server.py                # WebSocket server
│   ├── handlers.py              # Message handlers
│   └── subscriptions.py         # Client subscriptions
│
├── ai/                          # AI Signal Engine
│   ├── signal_generator.py      # Generate EURUSD signals
│   ├── rsi_calculator.py        # RSI calculation
│   ├── macd_calculator.py       # MACD calculation
│   ├── ma_calculator.py         # MA calculation
│   ├── sr_detector.py           # Support/Resistance
│   └── pattern_analyzer.py      # Pattern analysis
│
├── risk/                        # Risk Management
│   ├── position_limiter.py      # Position sizing
│   ├── drawdown_limiter.py      # Drawdown protection
│   ├── exposure_limiter.py      # Exposure limit
│   └── eur_risk_manager.py      # EURUSD specific
│
├── notification/                # Notifications
│   ├── telegram.py              # Telegram notifier
│   ├── email.py                 # Email notifier
│   └── notification_manager.py  # Manager
│
├── models/                      # Database Models
│   ├── position.py
│   ├── trade.py
│   ├── signal.py
│   ├── account.py
│   └── performance.py
│
└── utils/                       # Utilities
    ├── logger.py
    └── helpers.py
```

---

## 🚀 Implementation Roadmap (EURUSD Specific)

### Phase 1: Backend Setup (Week 1)
- [ ] Setup Python backend structure
- [ ] Install MetaTrader5 library
- [ ] Create MT5 connector for EURUSD
- [ ] Create basic REST API endpoints
- [ ] Setup PostgreSQL database

### Phase 2: Real-time Data (Week 2)
- [ ] Implement WebSocket server
- [ ] Implement price streaming for EURUSD
- [ ] Implement position updates
- [ ] Update frontend to use WebSocket
- [ ] Test price accuracy

### Phase 3: Trade Management (Week 3)
- [ ] Implement position manager
- [ ] Implement order manager
- [ ] Add trade execution endpoints
- [ ] Add position modification endpoints
- [ ] Test manual order execution

### Phase 4: AI Signals (Week 4)
- [ ] Implement RSI calculator
- [ ] Implement MACD calculator
- [ ] Implement MA calculator
- [ ] Implement Support/Resistance detector
- [ ] Implement signal generator for EURUSD
- [ ] Add confidence scoring
- [ ] Connect AI signals to UI

### Phase 5: Notifications (Week 5)
- [ ] Setup Telegram bot
- [ ] Setup Email service
- [ ] Implement notification manager
- [ ] Add signal notifications
- [ ] Add position update notifications
- [ ] Add trade closed notifications
- [ ] Add daily summary notifications

### Phase 6: Risk Management (Week 6)
- [ ] Implement position limiter
- [ ] Implement drawdown limiter
- [ ] Implement exposure limiter
- [ ] Add risk checks before execution
- [ ] Add risk alerts

### Phase 7: Database & History (Week 7)
- [ ] Implement position model
- [ ] Implement trade history model
- [ ] Implement signal model
- [ ] Implement account model
- [ ] Implement daily performance model
- [ ] Add data persistence
- [ ] Add trade history queries

### Phase 8: Testing & Deployment (Week 8)
- [ ] Unit testing
- [ ] Integration testing
- [ ] Test on demo account
- [ ] Deploy backend server
- [ ] Deploy frontend
- [ ] Final testing

---

## 🔧 Configuration Files

### .env (EURUSD)
```
# MT5 Connection
MT5_LOGIN=123456
MT5_PASSWORD=your_password
MT5_SERVER=MetaQuotes-Demo
MT5_PATH=C:\Program Files\MetaTrader 5

# WebSocket
WS_HOST=0.0.0.0
WS_PORT=8765

# REST API
API_HOST=0.0.0.0
API_PORT=8000

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/aitrading_eurusd

# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Email
EMAIL_ENABLED=true
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_FROM=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_FROM_NAME=AI Trading System

# Risk Management
MAX_POSITION_SIZE_PERCENT=2
MAX_TOTAL_EXPOSURE_PERCENT=10
MAX_DAILY_LOSS_PERCENT=5
MIN_RISK_REWARD=1.5
MAX_OPEN_POSITIONS=5
```

### requirements.txt
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
python-telegram-bot==20.7
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
```

---

## 📊 Frontend Updates Required

### 1. TradingTerminal.tsx
- Replace mock positions with WebSocket data
- Show real PnL from MT5
- Display signal confidence

### 2. AiSidebar.tsx
- Replace mock signals with real signals from backend
- Show technical indicators (RSI, MACD, MA)
- Show Support/Resistance levels

### 3. ChartArea.tsx
- Use MT5 real-time prices
- Show RSI indicator from backend
- Show Support/Resistance lines

### 4. New Components Needed
- SignalDetailModal.tsx - Show detailed signal analysis
- RiskMonitor.tsx - Show current risk exposure
- NotificationPanel.tsx - Show recent notifications

---

## 🎯 Key Metrics to Track

| Metric | Target |
|--------|--------|
| Win Rate | 55-60% |
| Average Risk/Reward | 1.5:1 - 2.0:1 |
| Max Drawdown | < 5% |
| Daily Loss Limit | 5% |
| Max Positions | 5 |
| Signal Confidence | > 70% |

---

## ⚠️ Important Notes

1. **MT5 Terminal Must Be Running**: Backend needs MT5 terminal open
2. **Demo Account First**: Test thoroughly on demo before live
3. **Risk Management**: Always use SL and TP
4. **Telegram Bot**: Create bot at @BotFather
5. **Email Password**: Use App Password, not account password
6. **Database**: PostgreSQL recommended for reliability
7. **Local Testing**: Can run both on same machine

---

## 📞 Support & Troubleshooting

### Common Issues
1. **MT5 Connection Failed**: Check MT5 terminal is running
2. **WebSocket Connection Failed**: Check firewall settings
3. **Telegram Not Working**: Verify bot token and chat ID
4. **Email Not Working**: Check SMTP credentials
5. **Price Not Updating**: Check MT5 terminal settings

---

## 📝 Summary

This design provides a complete solution for **EURUSD Day Trading** with:
- Real-time data from MT5
- AI signal generation with RSI, MACD, MA, Support/Resistance
- Manual execution with confirmation
- Telegram + Email notifications
- Comprehensive risk management
- Complete trade history tracking
- 8-week implementation roadmap

The system is designed for **local development** with flexibility to scale to VPS if needed.
