'use client';

import { useEffect, useRef, useCallback, useState } from 'react';

export interface MarketData {
    prices: Record<string, { bid: number; ask: number; spread: number; time: number }>;
    positions: Array<{
        ticket: number;
        symbol: string;
        type: string;
        volume: number;
        entry: number;
        current: number;
        sl: number;
        tp: number;
        pnl: number;
        swap: number;
        commission: number;
    }>;
    totalPnl: number;
    account: {
        balance: number;
        equity: number;
        margin: number;
        free_margin: number;
        margin_level: number;
        leverage: number;
    } | null;
    timestamp: number;
}

export function useWebSocket() {
    const wsRef = useRef<WebSocket | null>(null);
    const [data, setData] = useState<MarketData | null>(null);
    const [connected, setConnected] = useState(false);
    const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

    const connect = useCallback(() => {
        if (wsRef.current?.readyState === WebSocket.OPEN) return;

        const wsUrl = process.env.NODE_ENV === 'development'
            ? 'ws://localhost:8000/ws'
            : `ws://${window.location.host}/ws`;

        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
            console.log('[WS] Connected to realtime stream');
            setConnected(true);
        };

        ws.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                if (message.type === 'market_update') {
                    setData({
                        prices: message.prices,
                        positions: message.positions,
                        totalPnl: message.total_pnl,
                        account: message.account,
                        timestamp: message.timestamp
                    });
                }
            } catch (e) {
                console.error('[WS] Parse error:', e);
            }
        };

        ws.onclose = () => {
            console.log('[WS] Disconnected');
            setConnected(false);
            // Auto reconnect after 2 seconds
            reconnectTimeoutRef.current = setTimeout(() => connect(), 2000);
        };

        ws.onerror = (error) => {
            console.error('[WS] Error:', error);
            ws.close();
        };
    }, []);

    const disconnect = useCallback(() => {
        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
        }
        wsRef.current?.close();
        wsRef.current = null;
    }, []);

    useEffect(() => {
        connect();
        return () => disconnect();
    }, [connect, disconnect]);

    return { data, connected, reconnect: connect };
}