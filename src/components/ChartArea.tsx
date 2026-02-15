'use client';

import React, { useEffect, useRef, useState, useCallback } from 'react';
import { createChart, ColorType, IChartApi, CandlestickSeries, LineSeries, HistogramSeries, ISeriesApi, CrosshairMode, MouseEventParams } from 'lightweight-charts';
import { getCandlesWithDigits, getPrices, getPositions, getBrokerSymbols, type CandleData, type PriceData, type Position, type CandlesResponse, type BrokerSymbol } from '@/lib/api';

// Better Icons - TradingView Style (filled variants)
const Icons = {
    Crosshair: () => (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10" />
            <line x1="22" y1="12" x2="18" y2="12" />
            <line x1="6" y1="12" x2="2" y2="12" />
            <line x1="12" y1="6" x2="12" y2="2" />
            <line x1="12" y1="22" x2="12" y2="18" />
        </svg>
    ),
    Pan: () => (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
            <path d="M13 2a1 1 0 0 1 1 1v6h2a1 1 0 0 1 .8 1.6l-4 5.5a1 1 0 0 1-1.6 0l-4-5.5A1 1 0 0 1 8 9h2V3a1 1 0 0 1 1-1h2z" />
            <path d="M7 17a1 1 0 0 1 1-1h8a1 1 0 0 1 1 1v3a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2v-3z" />
        </svg>
    ),
    Reset: () => (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="1 4 1 10 7 10" />
            <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" />
        </svg>
    ),
    Indicator: () => (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="4" y1="21" x2="4" y2="14" />
            <line x1="4" y1="10" x2="4" y2="3" />
            <line x1="12" y1="21" x2="12" y2="12" />
            <line x1="12" y1="8" x2="12" y2="3" />
            <line x1="20" y1="21" x2="20" y2="16" />
            <line x1="20" y1="12" x2="20" y2="3" />
            <line x1="1" y1="14" x2="7" y2="14" />
            <line x1="9" y1="8" x2="15" y2="8" />
            <line x1="17" y1="16" x2="23" y2="16" />
        </svg>
    ),
    Layout: () => (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
            <line x1="3" y1="9" x2="21" y2="9" />
            <line x1="9" y1="21" x2="9" y2="9" />
        </svg>
    ),
    Fullscreen: () => (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3" />
        </svg>
    ),
    Camera: () => (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
            <circle cx="12" cy="13" r="4" />
        </svg>
    ),
};

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

interface IndicatorSettings {
    rsi: { period: number; visible: boolean };
    macd: { fast: number; slow: number; signal: number; visible: boolean };
    ema: { period1: number; period2: number; period3: number; visible: boolean };
    bollinger: { period: number; stdDev: number; visible: boolean };
    volume: { visible: boolean };
}

