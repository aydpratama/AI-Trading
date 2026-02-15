"""
AI Service - Integration with external AI providers (Gemini, OpenAI, etc.)
"""
import httpx
import logging
import json
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class AIService:
    """Service untuk komunikasi dengan AI providers"""

    # API endpoints
    ENDPOINTS = {
        "gemini": "https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent",
        "google": "https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent",
        "openai": "https://api.openai.com/v1/chat/completions",
        "kimi": "https://api.moonshot.cn/v1/chat/completions",
        "zai": "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    }

    # Available models for each provider
    MODELS = {
        "zai": ["glm-4-plus", "glm-4-air", "glm-3-turbo"],
        "kimi": ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"],
        "openai": ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"]
    }

    async def analyze_with_ai(
        self,
        provider: str,
        api_key: str,
        symbol: str,
        timeframe: str,
        technical_data: Dict[str, Any],
        signal_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Gunakan AI untuk enhance analisis trading

        Returns:
            Dict dengan AI insights, enhanced confidence, dan reasoning
        Raises:
            Exception with descriptive error message for the frontend
        """
        provider = provider.lower()

        if provider in ["gemini", "google"]:
            return await self._call_gemini(api_key, symbol, timeframe, technical_data, signal_data)
        elif provider == "openai":
            return await self._call_openai(api_key, symbol, timeframe, technical_data, signal_data)
        elif provider in ["kimi", "zai"]:
            return await self._call_openai_compatible(provider, api_key, symbol, timeframe, technical_data, signal_data)
        else:
            raise Exception(f"AI provider '{provider}' tidak dikenali. Gunakan: gemini, openai, kimi, atau zai.")

    async def _call_gemini(
        self,
        api_key: str,
        symbol: str,
        timeframe: str,
        technical_data: Dict[str, Any],
        signal_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Call Gemini API untuk analisis trading"""

        prompt = self._build_trading_prompt(symbol, timeframe, technical_data, signal_data)

        url = f"{self.ENDPOINTS['gemini']}?key={api_key}"

        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 2048
            }
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, json=payload)

                if response.status_code == 200:
                    data = response.json()
                    candidates = data.get("candidates", [])
                    if not candidates:
                        logger.error(f"No candidates in Gemini response for {symbol}")
                        return None

                    # Extract text from all parts (gemini-3 may have thinking + response parts)
                    parts = candidates[0].get("content", {}).get("parts", [])
                    text = ""
                    for part in parts:
                        if "text" in part:
                            # Use the last text part (which is typically the actual response, not thinking)
                            text = part["text"]

                    if not text:
                        logger.error(f"Empty text in Gemini response for {symbol}")
                        return None

                    logger.info(f"Gemini raw response for {symbol}: {text[:200]}...")
                    result = self._parse_ai_response(text)
                    if result is None:
                        logger.error(f"Failed to parse Gemini response for {symbol}: {text[:300]}")
                    return result
                elif response.status_code == 429:
                    logger.error(f"Gemini API quota exceeded")
                    raise Exception("Kuota API Gemini habis. Periksa billing di Google AI Studio.")
                elif response.status_code == 403:
                    logger.error(f"Gemini API forbidden: invalid API key")
                    raise Exception("API Key Gemini tidak valid atau tidak memiliki akses.")
                else:
                    error_msg = response.text[:200]
                    logger.error(f"Gemini API error: {response.status_code} - {error_msg}")
                    raise Exception(f"Gemini error {response.status_code}: {error_msg}")

        except httpx.TimeoutException:
            logger.error("Gemini API timeout")
            raise Exception("Gemini API timeout - server tidak merespons dalam 60 detik")
        except Exception as e:
            if "Kuota" in str(e) or "API Key" in str(e) or "timeout" in str(e).lower() or "Gemini error" in str(e):
                raise  # Re-raise our specific errors
            logger.error(f"Gemini API error: {e}")
            raise Exception(f"Gemini error: {str(e)}")

    async def _call_openai(
        self,
        api_key: str,
        symbol: str,
        timeframe: str,
        technical_data: Dict[str, Any],
        signal_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Call OpenAI API untuk analisis trading"""

        prompt = self._build_trading_prompt(symbol, timeframe, technical_data, signal_data)

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "You are an expert forex/trading analyst. Respond only with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 1024
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(self.ENDPOINTS["openai"], headers=headers, json=payload)

                if response.status_code == 200:
                    data = response.json()
                    text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    return self._parse_ai_response(text)
                else:
                    logger.error(f"OpenAI API error: {response.status_code}")
                    return None

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return None

    async def _call_openai_compatible(
        self,
        provider: str,
        api_key: str,
        symbol: str,
        timeframe: str,
        technical_data: Dict[str, Any],
        signal_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Call OpenAI-compatible API (Kimi, ZAI)"""

        prompt = self._build_trading_prompt(symbol, timeframe, technical_data, signal_data)

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        # Updated model names - ZAI uses glm-4-plus (glm-4 and glm-4-flash are deprecated)
        model = "glm-4-plus" if provider == "zai" else "moonshot-v1-8k"

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are an expert forex/trading analyst. Respond only with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 1024
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                logger.info(f"Calling {provider} API with model {model} for {symbol}")
                response = await client.post(self.ENDPOINTS[provider], headers=headers, json=payload)

                if response.status_code == 200:
                    data = response.json()
                    choices = data.get("choices", [])
                    if not choices:
                        error_msg = f"{provider} response has no choices: {str(data)[:300]}"
                        logger.error(error_msg)
                        raise Exception(error_msg)

                    text = choices[0].get("message", {}).get("content", "")
                    if not text:
                        raise Exception(f"{provider} returned empty content")

                    result = self._parse_ai_response(text)
                    if result is None:
                        raise Exception(f"Failed to parse {provider} response JSON: {text[:200]}")

                    logger.info(f"{provider} analysis complete for {symbol}")
                    return result
                elif response.status_code == 401:
                    logger.error(f"{provider} API unauthorized: invalid API key")
                    raise Exception(f"API Key {provider.upper()} tidak valid atau tidak memiliki akses.")
                elif response.status_code == 429:
                    logger.error(f"{provider} API rate limit exceeded")
                    raise Exception(f"Kuota API {provider.upper()} habis atau rate limit exceeded. Coba lagi nanti.")
                elif response.status_code == 403:
                    logger.error(f"{provider} API forbidden")
                    raise Exception(f"Akses ditolak oleh {provider.upper()}. Periksa permission API Key.")
                elif response.status_code == 500 or response.status_code == 502 or response.status_code == 503:
                    logger.error(f"{provider} API server error: {response.status_code}")
                    raise Exception(f"Server {provider.upper()} sedang mengalami gangguan ({response.status_code}). Coba lagi nanti.")
                else:
                    error_text = response.text[:300]
                    logger.error(f"{provider} API error: {response.status_code} - {error_text}")
                    raise Exception(f"{provider.upper()} error {response.status_code}: {error_text}")

        except httpx.TimeoutException:
            logger.error(f"{provider} API timeout")
            raise Exception(f"{provider.upper()} API timeout - server tidak merespons dalam 60 detik")
        except Exception as e:
            if "API Key" in str(e) or "Kuota" in str(e) or "Akses ditolak" in str(e) or "Server" in str(e) or "timeout" in str(e).lower() or provider.upper() in str(e):
                raise  # Re-raise our specific errors
            logger.error(f"{provider} API exception: {str(e)}")
            raise Exception(f"{provider.upper()} error: {str(e)}")

    def _build_trading_prompt(
        self,
        symbol: str,
        timeframe: str,
        technical_data: Dict[str, Any],
        signal_data: Dict[str, Any]
    ) -> str:
        """
        Build enhanced prompt untuk AI analisis trading dengan SEMUA data yang tersedia

        Token optimization strategy:
        - Level 1 (Always): Primary timeframe detailed data, basic indicators
        - Level 2 (High): MTF confluence, high-confidence patterns, advanced indicators
        - Level 3 (Medium): Market context (sessions, volatility)
        - Level 4 (Low): Account data (if custom capital used)
        """
        # Token management - build prompt with compression techniques
        prompt_parts = []

        # === HEADER ===
        prompt_parts.append(f"Analyze trading data for {symbol} {timeframe}. Provide AI assessment.")
        prompt_parts.append(f"Current Price: {technical_data.get('current_price', 'N/A')}")

        # === LEVEL 1: PRIMARY TECHNICAL INDICATORS (Always included) ===
        prompt_parts.append("\n# PRIMARY INDICATORS:")
        prompt_parts.append(f"RSI: {technical_data.get('rsi', {}).get('value', 'N/A')} ({technical_data.get('rsi', {}).get('status', 'N/A')})")
        prompt_parts.append(f"MACD: {technical_data.get('macd', {}).get('histogram', 'N/A')} ({technical_data.get('macd', {}).get('status', 'N/A')}) | Crossover: {technical_data.get('macd', {}).get('crossover', 'NONE')}")
        prompt_parts.append(f"EMA: Trend={technical_data.get('ema', {}).get('trend', 'N/A')} | EMA9={technical_data.get('ema', {}).get('ema9', 'N/A')} | EMA21={technical_data.get('ema', {}).get('ema21', 'N/A')} | EMA50={technical_data.get('ema', {}).get('ema50', 'N/A')}")
        prompt_parts.append(f"Price Position: {technical_data.get('ema', {}).get('price_position', 'N/A')} vs EMA21")
        prompt_parts.append(f"Divergence: {technical_data.get('divergence', 'NONE')}")

        # Support/Resistance levels
        sr = technical_data.get('support_resistance', {})
        if sr:
            prompt_parts.append(f"\nS/R Levels: Support={[round(s, 5) for s in sr.get('support', [])[:3]]} | Resistance={[round(s, 5) for s in sr.get('resistance', [])[:3]]}")

        # === LEVEL 2: MULTI-TIMEFRAME ANALYSIS ===
        mtf_data = technical_data.get('multi_timeframe', {})
        if mtf_data:
            prompt_parts.append(f"\n# MULTI-TIMEFRAME ANALYSIS:")
            prompt_parts.append(f"Overall: {mtf_data.get('trend_direction', 'N/A')} | Alignment: {mtf_data.get('alignment_score', 0)}% | Conf: {mtf_data.get('confidence', 0)}%")
            prompt_parts.append(f"Bullish TFs: {mtf_data.get('bullish_count', 0)} | Bearish TFs: {mtf_data.get('bearish_count', 0)} | Neutral: {mtf_data.get('neutral_count', 0)}")

            # Detailed timeframe data (compressed)
            tf_details = []
            for tf, data in mtf_data.get('timeframes', {}).items():
                tf_str = f"{tf}: {data.get('trend', 'N/A')} | Str={data.get('signal_strength', 0)} | RSI={data.get('indicators', {}).get('rsi', 'N/A')}"
                tf_details.append(tf_str)
            prompt_parts.append(f"Timeframes: {' | '.join(tf_details)}")

            # MTF patterns (top 3 each)
            mtf_patterns = mtf_data.get('patterns', {})
            if mtf_patterns:
                bullish_patterns = [f"{p.get('name', '')}({p.get('strength', 0)})" for p in mtf_patterns.get('bullish', [])[:3]]
                bearish_patterns = [f"{p.get('name', '')}({p.get('strength', 0)})" for p in mtf_patterns.get('bearish', [])[:3]]
                if bullish_patterns:
                    prompt_parts.append(f"MTF Bullish Patterns: {', '.join(bullish_patterns)}")
                if bearish_patterns:
                    prompt_parts.append(f"MTF Bearish Patterns: {', '.join(bearish_patterns)}")

        # === PATTERN RECOGNITION ===
        patterns = technical_data.get('patterns', {})
        if patterns:
            prompt_parts.append(f"\n# PATTERNS (Primary TF):")
            prompt_parts.append(f"Bullish: {[p['name'] for p in patterns.get('bullish', [])[:3]]} | Total Str: {patterns.get('total_bullish_strength', 0)}")
            prompt_parts.append(f"Bearish: {[p['name'] for p in patterns.get('bearish', [])[:3]]} | Total Str: {patterns.get('total_bearish_strength', 0)}")

        # === LEVEL 2: ADVANCED INDICATORS ===
        adv_ind = technical_data.get('advanced_indicators', {})
        if adv_ind:
            prompt_parts.append(f"\n# ADVANCED INDICATORS:")

            # Stochastic
            stoch = adv_ind.get('stochastic')
            if stoch:
                prompt_parts.append(f"Stochastic: K={stoch.get('k_value', 'N/A')} | D={stoch.get('d_value', 'N/A')} | {stoch.get('status', 'N/A')} | Cross: {stoch.get('crossover', 'NONE')}")

            # Bollinger Bands
            bb = adv_ind.get('bollinger_bands')
            if bb:
                prompt_parts.append(f"Bollinger Bands: Upper={bb.get('upper', 'N/A')} | Middle={bb.get('middle', 'N/A')} | Lower={bb.get('lower', 'N/A')} | Pos: {bb.get('position', 'N/A')} | Squeeze: {bb.get('squeeze', False)}")

            # ADX
            adx = adv_ind.get('adx')
            if adx:
                prompt_parts.append(f"ADX: {adx.get('adx', 'N/A')} | Strength={adx.get('trend_strength', 'N/A')} | Dir={adx.get('direction', 'N/A')} | +DI={adx.get('di_plus', 'N/A')} | -DI={adx.get('di_minus', 'N/A')}")

            # ATR
            atr = adv_ind.get('atr')
            if atr:
                prompt_parts.append(f"ATR: {atr.get('atr', 'N/A')} | Vol={atr.get('volatility', 'N/A')} | ATR%={atr.get('atr_percent', 'N/A')}")

        # === SMART MONEY CONCEPTS ===
        smc = technical_data.get('smart_money', {})
        if smc and smc.get('score'):
            prompt_parts.append(f"\n# SMART MONEY CONCEPTS:")
            smc_score = smc['score']
            prompt_parts.append(f"SMC Bias: {smc_score.get('bias', 'NEUTRAL')} | Bull={smc_score.get('bullish', 0)} | Bear={smc_score.get('bearish', 0)}")
            
            # Structure
            structure = smc.get('structure', {})
            if structure:
                prompt_parts.append(f"Structure Trend: {structure.get('trend', 'N/A')}")
                for bos in structure.get('bos', [])[:2]:
                    prompt_parts.append(f"  BOS: {bos.get('description', '')}")
                for choch in structure.get('choch', [])[:2]:
                    prompt_parts.append(f"  CHoCH: {choch.get('description', '')}")
            
            # Order Blocks
            obs = smc.get('order_blocks', [])
            if obs:
                ob_strs = [f"{ob['type']} OB({ob['low']:.5f}-{ob['high']:.5f}, str={ob['strength']})" for ob in obs[:3]]
                prompt_parts.append(f"Order Blocks: {', '.join(ob_strs)}")
            
            # FVGs
            fvgs = smc.get('fair_value_gaps', [])
            if fvgs:
                fvg_strs = [f"{fvg['type']} FVG({fvg['bottom']:.5f}-{fvg['top']:.5f})" for fvg in fvgs[:3]]
                prompt_parts.append(f"FVGs: {', '.join(fvg_strs)}")
            
            # Liquidity
            liq = smc.get('liquidity', {})
            sweeps = liq.get('sweeps', [])
            if sweeps:
                for sweep in sweeps[:2]:
                    prompt_parts.append(f"  Sweep: {sweep.get('description', '')}")
            
            # Premium/Discount
            zones = smc.get('zones', {})
            if zones.get('premium_discount') != 'NEUTRAL':
                prompt_parts.append(f"Zone: {zones.get('premium_discount', 'N/A')} ({zones.get('position_pct', 50):.0f}%) - {zones.get('description', '')}")

        # === VOLUME ANALYSIS ===
        vol = technical_data.get('volume', {})
        if vol and vol.get('score'):
            prompt_parts.append(f"\n# VOLUME ANALYSIS:")
            vol_score = vol['score']
            prompt_parts.append(f"Volume Bias: {vol_score.get('bias', 'NEUTRAL')} | Bull={vol_score.get('bullish', 0)} | Bear={vol_score.get('bearish', 0)}")
            
            vwap = vol.get('vwap')
            if vwap:
                prompt_parts.append(f"VWAP: {vwap.get('value', 'N/A')} | Position: {vwap.get('position', 'N/A')} | Dist: {vwap.get('distance_pct', 0)}%")
            
            obv = vol.get('obv')
            if obv:
                prompt_parts.append(f"OBV: Trend={obv.get('trend', 'N/A')} | Bias={obv.get('bias', 'N/A')}")
            
            div = vol.get('divergence')
            if div and div.get('type') != 'NONE':
                prompt_parts.append(f"Vol Divergence: {div.get('type', 'NONE')} - {div.get('description', '')}")

        # === MARKET STRUCTURE ===
        mkt = technical_data.get('market_structure', {})
        if mkt:
            prompt_parts.append(f"\n# MARKET STRUCTURE:")
            prompt_parts.append(f"Trend: {mkt.get('trend_summary', 'N/A')}")
            
            fib = mkt.get('fibonacci', {})
            if fib and fib.get('nearest_level'):
                nearest = fib['nearest_level']
                prompt_parts.append(f"Fibonacci: Dir={fib.get('direction', 'N/A')} | Nearest: {nearest.get('level', 'N/A')} at {nearest.get('price', 'N/A')} ({nearest.get('distance_pct', 0)}%)")
            
            sd = mkt.get('supply_demand', {})
            if sd:
                demand = sd.get('demand', [])
                supply = sd.get('supply', [])
                if demand:
                    demand_strs = [f"{z['low']:.5f}-{z['high']:.5f}" for z in demand[:2]]
                    prompt_parts.append(f"Demand Zones: {demand_strs}")
                if supply:
                    supply_strs = [f"{z['low']:.5f}-{z['high']:.5f}" for z in supply[:2]]
                    prompt_parts.append(f"Supply Zones: {supply_strs}")

        # === LEVEL 3: MARKET CONTEXT ===
        market_context = technical_data.get('market_context', {})
        if market_context:
            prompt_parts.append(f"\n# MARKET CONTEXT:")
            prompt_parts.append(f"Session Quality: {market_context.get('session_quality', 'N/A')} | Best Time: {market_context.get('is_best_time', False)} | Sessions: {market_context.get('active_sessions', [])}")
            prompt_parts.append(f"Spread: {market_context.get('spread_pips', 0)} pips | Point: {market_context.get('point', 'N/A')}")

        # === LEVEL 4: ACCOUNT DATA (if available) ===
        account = technical_data.get('account', {})
        if account:
            prompt_parts.append(f"\n# ACCOUNT:")
            prompt_parts.append(f"Balance: ${account.get('balance', 0):.2f} | Equity: ${account.get('equity', 0):.2f} | Free Margin: ${account.get('free_margin', 0):.2f}")
            prompt_parts.append(f"Drawdown: {account.get('drawdown_pct', 0):.1f}%")

        # === INITIAL SIGNAL ===
        prompt_parts.append(f"\n# INITIAL SIGNAL:")
        prompt_parts.append(f"Direction: {signal_data.get('direction', 'N/A')}")
        prompt_parts.append(f"Confidence: {signal_data.get('confidence', 0)}%")
        prompt_parts.append(f"Scores: Bullish={signal_data.get('bullish_score', 0)} | Bearish={signal_data.get('bearish_score', 0)}")
        
        # Score breakdown
        breakdown = signal_data.get('score_breakdown', {})
        if breakdown:
            prompt_parts.append(f"Breakdown: MTF={breakdown.get('mtf', 0)} | Tech={breakdown.get('technical', 0)} | SMC={breakdown.get('smart_money', 0)} | Pat={breakdown.get('patterns', 0)} | Vol={breakdown.get('volume', 0)} | S/R={breakdown.get('sr_proximity', 0)}")
        
        prompt_parts.append(f"Reasons: {', '.join(signal_data.get('reasons', []))}")

        # === RESPONSE FORMAT ===
        prompt_parts.append("\n# RESPONSE:")
        prompt_parts.append("Respond with ONLY valid JSON (no markdown code blocks).")
        prompt_parts.append("IMPORTANT: Provide 'reasoning' and 'risk_warning' in INDONESIAN language (Bahasa Indonesia).")
        prompt_parts.append("Keep 'ai_direction' in English (BUY/SELL/WAIT).")

        prompt_parts.append("""{
    "ai_direction": "BUY" or "SELL" or "WAIT",
    "ai_confidence": <number 0-100>,
    "agreement": <true if AI agrees with initial signal>,
    "confidence_adjustment": <number -20 to +20>,
    "reasoning": "<penjelasan singkat dan padat dalam Bahasa Indonesia>",
    "risk_warning": "<peringatan risiko spesifik dalam Bahasa Indonesia jika ada>",
    "key_levels": {
        "support": <nearest support level estimate>,
        "resistance": <nearest resistance level estimate>
    }
}""")

        return "\n".join(prompt_parts)

    def _parse_ai_response(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse AI response JSON"""
        try:
            if not text or not text.strip():
                logger.error("Empty AI response text")
                return None

            # Clean response - remove markdown code blocks if present
            text = text.strip()
            if text.startswith("```json"):
                text = text[7:]
            elif text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()

            # Try to extract JSON from text if it contains extra content
            if not text.startswith('{'):
                start = text.find('{')
                if start != -1:
                    end = text.rfind('}') + 1
                    if end > start:
                        text = text[start:end]

            result = json.loads(text)

            # Validate required fields
            if not isinstance(result, dict):
                logger.error(f"AI response is not a dict: {type(result)}")
                return None

            return result
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response: {e}\nText: {text[:200]}")
            return None


# Singleton
ai_service = AIService()
