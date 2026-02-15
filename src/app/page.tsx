'use client';

import React, { useState, useEffect } from 'react';
import Header from '@/components/Header';
import AiSidebar from '@/components/AiSidebar';
import ChartArea from '@/components/ChartArea';
import TradingTerminal from '@/components/TradingTerminal';
import OrderModal from '@/components/OrderModal';
import AnalyticsDashboard from '@/components/AnalyticsDashboard';
import SettingsModal, { TradingSettings } from '@/components/SettingsModal';
import { ToastContainer, ToastType } from '@/components/Toast';
import { useTheme } from '@/components/ThemeProvider';
import { PanelRightClose, PanelRightOpen } from 'lucide-react';

export interface SignalPreview {
  symbol: string;
  direction: 'BUY' | 'SELL';
  entry: number;
  sl: number;
  tp: number;
  lotSize: number;
  confidence: number;
  reasons: string[];
}

export default function Home() {
  const { theme, toggleTheme } = useTheme();
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [selectedPair, setSelectedPair] = useState('EURUSD');
  const [selectedPosition, setSelectedPosition] = useState<any>(null);
  const [signalPreview, setSignalPreview] = useState<SignalPreview | null>(null);
  const [isTerminalExpanded, setIsTerminalExpanded] = useState(true);
  const [isOrderModalOpen, setOrderModalOpen] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isAnalyticsOpen, setIsAnalyticsOpen] = useState(false);
  const [toasts, setToasts] = useState<{ id: number; message: string; type: ToastType }[]>([]);

  // Trading & AI Settings (centralized)
  const [tradingSettings, setTradingSettings] = useState<TradingSettings>({
    lotSize: 0.01,
    riskPercent: 1,
    riskReward: 2,
    customCapital: null,
    aiProvider: 'zai',
    apiKey: '',
    aiConnected: false
  });

  // Load settings from localStorage on mount
  useEffect(() => {
    const savedProvider = localStorage.getItem('ai_provider');
    const savedApiKey = localStorage.getItem('ai_api_key');
    const savedLotSize = localStorage.getItem('trading_lot_size');
    const savedRiskPercent = localStorage.getItem('trading_risk_percent');
    const savedRiskReward = localStorage.getItem('trading_risk_reward');
    const savedCapital = localStorage.getItem('trading_custom_capital');

    setTradingSettings(prev => ({
      ...prev,
      aiProvider: savedProvider || prev.aiProvider,
      apiKey: savedApiKey || prev.apiKey,
      aiConnected: !!(savedProvider && savedApiKey),
      lotSize: savedLotSize ? parseFloat(savedLotSize) : prev.lotSize,
      riskPercent: savedRiskPercent ? parseFloat(savedRiskPercent) : prev.riskPercent,
      riskReward: savedRiskReward ? parseFloat(savedRiskReward) : prev.riskReward,
      customCapital: savedCapital ? parseFloat(savedCapital) : null
    }));
  }, []);

  const addToast = (message: string, type: ToastType) => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, message, type }]);
  };

  const removeToast = (id: number) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  };

  useEffect(() => {
    if (typeof window !== 'undefined' && window.innerWidth < 768) {
      setIsSidebarOpen(false);
    }
  }, []);

  return (
    <main className="flex flex-col h-screen w-full bg-background overflow-hidden text-foreground">
      <Header
        toggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
        theme={theme}
        toggleTheme={toggleTheme}
        onTradeClick={() => setOrderModalOpen(true)}
        onSettingsClick={() => setIsSettingsOpen(true)}
        onAnalyticsClick={() => setIsAnalyticsOpen(true)}
        aiConnected={tradingSettings.aiConnected}
        aiProvider={tradingSettings.aiProvider}
      />

      <div className="flex flex-1 pt-10 h-screen overflow-hidden">
        <section className="relative h-full w-full transition-all duration-300 ease-in-out">
          <div className={`flex flex-col h-full transition-all duration-300 ${isSidebarOpen ? 'md:mr-[380px]' : ''} overflow-hidden`}>
            <div className="flex-1 relative min-h-0">
              <ChartArea
                theme={theme}
                selectedPair={selectedPair}
                selectedPosition={selectedPosition}
                signalPreview={signalPreview}
                onClearSignalPreview={() => setSignalPreview(null)}
                onExecuteOrder={() => setOrderModalOpen(true)}
                onSymbolChange={setSelectedPair}
              />
            </div>
            <TradingTerminal
              isExpanded={isTerminalExpanded}
              onToggle={() => setIsTerminalExpanded(!isTerminalExpanded)}
              onSelectPosition={setSelectedPosition}
            />
          </div>

          <button
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className={`absolute top-4 z-40 p-2 rounded-full bg-background/50 backdrop-blur border text-muted-foreground hover:text-foreground hover:bg-accent transition-all hidden md:flex duration-300 ${isSidebarOpen ? 'right-[400px]' : 'right-4'}`}
            title={isSidebarOpen ? "Tutup Sidebar" : "Buka Sidebar"}
          >
            {isSidebarOpen ? <PanelRightClose size={20} /> : <PanelRightOpen size={20} />}
          </button>
        </section>

        <AiSidebar
          isOpen={isSidebarOpen}
          theme={theme}
          onSelectPair={setSelectedPair}
          selectedPair={selectedPair}
          tradingSettings={tradingSettings}
          onSignalPreview={(signal: SignalPreview | null) => {
            setSignalPreview(signal);
            if (signal) {
              setSelectedPair(signal.symbol);
            }
          }}
        />
      </div>

      <OrderModal
        isOpen={isOrderModalOpen}
        onClose={() => setOrderModalOpen(false)}
        symbol={selectedPair}
        onSuccess={addToast}
      />

      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        settings={tradingSettings}
        onSettingsChange={setTradingSettings}
      />

      <AnalyticsDashboard
        isOpen={isAnalyticsOpen}
        onClose={() => setIsAnalyticsOpen(false)}
      />

      <ToastContainer toasts={toasts} removeToast={removeToast} />
    </main>
  );
}