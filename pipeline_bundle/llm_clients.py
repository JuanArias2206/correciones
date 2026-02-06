# -*- coding: utf-8 -*-
"""
Cliente DeepSeek (OpenAI compatible) para clasificación de sustancias psicoactivas.
"""


class DeepSeekClient:
    def __init__(self, api_key: str, model: str, base_url: str, timeout: int = 60, temperature: float = 0.0):
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY no está configurada")
        try:
            from openai import OpenAI
        except Exception as e:
            raise ImportError("Falta el paquete 'openai'. Instala con: pip install openai") from e
        self._client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)
        self._model = model
        self._temperature = temperature

    def generate(self, prompt: str) -> str:
        """
        Llama a DeepSeek con temperature configurable.
        Temperature=0.0 para máxima consistencia en clasificación.
        """
        resp = self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self._temperature,
        )
        return resp.choices[0].message.content


def build_llm_client(
    provider: str,
    api_key: str,
    model: str,
    base_url: str = "https://api.deepseek.com",
    timeout: int = 60,
    temperature: float = 0.0,
) -> DeepSeekClient:
    """
    Construye un cliente DeepSeek. El parámetro provider debe ser 'deepseek'.
    """
    provider_norm = (provider or '').strip().lower()
    if provider_norm != 'deepseek':
        raise ValueError(f"Solo DeepSeek está soportado. Se recibió: {provider}")
    return DeepSeekClient(api_key=api_key, model=model, base_url=base_url, timeout=timeout, temperature=temperature)
