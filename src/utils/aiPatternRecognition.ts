
export interface CandleData {
    time: string;
    open: number;
    high: number;
    low: number;
    close: number;
    color?: string;
    borderColor?: string;
    wickColor?: string;
}

const formatDate = (date: Date): string => {
    return date.toISOString().split('T')[0];
};

/**
 * Generates Realistic AI-detected Chart Patterns
 * Sekarang dengan "Market Noise" agar candle terlihat alami (tidak terlalu rapi/buatan).
 */
export function generateSmartPatternData(basePrice: number = 25000): CandleData[] {
    const data: CandleData[] = [];
    let currentPrice = basePrice;
    let currentDate = new Date();
    currentDate.setDate(currentDate.getDate() - 100);

    const AI_PATTERN_COLOR = '#F59E0B'; // Gold for Pattern

    const randomRange = (min: number, max: number) => Math.random() * (max - min) + min;

    const addCandle = (trendBias: number, volatility: number, isPattern: boolean = false) => {
        const open = currentPrice;

        // 1. Natural Volatility (Chaos Factor)
        const noise = (Math.random() - 0.5) * volatility * 1.5;
        const trendMove = trendBias * volatility;

        let change = trendMove + noise;

        // 2. Occasional "Big Moves" (Momentum Candles)
        if (Math.random() > 0.9) change *= 1.5;

        const close = open + change;

        // 3. Realistic Wicks (Shadows)
        const bodyHigh = Math.max(open, close);
        const bodyLow = Math.min(open, close);

        const highWick = Math.random() * volatility * (Math.random() > 0.7 ? 1.0 : 0.3);
        const lowWick = Math.random() * volatility * (Math.random() > 0.7 ? 1.0 : 0.3);

        const high = bodyHigh + highWick;
        const low = bodyLow - lowWick;

        currentPrice = close; // Continuity
        currentDate.setDate(currentDate.getDate() + 1);

        const candle: CandleData = {
            time: formatDate(currentDate),
            open: Number(open.toFixed(2)),
            high: Number(high.toFixed(2)),
            low: Number(low.toFixed(2)),
            close: Number(close.toFixed(2)),
        };

        if (isPattern) {
            candle.color = AI_PATTERN_COLOR;
            candle.borderColor = AI_PATTERN_COLOR;
            candle.wickColor = AI_PATTERN_COLOR;
        }

        data.push(candle);
    };

    const VOLATILITY = 300;

    // 1. Pre-Pattern Noise (Sideways/Choppy)
    for (let i = 0; i < 15; i++) {
        addCandle(randomRange(-0.2, 0.2), VOLATILITY * 0.8);
    }

    // 2. Initial Uptrend (Rally)
    for (let i = 0; i < 15; i++) {
        const isPullback = Math.random() > 0.8;
        addCandle(isPullback ? -0.5 : 0.8, VOLATILITY);
    }

    // --- PATTERN FORMATION (HEAD & SHOULDERS) ---
    // Left Shoulder
    for (let i = 0; i < 4; i++) addCandle(0.6, VOLATILITY * 1.2, true);
    addCandle(-0.2, VOLATILITY, true);
    for (let i = 0; i < 3; i++) addCandle(-0.5, VOLATILITY, true);

    // Head
    for (let i = 0; i < 5; i++) addCandle(1.0, VOLATILITY * 1.5, true);
    addCandle(0.1, VOLATILITY * 2, true);
    for (let i = 0; i < 5; i++) addCandle(-0.9, VOLATILITY * 1.5, true);

    // Right Shoulder
    for (let i = 0; i < 4; i++) addCandle(0.5, VOLATILITY, true);
    addCandle(0, VOLATILITY, true);
    for (let i = 0; i < 4; i++) addCandle(-0.7, VOLATILITY * 1.2, true);

    // --- POST PATTERN ---
    // 3. Breakdown & Panic Dump
    for (let i = 0; i < 5; i++) {
        addCandle(-1.2, VOLATILITY * 2);
    }

    // 4. Consolidation
    for (let i = 0; i < 15; i++) {
        addCandle(randomRange(-0.3, 0.3), VOLATILITY);
    }

    return data;
}

/**
 * Calculates RSI (Relative Strength Index)
 * Uses Wilder's Smoothing method for accuracy.
 */
export function calculateRSI(data: CandleData[], period: 14 = 14): { time: string, value: number }[] {
    const rsiData: { time: string, value: number }[] = [];

    if (data.length <= period) return rsiData;

    let avgGain = 0;
    let avgLoss = 0;

    // 1. Calculate Initial Average (Simple Moving Average)
    for (let i = 1; i <= period; i++) {
        const change = data[i].close - data[i - 1].close;
        if (change > 0) avgGain += change;
        else avgLoss += Math.abs(change);
    }

    avgGain /= period;
    avgLoss /= period;

    // 2. Wilder's Smoothing Loop
    for (let i = period + 1; i < data.length; i++) {
        const change = data[i].close - data[i - 1].close;
        const gain = change > 0 ? change : 0;
        const loss = change < 0 ? Math.abs(change) : 0;

        // Formula: Previous Average * (period - 1) + Current Gain / period
        avgGain = ((avgGain * (period - 1)) + gain) / period;
        avgLoss = ((avgLoss * (period - 1)) + loss) / period;

        let rs = 0;
        if (avgLoss !== 0) {
            rs = avgGain / avgLoss;
        }

        const rsi = avgLoss === 0 ? 100 : 100 - (100 / (1 + rs));

        rsiData.push({
            time: data[i].time,
            value: Number(rsi.toFixed(2))
        });
    }

    return rsiData;
}
