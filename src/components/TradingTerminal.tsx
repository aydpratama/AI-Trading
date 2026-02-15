'use client';

import React, { useState, useEffect, useCallback } from 'react';
import {
    Layers, History, Wallet, XCircle,
    MoreHorizontal, ChevronUp, ChevronDown, RefreshCw, Loader2,
    AlertCircle, CheckCircle2, WifiOff, Wifi
} from 'lucide-react';
import { getPositions, getAccount, closePosition, getHealth, type Position, type Account } from '@/lib/api';
import { useWebSocket } from '@/hooks/useWebSocket';

export default function TradingTerminal({ isExpanded, onToggle, onSelectPosition }: { isExpanded: boolean, onToggle: () => void, onSelectPosition?: (position: Position | null) => void }) {
    const [activeTab, setActiveTab] = useState<'positions' | 'history' | 'assets'>('positions');
    const [positions, setPositions] = useState<Position[]>([]);
    const [account, setAccount] = useState<Account | null>(null);
    const [loading, setLoading] = useState(false);
    const [mt5Connected, setMt5Connected] = useState(false);
    const [closingTicket, setClosingTicket] = useState<number | null>(null);
    const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

    // WebSocket for realtime data
    const { data: wsData, connected: wsConnected } = useWebSocket();

    // Check MT5 health
    const checkHealth = useCallback(async () => {
        try {
            const health = await getHealth();
            setMt5Connected(health.mt5_connected);
        } catch {
            setMt5Connected(false);
        }
    }, []);

    // Load data from MT5 backend (initial load only)
    const loadData = useCallback(async () => {
        setLoading(true);
        try {
            const [positionsData, accountData] = await Promise.all([
                getPositions(),
                getAccount()
            ]);

            setPositions(positionsData || []);
            if (accountData) {
                setAccount(accountData);
            }

            setLastUpdate(new Date());
            setMt5Connected(true);
        } catch (error) {
            console.error('Error loading data:', error);
            setMt5Connected(false);
        } finally {
            setLoading(false);
        }
    }, []);

    // Update positions from WebSocket (realtime)
    useEffect(() => {
        if (wsData?.positions) {
            // Map WS data to match Position type
            const wsPositions = wsData.positions.map(p => ({
                ticket: p.ticket,
                symbol: p.symbol,
                type: p.type,
                volume: p.volume,
                entry: p.entry,
                current: p.current,
                sl: p.sl,
                tp: p.tp,
                pnl: p.pnl,
                profit: p.pnl,
                swap: p.swap,
                margin: 0,
                status: 'open' as const,
                open_time: '',
                close_time: null,
                timeframe: '1H',
                reason: '',
                confidence: 0
            }));
            setPositions(wsPositions as any);
            setLastUpdate(new Date());
        }
        if (wsData?.account) {
            setAccount(prev => prev ? {
                ...prev,
                balance: wsData.account!.balance,
                equity: wsData.account!.equity,
                margin: wsData.account!.margin,
                free_margin: wsData.account!.free_margin,
                margin_level: wsData.account!.margin_level
            } : null);
        }
    }, [wsData]);

    // Close position via real MT5
    const handleClosePosition = async (ticket: number) => {
        if (!mt5Connected) return;
        setClosingTicket(ticket);
        try {
            await closePosition(ticket);
            await loadData();
        } catch (error) {
            console.error('Error closing position:', error);
        } finally {
            setClosingTicket(null);
        }
    };

    // Initial load and health check
    useEffect(() => {
        checkHealth();
        loadData();
        const interval = setInterval(checkHealth, 10000); // Health check every 10s
        return () => clearInterval(interval);
    }, [checkHealth, loadData]);

    // Calculate totals from realtime data
    const totalPnL = positions.reduce((sum, pos) => sum + (pos.pnl || pos.profit || 0), 0);
    const equity = account?.equity ?? 0;
    const balance = account?.balance ?? 0;
    const freeMargin = account?.free_margin ?? 0;
    const margin = account?.margin ?? 0;
    const leverage = account?.leverage ?? 0;

    return (
        <div className={`flex flex-col bg-background/95 backdrop-blur border-t border-border transition-all duration-300 ease-in-out ${isExpanded ? 'h-[280px]' : 'h-[40px]'}`}>

            {/* Terminal Header */}
            <div className="flex items-center justify-between px-4 h-[40px] border-b bg-secondary/10 shrink-0">
                <div className="flex items-center gap-1">
                    <TabButton
                        active={activeTab === 'positions'}
                        icon={Layers}
                        label="Posisi Terbuka"
                        count={positions.length}
                        onClick={() => { setActiveTab('positions'); if (!isExpanded) onToggle(); }}
                    />
                    <TabButton
                        active={activeTab === 'history'}
                        icon={History}
                        label="Riwayat Order"
                        onClick={() => { setActiveTab('history'); if (!isExpanded) onToggle(); }}
                    />
                    <TabButton
                        active={activeTab === 'assets'}
                        icon={Wallet}
                        label="Aset & Margin"
                        onClick={() => { setActiveTab('assets'); if (!isExpanded) onToggle(); }}
                    />
                </div>

                <div className="flex items-center gap-2">
                    <div className="hidden md:flex items-center gap-4 mr-4 text-xs">
                        {/* WebSocket Status */}
                        <span className={`flex items-center gap-1 ${wsConnected ? 'text-emerald-500' : 'text-yellow-500'}`}>
                            {wsConnected ? <Wifi size={12} /> : <Loader2 size={12} className="animate-spin" />}
                            {wsConnected ? 'WS' : 'Connecting...'}
                        </span>

                        {/* MT5 Connection Status */}
                        <span className={`flex items-center gap-1 ${mt5Connected ? 'text-emerald-500' : 'text-red-500'}`}>
                            {mt5Connected ? <CheckCircle2 size={12} /> : <WifiOff size={12} />}
                            {mt5Connected ? 'MT5' : 'Disconnected'}
                        </span>

                        <span className="text-muted-foreground">Balance: <span className="font-mono text-foreground font-bold">${balance.toLocaleString('en-US', { minimumFractionDigits: 2 })}</span></span>
                        <span className="text-muted-foreground">Equity: <span className="font-mono text-foreground font-bold">${equity.toLocaleString('en-US', { minimumFractionDigits: 2 })}</span></span>
                        <span className="text-muted-foreground">PnL: <span className={`font-mono font-bold ${totalPnL >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>{totalPnL >= 0 ? '+' : ''}{totalPnL.toFixed(2)}</span></span>
                    </div>
                    <button onClick={loadData} className="p-1 hover:bg-accent rounded text-muted-foreground" title="Refresh">
                        <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
                    </button>
                    <button onClick={onToggle} className="p-1 hover:bg-accent rounded text-muted-foreground">
                        {isExpanded ? <ChevronDown size={16} /> : <ChevronUp size={16} />}
                    </button>
                </div>
            </div>

            {/* Terminal Content */}
            <div className={`flex-1 overflow-auto custom-scrollbar p-0 ${!isExpanded ? 'hidden' : ''}`}>

                {/* TAB: POSITIONS */}
                {activeTab === 'positions' && (
                    <>
                        {!mt5Connected ? (
                            <div className="p-8 text-center text-muted-foreground">
                                <WifiOff size={48} className="mx-auto mb-4 opacity-20" />
                                <p className="font-medium">MT5 Tidak Terhubung</p>
                                <p className="text-xs mt-2">Pastikan backend Python berjalan dan MT5 Terminal aktif</p>
                                <button onClick={loadData} className="mt-3 px-4 py-1.5 rounded bg-blue-500 text-white text-xs hover:bg-blue-600 transition-colors">
                                    Coba Lagi
                                </button>
                            </div>
                        ) : positions.length === 0 ? (
                            <div className="p-8 text-center text-muted-foreground">
                                <CheckCircle2 size={48} className="mx-auto mb-4 opacity-20" />
                                <p className="font-medium">Tidak Ada Posisi Terbuka</p>
                                <p className="text-xs mt-2">Buka posisi baru melalui tombol Trade</p>
                            </div>
                        ) : (
                            <table className="w-full text-left text-sm border-collapse">
                                <thead className="bg-secondary/20 sticky top-0 backdrop-blur z-10">
                                    <tr>
                                        <th className="py-2 px-4 font-medium text-xs text-muted-foreground">Ticket</th>
                                        <th className="py-2 px-4 font-medium text-xs text-muted-foreground">Simbol</th>
                                        <th className="py-2 px-4 font-medium text-xs text-muted-foreground">Ukuran</th>
                                        <th className="py-2 px-4 font-medium text-xs text-muted-foreground text-right">Harga Masuk</th>
                                        <th className="py-2 px-4 font-medium text-xs text-muted-foreground text-right">Harga Saat Ini</th>
                                        <th className="py-2 px-4 font-medium text-xs text-muted-foreground text-right">SL</th>
                                        <th className="py-2 px-4 font-medium text-xs text-muted-foreground text-right">TP</th>
                                        <th className="py-2 px-4 font-medium text-xs text-muted-foreground text-right">PnL ($)</th>
                                        <th className="py-2 px-4 font-medium text-xs text-muted-foreground text-center">Aksi</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-border">
                                    {positions.map((pos) => {
                                        const pnl = pos.pnl || pos.profit || 0;
                                        const isProfit = pnl >= 0;
                                        return (
                                            <tr
                                                key={pos.ticket}
                                                className="hover:bg-accent/30 group transition-colors cursor-pointer"
                                                onClick={() => onSelectPosition && onSelectPosition(pos)}
                                                title="Klik untuk melihat chart"
                                            >
                                                <td className="py-3 px-4 font-mono text-xs text-muted-foreground">{pos.ticket}</td>
                                                <td className="py-3 px-4 font-bold flex items-center gap-2 text-foreground">
                                                    <span className={`w-1 h-4 rounded-full ${pos.type === 'BUY' ? 'bg-emerald-500' : 'bg-red-500'}`}></span>
                                                    {pos.symbol}
                                                    <span className={`text-[10px] px-1.5 py-0.5 rounded border ${pos.type === 'BUY'
                                                        ? 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20'
                                                        : 'bg-red-500/10 text-red-500 border-red-500/20'}`}>
                                                        {pos.type}
                                                    </span>
                                                </td>
                                                <td className="py-3 px-4 font-mono text-foreground">{pos.volume}</td>
                                                <td className="py-3 px-4 text-right font-mono text-muted-foreground">
                                                    {pos.entry.toLocaleString(undefined, { minimumFractionDigits: 5 })}
                                                </td>
                                                <td className="py-3 px-4 text-right font-mono text-foreground font-medium">
                                                    {pos.current.toLocaleString(undefined, { minimumFractionDigits: 5 })}
                                                </td>
                                                <td className="py-3 px-4 text-right font-mono text-muted-foreground text-xs">
                                                    {pos.sl ? pos.sl.toLocaleString(undefined, { minimumFractionDigits: 5 }) : '—'}
                                                </td>
                                                <td className="py-3 px-4 text-right font-mono text-muted-foreground text-xs">
                                                    {pos.tp ? pos.tp.toLocaleString(undefined, { minimumFractionDigits: 5 }) : '—'}
                                                </td>
                                                <td className={`py-3 px-4 text-right font-mono font-bold ${isProfit ? 'text-emerald-500' : 'text-red-500'}`}>
                                                    {isProfit ? '+' : ''}{pnl.toFixed(2)}
                                                </td>
                                                <td className="py-3 px-4 text-center">
                                                    <button
                                                        onClick={(e) => { e.stopPropagation(); handleClosePosition(pos.ticket); }}
                                                        disabled={closingTicket === pos.ticket}
                                                        className="p-1 hover:bg-red-500/10 hover:text-red-500 rounded text-muted-foreground transition-colors disabled:opacity-50"
                                                        title="Tutup Posisi"
                                                    >
                                                        {closingTicket === pos.ticket ? (
                                                            <Loader2 size={16} className="animate-spin" />
                                                        ) : (
                                                            <XCircle size={16} />
                                                        )}
                                                    </button>
                                                </td>
                                            </tr>
                                        );
                                    })}
                                </tbody>
                            </table>
                        )}
                    </>
                )}

                {/* TAB: HISTORY */}
                {activeTab === 'history' && (
                    <div className="p-8 text-center text-muted-foreground">
                        <History size={48} className="mx-auto mb-4 opacity-20" />
                        <p className="font-medium">Riwayat Trading</p>
                        <p className="text-xs mt-2">Riwayat diambil dari MT5 saat terhubung</p>
                        {lastUpdate && (
                            <p className="text-xs mt-1 text-muted-foreground">
                                Update terakhir: {lastUpdate.toLocaleTimeString()}
                            </p>
                        )}
                    </div>
                )}

                {/* TAB: ASSETS */}
                {activeTab === 'assets' && (
                    <div className="p-4">
                        {!mt5Connected ? (
                            <div className="p-8 text-center text-muted-foreground">
                                <WifiOff size={48} className="mx-auto mb-4 opacity-20" />
                                <p>MT5 Tidak Terhubung</p>
                            </div>
                        ) : account ? (
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                <AssetCard label="Balance" value={`$${balance.toLocaleString('en-US', { minimumFractionDigits: 2 })}`} />
                                <AssetCard label="Equity" value={`$${equity.toLocaleString('en-US', { minimumFractionDigits: 2 })}`} />
                                <AssetCard label="Free Margin" value={`$${freeMargin.toLocaleString('en-US', { minimumFractionDigits: 2 })}`} />
                                <AssetCard label="Used Margin" value={`$${margin.toLocaleString('en-US', { minimumFractionDigits: 2 })}`} />
                                <AssetCard label="Leverage" value={`1:${leverage}`} />
                                <AssetCard label="Server" value={account.server || '—'} />
                                <AssetCard label="Login" value={`${account.login}`} />
                                <AssetCard
                                    label="Unrealized P/L"
                                    value={`${totalPnL >= 0 ? '+' : ''}$${totalPnL.toFixed(2)}`}
                                    valueColor={totalPnL >= 0 ? 'text-emerald-500' : 'text-red-500'}
                                />
                            </div>
                        ) : (
                            <div className="p-8 text-center text-muted-foreground">
                                <Loader2 size={32} className="mx-auto mb-4 animate-spin opacity-20" />
                                <p>Loading account data...</p>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}

function TabButton({ active, icon: Icon, label, count, onClick }: any) {
    return (
        <button
            onClick={onClick}
            className={`flex items-center gap-2 px-4 h-full text-xs font-medium border-b-2 transition-all ${active
                ? 'border-blue-500 text-foreground bg-background'
                : 'border-transparent text-muted-foreground hover:text-foreground hover:bg-accent/50'
                }`}
        >
            <Icon size={14} />
            {label}
            {count !== undefined && (
                <span className={`px-1.5 rounded-full text-[10px] ${active ? 'bg-secondary text-foreground' : 'bg-secondary/50'}`}>
                    {count}
                </span>
            )}
        </button>
    );
}

function AssetCard({ label, value, valueColor }: { label: string; value: string; valueColor?: string }) {
    return (
        <div className="p-3 rounded-lg bg-secondary/20 border border-border/50">
            <p className="text-xs text-muted-foreground mb-1">{label}</p>
            <p className={`font-mono font-bold text-sm ${valueColor || 'text-foreground'}`}>{value}</p>
        </div>
    );
}