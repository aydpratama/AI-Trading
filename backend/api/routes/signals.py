"""
AI Signals API Routes - Enhanced with external AI providers
"""
from fastapi import APIRouter, HTTPException, Query, Header
from fastapi.responses import JSONResponse
from datetime import datetime
from typing import Optional
from mt5.connector import connector
from ai.genius_ai import genius_ai
from ai.ai_service import ai_service
import logging
import asyncio

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/signals", tags=["signals"])


@router.get("/analyze")
async def analyze_symbol(
    symbol: str = Query(...),
    timeframe: str = Query(default="H1"),
    risk_level: str = Query(default="moderate"),
    capital: Optional[float] = Query(default=None),
    risk_percent: Optional[float] = Query(default=None),
    ai_provider: Optional[str] = Query(default=None),
    x_api_key: Optional[str] = Header(default=None)
):
    """
    Get AI analysis for a symbol

    Parameters:
    - symbol: Trading symbol (e.g., EURUSD, XAUUSD)
    - timeframe: Chart timeframe (M5, M15, H1, H4, D1)
    - risk_level: Risk level (conservative/moderate/aggressive)
    - capital: Optional custom capital
    - risk_percent: Optional explicit risk percentage (e.g., 1.0, 2.0)
    - ai_provider: AI provider to use (gemini, openai, kimi, zai)
    - x-api-key: API key for AI provider (via header)
    """
    try:
        # Check MT5 connection with better error handling
        if not connector.is_connected():
            logger.warning(f"MT5 not connected when analyzing {symbol}")
            return {
                "id": None,
                "symbol": symbol,
                "timeframe": timeframe,
                "status": "ERROR",
                "error": "MT5 tidak terkoneksi. Silakan cek MT5 terminal dan credentials.",
                "signal": None,
                "analysis": None,
                "setup": None,
                "recommendation": "WAIT"
            }

        logger.info(f"Analyze request: symbol={symbol}, ai_provider={ai_provider}, has_api_key={bool(x_api_key)}")

        # Get base technical analysis with try-catch for better error handling
        try:
            analysis = genius_ai.analyze(symbol, timeframe, risk_level, custom_capital=capital, risk_percentage=risk_percent)
        except Exception as e:
            logger.error(f"Error in genius_ai.analyze() for {symbol}: {e}")
            return {
                "id": None,
                "symbol": symbol,
                "timeframe": timeframe,
                "status": "ERROR",
                "error": f"Analysis error: {str(e)}",
                "signal": None,
                "analysis": None,
                "setup": None,
                "recommendation": "WAIT"
            }

        # If AI provider and API key provided, enhance with AI
        api_key = x_api_key
        if ai_provider and api_key and analysis.get("signal"):
            logger.info(f"Enhancing analysis with {ai_provider} for {symbol}")

            try:
                # Pass ENHANCED data to AI service - complete analysis dictionary
                ai_insight = await ai_service.analyze_with_ai(
                    provider=ai_provider,
                    api_key=api_key,
                    symbol=symbol,
                    timeframe=timeframe,
                    # Pass complete analysis data (not just technical)
                    technical_data=analysis.get("analysis", {}),
                    signal_data=analysis.get("signal", {})
                )

                if ai_insight:
                    # Add AI insights to response
                    analysis["ai_insight"] = ai_insight

                    # Adjust confidence if AI agrees/disagrees
                    if ai_insight.get("agreement"):
                        adjustment = ai_insight.get("confidence_adjustment", 5)
                        analysis["signal"]["confidence"] = min(95, analysis["signal"]["confidence"] + adjustment)
                        analysis["signal"]["reasons"].append(f"✅ AI ({ai_provider}) agrees")
                    else:
                        adjustment = ai_insight.get("confidence_adjustment", -10)
                        analysis["signal"]["confidence"] = max(40, analysis["signal"]["confidence"] + adjustment)
                        if ai_insight.get("ai_direction") == "WAIT":
                            analysis["signal"]["reasons"].append(f"⚠️ AI ({ai_provider}) suggests WAIT")
                            analysis["recommendation"] = "WAIT"
                        else:
                            analysis["signal"]["reasons"].append(f"❌ AI ({ai_provider}) disagrees")

                    # Add AI reasoning
                    if ai_insight.get("reasoning"):
                        analysis["ai_reasoning"] = ai_insight["reasoning"]

                    # Add risk warning
                    if ai_insight.get("risk_warning"):
                        if not analysis.get("setup", {}).get("risk_assessment"):
                            analysis["setup"]["risk_assessment"] = {"warnings": []}
                        analysis["setup"]["risk_assessment"]["warnings"].append(ai_insight["risk_warning"])

                    # Update key levels if provided
                    if ai_insight.get("key_levels"):
                        analysis["ai_key_levels"] = ai_insight["key_levels"]

                    logger.info(f"AI enhancement complete for {symbol}")
                else:
                    logger.warning(f"AI service returned no insight for {symbol}")
                    analysis["ai_error"] = f"AI ({ai_provider}) tidak mengembalikan hasil. Coba lagi nanti."

            except Exception as e:
                logger.error(f"Error enhancing with AI: {e}")
                # Continue without AI enhancement
                analysis["ai_error"] = str(e)

        # Auto-send Telegram notification for strong signals
        if analysis.get("signal") and analysis["signal"].get("confidence", 0) >= 70:
            try:
                from notification.telegram import telegram_notifier
                if telegram_notifier.enabled:
                    setup = analysis.get("setup", {})
                    notif_data = {
                        "symbol": symbol,
                        "direction": analysis["signal"]["direction"],
                        "confidence": analysis["signal"]["confidence"],
                        "entry": setup.get("entry", 0),
                        "stop_loss": setup.get("stop_loss", 0),
                        "take_profit": setup.get("take_profit", 0),
                        "lot_size": setup.get("lot_size", 0),
                        "risk_reward": setup.get("risk_reward", 0),
                        "reasons": analysis["signal"].get("reasons", [])
                    }
                    asyncio.create_task(telegram_notifier.send_signal(notif_data))
            except Exception as e:
                logger.error(f"Error sending Telegram notification: {e}")

        return analysis

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in analyze_symbol: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scan")
async def scan_signals(
    symbols: Optional[str] = Query(default=None),
    timeframe: str = Query(default="H1"),
    risk_level: str = Query(default="moderate"),
    min_confidence: int = Query(default=60),
    ai_provider: Optional[str] = Query(default=None),
    x_api_key: Optional[str] = Header(default=None)
):
    """
    Scan multiple symbols for signals

    Optionally enhance with AI if provider and key provided
    """
    try:
        if not connector.is_connected():
            raise HTTPException(status_code=503, detail="MT5 tidak terkoneksi")

        # Get symbols to scan
        if symbols:
            symbol_list = symbols.split(",")
        else:
            # Default symbols
            symbol_list = ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD"]

        results = []
        api_key = x_api_key

        for symbol in symbol_list:
            try:
                analysis = genius_ai.analyze(symbol.strip(), timeframe, risk_level)

                if analysis and analysis.get("signal"):
                    signal = analysis["signal"]

                    if signal.get("confidence", 0) >= min_confidence:
                        # Optionally enhance with AI (only for top signals to save API calls)
                        if ai_provider and api_key and signal.get("confidence", 0) >= 70:
                            try:
                                ai_insight = await ai_service.analyze_with_ai(
                                    provider=ai_provider,
                                    api_key=api_key,
                                    symbol=symbol.strip(),
                                    timeframe=timeframe,
                                    technical_data=analysis.get("analysis", {}),
                                    signal_data=signal
                                )

                                if ai_insight:
                                    signal["ai_agreement"] = ai_insight.get("agreement")
                                    signal["ai_reasoning"] = ai_insight.get("reasoning")
                            except:
                                pass

                        results.append({
                            "symbol": symbol.strip(),
                            "signal": signal,
                            "recommendation": analysis.get("recommendation"),
                            "ai_enhanced": bool(ai_provider and api_key),
                            "timestamp": datetime.now().isoformat()
                        })

            except Exception as e:
                logger.error(f"Error analyzing {symbol}: {e}")
                continue

        # Sort by confidence
        results.sort(key=lambda x: x["signal"]["confidence"], reverse=True)

        return {"signals": results, "count": len(results), "ai_provider": ai_provider}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in scan_signals: {e}")
        raise HTTPException(status_code=500, detail=str(e))
