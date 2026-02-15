# AI Trading Platform - UI Architecture Documentation

## 1. Overview
This document outlines the User Interface structure and component hierarchy for the AI Trading Dashboard (`aitrading_v1`). The application is a single-page React application built with Next.js 15, utilizing Tailwind CSS for styling and Lucide React for iconography.

**Core Philosophy:** 
- **High Contrast & Clarity:** Emphasis on pure white text in dark mode for readability.
- **Data Density:** Dashboard layout maximizing screen real estate (Chart + Sidebar + Terminal).
- **Interactive Feedback:** Immediate visual response (Toasts) for user actions.

## 2. Component Hierarchy

### `src/app/page.tsx` (Main Layout Controller)
The central hub managing global state and layout composition.
- **State Managed:**
  - `isSidebarOpen`: Toggles AiSidebar visibility.
  - `selectedPair`: Directs chart and order context (e.g., 'BTCUSDT').
  - `isTerminalExpanded`: Toggles TradingTerminal height.
  - `isOrderModalOpen`: Controls trade execution modal visibility.
  - `toasts`: Array of active notifications.
- **Children:** `Header`, `ChartArea`, `TradingTerminal`, `AiSidebar`, `OrderModal`, `ToastContainer`.

### `src/components/Header.tsx`
Function: Top navigation and global controls.
- **Features:** Theme Toggle (Dark/Light), Sidebar Toggle (Mobile), Wallet Balance Indicator, Trade Button.
- **Props:** `onTradeClick` (Triggers OrderModal).

### `src/components/ChartArea.tsx`
Function: Main visualization area.
- **Features:** TradingView Widget integration.
- **Logic:** Updates symbol dynamically based on `selectedPair` prop.
- **AI Overlay:** Renders prediction overlays (Entry, Stop Loss, Take Profit lines) on top of the chart.

### `src/components/AiSidebar.tsx`
Function: Intelligence and Signal hub.
- **Structure:**
  - **Tabs:** Market (Watchlist), Signals (AI Picks), Strategy (Deep Dive).
- **Styling:** *Strict Dark Mode Compliance* (All text is `dark:text-white`).
- **Interactions:** Clicking a signal updates `selectedPair` globally.

### `src/components/TradingTerminal.tsx`
Function: Bottom panel for account tracking.
- **State:** Local tabs for `Positions`, `History`, `Assets`.
- **Features:** Real-time PnL simulation (visual mock).
- **Responsiveness:** Collapsible panel.

### `src/components/OrderModal.tsx`
Function: Trade execution interface.
- **Inputs:** Order Type (Limit/Market), Side (Buy/Sell), Amount, Leverage.
- **Feedback:** Uses `onSuccess` callback to trigger Toast notifications.

### `src/components/Toast.tsx`
Function: System notifications.
- **Types:** Success (Green), Error (Red), Info (Blue).
- **Animation:** Slide-in/Fade-out.

## 3. Data Flow & Integration Points (For Backend)

| Source Component | Action | Target Integration Point (Future) |
| :--- | :--- | :--- |
| **AiSidebar** | Select Signal | Fetch updated Chart Data & Analysis from API |
| **OrderModal** | Click "Buy/Sell" | POST `/api/orders` (Execute Trade) |
| **TradingTerminal** | Load Positions | GET `/api/positions` (Sync with Exchange) |
| **Header** | Load Wallet | GET `/api/wallet` (Balance & Margin) |
| **ChartArea** | Symbol Change | Fetch Historic Candle Data for AI Model |

## 4. Styling Guidelines
- **Dark Mode Strategy:** Utilize `dark:` prefix.
- **Text Contrast:** Avoid `text-muted-foreground` in dark mode; prefer `dark:text-white`.
- **Accents:**
  - Success/Buy: `text-emerald-500` / `bg-emerald-600`
  - Error/Sell: `text-red-500` / `bg-red-600`
  - Primary Action: `blue-600`

## 5. Directory Structure
```
src/
├── app/
│   ├── layout.tsx       # Global Font & ThemeProvider wrapper
│   └── page.tsx         # Main Dashboard Logic
├── components/
│   ├── AiSidebar.tsx    # AI Signals & Market List
│   ├── ChartArea.tsx    # Chart Visualization
│   ├── Header.tsx       # Navigation & Wallet
│   ├── OrderModal.tsx   # Trade Execution
│   ├── ThemeProvider.tsx# Context for Theme Management
│   ├── Toast.tsx        # Notification System
│   └── TradingTerminal.tsx # Positions & History
└── data/
    └── brokerInfo.ts    # Static Mock Data (Broker Spreads etc.)
```
