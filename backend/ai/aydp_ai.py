"""
AYDP AI - Multi-Provider AI Service
Supports: ZAI (GLM), Google AI, Gemini, Kimi
"""
import os
import httpx
import asyncio
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import json

class AIProvider(Enum):
    ZAI = "zai"
    GOOGLE = "google"
    GEMINI = "gemini"
    KIMI = "kimi"
    OPENAI = "openai"


@dataclass
class AYDPConfig:
    """Configuration for AYDP AI"""
    provider: AIProvider = AIProvider.ZAI
    api_key: Optional[str] = None
    api_url: Optional[str] = None
    model: str = "glm-4-plus"
    max_tokens: int = 2000
    temperature: float = 0.7


class AYDPAI:
    """
    AYDP AI - Multi-provider AI service for trading analysis
    """

    def __init__(self, provider: str = None):
        self.provider_name = provider or os.getenv("AI_PROVIDER", "zai")
        self.provider = AIProvider(self.provider_name)
        self.config = self._load_config()
        self.client = httpx.AsyncClient(timeout=60.0)

    def _load_config(self) -> AYDPConfig:
        """Load configuration based on provider"""
        config = AYDPConfig()
        config.provider = self.provider

        if self.provider == AIProvider.ZAI:
            config.api_key = os.getenv("ZAI_API_KEY")
            config.api_url = os.getenv("ZAI_API_URL", "https://api.z.ai/api/paas/v4")
            config.model = os.getenv("ZAI_MODEL", "glm-4-plus")
        elif self.provider == AIProvider.GOOGLE:
            config.api_key = os.getenv("GOOGLE_API_KEY")
            config.api_url = "https://generativelanguage.googleapis.com/v1"
            config.model = os.getenv("GOOGLE_MODEL", "gemini-pro")
        elif self.provider == AIProvider.GEMINI:
            config.api_key = os.getenv("GEMINI_API_KEY")
            config.api_url = "https://generativelanguage.googleapis.com/v1"
            config.model = os.getenv("GEMINI_MODEL", "gemini-pro")
        elif self.provider == AIProvider.KIMI:
            config.api_key = os.getenv("KIMI_API_KEY")
            config.api_url = os.getenv("KIMI_API_URL", "https://api.moonshot.cn/v1")
            config.model = os.getenv("KIMI_MODEL", "moonshot-v1-8k")
        elif self.provider == AIProvider.OPENAI:
            config.api_key = os.getenv("OPENAI_API_KEY")
            config.api_url = "https://api.openai.com/v1"
            config.model = os.getenv("OPENAI_MODEL", "gpt-4")

        return config

    async def analyze(self, prompt: str, system_prompt: str = None) -> str:
        """
        Send analysis request to AI provider
        """
        if not self.config.api_key:
            return self._mock_response(prompt)

        try:
            if self.provider == AIProvider.ZAI:
                return await self._call_zai(prompt, system_prompt)
            elif self.provider in [AIProvider.GOOGLE, AIProvider.GEMINI]:
                return await self._call_google(prompt, system_prompt)
            elif self.provider == AIProvider.KIMI:
                return await self._call_kimi(prompt, system_prompt)
            elif self.provider == AIProvider.OPENAI:
                return await self._call_openai(prompt, system_prompt)
        except Exception as e:
            print(f"AYDP AI Error ({self.provider.value}): {e}")
            return self._mock_response(prompt)

    async def _call_zai(self, prompt: str, system_prompt: str = None) -> str:
        """Call ZAI (GLM) API"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await self.client.post(
            f"{self.config.api_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": self.config.model,
                "messages": messages,
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature
            }
        )

        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"]
        else:
            raise Exception(f"ZAI API error: {response.status_code}")

    async def _call_google(self, prompt: str, system_prompt: str = None) -> str:
        """Call Google/Gemini API"""
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        response = await self.client.post(
            f"{self.config.api_url}/models/{self.config.model}:generateContent",
            headers={"Content-Type": "application/json"},
            params={"key": self.config.api_key},
            json={
                "contents": [{"parts": [{"text": full_prompt}]}],
                "generationConfig": {
                    "maxOutputTokens": self.config.max_tokens,
                    "temperature": self.config.temperature
                }
            }
        )

        if response.status_code == 200:
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
        else:
            raise Exception(f"Google API error: {response.status_code}")

    async def _call_kimi(self, prompt: str, system_prompt: str = None) -> str:
        """Call Kimi (Moonshot) API"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await self.client.post(
            f"{self.config.api_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": self.config.model,
                "messages": messages,
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature
            }
        )

        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"]
        else:
            raise Exception(f"Kimi API error: {response.status_code}")

    async def _call_openai(self, prompt: str, system_prompt: str = None) -> str:
        """Call OpenAI API"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await self.client.post(
            f"{self.config.api_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": self.config.model,
                "messages": messages,
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature
            }
        )

        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"]
        else:
            raise Exception(f"OpenAI API error: {response.status_code}")

    def _mock_response(self, prompt: str) -> str:
        """Return mock response when no API key configured"""
        if "trailing" in prompt.lower() or "sl+" in prompt.lower():
            return json.dumps({
                "action": "HOLD",
                "new_sl": None,
                "reason": "Position dalam kondisi aman. Tidak perlu adjust SL.",
                "confidence": 75
            })
        return "AYDP AI: API key tidak dikonfigurasi. Mohon set API key di .env"

    async def analyze_trailing_stop(
        self,
        symbol: str,
        direction: str,
        entry: float,
        current_sl: float,
        current_tp: float,
        current_price: float,
        profit_pips: float,
        profit_amount: float
    ) -> Dict[str, Any]:
        """
        Analyze if SL should be moved (Smart Trailing)
        Returns recommendation for SL adjustment
        """
        system_prompt = """Kamu adalah AYDP AI Trading Assistant yang ahli dalam manajemen risk trading forex.
