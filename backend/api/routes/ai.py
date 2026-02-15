"""
AI Provider Routes - Test API Key connections and AI analysis
"""
from fastapi import APIRouter, HTTPException, Query, Header
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
import httpx
import asyncio

from ai.ai_service import ai_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ai", tags=["AI"])


class AITestRequest(BaseModel):
    provider: str
    api_key: str


class AITestResponse(BaseModel):
    success: bool
    message: str


# API endpoints untuk test koneksi
AI_ENDPOINTS = {
    "zai": {
        # Zhipu AI (GLM) - ChatGLM API
        "url": "https://open.bigmodel.cn/api/paas/v4/models",
        "auth_type": "bearer_jwt",
        "min_length": 20
    },
    "google": {
        "url": "https://generativelanguage.googleapis.com/v1/models?key={api_key}",
        "auth_type": "query",
        "min_length": 30
    },
    "gemini": {
        "url": "https://generativelanguage.googleapis.com/v1/models?key={api_key}",
        "auth_type": "query", 
        "min_length": 20
    },
    "kimi": {
        "url": "https://api.moonshot.cn/v1/models",
        "auth_type": "bearer",
        "min_length": 20
    },
    "openai": {
        "url": "https://api.openai.com/v1/models",
        "auth_type": "bearer",
        "min_length": 40
    }
}


@router.post("/test", response_model=AITestResponse)
async def test_ai_connection(request: AITestRequest):
    """
    Test AI provider API key connection to real API
    """
    try:
        provider = request.provider.lower()
        api_key = request.api_key.strip()
        
        if not api_key:
            return AITestResponse(success=False, message="API Key tidak boleh kosong")
        
        # Mask API key for logging
        masked_key = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
        logger.info(f"Testing AI provider: {provider} with key: {masked_key}")
        
        # Get provider config
        config = AI_ENDPOINTS.get(provider)
        
        if not config:
            # Unknown provider - just validate minimum length
            if len(api_key) >= 10:
                return AITestResponse(success=True, message=f"API Key tersimpan untuk {provider}")
            else:
                return AITestResponse(success=False, message="API Key terlalu pendek")
        
        # Check minimum length
        if len(api_key) < config["min_length"]:
            return AITestResponse(success=False, message=f"API Key terlalu pendek (minimal {config['min_length']} karakter)")
        
        # Test real API connection
        url = config["url"]
        if "{api_key}" in url:
            url = url.format(api_key=api_key)
        
        headers = {}
        auth = None
        
        if config["auth_type"] == "bearer":
            headers["Authorization"] = f"Bearer {api_key}"
        elif config["auth_type"] == "bearer_jwt":
            # Zhipu AI / ZAI uses JWT token directly
            headers["Authorization"] = f"Bearer {api_key}"
        elif config["auth_type"] == "basic":
            # Basic auth
            import base64
            auth_str = base64.b64encode(f"{api_key}:".encode()).decode()
            headers["Authorization"] = f"Basic {auth_str}"
        
        timeout = httpx.Timeout(10.0)
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                response = await client.get(url, headers=headers)
                
                if response.status_code == 200:
                    return AITestResponse(success=True, message=f"✅ Terhubung ke {provider.upper()}! API Key valid.")
                elif response.status_code == 401:
                    return AITestResponse(success=False, message=f"❌ API Key tidak valid untuk {provider.upper()}")
                elif response.status_code == 403:
                    return AITestResponse(success=False, message=f"❌ Akses ditolak. Periksa permission API Key.")
                else:
                    logger.warning(f"API test returned {response.status_code}: {response.text[:200]}")
                    return AITestResponse(success=False, message=f"⚠️ Respon tidak expected: {response.status_code}")
                    
            except httpx.TimeoutException:
                return AITestResponse(success=False, message="⏱️ Timeout - server tidak merespons")
            except httpx.ConnectError:
                return AITestResponse(success=False, message="❌ Tidak bisa konek ke server. Periksa internet.")
                
    except Exception as e:
        logger.error(f"Error testing AI connection: {e}")
        return AITestResponse(success=False, message=f"Error: {str(e)}")


class AIAnalyzeRequest(BaseModel):
    provider: str
    api_key: str
    symbol: str
    timeframe: str = "H1"
    technical_data: Dict[str, Any] = {}
    signal_data: Dict[str, Any] = {}


@router.post("/analyze")
async def analyze_with_ai(request: AIAnalyzeRequest):
    """
    Call AI provider for trading analysis
    """
    try:
        result = await ai_service.analyze_with_ai(
            provider=request.provider,
            api_key=request.api_key,
            symbol=request.symbol,
            timeframe=request.timeframe,
            technical_data=request.technical_data,
            signal_data=request.signal_data
        )
        
        if result:
            return {"success": True, "insight": result}
        else:
            return {"success": False, "message": "AI provider returned no result"}
            
    except Exception as e:
        logger.error(f"Error in AI analysis: {e}")
        return {"success": False, "message": str(e)}


@router.get("/providers")
async def get_providers():
    """Get list of available AI providers"""
    return {
        "providers": [
            {"id": "zai", "name": "ZAI (GLM-4)", "description": "Zhipu AI - Chinese AI provider"},
            {"id": "google", "name": "Google AI", "description": "Google Gemini AI"},
            {"id": "gemini", "name": "Gemini", "description": "Google Gemini (alias)"},
            {"id": "kimi", "name": "Kimi", "description": "Moonshot AI - Kimi"},
            {"id": "openai", "name": "OpenAI", "description": "OpenAI GPT-4o-mini"}
        ]
    }