export default function ChartArea({
    theme,
    selectedPair,
    selectedPosition,
    signalPreview,
    onClearSignalPreview,
    onExecuteOrder,
    onSymbolChange
}: {
    theme: string;
    selectedPair?: string;
    selectedPosition?: Position | null;
    signalPreview?: SignalPreview | null;
    onClearSignalPreview?: () => void;
    onExecuteOrder?: () => void;
    onSymbolChange?: (symbol: string) => void;
}) {
    const chartContainerRef = useRef<HTMLDivElement>(null);
    const chartRef = useRef<IChartApi | null>(null);
    const candleSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
    const volumeSeriesRef = useRef<ISeriesApi<'Histogram'> | null>(null);
    const rsiSeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
    const macdHistogramRef = useRef<ISeriesApi<'Histogram'> | null>(null);
    const macdLineRef = useRef<ISeriesApi<'Line'> | null>(null);
    const macdSignalRef = useRef<ISeriesApi<'Line'> | null>(null);
    const ema1Ref = useRef<ISeriesApi<'Line'> | null>(null);
    const ema2Ref = useRef<ISeriesApi<'Line'> | null>(null);
    const ema3Ref = useRef<ISeriesApi<'Line'> | null>(null);
    const bollingerUpperRef = useRef<ISeriesApi<'Line'> | null>(null);
    const bollingerMiddleRef = useRef<ISeriesApi<'Line'> | null>(null);
    const bollingerLowerRef = useRef<ISeriesApi<'Line'> | null>(null);

    const [splitRatio, setSplitRatio] = useState(0.7);
    const [candles, setCandles] = useState<CandleData[]>([]);
    const [localPositions, setLocalPositions] = useState<Position[]>([]);
    const [loading, setLoading] = useState(true);
    const [isDraggingState, setIsDraggingState] = useState(false);
    const [chartLayout, setChartLayout] = useState<'split' | 'single'>('single');
    const [timeframe, setTimeframe] = useState<string>('1H');
    const [symbolDigits, setSymbolDigits] = useState<number>(5);
    const [cursorMode, setCursorMode] = useState<'crosshair' | 'pan'>('crosshair');
    const [indicatorSettings, setIndicatorSettings] = useState<IndicatorSettings>({
        rsi: { period: 14, visible: false },
        macd: { fast: 12, slow: 26, signal: 9, visible: false },
        ema: { period1: 9, period2: 21, period3: 50, visible: false },
        bollinger: { period: 20, stdDev: 2, visible: false },
        volume: { visible: true },
    });
    const [showIndicatorPanel, setShowIndicatorPanel] = useState(false);
    const [priceData, setPriceData] = useState<{ open: number; high: number; low: number; close: number; volume: number; time: string } | null>(null);
    const [isFullscreen, setIsFullscreen] = useState(false);
    const [brokerSymbols, setBrokerSymbols] = useState<BrokerSymbol[]>([]);
    const [showSymbolSelector, setShowSymbolSelector] = useState(false);
    const [symbolSearch, setSymbolSearch] = useState('');
    const [selectedCategory, setSelectedCategory] = useState<string>('all');

    // Calculate candles needed for 5 months based on timeframe
    const getCandleCountFor5Months = (tf: string): number => {
        switch (tf) {
            case '1M': return 100 * 24 * 60;
            case '5M': return 100 * 24 * 12;
            case '15M': return 100 * 24 * 4;
            case '30M': return 100 * 24 * 2;
            case '1H': return 100 * 24;
            case '4H': return 100 * 6;
            case '1D': return 100;
            default: return 2400;
        }
    };

    const TIMEFRAMES = [
        { value: '1M', label: '1m' },
        { value: '5M', label: '5m' },
        { value: '15M', label: '15m' },
        { value: '30M', label: '30m' },
        { value: '1H', label: '1H' },
        { value: '4H', label: '4H' },
        { value: '1D', label: '1D' },
    ];

    // Technical indicator calculations
    const calculateRSI = useCallback((data: CandleData[], period: number = 14): { time: number | string, value: number }[] => {
        if (data.length < period + 1) return [];
        const rsiData: { time: number | string, value: number }[] = [];
        for (let i = period; i < data.length; i++) {
            let gains = 0, losses = 0;
            for (let j = i - period + 1; j <= i; j++) {
                const change = data[j].close - data[j - 1].close;
                if (change > 0) gains += change;
                else losses -= change;
            }
            const avgGain = gains / period;
            const avgLoss = losses / period;
            if (avgLoss === 0) {
                rsiData.push({ time: data[i].time, value: 100 });
            } else {
                const rs = avgGain / avgLoss;
                rsiData.push({ time: data[i].time, value: 100 - (100 / (1 + rs)) });
            }
        }
        return rsiData;
    }, []);

    const calculateEMA = useCallback((data: CandleData[], period: number): { time: number | string, value: number }[] => {
        if (data.length < period) return [];
        const multiplier = 2 / (period + 1);
        const emaData: { time: number | string, value: number }[] = [];

        // Calculate first EMA using SMA
        let sum = 0;
        for (let i = 0; i < period; i++) {
            sum += data[i].close;
        }
        let ema = sum / period;
        emaData.push({ time: data[period - 1].time, value: ema });

        // Calculate rest using EMA formula
        for (let i = period; i < data.length; i++) {
            ema = (data[i].close - ema) * multiplier + ema;
            emaData.push({ time: data[i].time, value: ema });
        }
        return emaData;
    }, []);

    const calculateMACD = useCallback((data: CandleData[], fast: number = 12, slow: number = 26, signal: number = 9) => {
        if (data.length < slow + signal) return { macd: [], signal: [], histogram: [] };

        const fastEMA = calculateEMA(data, fast);
        const slowEMA = calculateEMA(data, slow);

        const macdLine: { time: number | string, value: number }[] = [];
        const startIdx = data.length - fastEMA.length;

        for (let i = 0; i < slowEMA.length; i++) {
            const fastIdx = fastEMA.length - slowEMA.length + i;
            if (fastIdx >= 0) {
                macdLine.push({
                    time: slowEMA[i].time,
                    value: fastEMA[fastIdx].value - slowEMA[i].value
                });
            }
        }

        // Calculate signal line (EMA of MACD)
        const multiplier = 2 / (signal + 1);
        const signalLine: { time: number | string, value: number }[] = [];

        if (macdLine.length >= signal) {
            let sum = 0;
            for (let i = 0; i < signal; i++) {
                sum += macdLine[i].value;
            }
            let sig = sum / signal;
            signalLine.push({ time: macdLine[signal - 1].time, value: sig });

            for (let i = signal; i < macdLine.length; i++) {
                sig = (macdLine[i].value - sig) * multiplier + sig;
                signalLine.push({ time: macdLine[i].time, value: sig });
            }
        }

        // Calculate histogram
        const histogram: { time: number | string, value: number, color: string }[] = [];
        for (let i = 0; i < signalLine.length; i++) {
            const macdIdx = macdLine.length - signalLine.length + i;
            if (macdIdx >= 0) {
                const histValue = macdLine[macdIdx].value - signalLine[i].value;
                histogram.push({
                    time: signalLine[i].time,
                    value: histValue,
                    color: histValue >= 0 ? '#26a69a' : '#ef5350'
                });
            }
        }

        return { macd: macdLine, signal: signalLine, histogram };
    }, [calculateEMA]);

    const calculateBollingerBands = useCallback((data: CandleData[], period: number = 20, stdDev: number = 2) => {
        if (data.length < period) return { upper: [], middle: [], lower: [] };

        const upper: { time: number | string, value: number }[] = [];
        const middle: { time: number | string, value: number }[] = [];
        const lower: { time: number | string, value: number }[] = [];

        for (let i = period - 1; i < data.length; i++) {
            let sum = 0;
            for (let j = i - period + 1; j <= i; j++) {
                sum += data[j].close;
            }
            const sma = sum / period;

            let squaredDiffs = 0;
            for (let j = i - period + 1; j <= i; j++) {
                squaredDiffs += Math.pow(data[j].close - sma, 2);
            }
            const std = Math.sqrt(squaredDiffs / period);

            upper.push({ time: data[i].time, value: sma + stdDev * std });
            middle.push({ time: data[i].time, value: sma });
            lower.push({ time: data[i].time, value: sma - stdDev * std });
        }

        return { upper, middle, lower };
    }, []);

    // Initialize chart with TradingView-like settings
    useEffect(() => {
        if (!chartContainerRef.current || chartRef.current) return;

        const chart = createChart(chartContainerRef.current, {
            layout: {
                background: { type: ColorType.Solid, color: theme === 'dark' ? '#131722' : '#ffffff' },
                textColor: theme === 'dark' ? '#d1d4db' : '#4a4a4a',
                fontSize: 11,
                fontFamily: "'Trebuchet MS', Roboto, Ubuntu, sans-serif",
            },
            grid: {
                vertLines: { color: theme === 'dark' ? '#1e222d' : '#e1e1e1' },
                horzLines: { color: theme === 'dark' ? '#1e222d' : '#e1e1e1' },
            },
            width: chartContainerRef.current.clientWidth,
            height: chartContainerRef.current.clientHeight,
            timeScale: {
                timeVisible: true,
                secondsVisible: false,
                borderVisible: true,
                borderColor: theme === 'dark' ? '#2a2e39' : '#d1d4db',
                rightOffset: 5,
                barSpacing: 6,
                fixLeftEdge: false,
                fixRightEdge: false,
                lockVisibleTimeRangeOnResize: true,
            },
            rightPriceScale: {
                visible: true,
                autoScale: true,
                scaleMargins: { top: 0.1, bottom: 0.2 },
                borderVisible: true,
                borderColor: theme === 'dark' ? '#2a2e39' : '#d1d4db',
                entireTextOnly: true,
            },
            leftPriceScale: {
                visible: false,
            },
            crosshair: {
                mode: CrosshairMode.Normal,
                vertLine: {
                    color: theme === 'dark' ? '#758696' : '#959da5',
                    width: 1,
                    style: 3,
                    labelBackgroundColor: theme === 'dark' ? '#2962ff' : '#2962ff',
                },
                horzLine: {
                    color: theme === 'dark' ? '#758696' : '#959da5',
                    width: 1,
                    style: 3,
                    labelBackgroundColor: theme === 'dark' ? '#2962ff' : '#2962ff',
                },
            },
            handleScroll: {
                vertTouchDrag: true,
                horzTouchDrag: true,
                mouseWheel: true,
                pressedMouseMove: true,
            },
            handleScale: {
                axisPressedMouseMove: true,
                mouseWheel: true,
                pinch: true,
            },
            kineticScroll: {
                touch: true,
                mouse: true,
            },
        });

        // Main candlestick series
        const candleSeries = chart.addSeries(CandlestickSeries, {
            upColor: '#26a69a',
            downColor: '#ef5350',
            borderUpColor: '#26a69a',
            borderDownColor: '#ef5350',
            wickUpColor: '#26a69a',
            wickDownColor: '#ef5350',
            priceScaleId: 'right',
        });

        // Volume series (at bottom)
        const volumeSeries = chart.addSeries(HistogramSeries, {
            color: '#26a69a',
            priceFormat: { type: 'volume' },
            priceScaleId: 'volume',
            lastValueVisible: false,
        });

        chart.priceScale('volume').applyOptions({
            autoScale: true,
            scaleMargins: { top: 0.85, bottom: 0 },
            borderVisible: false,
        });

        // RSI series
        const rsiSeries = chart.addSeries(LineSeries, {
            color: '#7b1fa2',
            lineWidth: 2,
            priceScaleId: 'rsi',
            priceFormat: { type: 'price', precision: 1, minMove: 0.1 },
        });

        chart.priceScale('rsi').applyOptions({
            autoScale: false,
            scaleMargins: { top: 0.75, bottom: 0.02 },
            borderVisible: false,
        });

        // RSI levels
        rsiSeries.createPriceLine({ price: 70, color: '#ef5350', lineWidth: 1, lineStyle: 2, axisLabelVisible: false });
        rsiSeries.createPriceLine({ price: 30, color: '#26a69a', lineWidth: 1, lineStyle: 2, axisLabelVisible: false });
        rsiSeries.createPriceLine({ price: 50, color: '#555555', lineWidth: 1, lineStyle: 1, axisLabelVisible: false });

        chartRef.current = chart;
        candleSeriesRef.current = candleSeries;
        volumeSeriesRef.current = volumeSeries;
        rsiSeriesRef.current = rsiSeries;

        // Subscribe to crosshair move for price data display
        chart.subscribeCrosshairMove((param: MouseEventParams) => {
            if (!param.time || !param.seriesData) {
                // Show latest price when not hovering
                if (candles.length > 0) {
                    const last = candles[candles.length - 1];
                    setPriceData({
                        open: last.open,
                        high: last.high,
                        low: last.low,
                        close: last.close,
                        volume: 0,
                        time: new Date(last.time * 1000).toLocaleString()
                    });
                }
                return;
            }

            const candleData = param.seriesData.get(candleSeries);
            if (candleData && 'open' in candleData) {
                setPriceData({
                    open: candleData.open as number,
                    high: candleData.high as number,
                    low: candleData.low as number,
                    close: candleData.close as number,
                    volume: 0,
                    time: new Date((param.time as number) * 1000).toLocaleString()
                });
            }
        });

        // Resize observer
        const resizeObserver = new ResizeObserver((entries) => {
            if (entries.length === 0) return;
            const { width, height } = entries[0].contentRect;
            chart.applyOptions({ width, height });
        });
        resizeObserver.observe(chartContainerRef.current);

        return () => {
            resizeObserver.disconnect();
            chart.remove();
            chartRef.current = null;
            candleSeriesRef.current = null;
            volumeSeriesRef.current = null;
            rsiSeriesRef.current = null;
        };
    }, []); // Only run once

    // Update theme
    useEffect(() => {
        if (!chartRef.current) return;

        chartRef.current.applyOptions({
            layout: {
                background: { type: ColorType.Solid, color: theme === 'dark' ? '#131722' : '#ffffff' },
                textColor: theme === 'dark' ? '#d1d4db' : '#4a4a4a',
            },
            grid: {
                vertLines: { color: theme === 'dark' ? '#1e222d' : '#e1e1e1' },
                horzLines: { color: theme === 'dark' ? '#1e222d' : '#e1e1e1' },
            },
            timeScale: {
                borderColor: theme === 'dark' ? '#2a2e39' : '#d1d4db',
            },
            rightPriceScale: {
                borderColor: theme === 'dark' ? '#2a2e39' : '#d1d4db',
            },
            crosshair: {
                vertLine: {
                    color: theme === 'dark' ? '#758696' : '#959da5',
                    labelBackgroundColor: '#2962ff',
                },
                horzLine: {
                    color: theme === 'dark' ? '#758696' : '#959da5',
                    labelBackgroundColor: '#2962ff',
                },
            },
        });
    }, [theme]);

    // Update crosshair mode
    useEffect(() => {
        if (!chartRef.current) return;
        chartRef.current.applyOptions({
            crosshair: {
                mode: cursorMode === 'crosshair' ? CrosshairMode.Normal : CrosshairMode.Hidden,
            },
        });
    }, [cursorMode]);

    // Resize chart when layout changes
    useEffect(() => {
        if (!chartRef.current || !chartContainerRef.current) return;
        const timer = setTimeout(() => {
            if (chartRef.current && chartContainerRef.current) {
                const { width, height } = chartContainerRef.current.getBoundingClientRect();
                chartRef.current.applyOptions({ width, height });
                chartRef.current.timeScale().fitContent();
            }
        }, 100);
        return () => clearTimeout(timer);
    }, [chartLayout]);

    // Update chart data
    useEffect(() => {
        if (!candleSeriesRef.current || !volumeSeriesRef.current || !rsiSeriesRef.current || candles.length === 0) return;

        const candlesForChart = candles.map(c => ({
            time: c.time as any,
            open: c.open,
            high: c.high,
            low: c.low,
            close: c.close
        }));

        // Volume with TradingView-style coloring (based on previous candle)
        const volumeData = candles.map((c, i) => {
            // Determine volume bar color:
            // - Green if close > open (bullish candle)
            // - Red if close < open (bearish candle)
            // Also compare to previous volume for height variation
            const prevVolume = i > 0 ? (candles[i - 1].tick_volume || candles[i - 1].volume || 1000) : 1000;
            const currentVolume = c.tick_volume || c.volume || 1000;

            return {
                time: c.time as any,
                value: currentVolume,
                color: c.close >= c.open
                    ? 'rgba(38, 166, 154, 0.6)'   // Green for bullish
                    : 'rgba(239, 53, 80, 0.6)'    // Red for bearish
            };
        });

        candleSeriesRef.current.setData(candlesForChart as any);

        // Volume visibility
        if (indicatorSettings.volume.visible) {
            volumeSeriesRef.current.setData(volumeData as any);
            volumeSeriesRef.current.applyOptions({ visible: true });
        } else {
            volumeSeriesRef.current.applyOptions({ visible: false });
        }

        // RSI
        if (indicatorSettings.rsi.visible) {
            const rsiData = calculateRSI(candles, indicatorSettings.rsi.period);
            rsiSeriesRef.current.setData(rsiData as any);
            rsiSeriesRef.current.applyOptions({ visible: true });
        } else {
            rsiSeriesRef.current.applyOptions({ visible: false });
        }

        // EMAs
        if (indicatorSettings.ema.visible) {
            const ema1 = calculateEMA(candles, indicatorSettings.ema.period1);
            const ema2 = calculateEMA(candles, indicatorSettings.ema.period2);
            const ema3 = calculateEMA(candles, indicatorSettings.ema.period3);

            if (!ema1Ref.current) {
                ema1Ref.current = chartRef.current?.addSeries(LineSeries, {
                    color: '#2962ff',
                    lineWidth: 1,
                    priceScaleId: 'right',
                    lastValueVisible: false,
                }) || null;
            }
            if (!ema2Ref.current) {
                ema2Ref.current = chartRef.current?.addSeries(LineSeries, {
                    color: '#ff6d00',
                    lineWidth: 1,
                    priceScaleId: 'right',
                    lastValueVisible: false,
                }) || null;
            }
            if (!ema3Ref.current) {
                ema3Ref.current = chartRef.current?.addSeries(LineSeries, {
                    color: '#e91e63',
                    lineWidth: 1,
                    priceScaleId: 'right',
                    lastValueVisible: false,
                }) || null;
            }

            ema1Ref.current?.setData(ema1 as any);
            ema2Ref.current?.setData(ema2 as any);
            ema3Ref.current?.setData(ema3 as any);
        } else {
            if (ema1Ref.current) { try { chartRef.current?.removeSeries(ema1Ref.current); } catch (e) { } ema1Ref.current = null; }
            if (ema2Ref.current) { try { chartRef.current?.removeSeries(ema2Ref.current); } catch (e) { } ema2Ref.current = null; }
            if (ema3Ref.current) { try { chartRef.current?.removeSeries(ema3Ref.current); } catch (e) { } ema3Ref.current = null; }
        }

        // Fit content
        if (chartRef.current) {
            chartRef.current.timeScale().fitContent();
        }
    }, [candles, indicatorSettings, calculateRSI, calculateEMA]);

    // Position markers
    const positionLinesRef = useRef<any[]>([]);
    const signalLinesRef = useRef<any[]>([]);

    const clearPositionMarkers = useCallback(() => {
        if (!candleSeriesRef.current) return;
        positionLinesRef.current.forEach(line => {
            try { candleSeriesRef.current?.removePriceLine(line); } catch (e) { }
        });
        positionLinesRef.current = [];
    }, []);

    const clearSignalPreviewMarkers = useCallback(() => {
        if (!candleSeriesRef.current) return;
        signalLinesRef.current.forEach(line => {
            try { candleSeriesRef.current?.removePriceLine(line); } catch (e) { }
        });
        signalLinesRef.current = [];
    }, []);

    const addSignalPreviewMarkers = useCallback((signal: SignalPreview) => {
        if (!candleSeriesRef.current || !chartRef.current) return;
        clearSignalPreviewMarkers();

        // Entry line
        const entryLine = candleSeriesRef.current.createPriceLine({
            price: signal.entry,
            color: signal.direction === 'BUY' ? '#3b82f6' : '#f97316',
            lineWidth: 2,
            lineStyle: 0,
            axisLabelVisible: true,
            title: `AI Entry ${signal.direction}`
        });
        signalLinesRef.current.push(entryLine);

        // Stop Loss line
        const slLine = candleSeriesRef.current.createPriceLine({
            price: signal.sl,
            color: '#ef4444',
            lineWidth: 2,
            lineStyle: 2,
            axisLabelVisible: true,
            title: 'AI SL'
        });
        signalLinesRef.current.push(slLine);

        // Take Profit line
        const tpLine = candleSeriesRef.current.createPriceLine({
            price: signal.tp,
            color: '#22c55e',
            lineWidth: 2,
            lineStyle: 2,
            axisLabelVisible: true,
            title: 'AI TP'
        });
        signalLinesRef.current.push(tpLine);
    }, [clearSignalPreviewMarkers]);

    // Update signal preview markers when signalPreview changes
    useEffect(() => {
        if (signalPreview) {
            // Add small delay to ensure chart is ready
            const timer = setTimeout(() => {
                addSignalPreviewMarkers(signalPreview);
            }, 100);
            return () => clearTimeout(timer);
        } else {
            clearSignalPreviewMarkers();
        }
    }, [signalPreview, addSignalPreviewMarkers, clearSignalPreviewMarkers]);

    const addPositionMarkers = useCallback((position: Position) => {
        if (!candleSeriesRef.current || !chartRef.current) return;
        clearPositionMarkers();

        const entryLine = candleSeriesRef.current.createPriceLine({
            price: position.entry,
            color: position.type === 'BUY' ? '#3b82f6' : '#f97316',
            lineWidth: 2,
            lineStyle: 0,
            axisLabelVisible: true,
            title: `Entry ${position.type}`
        });
        positionLinesRef.current.push(entryLine);

        if (position.sl && position.sl > 0) {
            const slLine = candleSeriesRef.current.createPriceLine({
                price: position.sl,
                color: '#ef4444',
                lineWidth: 2,
                lineStyle: 2,
                axisLabelVisible: true,
                title: 'SL'
            });
            positionLinesRef.current.push(slLine);
        }

        if (position.tp && position.tp > 0) {
            const tpLine = candleSeriesRef.current.createPriceLine({
                price: position.tp,
                color: '#22c55e',
                lineWidth: 2,
                lineStyle: 2,
                axisLabelVisible: true,
                title: 'TP'
            });
            positionLinesRef.current.push(tpLine);
        }
    }, [clearPositionMarkers]);

    // Track previous symbol to detect changes
    const prevSymbolRef = useRef<string>('');

    // Load data
    useEffect(() => {
        const loadData = async () => {
            const symbolToLoad = selectedPosition?.symbol || selectedPair || 'EURUSD';
            const candleCount = getCandleCountFor5Months(timeframe);

            // Check if symbol actually changed
            const symbolChanged = prevSymbolRef.current !== '' && prevSymbolRef.current !== symbolToLoad;
            prevSymbolRef.current = symbolToLoad;

            setLoading(true);

            // Clear existing candles when symbol changes
            if (symbolChanged) {
                setCandles([]);
                clearPositionMarkers();
            }

            try {
                const [candlesResponse, , positionsData] = await Promise.all([
                    getCandlesWithDigits(symbolToLoad, timeframe, candleCount),
                    getPrices(symbolToLoad),
                    getPositions()
                ]);

                // Only update if this is still the current symbol
                if (prevSymbolRef.current === symbolToLoad) {
                    setCandles(candlesResponse.candles);
                    setSymbolDigits(candlesResponse.digits);
                    setLocalPositions(positionsData);
                }

                if (candleSeriesRef.current) {
                    candleSeriesRef.current.applyOptions({
                        priceFormat: {
                            type: 'price',
                            precision: candlesResponse.digits,
                            minMove: Math.pow(10, -candlesResponse.digits)
                        }
                    });
                }

                if (selectedPosition) {
                    setTimeout(() => addPositionMarkers(selectedPosition), 100);
                }

                // Auto-reset chart like TradingView (reset view when changing pairs)
                setTimeout(() => {
                    if (chartRef.current) {
                        chartRef.current.timeScale().resetTimeScale();
                        chartRef.current.priceScale('right').applyOptions({ autoScale: true });
                        setTimeout(() => {
                            chartRef.current?.priceScale('right').applyOptions({ autoScale: false });
                        }, 200);
                    }
                }, 150);
            } catch (error) {
                console.error('Error loading chart data:', error);
            } finally {
                setLoading(false);
            }
        };

        loadData();
        return () => { clearPositionMarkers(); };
    }, [selectedPair, selectedPosition, timeframe, addPositionMarkers, clearPositionMarkers]);

    const startResizing = (mouseDownEvent: React.MouseEvent) => {
        mouseDownEvent.preventDefault();
        setIsDraggingState(true);

        const onMouseMove = (mouseMoveEvent: MouseEvent) => {
            const containerHeight = window.innerHeight - 64;
            const newTopHeight = mouseMoveEvent.clientY - 64;
            const newRatio = Math.min(Math.max(newTopHeight / containerHeight, 0.2), 0.8);
            setSplitRatio(newRatio);
        };

        const onMouseUp = () => {
            setIsDraggingState(false);
            window.removeEventListener('mousemove', onMouseMove);
            window.removeEventListener('mouseup', onMouseUp);
        };

        window.addEventListener('mousemove', onMouseMove);
        window.addEventListener('mouseup', onMouseUp);
    };

    const toggleFullscreen = () => {
        if (!document.fullscreenElement) {
            chartContainerRef.current?.parentElement?.requestFullscreen();
            setIsFullscreen(true);
        } else {
            document.exitFullscreen();
            setIsFullscreen(false);
        }
    };

    const takeScreenshot = useCallback(() => {
        if (!chartRef.current) return;
        chartRef.current.takeScreenshot().toDataURL('image/png');
    }, []);

    const resetChart = useCallback(() => {
        if (!chartRef.current) return;
        chartRef.current.timeScale().resetTimeScale();
        chartRef.current.priceScale('right').applyOptions({ autoScale: true });
        setTimeout(() => {
            chartRef.current?.priceScale('right').applyOptions({ autoScale: false });
        }, 200);
    }, []);

    // Load broker symbols
    useEffect(() => {
        const loadBrokerSymbols = async () => {
            try {
                const symbols = await getBrokerSymbols();
                setBrokerSymbols(symbols);
            } catch (error) {
                console.error('Error loading broker symbols:', error);
            }
        };
        loadBrokerSymbols();
    }, []);

    // Filter symbols based on search and category
    const filteredSymbols = brokerSymbols.filter(symbol => {
        const matchesSearch = symbolSearch === '' ||
            symbol.name.toLowerCase().includes(symbolSearch.toLowerCase()) ||
            symbol.description.toLowerCase().includes(symbolSearch.toLowerCase());
        const matchesCategory = selectedCategory === 'all' || symbol.category === selectedCategory;
        return matchesSearch && matchesCategory;
    });

    // Get unique categories
    const categories = ['all', ...new Set(brokerSymbols.map(s => s.category).filter(Boolean))];

    // Handle symbol selection
    const handleSymbolSelect = (symbol: string) => {
        setShowSymbolSelector(false);
        setSymbolSearch('');
        if (onSymbolChange) {
            onSymbolChange(symbol);
        }
    };

    // Symbol for display
    const displaySymbol = selectedPosition?.symbol || selectedPair || 'EURUSD';

    return (
        <div className="w-full h-full flex flex-col relative overflow-hidden select-none" style={{ background: theme === 'dark' ? '#131722' : '#ffffff' }}>
            {isDraggingState && chartLayout === 'split' && <div className="fixed inset-0 z-[9999] cursor-row-resize bg-transparent" />}

            {/* Chart Toolbar - TradingView Style */}
            <div className="flex items-center px-2 py-1 gap-1 border-b shrink-0 z-20" style={{
                background: theme === 'dark' ? '#1e222d' : '#ffffff',
                borderColor: theme === 'dark' ? '#2a2e39' : '#e1e1e1'
            }}>
                {/* Symbol Selector with Dropdown */}
                <div className="relative">
                    <div
                        className="flex items-center px-2 py-1 rounded hover:bg-gray-500/10 cursor-pointer"
                        onClick={() => setShowSymbolSelector(!showSymbolSelector)}
                    >
                        <span className="font-semibold text-sm" style={{ color: theme === 'dark' ? '#d1d4db' : '#4a4a4a' }}>
                            {displaySymbol}
                        </span>
                        <svg className="ml-1" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <polyline points="6 9 12 15 18 9" />
                        </svg>
                    </div>

                    {/* Symbol Dropdown */}
                    {showSymbolSelector && (
                        <div
                            className="absolute left-0 top-full mt-1 w-72 max-h-96 overflow-hidden rounded-lg shadow-xl z-50"
                            style={{
                                background: theme === 'dark' ? '#1e222d' : '#ffffff',
                                border: `1px solid ${theme === 'dark' ? '#2a2e39' : '#e1e1e1'}`
                            }}
                        >
                            {/* Search */}
                            <div className="p-2 border-b" style={{ borderColor: theme === 'dark' ? '#2a2e39' : '#e1e1e1' }}>
                                <input
                                    type="text"
                                    placeholder="Search symbols..."
                                    value={symbolSearch}
                                    onChange={(e) => setSymbolSearch(e.target.value)}
                                    className="w-full px-2 py-1 text-xs rounded outline-none"
                                    style={{
                                        background: theme === 'dark' ? '#2a2e39' : '#f0f0f0',
                                        color: theme === 'dark' ? '#d1d4db' : '#4a4a4a'
                                    }}
                                    autoFocus
                                />
                            </div>

                            {/* Category Filter */}
                            <div className="flex gap-1 p-2 overflow-x-auto border-b" style={{ borderColor: theme === 'dark' ? '#2a2e39' : '#e1e1e1' }}>
                                {categories.slice(0, 6).map(cat => (
                                    <button
                                        key={cat}
                                        onClick={() => setSelectedCategory(cat)}
                                        className={`px-2 py-0.5 text-xs rounded whitespace-nowrap ${selectedCategory === cat ? 'bg-blue-500 text-white' : ''}`}
                                        style={{
                                            background: selectedCategory === cat ? '#2962ff' : theme === 'dark' ? '#2a2e39' : '#f0f0f0',
                                            color: selectedCategory === cat ? '#fff' : theme === 'dark' ? '#d1d4db' : '#4a4a4a'
                                        }}
                                    >
                                        {cat || 'other'}
                                    </button>
                                ))}
                            </div>

                            {/* Symbol List */}
                            <div className="overflow-y-auto max-h-64">
                                {filteredSymbols.slice(0, 100).map(symbol => (
                                    <div
                                        key={symbol.name}
                                        onClick={() => handleSymbolSelect(symbol.name)}
                                        className="flex justify-between items-center px-3 py-1.5 cursor-pointer hover:bg-blue-500/20"
                                        style={{ borderBottom: `1px solid ${theme === 'dark' ? '#1e222d' : '#f0f0f0'}` }}
                                    >
                                        <span className="text-xs font-medium" style={{ color: theme === 'dark' ? '#d1d4db' : '#4a4a4a' }}>
                                            {symbol.name}
                                        </span>
                                        <span className="text-xs truncate ml-2 max-w-32" style={{ color: theme === 'dark' ? '#6b7280' : '#9ca3af' }}>
                                            {symbol.description}
                                        </span>
                                    </div>
                                ))}
                                {filteredSymbols.length === 0 && (
                                    <div className="p-4 text-center text-xs" style={{ color: theme === 'dark' ? '#6b7280' : '#9ca3af' }}>
                                        No symbols found
                                    </div>
                                )}
                            </div>
                        </div>
                    )}
                </div>

                {/* Timeframe Selector */}
                <div className="flex items-center rounded overflow-hidden" style={{ background: theme === 'dark' ? '#2a2e39' : '#f0f0f0' }}>
                    {TIMEFRAMES.map((tf) => (
                        <button
                            key={tf.value}
                            onClick={() => setTimeframe(tf.value)}
                            className={`px-2 py-1 text-xs font-medium transition-colors ${timeframe === tf.value
                                ? 'bg-blue-500 text-white'
                                : 'hover:bg-gray-500/20'
                                }`}
                            style={{ color: timeframe === tf.value ? '#fff' : theme === 'dark' ? '#d1d4db' : '#4a4a4a' }}
                        >
                            {tf.label}
                        </button>
                    ))}
                </div>

                {/* Separator */}
                <div className="w-px h-5 mx-1" style={{ background: theme === 'dark' ? '#2a2e39' : '#e1e1e1' }} />

                {/* Indicators Button */}
                <button
                    onClick={() => setShowIndicatorPanel(!showIndicatorPanel)}
                    className={`flex items-center px-2 py-1 rounded hover:bg-gray-500/10 ${showIndicatorPanel ? 'bg-blue-500/20' : ''}`}
                    title="Indicators"
                >
                    <Icons.Indicator />
                </button>

                {/* Reset */}
                <button
                    onClick={resetChart}
                    className="flex items-center px-2 py-1 rounded hover:bg-gray-500/10"
                    title="Reset Chart"
                >
                    <Icons.Reset />
                </button>

                {/* Separator */}
                <div className="w-px h-5 mx-1" style={{ background: theme === 'dark' ? '#2a2e39' : '#e1e1e1' }} />

                {/* Screenshot */}
                <button
                    onClick={takeScreenshot}
                    className="flex items-center px-2 py-1 rounded hover:bg-gray-500/10"
                    title="Take Screenshot"
                >
                    <Icons.Camera />
                </button>

                {/* Fullscreen */}
                <button
                    onClick={toggleFullscreen}
                    className="flex items-center px-2 py-1 rounded hover:bg-gray-500/10"
                    title="Fullscreen"
                >
                    <Icons.Fullscreen />
                </button>

                {/* Price Data Display */}
                <div className="ml-auto flex items-center gap-3 text-xs" style={{ color: theme === 'dark' ? '#d1d4db' : '#4a4a4a' }}>
                    {priceData && (
                        <>
                            <span>O: <span style={{ color: priceData.close >= priceData.open ? '#26a69a' : '#ef5350' }}>{priceData.open.toFixed(symbolDigits)}</span></span>
                            <span>H: <span className="text-green-500">{priceData.high.toFixed(symbolDigits)}</span></span>
                            <span>L: <span className="text-red-500">{priceData.low.toFixed(symbolDigits)}</span></span>
                            <span>C: <span style={{ color: priceData.close >= priceData.open ? '#26a69a' : '#ef5350', fontWeight: 'bold' }}>{priceData.close.toFixed(symbolDigits)}</span></span>
                            <span className="text-gray-500">{priceData.time}</span>
                        </>
                    )}
                    <span className="text-gray-500">| {candles.length} bars</span>
                </div>
            </div>

            {/* Chart Container with relative positioning for indicator panel */}
            <div
                style={{ height: chartLayout === 'single' ? 'calc(100% - 36px)' : `calc(${(1 - splitRatio) * 100}% - 36px)` }}
                className="w-full relative"
                ref={chartContainerRef}
            >
                {/* Signal Preview Floating Action Button - REMOVED as per request */}
                {/* 
                   Previously contained buttons for clearing signal lines and executing orders.
                   These are no longer needed here.
                */}

                {/* Indicator Panel - inside chart container */}
                {showIndicatorPanel && (
                    <div className="absolute left-2 top-2 z-50 p-2 rounded shadow-lg" style={{
                        background: theme === 'dark' ? '#1e222d' : '#ffffff',
                        border: `1px solid ${theme === 'dark' ? '#2a2e39' : '#e1e1e1'}`
                    }}>
                        <div className="text-xs font-semibold mb-2 px-2" style={{ color: theme === 'dark' ? '#d1d4db' : '#4a4a4a' }}>
                            Indicators
                        </div>
                        <div className="flex flex-col gap-1">
                            {[
                                { key: 'rsi', label: 'RSI (14)', checked: indicatorSettings.rsi.visible },
                                { key: 'ema', label: 'EMA (9,21,50)', checked: indicatorSettings.ema.visible },
                                { key: 'macd', label: 'MACD', checked: indicatorSettings.macd.visible },
                                { key: 'bollinger', label: 'Bollinger Bands', checked: indicatorSettings.bollinger.visible },
                                { key: 'volume', label: 'Volume', checked: indicatorSettings.volume.visible },
                            ].map((item) => (
                                <label key={item.key} className="flex items-center gap-2 px-2 py-1 rounded hover:bg-gray-500/10 cursor-pointer">
                                    <input
                                        type="checkbox"
                                        checked={item.checked}
                                        onChange={(e) => {
                                            setIndicatorSettings(prev => ({
                                                ...prev,
                                                [item.key]: { ...prev[item.key as keyof IndicatorSettings], visible: e.target.checked }
                                            }));
                                            // Reset chart when changing indicators
                                            setTimeout(() => {
                                                if (chartRef.current) {
                                                    chartRef.current.timeScale().resetTimeScale();
                                                    chartRef.current.priceScale('right').applyOptions({ autoScale: true });
                                                    setTimeout(() => {
                                                        chartRef.current?.priceScale('right').applyOptions({ autoScale: false });
                                                    }, 200);
                                                }
                                            }, 50);
                                        }}
                                        className="rounded"
                                    />
                                    <span className="text-xs" style={{ color: theme === 'dark' ? '#d1d4db' : '#4a4a4a' }}>
                                        {item.label}
                                    </span>
                                </label>
                            ))}
                        </div>
                    </div>
                )}
                {loading && chartLayout === 'single' && (
                    <div className="absolute inset-0 flex items-center justify-center bg-background/50">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
                    </div>
                )}
            </div>
        </div>
    );
}