Tugasmu adalah menganalisis posisi trading dan memberikan rekomendasi apakah SL perlu dipindahkan.

Prinsip utama:
1. "Mending profit sedikit daripada loss" - prioritaskan proteksi profit
2. Tapi "kalau bisa profit lebih banyak kenapa tidak" - biarkan profit berjalan jika market mendukung

Respons dalam format JSON:
{
    "action": "MOVE_SL" | "HOLD" | "TAKE_PROFIT",
    "new_sl": <harga baru atau null>,
    "reason": "<alasan dalam bahasa Indonesia>",
    "confidence": <0-100>,
    "market_condition": "<BULLISH | BEARISH | SIDEWAYS | VOLATILE>",
    "momentum": "<STRONG | MODERATE | WEAK>"
}
"""

        prompt = f"""
Analisis posisi berikut untuk Smart Trailing Stop:

Symbol: {symbol}
Direction: {direction}
Entry: {entry}
Current SL: {current_sl}
Current TP: {current_tp}
Current Price: {current_price}
Profit: {profit_pips:.1f} pips (${profit_amount:.2f})

Pertimbangkan:
1. Apakah profit sudah cukup untuk lock profit?
2. Apakah momentum masih kuat untuk hold?
3. Apakah ada support/resistance dekat yang bisa jadi target?

Berikan rekomendasi dalam format JSON.
"""

        try:
            response = await self.analyze(prompt, system_prompt)
            # Parse JSON from response
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]

            return json.loads(response.strip())
        except Exception as e:
            print(f"Error parsing trailing response: {e}")
            return {
                "action": "HOLD",
                "new_sl": None,
                "reason": "Tidak dapat menganalisis, pertahankan SL saat ini",
                "confidence": 50,
                "market_condition": "UNKNOWN",
                "momentum": "UNKNOWN"
            }

    async def validate_trade(
        self,
        symbol: str,
        direction: str,
        entry: float,
        sl: float,
        tp: float,
        lot_size: float,
        risk_amount: float,
        account_balance: float
    ) -> Dict[str, Any]:
        """
        Validate trade setup before execution
        Returns risk assessment and recommendations
        """
        system_prompt = """Kamu adalah AYDP AI Risk Validator.
Validasi setup trading sebelum dieksekusi.

Respons dalam format JSON:
{
    "approved": true | false,
    "risk_score": <1-10>,
    "risk_level": "<LOW | MEDIUM | HIGH>",
    "warnings": ["<peringatan1>", "<peringatan2>"],
    "suggestions": ["<saran1>", "<saran2>"],
    "final_verdict": "<alasan singkat dalam bahasa Indonesia>"
}
"""

        risk_percent = (risk_amount / account_balance) * 100
        sl_pips = abs(entry - sl) * 10000 if 'JPY' not in symbol else abs(entry - sl) * 100
        tp_pips = abs(tp - entry) * 10000 if 'JPY' not in symbol else abs(tp - entry) * 100
        rr_ratio = tp_pips / sl_pips if sl_pips > 0 else 0

        prompt = f"""
Validasi setup trading berikut:

Symbol: {symbol}
Direction: {direction}
Entry: {entry}
SL: {sl} ({sl_pips:.1f} pips)
TP: {tp} ({tp_pips:.1f} pips)
Lot Size: {lot_size}
Risk: ${risk_amount:.2f} ({risk_percent:.1f}% dari modal)
Account Balance: ${account_balance:.2f}
Risk:Reward Ratio: 1:{rr_ratio:.1f}

Apakah setup ini aman untuk dieksekusi?
"""

        try:
            response = await self.analyze(prompt, system_prompt)
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]

            return json.loads(response.strip())
        except Exception as e:
            print(f"Error parsing validation response: {e}")
            return {
                "approved": True,
                "risk_score": 5,
                "risk_level": "MEDIUM",
                "warnings": ["Tidak dapat memvalidasi dengan AI"],
                "suggestions": [],
                "final_verdict": "Lanjutkan dengan hati-hati"
            }

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


# Singleton instance
_aydp_ai = None

def get_aydp_ai() -> AYDPAI:
    """Get or create AYDP AI instance"""
    global _aydp_ai
    if _aydp_ai is None:
        _aydp_ai = AYDPAI()
    return _aydp_ai
