'use client';

import React, { useState, useEffect, useCallback } from 'react';
import {
    BarChart2, TrendingUp, TrendingDown, Award, AlertTriangle,
    Target, Clock, Flame, RefreshCw,
    Trophy, Skull, Zap, Activity, DollarSign, X
} from 'lucide-react';
import { getJournalAnalytics, type JournalAnalytics } from '@/lib/api';

interface AnalyticsDashboardProps {
    isOpen: boolean;
    onClose: () => void;
}

export default function AnalyticsDashboard({ isOpen, onClose }: AnalyticsDashboardProps) {
    const [analytics, setAnalytics] = useState<JournalAnalytics | null>(null);
    const [loading, setLoading] = useState(false);
    const [days, setDays] = useState(30);
    const [error, setError] = useState<string | null>(null);

    const fetchAnalytics = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await getJournalAnalytics(days);
            setAnalytics(data);
        } catch (err) {
            setError('Failed to load analytics. Make sure the backend is running.');
            console.error(err);
        } finally {
            setLoading(false);
        }
    }, [days]);

    useEffect(() => {
        if (isOpen) fetchAnalytics();
    }, [isOpen, fetchAnalytics]);

    if (!isOpen) return null;

    return (
        <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
            onClick={onClose}
        >
            <div
                className="bg-card border border-border rounded-2xl shadow-2xl w-[95vw] max-w-3xl max-h-[90vh] overflow-hidden flex flex-col"
                onClick={e => e.stopPropagation()}
            >
                {/* Header */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-border bg-card/80 backdrop-blur">
                    <div className="flex items-center gap-3">
                        <div className="p-2 rounded-xl bg-primary/10">
                            <BarChart2 size={22} className="text-primary" />
                        </div>
                        <h2 className="text-lg font-bold text-foreground">Performance Analytics</h2>
                    </div>
                    <div className="flex items-center gap-2">
                        <select
                            value={days}
                            onChange={e => setDays(Number(e.target.value))}
                            className="bg-muted border border-border rounded-lg px-3 py-1.5 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/40"
                        >
                            <option value={7}>7 Days</option>
                            <option value={14}>14 Days</option>
                            <option value={30}>30 Days</option>
                            <option value={90}>90 Days</option>
                            <option value={365}>1 Year</option>
                        </select>
                        <button
                            onClick={fetchAnalytics}
                            disabled={loading}
                            className="p-2 rounded-lg bg-muted hover:bg-accent transition-colors disabled:opacity-50"
                        >
                            <RefreshCw size={16} className={`text-muted-foreground ${loading ? 'animate-spin' : ''}`} />
                        </button>
                        <button
                            onClick={onClose}
                            className="p-2 rounded-lg hover:bg-destructive/10 transition-colors"
                        >
                            <X size={18} className="text-muted-foreground hover:text-destructive" />
                        </button>
                    </div>
                </div>

                {/* Body */}
                <div className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar">
                    {error && (
                        <div className="flex items-center gap-2 px-4 py-3 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive text-sm">
                            <AlertTriangle size={16} />
                            {error}
                        </div>
                    )}

                    {loading && !analytics && (
                        <div className="flex flex-col items-center justify-center py-16 gap-3 text-muted-foreground">
                            <RefreshCw size={28} className="animate-spin" />
                            <span className="text-sm">Loading analytics...</span>
                        </div>
                    )}

                    {analytics && analytics.total_trades === 0 && (
                        <div className="flex flex-col items-center justify-center py-16 gap-3 text-muted-foreground">
                            <BarChart2 size={48} className="opacity-30" />
                            <h3 className="text-lg font-semibold text-foreground">No Trades Yet</h3>
                            <p className="text-sm">Start trading to see your performance analytics here.</p>
                        </div>
                    )}

                    {analytics && analytics.total_trades > 0 && (
                        <>
                            {/* KPI Cards */}
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                                <KPICard
                                    icon={<Target size={18} />}
                                    label="Win Rate"
                                    value={`${analytics.win_rate}%`}
                                    color={analytics.win_rate >= 50 ? 'text-emerald-500' : 'text-red-500'}
                                    bg={analytics.win_rate >= 50 ? 'bg-emerald-500/10' : 'bg-red-500/10'}
                                    sub={`${analytics.wins}W / ${analytics.losses}L`}
                                />
                                <KPICard
                                    icon={<DollarSign size={18} />}
                                    label="Total P&L"
                                    value={`$${analytics.total_profit.toFixed(2)}`}
                                    color={analytics.total_profit >= 0 ? 'text-emerald-500' : 'text-red-500'}
                                    bg={analytics.total_profit >= 0 ? 'bg-emerald-500/10' : 'bg-red-500/10'}
                                    sub={`${analytics.total_trades} trades`}
                                />
                                <KPICard
                                    icon={<Zap size={18} />}
                                    label="Profit Factor"
                                    value={analytics.profit_factor === Infinity ? '∞' : analytics.profit_factor.toFixed(2)}
                                    color={analytics.profit_factor >= 1.5 ? 'text-emerald-500' : analytics.profit_factor >= 1.0 ? 'text-amber-500' : 'text-red-500'}
                                    bg={analytics.profit_factor >= 1.5 ? 'bg-emerald-500/10' : analytics.profit_factor >= 1.0 ? 'bg-amber-500/10' : 'bg-red-500/10'}
                                    sub={analytics.profit_factor >= 1.5 ? 'Excellent' : analytics.profit_factor >= 1.0 ? 'Profitable' : 'Losing'}
                                />
                                <KPICard
                                    icon={<Activity size={18} />}
                                    label="Expectancy"
                                    value={`$${analytics.expectancy.toFixed(2)}`}
                                    color={analytics.expectancy >= 0 ? 'text-emerald-500' : 'text-red-500'}
                                    bg={analytics.expectancy >= 0 ? 'bg-emerald-500/10' : 'bg-red-500/10'}
                                    sub="Per trade"
                                />
                            </div>

                            {/* Detail Cards */}
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                                {/* Win/Loss */}
                                <div className="bg-muted/50 border border-border rounded-xl p-4">
                                    <h4 className="flex items-center gap-2 text-sm font-semibold text-foreground mb-3">
                                        <TrendingUp size={14} className="text-emerald-500" />
                                        Win & Loss Stats
                                    </h4>
                                    <div className="space-y-2">
                                        <DetailRow label="Avg Win" value={`$${analytics.avg_win.toFixed(2)}`} color="text-emerald-500" />
                                        <DetailRow label="Avg Loss" value={`$${analytics.avg_loss.toFixed(2)}`} color="text-red-500" />
                                        <DetailRow label="Best" value={`$${analytics.best_trade.profit.toFixed(2)} (${analytics.best_trade.symbol})`} color="text-emerald-500" />
                                        <DetailRow label="Worst" value={`$${analytics.worst_trade.profit.toFixed(2)} (${analytics.worst_trade.symbol})`} color="text-red-500" />
                                    </div>
                                </div>

                                {/* Streaks */}
                                <div className="bg-muted/50 border border-border rounded-xl p-4">
                                    <h4 className="flex items-center gap-2 text-sm font-semibold text-foreground mb-3">
                                        <Flame size={14} className="text-orange-500" />
                                        Streaks & Timing
                                    </h4>
                                    <div className="space-y-2">
                                        <DetailRow
                                            label="Current"
                                            value={`${analytics.streaks.current} ${analytics.streaks.current_type}`}
                                            color={analytics.streaks.current_type === 'WIN' ? 'text-emerald-500' : 'text-red-500'}
                                        />
                                        <DetailRow label="Max Win" value={`${analytics.streaks.max_win}`} color="text-emerald-500" />
                                        <DetailRow label="Max Loss" value={`${analytics.streaks.max_loss}`} color="text-red-500" />
                                        <DetailRow label="Avg Duration" value={formatDuration(analytics.avg_duration_minutes)} color="text-violet-500" />
                                    </div>
                                </div>

                                {/* Confidence */}
                                <div className="bg-muted/50 border border-border rounded-xl p-4">
                                    <h4 className="flex items-center gap-2 text-sm font-semibold text-foreground mb-3">
                                        <Award size={14} className="text-amber-500" />
                                        Confidence Analysis
                                    </h4>
                                    <div className="space-y-2">
                                        <DetailRow label="Win Conf." value={`${analytics.avg_win_confidence.toFixed(0)}%`} color="text-emerald-500" />
                                        <DetailRow label="Loss Conf." value={`${analytics.avg_loss_confidence.toFixed(0)}%`} color="text-red-500" />
                                        <DetailRow
                                            label="Delta"
                                            value={`${(analytics.avg_win_confidence - analytics.avg_loss_confidence).toFixed(0)}%`}
                                            color="text-violet-500"
                                        />
                                        <DetailRow label="Breakeven" value={`${analytics.breakeven}`} color="text-muted-foreground" />
                                    </div>
                                </div>
                            </div>

                            {/* Symbol Breakdown */}
                            {Object.keys(analytics.symbol_breakdown).length > 0 && (
                                <div className="bg-muted/50 border border-border rounded-xl p-4">
                                    <h4 className="flex items-center gap-2 text-sm font-semibold text-foreground mb-3">
                                        <BarChart2 size={14} className="text-primary" />
                                        Symbol Breakdown
                                    </h4>
                                    <div className="overflow-x-auto">
                                        <table className="w-full text-sm">
                                            <thead>
                                                <tr className="text-muted-foreground text-xs border-b border-border">
                                                    <th className="text-left py-2 font-medium">Symbol</th>
                                                    <th className="text-center py-2 font-medium">Trades</th>
                                                    <th className="text-center py-2 font-medium">Win Rate</th>
                                                    <th className="text-right py-2 font-medium">P&L</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {Object.entries(analytics.symbol_breakdown).map(([symbol, stats]) => (
                                                    <tr key={symbol} className="border-b border-border/50 last:border-0">
                                                        <td className="py-2 font-mono font-semibold text-foreground">{symbol}</td>
                                                        <td className="py-2 text-center text-muted-foreground">{stats.trades}</td>
                                                        <td className={`py-2 text-center font-semibold ${stats.win_rate >= 50 ? 'text-emerald-500' : 'text-red-500'}`}>
                                                            {stats.win_rate}%
                                                        </td>
                                                        <td className={`py-2 text-right font-mono font-semibold ${stats.profit >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>
                                                            ${stats.profit.toFixed(2)}
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            )}
                        </>
                    )}
                </div>
            </div>
        </div>
    );
}

// Sub-components
function KPICard({ icon, label, value, color, bg, sub }: {
    icon: React.ReactNode; label: string; value: string; color: string; bg: string; sub: string;
}) {
    return (
        <div className="bg-muted/50 border border-border rounded-xl p-4 flex flex-col items-center text-center gap-1.5">
            <div className={`p-2 rounded-lg ${bg}`}>
                <span className={color}>{icon}</span>
            </div>
            <div className="text-[11px] uppercase tracking-wider text-muted-foreground font-medium">{label}</div>
            <div className={`text-xl font-bold ${color}`}>{value}</div>
            <div className="text-[11px] text-muted-foreground">{sub}</div>
        </div>
    );
}

function DetailRow({ label, value, color }: { label: string; value: string; color: string }) {
    return (
        <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground">{label}</span>
            <span className={`font-semibold ${color}`}>{value}</span>
        </div>
    );
}

function formatDuration(minutes: number): string {
    if (minutes < 60) return `${minutes}m`;
    const hours = Math.floor(minutes / 60);
    const mins = Math.round(minutes % 60);
    if (hours < 24) return `${hours}h ${mins}m`;
    const dys = Math.floor(hours / 24);
    return `${dys}d ${hours % 24}h`;
}
