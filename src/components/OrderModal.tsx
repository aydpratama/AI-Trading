'use client';

import React, { useState, useEffect } from 'react';
import { X, DollarSign, Loader2 } from 'lucide-react';
import { openPosition, placeLimitOrder, getPrices, getHealth } from '@/lib/api';

export default function OrderModal({ isOpen, onClose, symbol = "EURUSD", onSuccess }: { isOpen: boolean, onClose: () => void, symbol?: string, onSuccess?: (msg: string, type: 'success' | 'error') => void }) {
    const [orderType, setOrderType] = useState<'MARKET' | 'LIMIT'>('MARKET');
    const [side, setSide] = useState<'BUY' | 'SELL'>('BUY');
    const [volume, setVolume] = useState('0.01');
    const [limitPrice, setLimitPrice] = useState('');
    const [slPrice, setSlPrice] = useState('');
    const [tpPrice, setTpPrice] = useState('');
    const [currentPrice, setCurrentPrice] = useState<number>(0);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [mt5Connected, setMt5Connected] = useState(false);

    // Clean symbol for MT5 (remove / and other chars)
    const mt5Symbol = symbol.replace('/', '').replace('USDT', 'USD');

    // Check connection and get current price
    useEffect(() => {
        if (!isOpen) return;

        const fetchData = async () => {
            try {
                const health = await getHealth();
                setMt5Connected(health.mt5_connected);

                if (health.mt5_connected) {
                    const prices = await getPrices(mt5Symbol);
                    if (prices[mt5Symbol]) {
                        const price = side === 'BUY' ? prices[mt5Symbol].ask : prices[mt5Symbol].bid;
                        setCurrentPrice(price);
                    }
                }
            } catch (error) {
                console.error('Error fetching price:', error);
            }
        };

        fetchData();
        const interval = setInterval(fetchData, 2000);
        return () => clearInterval(interval);
    }, [isOpen, mt5Symbol, side]);

    if (!isOpen) return null;

    const handleSubmit = async () => {
        if (!mt5Connected) {
            onSuccess?.("MT5 tidak terhubung. Pastikan backend berjalan.", 'error');
            return;
        }

        const vol = parseFloat(volume);
        if (!vol || vol <= 0) {
            onSuccess?.("Mohon masukkan volume yang valid (min 0.01).", 'error');
            return;
        }

        setIsSubmitting(true);
        try {
            const sl = slPrice ? parseFloat(slPrice) : null;
            const tp = tpPrice ? parseFloat(tpPrice) : null;

            let result;

            if (orderType === 'LIMIT') {
                const limit = parseFloat(limitPrice);
                if (!limit || limit <= 0) {
                    onSuccess?.("Mohon masukkan harga limit yang valid.", 'error');
                    setIsSubmitting(false);
                    return;
                }
                result = await placeLimitOrder(mt5Symbol, side, vol, limit, sl, tp);
            } else {
                // MARKET
                result = await openPosition(mt5Symbol, side, vol, sl, tp);
            }

            if (result && result.success !== false) {
                const msg = orderType === 'LIMIT'
                    ? `Order LIMIT ${side} ${vol} lot ${mt5Symbol} @ ${limitPrice} berhasil ditempatkan!`
                    : `Order MARKET ${side} ${vol} lot ${mt5Symbol} berhasil dieksekusi!`;

                onSuccess?.(msg, 'success');
                onClose();
            } else {
                onSuccess?.(`Order gagal: ${result?.error || 'Unknown error code ' + (result?.retcode || '')}`, 'error');
            }
        } catch (error) {
            onSuccess?.(`Order gagal: ${error instanceof Error ? error.message : 'Network error'}`, 'error');
        } finally {
            setIsSubmitting(false);
        }
    };

    // Format price based on symbol
    const formatPrice = (price: number) => {
        if (mt5Symbol.includes('JPY')) return price.toFixed(3);
        if (mt5Symbol.includes('XAU')) return price.toFixed(2);
        return price.toFixed(5);
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
            <div className="w-[360px] bg-background border border-border rounded-xl shadow-2xl p-0 overflow-hidden animate-in zoom-in-95 duration-200">

                {/* Header */}
                <div className="flex items-center justify-between px-4 py-3 border-b bg-secondary/30">
                    <div className="flex flex-col">
                        <span className="font-bold text-lg">{mt5Symbol}</span>
                        <div className="flex items-center gap-2 text-xs">
                            <span className="font-mono text-muted-foreground dark:text-gray-400">
                                {currentPrice > 0 ? formatPrice(currentPrice) : 'Loading...'}
                            </span>
                            <span className={`flex items-center gap-1 ${mt5Connected ? 'text-emerald-500' : 'text-red-500'}`}>
                                <span className={`w-1.5 h-1.5 rounded-full ${mt5Connected ? 'bg-emerald-500' : 'bg-red-500'}`}></span>
                                {mt5Connected ? 'LIVE' : 'OFFLINE'}
                            </span>
                        </div>
                    </div>
                    <button onClick={onClose} className="p-1 hover:bg-accent rounded-full text-muted-foreground dark:text-white transition-colors">
                        <X size={20} />
                    </button>
                </div>

                {/* Body */}
                <div className="p-5 space-y-5">

                    {/* Buy/Sell Toggle */}
                    <div className="grid grid-cols-2 gap-2 bg-secondary/50 p-1 rounded-lg">
                        <button
                            onClick={() => setSide('BUY')}
                            className={`py-2 text-sm font-bold rounded-md transition-all ${side === 'BUY' ? 'bg-emerald-600 text-white shadow-sm' : 'text-muted-foreground hover:text-foreground'}`}
                        >
                            Buy / Long
                        </button>
                        <button
                            onClick={() => setSide('SELL')}
                            className={`py-2 text-sm font-bold rounded-md transition-all ${side === 'SELL' ? 'bg-red-600 text-white shadow-sm' : 'text-muted-foreground hover:text-foreground'}`}
                        >
                            Sell / Short
                        </button>
                    </div>

                    {/* Order Type */}
                    <div className="flex gap-4 text-sm font-medium border-b pb-2">
                        <button
                            onClick={() => setOrderType('MARKET')}
                            className={`pb-2 relative ${orderType === 'MARKET' ? 'text-blue-500' : 'text-muted-foreground'}`}
                        >
                            Market
                            {orderType === 'MARKET' && <span className="absolute bottom-[-9px] left-0 right-0 h-0.5 bg-blue-500"></span>}
                        </button>
                        <button
                            onClick={() => setOrderType('LIMIT')}
                            className={`pb-2 relative ${orderType === 'LIMIT' ? 'text-blue-500' : 'text-muted-foreground'}`}
                        >
                            Limit
                            {orderType === 'LIMIT' && <span className="absolute bottom-[-9px] left-0 right-0 h-0.5 bg-blue-500"></span>}
                        </button>
                    </div>

                    {/* Inputs */}
                    <div className="space-y-3">
                        {orderType === 'LIMIT' && (
                            <div className="relative">
                                <label className="text-xs text-muted-foreground dark:text-gray-400 mb-1 block">Limit Price</label>
                                <input
                                    type="number"
                                    step="any"
                                    value={limitPrice}
                                    onChange={(e) => setLimitPrice(e.target.value)}
                                    placeholder={currentPrice > 0 ? formatPrice(currentPrice) : '0.00'}
                                    className="w-full h-9 bg-secondary/30 border border-input rounded-md pl-3 pr-3 text-sm focus:border-blue-500 outline-none font-mono dark:text-white"
                                />
                            </div>
                        )}

                        <div className="relative">
                            <label className="text-xs text-muted-foreground dark:text-gray-400 mb-1 block">Volume (Lots)</label>
                            <input
                                type="number"
                                step="0.01"
                                min="0.01"
                                value={volume}
                                onChange={(e) => setVolume(e.target.value)}
                                placeholder="0.01"
                                className="w-full h-9 bg-secondary/30 border border-input rounded-md pl-3 pr-3 text-sm focus:border-blue-500 outline-none font-mono dark:text-white"
                            />
                            <div className="flex gap-1 mt-1">
                                {[0.01, 0.05, 0.1, 0.5, 1.0].map(v => (
                                    <button key={v} onClick={() => setVolume(v.toString())}
                                        className="px-2 py-0.5 text-[10px] rounded bg-secondary/50 hover:bg-accent text-muted-foreground font-mono">
                                        {v}
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* SL / TP */}
                        <div className="grid grid-cols-2 gap-2">
                            <div>
                                <label className="text-xs text-muted-foreground dark:text-gray-400 mb-1 block">Stop Loss</label>
                                <input
                                    type="number"
                                    step="any"
                                    value={slPrice}
                                    onChange={(e) => setSlPrice(e.target.value)}
                                    placeholder="Optional"
                                    className="w-full h-9 bg-secondary/30 border border-input rounded-md px-3 text-sm focus:border-red-500 outline-none font-mono dark:text-white"
                                />
                            </div>
                            <div>
                                <label className="text-xs text-muted-foreground dark:text-gray-400 mb-1 block">Take Profit</label>
                                <input
                                    type="number"
                                    step="any"
                                    value={tpPrice}
                                    onChange={(e) => setTpPrice(e.target.value)}
                                    placeholder="Optional"
                                    className="w-full h-9 bg-secondary/30 border border-input rounded-md px-3 text-sm focus:border-emerald-500 outline-none font-mono dark:text-white"
                                />
                            </div>
                        </div>
                    </div>

                    {/* Summary */}
                    <div className="bg-secondary/20 rounded-lg p-3 space-y-2 text-xs">
                        <div className="flex justify-between">
                            <span className="text-muted-foreground dark:text-gray-400">Symbol</span>
                            <span className="font-mono dark:text-white font-bold">{mt5Symbol}</span>
                        </div>
                        <div className="flex justify-between">
                            <span className="text-muted-foreground dark:text-gray-400">Type</span>
                            <span className={`font-mono font-bold ${side === 'BUY' ? 'text-emerald-500' : 'text-red-500'}`}>{side} {orderType}</span>
                        </div>
                        <div className="flex justify-between">
                            <span className="text-muted-foreground dark:text-gray-400">Volume</span>
                            <span className="font-mono dark:text-white">{volume} lot</span>
                        </div>
                        <div className="flex justify-between">
                            <span className="text-muted-foreground dark:text-gray-400">Price</span>
                            <span className="font-mono dark:text-white">{currentPrice > 0 ? formatPrice(currentPrice) : '—'}</span>
                        </div>
                    </div>

                </div>

                {/* Footer Action */}
                <div className="p-4 pt-0">
                    <button
                        onClick={handleSubmit}
                        disabled={isSubmitting || !mt5Connected}
                        className={`w-full h-10 rounded-lg font-bold text-white shadow-lg transition-transform active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 ${side === 'BUY' ? 'bg-emerald-600 hover:bg-emerald-700 shadow-emerald-900/20' : 'bg-red-600 hover:bg-red-700 shadow-red-900/20'}`}
                    >
                        {isSubmitting ? (
                            <>
                                <Loader2 size={16} className="animate-spin" />
                                Memproses...
                            </>
                        ) : (
                            <>
                                {side} {volume} lot {mt5Symbol}
                            </>
                        )}
                    </button>
                    {!mt5Connected && (
                        <p className="text-xs text-red-500 text-center mt-2">MT5 tidak terhubung</p>
                    )}
                </div>
            </div>
        </div>
    );
}
