'use client';

import React, { useState, useEffect, useCallback } from 'react';
import {
    Brain, Zap, TrendingUp, Activity, ArrowUpRight, ArrowDownRight,
    Target, Shield, Clock, BarChart2, AlertTriangle,
    CheckCircle2, Flame, Layers, Loader2,
    Play, RefreshCw, CandlestickChart, Eye
} from 'lucide-react';
import type { TradingSettings } from './SettingsModal';
import { getGeniusAnalysis, getAccount, getBrokerSymbols, executeOrder, type GeniusAnalysis, type Account, type BrokerSymbol } from '@/lib/api';


interface SignalItem {
    symbol: string;
    analysis: GeniusAnalysis;
    timestamp: Date;
}

export interface SignalPreviewData {
    symbol: string;
    direction: 'BUY' | 'SELL';
    entry: number;
    sl: number;
    tp: number;
    lotSize: number;
    confidence: number;
    reasons: string[];
    slPips: number;
    tpPips: number;
    riskAmount: number;
    profitAmount: number;
}

export default function AiSidebar({
    isOpen,
    theme,
    onSelectPair,
    selectedPair,
    tradingSettings,
    onSignalPreview
}: {
    isOpen: boolean;
    theme: string;
    onSelectPair?: (pair: string) => void;
    selectedPair?: string;
    tradingSettings?: TradingSettings;
    onSignalPreview?: (signal: SignalPreviewData | null) => void;
}) {
    // Main tabs: signals, analis, order
    const [mainTab, setMainTab] = useState<'signals' | 'analis' | 'order'>('signals');
    const [analisSubTab, setAnalisSubTab] = useState<'technical' | 'patterns' | 'multiTF'>('technical');
    const [loading, setLoading] = useState(false);
    const [scanningSignals, setScanningSignals] = useState(false);
    const [analysis, setAnalysis] = useState<GeniusAnalysis | null>(null);
    const [account, setAccount] = useState<Account | null>(null);
    const [signals, setSignals] = useState<SignalItem[]>([]);
    const [executing, setExecuting] = useState(false);
    const [executeResult, setExecuteResult] = useState<{ success: boolean; message: string } | null>(null);

    // Derive settings from props
    const aiProvider = tradingSettings?.aiProvider || 'zai';
    const apiKey = tradingSettings?.apiKey || '';
    const aiConnected = tradingSettings?.aiConnected || false;
    const lotSize = tradingSettings?.lotSize || 0.01;
    const riskPercent = tradingSettings?.riskPercent || 1;
    const riskReward = tradingSettings?.riskReward || 2;
    const customCapital = tradingSettings?.customCapital || null;

    const [selectedSignalSymbol, setSelectedSignalSymbol] = useState<string | null>(null);
    const [brokerSymbols, setBrokerSymbols] = useState<BrokerSymbol[]>([]);
    const [loadingSymbols, setLoadingSymbols] = useState(false);

    // Load broker symbols on mount
    useEffect(() => {
        const loadBrokerSymbols = async () => {
            setLoadingSymbols(true);
            try {
                const symbols = await getBrokerSymbols();
                setBrokerSymbols(symbols);
            } catch (error) {
                console.error('Error loading broker symbols:', error);
                setBrokerSymbols([
                    { name: 'EURUSD', category: 'forex', description: 'Euro/US Dollar', digits: 5 } as BrokerSymbol,
                    { name: 'GBPUSD', category: 'forex', description: 'British Pound/US Dollar', digits: 5 } as BrokerSymbol,
                    { name: 'USDJPY', category: 'forex', description: 'US Dollar/Japanese Yen', digits: 3 } as BrokerSymbol,
                    { name: 'XAUUSD', category: 'metals', description: 'Gold', digits: 2 } as BrokerSymbol,
                ]);
            } finally {
                setLoadingSymbols(false);
            }
        };
        loadBrokerSymbols();
    }, []);

    // Get symbols to scan
    const getSymbolsToScan = useCallback((): string[] => {
        if (brokerSymbols.length === 0) {
            return ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD'];
        }
        const scanSymbols = brokerSymbols
            .filter(s => s.category === 'forex' || s.category === 'metals')
            .map(s => s.name.endsWith('u') ? s.name.slice(0, -1) : s.name);
        return [...new Set(scanSymbols)].slice(0, 20);
    }, [brokerSymbols]);

    // Scan all pairs for signals
    const scanSignals = useCallback(async () => {
        setScanningSignals(true);
        try {
            const newSignals: SignalItem[] = [];
            const symbolsToScan = getSymbolsToScan();

            // Use AI provider if connected
            const useAI = aiConnected && apiKey;
            const provider = useAI ? aiProvider : undefined;
            const key = useAI ? apiKey : undefined;

            await Promise.all(
                symbolsToScan.map(async (symbol: string) => {
                    try {
                        const analysisData = await getGeniusAnalysis(symbol, 'H1', 'moderate', customCapital, provider, key, riskPercent);
                        if (analysisData && analysisData.signal && analysisData.signal.confidence >= 60) {
                            newSignals.push({
                                symbol,
                                analysis: analysisData,
                                timestamp: new Date()
                            });
                        }
                    } catch (error) {
                        console.error(`Error scanning ${symbol}:`, error);
                    }
                })
            );

            newSignals.sort((a, b) => (b.analysis.signal?.confidence || 0) - (a.analysis.signal?.confidence || 0));
            setSignals(newSignals);
        } catch (error) {
            console.error('Error scanning signals:', error);
        } finally {
            setScanningSignals(false);
        }
    }, [getSymbolsToScan, customCapital, aiConnected, apiKey, aiProvider]);

    // Load analysis for selected pair
    const loadAnalysis = useCallback(async (symbol: string) => {
        setLoading(true);
        try {
            // Remove broker suffixes (e.g., EURUSDu -> EURUSD, XAUUSD.u -> XAUUSD)
            const cleanSymbol = symbol.replace(/[.](u|m|raw|T)$/i, '').replace(/(u|m|T)$/i, (match, suffix, offset) => {
                // Only strip single-char suffix at end if it looks like a broker suffix
                // e.g. EURUSDu -> EURUSD, but not EURUSD -> EURSD
                const base = symbol.slice(0, offset);
                if (base.length >= 6) return ''; // Likely a broker suffix
                return match; // Keep it, it's part of the symbol
            });

            // Use AI provider if connected
            const useAI = aiConnected && apiKey;
            const provider = useAI ? aiProvider : undefined;
            const key = useAI ? apiKey : undefined;

            const [analysisData, accountData] = await Promise.all([
                getGeniusAnalysis(cleanSymbol, 'H1', 'moderate', customCapital, provider, key, riskPercent),
                getAccount()
            ]);
            setAnalysis(analysisData);
            setAccount(accountData);
        } catch (error) {
            console.error('Error loading analysis:', error);
        } finally {
            setLoading(false);
        }
    }, [customCapital, aiConnected, apiKey, aiProvider]);

    // Initial scan on mount
    useEffect(() => {
        scanSignals();
    }, []);

    // Load analysis when symbol changes
    useEffect(() => {
        const symbolToAnalyze = selectedSignalSymbol || selectedPair;
        if (symbolToAnalyze && mainTab !== 'signals') {
            loadAnalysis(symbolToAnalyze);
        }
    }, [selectedSignalSymbol, selectedPair, mainTab, loadAnalysis]);

    // Handle signal click - DIRECT preview on chart + load analysis
    const handleSignalClick = (signal: SignalItem) => {
        setSelectedSignalSymbol(signal.symbol);

        // Directly trigger chart preview
        if (onSignalPreview && signal.analysis.setup && signal.analysis.signal) {
            const setup = signal.analysis.setup;
            const sig = signal.analysis.signal;

            // Calculate pips and amounts
            const slDistance = Math.abs(setup.entry - setup.stop_loss);
            const tpDistance = Math.abs(setup.take_profit - setup.entry);
            const point = signal.symbol.includes('JPY') ? 0.01 : 0.0001;
            const slPips = Math.round(slDistance / point);
            const tpPips = Math.round(tpDistance / point);

            onSignalPreview({
                symbol: signal.symbol,
                direction: sig.direction as 'BUY' | 'SELL',
                entry: setup.entry,
                sl: setup.stop_loss,
                tp: setup.take_profit,
                lotSize: setup.lot_size,
                confidence: sig.confidence,
                reasons: sig.reasons,
                slPips,
                tpPips,
                riskAmount: setup.risk_amount,
                profitAmount: setup.risk_amount * setup.risk_reward
            });
        }

        if (onSelectPair) {
            onSelectPair(signal.symbol);
        }

        // Switch to analis tab
        setMainTab('analis');
    };

    // Execute order to MT5
    const handleExecuteMT5 = async () => {
        if (!analysis?.setup || !analysis?.signal) return;

        setExecuting(true);
        setExecuteResult(null);

        try {
            const result = await executeOrder({
                symbol: analysis.symbol,
                direction: analysis.signal.direction,
                volume: analysis.setup.lot_size,
                entry: analysis.setup.entry,
                sl: analysis.setup.stop_loss,
                tp: analysis.setup.take_profit,
                comment: `AYDP AI - ${analysis.signal.confidence}%`
            });

            if (result.success) {
                setExecuteResult({
                    success: true,
                    message: `Order berhasil! Ticket: ${result.ticket}`
                });
            } else {
                setExecuteResult({
                    success: false,
                    message: result.error || 'Gagal mengeksekusi order'
                });
            }
        } catch (error: any) {
            setExecuteResult({
                success: false,
                message: error.message || 'Terjadi kesalahan'
            });
        } finally {
            setExecuting(false);
        }
    };

    const sidebarClasses = isOpen ? "translate-x-0" : "translate-x-full";

    const getRecommendationColor = (rec: string) => {
        if (rec === 'STRONG_BUY') return 'text-emerald-500 bg-emerald-500/10 border-emerald-500';
        if (rec === 'BUY') return 'text-green-500 bg-green-500/10 border-green-500';
        if (rec === 'STRONG_SELL') return 'text-red-500 bg-red-500/10 border-red-500';
        if (rec === 'SELL') return 'text-orange-500 bg-orange-500/10 border-orange-500';
        return 'text-gray-500 bg-gray-500/10 border-gray-500';
    };

    const getRiskColor = (assessment: string) => {
        if (assessment === 'LOW RISK') return 'text-emerald-500';
        if (assessment === 'MODERATE RISK') return 'text-yellow-500';
        if (assessment === 'HIGH RISK') return 'text-orange-500';
        return 'text-red-500';
    };

    // Calculate pips for display
    const calculatePips = (price1: number, price2: number, symbol: string) => {
        const point = symbol.includes('JPY') ? 0.01 : 0.0001;
        return Math.abs(price1 - price2) / point;
    };


    return (
        <aside className={`fixed top-10 bottom-0 right-0 z-40 w-full md:w-[380px] border-l bg-background/95 backdrop-blur-sm flex flex-col transition-transform duration-300 ease-in-out ${sidebarClasses}`}>
            {/* Main Tab Header */}
            <div className="flex items-center px-1 pt-2 border-b">
                <button
                    onClick={() => setMainTab('signals')}
                    className={`relative flex-1 pb-3 pt-2 text-sm font-medium flex justify-center items-center gap-2 transition-all outline-none ${mainTab === 'signals'
                        ? 'text-foreground'
                        : 'text-gray-500 hover:text-foreground hover:bg-accent/50 rounded-t-md'
                        }`}
                >
                    <Zap size={16} className={mainTab === 'signals' ? "text-blue-600 dark:text-blue-500" : ""} />
                    Sinyal
                    {signals.length > 0 && (
                        <span className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-blue-600 text-white text-[10px] flex items-center justify-center">
                            {signals.length}
                        </span>
                    )}
                    {mainTab === 'signals' && (
                        <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600 dark:bg-blue-500" />
                    )}
                </button>

                <button
                    onClick={() => setMainTab('analis')}
                    className={`relative flex-1 pb-3 pt-2 text-sm font-medium flex justify-center items-center gap-2 transition-all outline-none ${mainTab === 'analis'
                        ? 'text-foreground'
                        : 'text-gray-500 hover:text-foreground hover:bg-accent/50 rounded-t-md'
                        }`}
                >
                    <BarChart2 size={16} className={mainTab === 'analis' ? "text-purple-600 dark:text-purple-500" : ""} />
                    Analis
                    {mainTab === 'analis' && (
                        <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-purple-600 dark:bg-purple-500" />
                    )}
                </button>

                <button
                    onClick={() => setMainTab('order')}
                    className={`relative flex-1 pb-3 pt-2 text-sm font-medium flex justify-center items-center gap-2 transition-all outline-none ${mainTab === 'order'
                        ? 'text-foreground'
                        : 'text-gray-500 hover:text-foreground hover:bg-accent/50 rounded-t-md'
                        }`}
                >
                    <Target size={16} className={mainTab === 'order' ? "text-emerald-600 dark:text-emerald-500" : ""} />
                    Order
                    {mainTab === 'order' && (
                        <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-emerald-600 dark:bg-emerald-500" />
                    )}
                </button>
            </div>

            {/* Sub-tabs for Analis */}
            {mainTab === 'analis' && (
                <div className="flex items-center px-1 border-b bg-secondary/30">
                    {[
                        { id: 'technical', label: 'Technical', icon: BarChart2 },
                        { id: 'patterns', label: 'Patterns', icon: CandlestickChart },
                        { id: 'multiTF', label: 'Multi-TF', icon: Clock }
                    ].map((tab) => (
                        <button
                            key={tab.id}
                            onClick={() => setAnalisSubTab(tab.id as any)}
                            className={`flex-1 py-2 text-xs font-medium flex justify-center items-center gap-1 transition-all relative outline-none ${analisSubTab === tab.id
                                ? 'text-foreground'
                                : 'text-gray-500 hover:text-foreground'
                                }`}
                        >
                            <tab.icon size={12} className={analisSubTab === tab.id ? "text-purple-600" : ""} />
                            {tab.label}
                            {analisSubTab === tab.id && (
                                <span className="absolute bottom-0 left-2 right-2 h-0.5 bg-purple-600" />
                            )}
                        </button>
                    ))}
                </div>
            )}

            <div className="flex-1 overflow-y-auto p-4 custom-scrollbar">
                {/* SIGNALS TAB */}
                {mainTab === 'signals' && (
                    <div className="space-y-4 animate-in fade-in slide-in-from-right-4 duration-300">
                        {/* Settings Status Bar */}
                        <div className="rounded-lg border bg-card p-3">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                    {aiConnected && apiKey ? (
                                        <>
                                            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                                            <span className="text-xs font-medium text-emerald-600 dark:text-emerald-400">
                                                {aiProvider.toUpperCase()} Connected
                                            </span>
                                        </>
                                    ) : (
                                        <>
                                            <span className="w-2 h-2 rounded-full bg-gray-400" />
                                            <span className="text-xs text-muted-foreground">
                                                AI belum dikonfigurasi
                                            </span>
                                        </>
                                    )}
                                </div>
                                <span className="text-[10px] text-muted-foreground">
                                    {lotSize.toFixed(2)} lot • {riskPercent}% risk • R:R 1:{riskReward}
                                </span>
                            </div>
                        </div>

                        {/* Scan Button */}
                        <button
                            onClick={scanSignals}
                            disabled={scanningSignals}
                            className="w-full py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium transition-colors flex items-center justify-center gap-2"
                        >
                            {scanningSignals ? (
                                <>
                                    <Loader2 size={16} className="animate-spin" />
                                    Scanning...
                                </>
                            ) : (
                                <>
                                    <RefreshCw size={16} />
                                    Scan Sinyal
                                </>
                            )}
                        </button>

                        {/* Signals List */}
                        <div className="space-y-2">
                            <div className="flex items-center justify-between">
                                <span className="text-xs text-gray-500">Sinyal Aktif</span>
                                <span className="text-xs text-gray-400">{signals.length} ditemukan</span>
                            </div>

                            {scanningSignals ? (
                                <div className="flex items-center justify-center py-12">
                                    <Loader2 size={24} className="animate-spin text-blue-500" />
                                    <span className="ml-2 text-sm text-gray-500">Scanning pairs...</span>
                                </div>
                            ) : signals.length === 0 ? (
                                <div className="text-center py-12">
                                    <Activity size={40} className="mx-auto text-gray-300 mb-3" />
                                    <p className="text-sm text-gray-500 font-medium">Tidak ada sinyal</p>
                                    <p className="text-xs text-gray-400 mt-1">Klik tombol scan untuk mencari ulang</p>
                                </div>
                            ) : (
                                signals.map((signal, idx) => {
                                    const sig = signal.analysis.signal;
                                    const setup = signal.analysis.setup;
                                    if (!sig) return null;

                                    const slPips = setup ? calculatePips(setup.entry, setup.stop_loss, signal.symbol) : 0;
                                    const tpPips = setup ? calculatePips(setup.entry, setup.take_profit, signal.symbol) : 0;

                                    return (
                                        <div
                                            key={idx}
                                            onClick={() => handleSignalClick(signal)}
                                            className={`p-3 rounded-lg border bg-card cursor-pointer transition-all hover:shadow-md ${sig.direction === 'BUY'
                                                ? 'border-l-4 border-l-emerald-500'
                                                : 'border-l-4 border-l-red-500'
                                                }`}
                                        >
                                            <div className="flex justify-between items-start">
                                                <div className="flex items-center gap-3">
                                                    <div className={`w-10 h-10 rounded-full flex items-center justify-center ${sig.direction === 'BUY' ? 'bg-emerald-500' : 'bg-red-500'} text-white`}>
                                                        {sig.direction === 'BUY' ? <ArrowUpRight size={18} /> : <ArrowDownRight size={18} />}
                                                    </div>
                                                    <div>
                                                        <span className="font-bold text-sm">{signal.symbol}</span>
                                                        <span className={`block text-xs font-bold ${sig.direction === 'BUY' ? 'text-emerald-600' : 'text-red-600'}`}>
                                                            {sig.direction}
                                                        </span>
                                                    </div>
                                                </div>
                                                <div className="text-right">
                                                    <span className={`block font-bold text-lg ${sig.confidence >= 80 ? 'text-emerald-600' : sig.confidence >= 70 ? 'text-blue-600' : 'text-orange-600'}`}>
                                                        {sig.confidence}%
                                                    </span>
                                                    <span className="text-[10px] text-gray-400">confidence</span>
                                                </div>
                                            </div>

                                            {setup && (
                                                <div className="mt-2 pt-2 border-t border-dashed">
                                                    <div className="grid grid-cols-3 gap-2 text-[10px] mb-2">
                                                        <div>
                                                            <span className="text-gray-500 block">Entry</span>
                                                            <span className="font-mono font-medium">{setup.entry.toFixed(5)}</span>
                                                        </div>
                                                        <div>
                                                            <span className="text-gray-500 block">SL</span>
                                                            <div className="flex items-center gap-1">
                                                                <span className="font-mono text-red-500">{setup.stop_loss.toFixed(5)}</span>
                                                                <span className="text-red-400">({slPips.toFixed(0)})</span>
                                                            </div>
                                                        </div>
                                                        <div>
                                                            <span className="text-gray-500 block">TP</span>
                                                            <div className="flex items-center gap-1">
                                                                <span className="font-mono text-emerald-500">{setup.take_profit.toFixed(5)}</span>
                                                                <span className="text-emerald-400">({tpPips.toFixed(0)})</span>
                                                            </div>
                                                        </div>
                                                    </div>
                                                    <div className="flex justify-between text-[10px]">
                                                        <span className="text-red-500">Risk: ${setup.risk_amount.toFixed(2)}</span>
                                                        <span className="text-emerald-500">Profit: ${(setup.risk_amount * setup.risk_reward).toFixed(2)}</span>
                                                    </div>
                                                </div>
                                            )}

                                            <div className="mt-2 flex items-center justify-between">
                                                <div className="flex gap-1">
                                                    {sig.reasons.slice(0, 2).map((reason: string, i: number) => (
                                                        <span key={i} className="text-[9px] px-1.5 py-0.5 rounded bg-secondary text-gray-600">
                                                            {reason}
                                                        </span>
                                                    ))}
                                                </div>
                                                <div className="flex items-center gap-1 text-blue-600">
                                                    <Eye size={12} />
                                                    <span className="text-[10px] font-medium">Lihat</span>
                                                </div>
                                            </div>
                                        </div>
                                    );
                                })
                            )}
                        </div>
                    </div>
                )}

                {/* ANALIS TAB - TECHNICAL */}
                {mainTab === 'analis' && analisSubTab === 'technical' && (
                    <div className="space-y-4 animate-in fade-in slide-in-from-right-4 duration-300">
                        {loading ? (
                            <div className="flex items-center justify-center py-8">
                                <Loader2 size={24} className="animate-spin text-blue-500" />
                            </div>
                        ) : !analysis ? (
                            <div className="text-center py-8">
                                <BarChart2 size={40} className="mx-auto text-gray-300 mb-3" />
                                <p className="text-sm text-gray-500">Pilih sinyal untuk melihat analisis technical</p>
                                <button onClick={() => setMainTab('signals')} className="mt-2 text-xs text-blue-600 hover:underline">
                                    ← Kembali ke Sinyal
                                </button>
                            </div>
                        ) : (
                            <>
                                {/* Symbol Header */}
                                <div className="flex items-center justify-between">
                                    <div>
                                        <h2 className="text-lg font-bold">{analysis.symbol}</h2>
                                        <p className="text-xs text-gray-500">{analysis.timeframe}</p>
                                    </div>
                                    {analysis.recommendation && (
                                        <span className={`px-3 py-1.5 rounded-full text-xs font-bold uppercase border ${getRecommendationColor(analysis.recommendation)}`}>
                                            {analysis.recommendation.replace('_', ' ')}
                                        </span>
                                    )}
                                </div>

                                {/* Signal Overview */}
                                {analysis.signal && (
                                    <div className="p-4 rounded-xl border bg-card">
                                        <div className="flex items-center gap-3 mb-3">
                                            <div className={`w-12 h-12 rounded-full flex items-center justify-center ${analysis.signal.direction === 'BUY' ? 'bg-emerald-500' : 'bg-red-500'} text-white`}>
                                                {analysis.signal.direction === 'BUY' ? <ArrowUpRight size={24} /> : <ArrowDownRight size={24} />}
                                            </div>
                                            <div>
                                                <span className={`text-xl font-bold ${analysis.signal.direction === 'BUY' ? 'text-emerald-500' : 'text-red-500'}`}>
                                                    {analysis.signal.direction}
                                                </span>
                                                <span className="block text-sm text-gray-500">{analysis.signal.confidence}% Confidence</span>
                                            </div>
                                        </div>
                                        <div className="flex flex-wrap gap-1">
                                            {analysis.signal.reasons.map((reason: string, i: number) => (
                                                <span key={i} className="text-[10px] px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-600">
                                                    {reason}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {/* AI Insight */}
                                {analysis.ai_insight && (
                                    <div className="p-4 rounded-xl border-2 border-purple-500/30 bg-purple-500/5">
                                        <div className="flex items-center gap-2 mb-3">
                                            <Brain size={18} className="text-purple-600" />
                                            <span className="text-sm font-bold text-purple-600">AI Insight</span>
                                            {analysis.ai_insight.agreement ? (
                                                <span className="text-[9px] px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-600 ml-auto">
                                                    ✓ Setuju
                                                </span>
                                            ) : (
                                                <span className="text-[9px] px-2 py-0.5 rounded-full bg-orange-500/20 text-orange-600 ml-auto">
                                                    ⚠ Berbeda
                                                </span>
                                            )}
                                        </div>
                                        <div className="space-y-2">
                                            <div className="flex justify-between text-xs">
                                                <span className="text-gray-500">AI Direction</span>
                                                <span className={`font-bold ${analysis.ai_insight.ai_direction === 'BUY' ? 'text-emerald-500' : analysis.ai_insight.ai_direction === 'SELL' ? 'text-red-500' : 'text-gray-500'}`}>
                                                    {analysis.ai_insight.ai_direction}
                                                </span>
                                            </div>
                                            <div className="flex justify-between text-xs">
                                                <span className="text-gray-500">AI Confidence</span>
                                                <span className="font-bold">{analysis.ai_insight.ai_confidence}%</span>
                                            </div>
                                            {analysis.ai_insight.reasoning && (
                                                <div className="mt-2 p-2 rounded bg-secondary/50">
                                                    <p className="text-xs text-gray-600 dark:text-gray-300">{analysis.ai_insight.reasoning}</p>
                                                </div>
                                            )}
                                            {analysis.ai_insight.risk_warning && (
                                                <div className="mt-2 p-2 rounded bg-orange-500/10 border border-orange-500/20">
                                                    <p className="text-xs text-orange-600 flex items-center gap-1">
                                                        <AlertTriangle size={12} />
                                                        {analysis.ai_insight.risk_warning}
                                                    </p>
                                                </div>
                                            )}
                                            {analysis.ai_insight.key_levels && (
                                                <div className="grid grid-cols-2 gap-2 mt-2">
                                                    <div className="p-2 rounded bg-emerald-500/10 text-center">
                                                        <span className="text-[9px] text-gray-500 block">AI Support</span>
                                                        <span className="text-xs font-mono text-emerald-600">
                                                            {typeof analysis.ai_insight.key_levels.support === 'number'
                                                                ? analysis.ai_insight.key_levels.support.toFixed(5)
                                                                : analysis.ai_insight.key_levels.support}
                                                        </span>
                                                    </div>
                                                    <div className="p-2 rounded bg-red-500/10 text-center">
                                                        <span className="text-[9px] text-gray-500 block">AI Resistance</span>
                                                        <span className="text-xs font-mono text-red-600">
                                                            {typeof analysis.ai_insight.key_levels.resistance === 'number'
                                                                ? analysis.ai_insight.key_levels.resistance.toFixed(5)
                                                                : analysis.ai_insight.key_levels.resistance}
                                                        </span>
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                )}

                                {/* AI Error */}
                                {analysis.ai_error && (
                                    <div className="p-3 rounded-lg border border-orange-200 bg-orange-50 dark:bg-orange-900/10">
                                        <p className="text-xs text-orange-600 flex items-center gap-2">
                                            <AlertTriangle size={14} />
                                            AI Error: {analysis.ai_error}
                                        </p>
                                    </div>
                                )}

                                {/* Technical Indicators Grid */}
                                <div className="grid grid-cols-3 gap-2">
                                    <div className="p-3 rounded-lg border bg-card text-center">
                                        <span className="text-[10px] text-gray-500 uppercase flex justify-center gap-1 items-center mb-1">
                                            <BarChart2 size={10} /> RSI
                                        </span>
                                        <span className={`text-lg font-bold ${(analysis.analysis.technical.rsi.value ?? 50) < 30 ? 'text-emerald-500' : (analysis.analysis.technical.rsi.value ?? 50) > 70 ? 'text-red-500' : 'text-foreground'}`}>
                                            {analysis.analysis.technical.rsi.value?.toFixed(1) || '-'}
                                        </span>
                                        <span className="text-[9px] block text-gray-400">{analysis.analysis.technical.rsi.status}</span>
                                    </div>
                                    <div className="p-3 rounded-lg border bg-card text-center">
                                        <span className="text-[10px] text-gray-500 uppercase flex justify-center gap-1 items-center mb-1">
                                            <Layers size={10} /> MACD
                                        </span>
                                        <span className={`text-lg font-bold ${(analysis.analysis.technical.macd.histogram ?? 0) > 0 ? 'text-emerald-500' : 'text-red-500'}`}>
                                            {(analysis.analysis.technical.macd.histogram ?? 0) > 0 ? '↑' : '↓'}
                                        </span>
                                        <span className="text-[9px] block text-gray-400">{analysis.analysis.technical.macd.status}</span>
                                    </div>
                                    <div className="p-3 rounded-lg border bg-card text-center">
                                        <span className="text-[10px] text-gray-500 uppercase flex justify-center gap-1 items-center mb-1">
                                            <Flame size={10} /> EMA
                                        </span>
                                        <span className={`text-lg font-bold ${analysis.analysis.technical.ema.trend === 'BULLISH' ? 'text-emerald-500' : 'text-red-500'}`}>
                                            {analysis.analysis.technical.ema.trend === 'BULLISH' ? '↑' : '↓'}
                                        </span>
                                        <span className="text-[9px] block text-gray-400">{analysis.analysis.technical.ema.trend}</span>
                                    </div>
                                </div>

                                {/* EMA Detail */}
                                <div className="p-3 rounded-lg border bg-card">
                                    <h4 className="text-sm font-semibold mb-2 flex items-center gap-2">
                                        <Flame size={14} className="text-orange-500" /> EMA Analysis
                                    </h4>
                                    <div className="space-y-2">
                                        <div className="flex justify-between text-xs">
                                            <span className="text-gray-500">Trend</span>
                                            <span className={`font-medium ${analysis.analysis.technical.ema.trend === 'BULLISH' ? 'text-emerald-500' : 'text-red-500'}`}>
                                                {analysis.analysis.technical.ema.trend}
                                            </span>
                                        </div>
                                        <div className="grid grid-cols-3 gap-2 mt-2 pt-2 border-t border-dashed">
                                            <div className="text-center">
                                                <span className="text-[9px] text-gray-400 block">EMA 9</span>
                                                <span className="text-xs font-mono">{analysis.analysis.technical.ema.ema9?.toFixed(5) || '-'}</span>
                                            </div>
                                            <div className="text-center">
                                                <span className="text-[9px] text-gray-400 block">EMA 21</span>
                                                <span className="text-xs font-mono">{analysis.analysis.technical.ema.ema21?.toFixed(5) || '-'}</span>
                                            </div>
                                            <div className="text-center">
                                                <span className="text-[9px] text-gray-400 block">EMA 50</span>
                                                <span className="text-xs font-mono">{analysis.analysis.technical.ema.ema50?.toFixed(5) || '-'}</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </>
                        )}
                    </div>
                )}

                {/* ANALIS TAB - PATTERNS */}
                {mainTab === 'analis' && analisSubTab === 'patterns' && (
                    <div className="space-y-4 animate-in fade-in slide-in-from-right-4 duration-300">
                        {loading ? (
                            <div className="flex items-center justify-center py-8">
                                <Loader2 size={24} className="animate-spin text-blue-500" />
                            </div>
                        ) : !analysis ? (
                            <div className="text-center py-8">
                                <CandlestickChart size={40} className="mx-auto text-gray-300 mb-3" />
                                <p className="text-sm text-gray-500">Pilih sinyal untuk melihat pola candlestick</p>
                            </div>
                        ) : (
                            <>
                                <div className="flex items-center justify-between">
                                    <h2 className="text-lg font-bold">{analysis.symbol}</h2>
                                    <span className="text-xs text-gray-500">{analysis.timeframe}</span>
                                </div>

                                {/* Bullish Patterns */}
                                {analysis.analysis.patterns?.bullish && analysis.analysis.patterns.bullish.length > 0 ? (
                                    <div className="space-y-2">
                                        <h4 className="text-sm font-semibold text-emerald-600 flex items-center gap-2">
                                            <ArrowUpRight size={16} /> Bullish Patterns
                                        </h4>
                                        {analysis.analysis.patterns.bullish.map((pattern: any, i: number) => (
                                            <div key={i} className="p-3 rounded-lg border border-emerald-500/30 bg-emerald-500/5">
                                                <div className="flex justify-between items-center">
                                                    <span className="font-medium text-sm">{pattern.name}</span>
                                                    <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-600">
                                                        {pattern.strength}%
                                                    </span>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                ) : (
                                    <div className="p-4 rounded-lg border bg-card text-center">
                                        <p className="text-xs text-gray-500">Tidak ada bullish pattern</p>
                                    </div>
                                )}

                                {/* Bearish Patterns */}
                                {analysis.analysis.patterns?.bearish && analysis.analysis.patterns.bearish.length > 0 ? (
                                    <div className="space-y-2">
                                        <h4 className="text-sm font-semibold text-red-600 flex items-center gap-2">
                                            <ArrowDownRight size={16} /> Bearish Patterns
                                        </h4>
                                        {analysis.analysis.patterns.bearish.map((pattern: any, i: number) => (
                                            <div key={i} className="p-3 rounded-lg border border-red-500/30 bg-red-500/5">
                                                <div className="flex justify-between items-center">
                                                    <span className="font-medium text-sm">{pattern.name}</span>
                                                    <span className="text-xs px-2 py-0.5 rounded-full bg-red-500/20 text-red-600">
                                                        {pattern.strength}%
                                                    </span>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                ) : (
                                    <div className="p-4 rounded-lg border bg-card text-center">
                                        <p className="text-xs text-gray-500">Tidak ada bearish pattern</p>
                                    </div>
                                )}

                                {/* Support & Resistance */}
                                {analysis.analysis.technical.support_resistance && (
                                    <div className="p-3 rounded-lg border bg-card">
                                        <h4 className="text-sm font-semibold mb-3 flex items-center gap-2">
                                            <Layers size={14} className="text-purple-500" /> Support & Resistance
                                        </h4>
                                        <div className="space-y-3">
                                            <div>
                                                <span className="text-xs text-red-500 font-medium">Resistance</span>
                                                <div className="flex flex-wrap gap-1 mt-1">
                                                    {analysis.analysis.technical.support_resistance.resistance?.map((r: number, i: number) => (
                                                        <span key={i} className="text-xs px-2 py-1 rounded bg-red-500/10 text-red-600 font-mono">
                                                            {r.toFixed(5)}
                                                        </span>
                                                    )) || <span className="text-xs text-gray-400">-</span>}
                                                </div>
                                            </div>
                                            <div>
                                                <span className="text-xs text-emerald-500 font-medium">Support</span>
                                                <div className="flex flex-wrap gap-1 mt-1">
                                                    {analysis.analysis.technical.support_resistance.support?.map((s: number, i: number) => (
                                                        <span key={i} className="text-xs px-2 py-1 rounded bg-emerald-500/10 text-emerald-600 font-mono">
                                                            {s.toFixed(5)}
                                                        </span>
                                                    )) || <span className="text-xs text-gray-400">-</span>}
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </>
                        )}
                    </div>
                )}

                {/* ANALIS TAB - MULTI-TF */}
                {mainTab === 'analis' && analisSubTab === 'multiTF' && (
                    <div className="space-y-4 animate-in fade-in slide-in-from-right-4 duration-300">
                        {loading ? (
                            <div className="flex items-center justify-center py-8">
                                <Loader2 size={24} className="animate-spin text-blue-500" />
                            </div>
                        ) : !analysis ? (
                            <div className="text-center py-8">
                                <Clock size={40} className="mx-auto text-gray-300 mb-3" />
                                <p className="text-sm text-gray-500">Pilih sinyal untuk melihat analisis multi-timeframe</p>
                            </div>
                        ) : (
                            <>
                                <div className="flex items-center justify-between">
                                    <h2 className="text-lg font-bold">{analysis.symbol}</h2>
                                    <span className="text-xs text-gray-500">Multi-Timeframe</span>
                                </div>

                                {/* Overall Confluence */}
                                {analysis.analysis.multi_timeframe && (
                                    <div className="p-4 rounded-xl border bg-card">
                                        <div className="text-center">
                                            <span className="text-xs text-gray-500">Overall Trend</span>
                                            <div className={`text-2xl font-bold mt-1 ${analysis.analysis.multi_timeframe.trend_direction === 'BULLISH' ? 'text-emerald-500' : 'text-red-500'}`}>
                                                {analysis.analysis.multi_timeframe.trend_direction}
                                            </div>
                                            <div className="mt-2">
                                                <span className="text-xs text-gray-500">Alignment Score</span>
                                                <div className="flex items-center justify-center gap-2 mt-1">
                                                    <div className="w-24 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                                                        <div
                                                            className={`h-2 rounded-full ${analysis.analysis.multi_timeframe.alignment_score >= 70 ? 'bg-emerald-500' : 'bg-yellow-500'}`}
                                                            style={{ width: `${analysis.analysis.multi_timeframe.alignment_score}%` }}
                                                        ></div>
                                                    </div>
                                                    <span className="text-sm font-bold">{analysis.analysis.multi_timeframe.alignment_score}%</span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                )}

                                {/* Timeframe Grid */}
                                {analysis.analysis.multi_timeframe?.timeframes && (
                                    <div className="grid grid-cols-2 gap-2">
                                        {Object.entries(analysis.analysis.multi_timeframe.timeframes).map(([tf, data]: [string, any]) => (
                                            <div key={tf} className="p-3 rounded-lg border bg-card">
                                                <div className="flex justify-between items-center mb-2">
                                                    <span className="text-sm font-bold">{tf}</span>
                                                    <span className={`text-xs px-2 py-0.5 rounded-full ${data.trend === 'BULLISH' ? 'bg-emerald-500/20 text-emerald-600' : 'bg-red-500/20 text-red-600'}`}>
                                                        {data.trend}
                                                    </span>
                                                </div>
                                                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5">
                                                    <div
                                                        className={`h-1.5 rounded-full ${data.signal_strength >= 70 ? 'bg-emerald-500' : 'bg-yellow-500'}`}
                                                        style={{ width: `${data.signal_strength}%` }}
                                                    ></div>
                                                </div>
                                                <span className="text-[10px] text-gray-400 mt-1 block text-right">{data.signal_strength}%</span>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </>
                        )}
                    </div>
                )}

                {/* ORDER TAB */}
                {mainTab === 'order' && (
                    <div className="space-y-4 animate-in fade-in slide-in-from-right-4 duration-300">
                        {loading ? (
                            <div className="flex items-center justify-center py-8">
                                <Loader2 size={24} className="animate-spin text-blue-500" />
                            </div>
                        ) : !analysis ? (
                            <div className="text-center py-8">
                                <Target size={40} className="mx-auto text-gray-300 mb-3" />
                                <p className="text-sm text-gray-500">Pilih sinyal untuk melihat setup order</p>
                                <button
                                    onClick={() => setMainTab('signals')}
                                    className="mt-2 text-xs text-blue-600 hover:underline"
                                >
                                    ← Kembali ke Sinyal
                                </button>
                            </div>
                        ) : (
                            <>
                                <div className="flex items-center justify-between">
                                    <div>
                                        <h2 className="text-lg font-bold">{analysis.symbol}</h2>
                                        <p className="text-xs text-gray-500">{analysis.timeframe}</p>
                                    </div>
                                    {analysis.recommendation && (
                                        <span className={`px-3 py-1.5 rounded-full text-xs font-bold uppercase border ${getRecommendationColor(analysis.recommendation)}`}>
                                            {analysis.recommendation.replace('_', ' ')}
                                        </span>
                                    )}
                                </div>

                                {/* Trading Setup */}
                                {analysis.setup && (
                                    <div className="rounded-xl border bg-card shadow-sm overflow-hidden">
                                        <div className="p-3 bg-secondary/50 border-b flex justify-between items-center">
                                            <h3 className="font-semibold text-sm flex items-center gap-2">
                                                <Target size={16} className="text-blue-600" />
                                                Setup Trading
                                            </h3>
                                            <span className="text-[10px] font-mono bg-primary text-primary-foreground px-2 py-0.5 rounded-full">
                                                R:R 1:{analysis.setup.risk_reward}
                                            </span>
                                        </div>

                                        <div className="p-4 space-y-4">
                                            {/* Entry */}
                                            <div className="flex items-center gap-3">
                                                <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white">
                                                    <Play size={14} />
                                                </div>
                                                <div className="flex-1">
                                                    <span className="text-xs text-gray-500">Entry Price</span>
                                                    <span className="block text-sm font-bold font-mono">{analysis.setup.entry.toFixed(5)}</span>
                                                </div>
                                            </div>

                                            {/* Stop Loss */}
                                            <div className="flex items-center gap-3">
                                                <div className="w-8 h-8 rounded-full bg-red-600 flex items-center justify-center text-white">
                                                    <Shield size={14} />
                                                </div>
                                                <div className="flex-1">
                                                    <span className="text-xs text-gray-500">Stop Loss</span>
                                                    <span className="block text-sm font-bold font-mono text-red-500">{analysis.setup.stop_loss.toFixed(5)}</span>
                                                </div>
                                                <div className="text-right">
                                                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-red-500/10 text-red-500 block">
                                                        {analysis.setup.position_details.sl_distance_pips} pips
                                                    </span>
                                                    <span className="text-[9px] text-red-400 block mt-0.5">
                                                        Risk: ${analysis.setup.risk_amount.toFixed(2)}
                                                    </span>
                                                </div>
                                            </div>

                                            {/* Take Profit */}
                                            <div className="flex items-center gap-3">
                                                <div className="w-8 h-8 rounded-full bg-emerald-600 flex items-center justify-center text-white">
                                                    <TrendingUp size={14} />
                                                </div>
                                                <div className="flex-1">
                                                    <span className="text-xs text-gray-500">Take Profit</span>
                                                    <span className="block text-sm font-bold font-mono text-emerald-500">{analysis.setup.take_profit.toFixed(5)}</span>
                                                </div>
                                                <div className="text-right">
                                                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-500 block">
                                                        {(analysis.setup.position_details.sl_distance_pips * analysis.setup.risk_reward).toFixed(0)} pips
                                                    </span>
                                                    <span className="text-[9px] text-emerald-400 block mt-0.5">
                                                        Profit: ${(analysis.setup.risk_amount * analysis.setup.risk_reward).toFixed(2)}
                                                    </span>
                                                </div>
                                            </div>
                                        </div>

                                        {/* Position Sizing */}
                                        <div className="p-3 border-t bg-secondary/20">
                                            <div className="grid grid-cols-3 gap-2 mb-3">
                                                <div className="text-center">
                                                    <span className="text-[10px] text-gray-500 block">Lot Size</span>
                                                    <span className="text-sm font-bold">{analysis.setup.lot_size}</span>
                                                </div>
                                                <div className="text-center">
                                                    <span className="text-[10px] text-gray-500 block">Risk $</span>
                                                    <span className="text-sm font-bold text-orange-500">${analysis.setup.risk_amount}</span>
                                                </div>
                                                <div className="text-center">
                                                    <span className="text-[10px] text-gray-500 block">Risk %</span>
                                                    <span className="text-sm font-bold">{analysis.setup.risk_percent}%</span>
                                                </div>
                                            </div>

                                            {/* Execute MT5 Button */}
                                            <button
                                                onClick={handleExecuteMT5}
                                                disabled={executing || !analysis.setup.risk_assessment.can_proceed}
                                                className={`w-full h-12 rounded-lg font-medium text-sm transition-colors flex items-center justify-center gap-2 ${executing
                                                    ? 'bg-gray-400 cursor-not-allowed'
                                                    : !analysis.setup.risk_assessment.can_proceed
                                                        ? 'bg-gray-400 cursor-not-allowed'
                                                        : 'bg-blue-600 hover:bg-blue-700 text-white'
                                                    }`}
                                            >
                                                {executing ? (
                                                    <>
                                                        <Loader2 size={16} className="animate-spin" />
                                                        Mengeksekusi...
                                                    </>
                                                ) : (
                                                    <>
                                                        <CheckCircle2 size={16} />
                                                        Execute MT5
                                                    </>
                                                )}
                                            </button>

                                            {/* Execute Result */}
                                            {executeResult && (
                                                <div className={`mt-2 p-2 rounded text-xs ${executeResult.success ? 'bg-emerald-500/10 text-emerald-600' : 'bg-red-500/10 text-red-600'}`}>
                                                    {executeResult.message}
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                )}

                                {/* Warnings */}
                                {analysis?.setup?.risk_assessment.warnings && analysis.setup.risk_assessment.warnings.length > 0 && (
                                    <div className="rounded-lg border border-orange-200 dark:border-orange-900/30 bg-orange-50 dark:bg-orange-900/10 p-3 flex gap-3 items-start">
                                        <AlertTriangle size={16} className="text-orange-600 shrink-0 mt-0.5" />
                                        <div>
                                            <p className="text-xs font-semibold text-orange-800 dark:text-orange-200 mb-1">Peringatan</p>
                                            <ul className="text-xs text-orange-700 dark:text-orange-300 space-y-1">
                                                {analysis.setup.risk_assessment.warnings.map((w: string, i: number) => (
                                                    <li key={i}>• {w}</li>
                                                ))}
                                            </ul>
                                        </div>
                                    </div>
                                )}
                            </>
                        )}
                    </div>
                )}
            </div>
        </aside>
    );
}
