export interface BrokerInstrument {
    symbol: string;
    description: string;
    tickSize: number;
    spread: number;
    commission: number;
    stopLevel: number;
    contractSize: number;
}

export const BROKER_DATA: BrokerInstrument[] = [
    {
        symbol: "AUDCAD",
        description: "Dolar Australia / Dolar Kanada",
        tickSize: 0.00001,
        spread: 0.00014,
        commission: 1.00,
        stopLevel: 0,
        contractSize: 100000
    },
    {
        symbol: "AUDCHF",
        description: "Dolar Australia / Franc Swiss",
        tickSize: 0.00001,
        spread: 0.00007,
        commission: 1.00,
        stopLevel: 0,
        contractSize: 100000
    },
    {
        symbol: "AUDJPY",
        description: "Dolar Australia / Yen Jepang",
        tickSize: 0.001,
        spread: 0.011,
        commission: 1.00,
        stopLevel: 0,
        contractSize: 100000
    },
    {
        symbol: "AUDNZD",
        description: "Dolar Australia / Dolar Selandia Baru",
        tickSize: 0.00001,
        spread: 0.00012,
        commission: 1.00,
        stopLevel: 0,
        contractSize: 100000
    },
    {
        symbol: "AUDUSD",
        description: "Dolar Australia / Dolar AS",
        tickSize: 0.00001,
        spread: 0.00007,
        commission: 1.00,
        stopLevel: 0,
        contractSize: 100000
    },
    {
        symbol: "CADJPY",
        description: "Dolar Kanada / Yen Jepang",
        tickSize: 0.001,
        spread: 0.013,
        commission: 1.00,
        stopLevel: 0,
        contractSize: 100000
    },
    {
        symbol: "CHFJPY",
        description: "Franc Swiss / Yen Jepang",
        tickSize: 0.001,
        spread: 0.015,
        commission: 1.00,
        stopLevel: 0,
        contractSize: 100000
    },
    {
        symbol: "EURAUD",
        description: "Euro / Dolar Australia",
        tickSize: 0.00001,
        spread: 0.00011,
        commission: 1.00,
        stopLevel: 0,
        contractSize: 100000
    },
    {
        symbol: "EURCAD",
        description: "Euro / Dolar Kanada",
        tickSize: 0.00001,
        spread: 0.00011,
        commission: 1.00,
        stopLevel: 0,
        contractSize: 100000
    },
    {
        symbol: "EURCHF",
        description: "Euro / Franc Swiss",
        tickSize: 0.00001,
        spread: 0.00013,
        commission: 1.00,
        stopLevel: 0,
        contractSize: 100000
    },
    {
        symbol: "EURGBP",
        description: "Euro / Pound Inggris",
        tickSize: 0.00001,
        spread: 0.00008,
        commission: 1.00,
        stopLevel: 0,
        contractSize: 100000
    },
    {
        symbol: "EURJPY",
        description: "Euro / Yen Jepang",
        tickSize: 0.001,
        spread: 0.009,
        commission: 1.00,
        stopLevel: 0,
        contractSize: 100000
    },
    {
        symbol: "EURNZD",
        description: "Euro / Dolar Selandia Baru",
        tickSize: 0.00001,
        spread: 0.0002,
        commission: 1.00,
        stopLevel: 0,
        contractSize: 100000
    },
    {
        symbol: "EURUSD",
        description: "Euro / Dolar AS",
        tickSize: 0.00001,
        spread: 0.00005,
        commission: 1.00,
        stopLevel: 0,
        contractSize: 100000
    },
    {
        symbol: "GBPAUD",
        description: "Pound Inggris / Dolar Australia",
        tickSize: 0.00001,
        spread: 0.00015,
        commission: 1.00,
        stopLevel: 0,
        contractSize: 100000
    },
    {
        symbol: "GBPCAD",
        description: "Pound Inggris / Dolar Kanada",
        tickSize: 0.00001,
        spread: 0.00019,
        commission: 1.00,
        stopLevel: 0,
        contractSize: 100000
    },
    {
        symbol: "GBPCHF",
        description: "Pound Inggris / Franc Swiss",
        tickSize: 0.00001,
        spread: 0.00015,
        commission: 1.00,
        stopLevel: 0,
        contractSize: 100000
    },
    {
        symbol: "GBPJPY",
        description: "Pound Inggris / Yen Jepang",
        tickSize: 0.001,
        spread: 0.011,
        commission: 1.00,
        stopLevel: 0,
        contractSize: 100000
    },
    {
        symbol: "GBPNZD",
        description: "Pound Inggris / Dolar Selandia Baru",
        tickSize: 0.00001,
        spread: 0.00027,
        commission: 1.00,
        stopLevel: 0,
        contractSize: 100000
    },
    {
        symbol: "GBPUSD",
        description: "Pound Inggris / Dolar AS",
        tickSize: 0.00001,
        spread: 0.00005,
        commission: 1.00,
        stopLevel: 0,
        contractSize: 100000
    },
    {
        symbol: "NZDCAD",
        description: "Dolar Selandia Baru / Dolar Kanada",
        tickSize: 0.00001,
        spread: 0.00012,
        commission: 1.00,
        stopLevel: 0,
        contractSize: 100000
    },
    {
        symbol: "NZDCHF",
        description: "Dolar Selandia Baru / Franc Swiss",
        tickSize: 0.00001,
        spread: 0.00009,
        commission: 1.00,
        stopLevel: 0,
        contractSize: 100000
    },
    {
        symbol: "NZDJPY",
        description: "Dolar Selandia Baru / Yen Jepang",
        tickSize: 0.001,
        spread: 0.015,
        commission: 1.00,
        stopLevel: 0,
        contractSize: 100000
    },
    {
        symbol: "NZDUSD",
        description: "Dolar Selandia Baru / Dolar AS",
        tickSize: 0.00001,
        spread: 0.00009,
        commission: 1.00,
        stopLevel: 0,
        contractSize: 100000
    },
    {
        symbol: "USDCAD",
        description: "Dolar AS / Dolar Kanada",
        tickSize: 0.00001,
        spread: 0.00008,
        commission: 1.00,
        stopLevel: 0,
        contractSize: 100000
    },
    {
        symbol: "USDCHF",
        description: "Dolar AS / Franc Swiss",
        tickSize: 0.00001,
        spread: 0.00006,
        commission: 1.00,
        stopLevel: 0,
        contractSize: 100000
    },
    {
        symbol: "USDJPY",
        description: "Dolar AS / Yen Jepang",
        tickSize: 0.001,
        spread: 0.006,
        commission: 1.00,
        stopLevel: 0,
        contractSize: 100000
    },
    // Commodities
    {
        symbol: "XAGUSD",
        description: "Perak / Dolar AS",
        tickSize: 0.001,
        spread: 0.0198,
        commission: 1.00,
        stopLevel: 10,
        contractSize: 5000
    },
    {
        symbol: "XAUUSD",
        description: "Emas / Dolar AS",
        tickSize: 0.01,
        spread: 0.14,
        commission: 1.00,
        stopLevel: 10,
        contractSize: 100
    },
    // Indices
    {
        symbol: "DE30",
        description: "Dow Jones Germany Titans 30",
        tickSize: 0.5,
        spread: 3.9,
        commission: 1.00,
        stopLevel: 500,
        contractSize: 25
    },
    {
        symbol: "HK50",
        description: "Hong Kong 50",
        tickSize: 1,
        spread: 7.4,
        commission: 1.00,
        stopLevel: 15,
        contractSize: 5
    },
    {
        symbol: "JP225",
        description: "Japan 225",
        tickSize: 5,
        spread: 11.4,
        commission: 1.00,
        stopLevel: 15,
        contractSize: 5
    },
    {
        symbol: "UK100",
        description: "FTSE 100",
        tickSize: 0.5,
        spread: 1.7,
        commission: 1.00,
        stopLevel: 500,
        contractSize: 10
    },
    {
        symbol: "US100",
        description: "Nasdaq-100",
        tickSize: 0.25,
        spread: 1.9,
        commission: 1.00,
        stopLevel: 500,
        contractSize: 20
    },
    {
        symbol: "US30",
        description: "Dow Jones Industrial Average",
        tickSize: 1,
        spread: 2.9,
        commission: 1.00,
        stopLevel: 15,
        contractSize: 5
    },
    {
        symbol: "US500",
        description: "S&P 500",
        tickSize: 0.25,
        spread: 1.4,
        commission: 1.00,
        stopLevel: 500,
        contractSize: 50
    }
];

export interface BrokerAccountConfig {
    commissionPerLot: number; // USD
    leverage: {
        forexMetals: number;
        indicesEnergies: number;
        stocks: number;
    };
    minTradeVolume: number; // Lots
    spreadType: 'Floating' | 'Fixed';
    minSpread: number; // Pips
}

export const BROKER_ACCOUNT_CONFIG: BrokerAccountConfig = {
    commissionPerLot: 1.00,
    leverage: {
        forexMetals: 500,
        indicesEnergies: 200,
        stocks: 25
    },
    minTradeVolume: 0.01,
    spreadType: 'Floating',
    minSpread: 0.5
};
