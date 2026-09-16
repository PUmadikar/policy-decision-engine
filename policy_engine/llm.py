import os
import json
import logging
import httpx
from typing import Dict, Any, Optional
from policy_engine.config import settings

logger = logging.getLogger(__name__)

class LlamaClient:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER.lower()
        self.ollama_host = settings.OLLAMA_HOST
        self.ollama_model = settings.OLLAMA_MODEL
        self.groq_api_key = settings.GROQ_API_KEY
        self.groq_model = settings.GROQ_MODEL

    def generate(self, prompt: str, system_prompt: str = "", temperature: float = 0.1) -> str:
        """Invokes Llama 3 model (via Ollama or API)."""
        if self.provider == "groq" and self.groq_api_key:
            return self._call_groq(prompt, system_prompt, temperature)
        else:
            return self._call_ollama(prompt, system_prompt, temperature)

    def _call_ollama(self, prompt: str, system_prompt: str, temperature: float) -> str:
        url = f"{self.ollama_host.rstrip('/')}/api/generate"
        payload = {
            "model": self.ollama_model,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False,
            "options": {"temperature": temperature}
        }
        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
                return data.get("response", "").strip()
        except Exception as e:
            logger.warning(f"Ollama call failed ({e}). Falling back to structured agent reasoning.")
            return ""

    def _call_groq(self, prompt: str, system_prompt: str, temperature: float) -> str:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json"
        }
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.groq_model,
            "messages": messages,
            "temperature": temperature
        }
        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.warning(f"Groq API call failed ({e}). Falling back to structured agent reasoning.")
            return ""

llm_client = LlamaClient()
