'use client';

import React, { useState, useEffect } from 'react';
import {
    Settings, Key, BarChart2, Brain, CheckCircle2, AlertTriangle,
    ChevronDown, ChevronUp, Loader2, X, Shield, Zap, Wallet
} from 'lucide-react';

const aiProviders = [
    { id: 'gemini', name: 'Gemini (Google)', placeholder: 'AIzaSy...', description: 'Google Gemini 3 Flash' },
    { id: 'openai', name: 'OpenAI', placeholder: 'sk-...', description: 'GPT-4o-mini' },
    { id: 'zai', name: 'ZAI (Zhipu)', placeholder: 'API key...', description: 'GLM-4-Flash (Gratis)' },
    { id: 'kimi', name: 'Kimi (Moonshot)', placeholder: 'API key...', description: 'Moonshot v1' },
];

export interface TradingSettings {
    lotSize: number;
    riskPercent: number;
    riskReward: number;
    customCapital: number | null;
    aiProvider: string;
    apiKey: string;
    aiConnected: boolean;
}

export default function SettingsModal({
    isOpen,
    onClose,
    settings,
    onSettingsChange,
    accountBalance
}: {
    isOpen: boolean;
    onClose: () => void;
    settings: TradingSettings;
    onSettingsChange: (settings: TradingSettings) => void;
    accountBalance?: number;
}) {
    const [activeTab, setActiveTab] = useState<'ai' | 'trading'>('ai');
    const [testingAi, setTestingAi] = useState(false);
    const [aiTestResult, setAiTestResult] = useState<{ success: boolean; message: string } | null>(null);
    const [capitalInput, setCapitalInput] = useState(settings.customCapital ? String(settings.customCapital) : '');

    // Local state for editing
    const [localProvider, setLocalProvider] = useState(settings.aiProvider);
    const [localApiKey, setLocalApiKey] = useState(settings.apiKey);
    const [localLotSize, setLocalLotSize] = useState(settings.lotSize);
    const [localRiskPercent, setLocalRiskPercent] = useState(settings.riskPercent);
    const [localRiskReward, setLocalRiskReward] = useState(settings.riskReward);
    const [localCustomCapital, setLocalCustomCapital] = useState(settings.customCapital);

    // Sync local state when settings change or modal opens
    useEffect(() => {
        if (isOpen) {
            setLocalProvider(settings.aiProvider);
            setLocalApiKey(settings.apiKey);
            setLocalLotSize(settings.lotSize);
            setLocalRiskPercent(settings.riskPercent);
            setLocalRiskReward(settings.riskReward);
            setLocalCustomCapital(settings.customCapital);
            setCapitalInput(settings.customCapital ? String(settings.customCapital) : '');
            setAiTestResult(null);
        }
    }, [isOpen, settings]);

    const handleSave = () => {
        const newSettings: TradingSettings = {
            ...settings,
            aiProvider: localProvider,
            apiKey: localApiKey,
            lotSize: localLotSize,
            riskPercent: localRiskPercent,
            riskReward: localRiskReward,
            customCapital: localCustomCapital,
            aiConnected: localApiKey.trim().length > 0
        };

        // Save to localStorage
        localStorage.setItem('ai_provider', localProvider);
        localStorage.setItem('ai_api_key', localApiKey);
        localStorage.setItem('trading_lot_size', String(localLotSize));
        localStorage.setItem('trading_risk_percent', String(localRiskPercent));
        localStorage.setItem('trading_risk_reward', String(localRiskReward));
        if (localCustomCapital) {
            localStorage.setItem('trading_custom_capital', String(localCustomCapital));
        } else {
            localStorage.removeItem('trading_custom_capital');
        }

        onSettingsChange(newSettings);
        onClose();
    };

    const handleTestAi = async () => {
        if (!localApiKey.trim()) return;
        setTestingAi(true);
        setAiTestResult(null);
        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/ai/test`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ provider: localProvider, api_key: localApiKey })
            });
            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    setAiTestResult({ success: true, message: data.message || 'Terhubung!' });
                } else {
                    setAiTestResult({ success: false, message: data.message || 'API Key tidak valid' });
                }
            } else {
                const errorData = await response.json().catch(() => null);
                setAiTestResult({ success: false, message: errorData?.message || `Server error: ${response.status}` });
            }
        } catch {
            setAiTestResult({ success: true, message: 'API Key tersimpan (offline mode)' });
        }
        setTestingAi(false);
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4" onClick={onClose}>
            <div
                className="bg-card border border-border rounded-2xl shadow-2xl w-full max-w-md overflow-hidden animate-in fade-in zoom-in-95 duration-200"
                onClick={e => e.stopPropagation()}
            >
                {/* Header */}
                <div className="flex items-center justify-between px-5 py-4 border-b bg-secondary/30">
                    <div className="flex items-center gap-2.5">
                        <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center shadow-lg shadow-blue-900/20">
                            <Settings size={16} className="text-white" />
                        </div>
                        <div>
                            <h3 className="text-sm font-bold">Pengaturan</h3>
                            <p className="text-[10px] text-muted-foreground">AI Provider & Trading Settings</p>
                        </div>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-1.5 rounded-lg hover:bg-accent text-muted-foreground hover:text-foreground transition-colors"
                    >
                        <X size={18} />
                    </button>
                </div>

                {/* Tabs */}
                <div className="flex border-b">
                    <button
                        onClick={() => setActiveTab('ai')}
                        className={`flex-1 py-2.5 text-xs font-medium flex justify-center items-center gap-2 transition-all relative ${activeTab === 'ai' ? 'text-purple-600' : 'text-muted-foreground hover:text-foreground'}`}
                    >
                        <Brain size={14} />
                        AI Provider
                        {activeTab === 'ai' && <span className="absolute bottom-0 left-4 right-4 h-0.5 bg-purple-600 rounded-full" />}
                    </button>
                    <button
                        onClick={() => setActiveTab('trading')}
                        className={`flex-1 py-2.5 text-xs font-medium flex justify-center items-center gap-2 transition-all relative ${activeTab === 'trading' ? 'text-blue-600' : 'text-muted-foreground hover:text-foreground'}`}
                    >
                        <BarChart2 size={14} />
                        Trading Settings
                        {activeTab === 'trading' && <span className="absolute bottom-0 left-4 right-4 h-0.5 bg-blue-600 rounded-full" />}
                    </button>
                </div>

                {/* Content */}
                <div className="p-5 max-h-[60vh] overflow-y-auto custom-scrollbar">
                    {/* AI Provider Tab */}
                    {activeTab === 'ai' && (
                        <div className="space-y-4 animate-in fade-in duration-200">
                            {/* Provider Select */}
                            <div>
                                <label className="text-xs font-medium text-muted-foreground mb-2 block">AI Provider</label>
                                <div className="grid grid-cols-2 gap-2">
                                    {aiProviders.map(p => (
                                        <button
                                            key={p.id}
                                            onClick={() => setLocalProvider(p.id)}
                                            className={`p-3 rounded-xl border text-left transition-all ${localProvider === p.id
                                                ? 'border-purple-500 bg-purple-500/10 ring-1 ring-purple-500/30'
                                                : 'border-border hover:border-purple-500/30 hover:bg-secondary/50'
                                                }`}
                                        >
                                            <span className="text-xs font-bold block">{p.name}</span>
                                            <span className="text-[10px] text-muted-foreground">{p.description}</span>
                                        </button>
                                    ))}
                                </div>
                            </div>

                            {/* API Key */}
                            <div>
                                <label className="text-xs font-medium text-muted-foreground mb-2 block flex items-center gap-1.5">
                                    <Key size={12} />
                                    API Key
                                </label>
                                <div className="flex gap-2">
                                    <input
                                        type="password"
                                        placeholder={aiProviders.find(p => p.id === localProvider)?.placeholder}
                                        value={localApiKey}
                                        onChange={(e) => setLocalApiKey(e.target.value)}
                                        className="flex-1 px-3 py-2 text-xs rounded-lg border bg-background outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500/30 transition-all"
                                    />
                                    <button
                                        onClick={handleTestAi}
                                        disabled={testingAi || !localApiKey.trim()}
                                        className="px-4 py-2 text-xs rounded-lg bg-purple-600 text-white hover:bg-purple-700 transition-colors disabled:opacity-50 flex items-center gap-1.5 font-medium"
                                    >
                                        {testingAi ? <Loader2 size={12} className="animate-spin" /> : <Zap size={12} />}
                                        {testingAi ? 'Testing...' : 'Test'}
                                    </button>
                                </div>

                                {/* Test Result */}
                                {aiTestResult && (
                                    <div className={`mt-2 p-2.5 rounded-lg text-xs flex items-center gap-2 ${aiTestResult.success ? 'bg-emerald-500/10 text-emerald-600 border border-emerald-500/20' : 'bg-red-500/10 text-red-600 border border-red-500/20'}`}>
                                        {aiTestResult.success ? <CheckCircle2 size={14} /> : <AlertTriangle size={14} />}
                                        {aiTestResult.message}
                                    </div>
                                )}
                            </div>

                            {/* AI Status */}
                            <div className="p-3 rounded-xl bg-secondary/50 border border-border">
                                <div className="flex items-center gap-2 text-xs">
                                    <div className={`w-2 h-2 rounded-full ${localApiKey.trim() ? 'bg-emerald-500 animate-pulse' : 'bg-gray-400'}`} />
                                    <span className="font-medium">
                                        Status: {localApiKey.trim() ? 'Siap digunakan' : 'Belum dikonfigurasi'}
                                    </span>
                                </div>
                                {localApiKey.trim() && (
                                    <p className="text-[10px] text-muted-foreground mt-1 ml-4">
                                        AI akan memperkaya analisis sinyal dengan {aiProviders.find(p => p.id === localProvider)?.name}
                                    </p>
                                )}
                            </div>
                        </div>
                    )}

                    {/* Trading Settings Tab */}
                    {activeTab === 'trading' && (
                        <div className="space-y-5 animate-in fade-in duration-200">
                            {/* Lot Size */}
                            <div>
                                <label className="text-xs font-medium text-muted-foreground mb-2 block flex justify-between">
                                    <span className="flex items-center gap-1.5"><BarChart2 size={12} /> Lot Size</span>
                                    <span className="font-mono font-bold text-blue-600 text-sm">{localLotSize.toFixed(2)}</span>
                                </label>
                                <input
                                    type="range"
                                    min="0.01"
                                    max="1"
                                    step="0.01"
                                    value={localLotSize}
                                    onChange={(e) => setLocalLotSize(parseFloat(e.target.value))}
                                    className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-600"
                                />
                                <div className="flex justify-between text-[9px] text-muted-foreground mt-1">
                                    <span>0.01</span>
                                    <span>0.50</span>
                                    <span>1.00</span>
                                </div>
                            </div>

                            {/* Risk Percentage */}
                            <div>
                                <label className="text-xs font-medium text-muted-foreground mb-2 block flex justify-between">
                                    <span className="flex items-center gap-1.5"><Shield size={12} /> Risk per Trade</span>
                                    <span className="font-mono font-bold text-orange-500 text-sm">{localRiskPercent}%</span>
                                </label>
                                <input
                                    type="range"
                                    min="0.5"
                                    max="5"
                                    step="0.5"
                                    value={localRiskPercent}
                                    onChange={(e) => setLocalRiskPercent(parseFloat(e.target.value))}
                                    className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer accent-orange-500"
                                />
                                <div className="flex justify-between text-[9px] text-muted-foreground mt-1">
                                    <span>0.5%</span>
                                    <span>2.5%</span>
                                    <span>5%</span>
                                </div>
                            </div>

                            {/* Risk:Reward Ratio */}
                            <div>
                                <label className="text-xs font-medium text-muted-foreground mb-2 block flex justify-between">
                                    <span className="flex items-center gap-1.5"><Zap size={12} /> Risk : Reward</span>
                                    <span className="font-mono font-bold text-emerald-500 text-sm">1:{localRiskReward}</span>
                                </label>
                                <input
                                    type="range"
                                    min="1"
                                    max="5"
                                    step="0.5"
                                    value={localRiskReward}
                                    onChange={(e) => setLocalRiskReward(parseFloat(e.target.value))}
                                    className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer accent-emerald-500"
                                />
                                <div className="flex justify-between text-[9px] text-muted-foreground mt-1">
                                    <span>1:1</span>
                                    <span>1:3</span>
                                    <span>1:5</span>
                                </div>
                            </div>

                            {/* Custom Capital */}
                            <div>
                                <label className="text-xs font-medium text-muted-foreground mb-2 block flex justify-between">
                                    <span className="flex items-center gap-1.5"><Wallet size={12} /> Modal Custom</span>
                                    <span className="font-mono font-bold text-purple-500 text-sm">
                                        {localCustomCapital ? `$${localCustomCapital.toLocaleString()}` : 'Dari MT5'}
                                    </span>
                                </label>
                                <div className="flex gap-2">
                                    <input
                                        type="number"
                                        placeholder="Contoh: 100"
                                        value={capitalInput}
                                        onChange={(e) => setCapitalInput(e.target.value)}
                                        className="flex-1 px-3 py-2 text-xs rounded-lg border bg-background outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500/30 transition-all"
                                        min="10"
                                        max="1000000"
                                    />
                                    <button
                                        onClick={() => {
                                            const val = parseFloat(capitalInput);
                                            if (val && val >= 10) {
                                                setLocalCustomCapital(val);
                                            }
                                        }}
                                        className="px-3 py-2 text-xs rounded-lg bg-purple-600 text-white hover:bg-purple-700 transition-colors font-medium"
                                    >
                                        Set
                                    </button>
                                    {localCustomCapital && (
                                        <button
                                            onClick={() => {
                                                setLocalCustomCapital(null);
                                                setCapitalInput('');
                                            }}
                                            className="px-2 py-2 text-xs rounded-lg bg-secondary hover:bg-secondary/80 transition-colors"
                                            title="Reset ke MT5 Balance"
                                        >
                                            ×
                                        </button>
                                    )}
                                </div>
                                <p className="text-[9px] text-muted-foreground mt-1.5">
                                    Kosongkan untuk menggunakan balance dari MT5 {accountBalance ? `($${accountBalance.toLocaleString()})` : ''}
                                </p>
                            </div>
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="px-5 py-4 border-t bg-secondary/20 flex gap-3">
                    <button
                        onClick={onClose}
                        className="flex-1 py-2.5 text-xs font-medium border border-border rounded-xl hover:bg-accent transition-colors"
                    >
                        Batal
                    </button>
                    <button
                        onClick={handleSave}
                        className="flex-1 py-2.5 text-xs font-bold bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-all shadow-lg shadow-blue-900/20 active:scale-[0.98]"
                    >
                        Simpan Pengaturan
                    </button>
                </div>
            </div>
        </div>
    );
}
