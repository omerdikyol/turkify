from __future__ import annotations

import os
import sys
from typing import Optional


_LLAMA_INSTANCE = None  # lazy-initialized llama.cpp model


def _prompt_for(text: str) -> str:
    return (
        "You are a Turkish deasciifier. Given text typed with an English keyboard, "
        "fix only the letters to proper Turkish (ç ğ ı İ ö ş ü). Do not translate or paraphrase. "
        "Preserve punctuation, spacing, and capitalization. Return only the corrected text.\n\n"
        f"Input: {text}\nOutput:"
    )


def _from_env():
    backend = os.getenv("TURKIFY_LLM_BACKEND")  # "ollama" or "llama_cpp"
    ollama_model = os.getenv("TURKIFY_OLLAMA_MODEL")
    ollama_host = os.getenv("TURKIFY_OLLAMA_HOST", "http://localhost:11434")
    llama_model = os.getenv("TURKIFY_LLAMA_MODEL")
    return backend, ollama_model, ollama_host, llama_model


def _try_ollama(text: str, model: str, host: str = "http://localhost:11434") -> Optional[str]:
    try:
        import requests  # type: ignore
    except Exception:
        return None

    url = host.rstrip("/") + "/api/generate"
    try:
        resp = requests.post(
            url,
            json={
                "model": model,
                "prompt": _prompt_for(text),
                "stream": False,
                "options": {"temperature": 0, "top_p": 0.9},
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        out = data.get("response")
        if isinstance(out, str) and out.strip():
            return out.strip()
    except Exception:
        return None
    return None


def _try_llama_cpp(text: str, model_path: str) -> Optional[str]:
    global _LLAMA_INSTANCE
    try:
        from llama_cpp import Llama  # type: ignore
    except Exception:
        return None

    try:
        if _LLAMA_INSTANCE is None:
            _LLAMA_INSTANCE = Llama(
                model_path=model_path,
                n_ctx=2048,
                verbose=False,
            )
        llm = _LLAMA_INSTANCE
        prompt = _prompt_for(text)
        # Prefer completion interface for broad compatibility
        res = llm.create_completion(
            prompt=prompt,
            temperature=0.0,
            max_tokens=512,
        )
        out = res.get("choices", [{}])[0].get("text", "")
        if isinstance(out, str) and out.strip():
            return out.strip()
    except Exception:
        return None
    return None


def deasciify_via_llm(
    text: str,
    backend: Optional[str] = None,
    ollama_model: Optional[str] = None,
    ollama_host: str = "http://localhost:11434",
    llama_model: Optional[str] = None,
    *,
    auto_download_model: bool = False,
    model_key: str = "qwen2.5-0.5b-instruct-q4_k_m",
    custom_model_url: Optional[str] = None,
) -> Optional[str]:
    """Try converting via a local LLM. Returns None if unavailable or fails.

    Supported backends:
      - "ollama": requires a running Ollama server and a local model name.
      - "llama_cpp": requires a GGUF model path for llama-cpp-python.
    If backend is None, infer from provided model args or environment.
    """
    env_backend, env_om, env_oh, env_lm = _from_env()
    backend = backend or env_backend
    ollama_model = ollama_model or env_om
    ollama_host = ollama_host or env_oh
    llama_model = llama_model or env_lm

    # Infer backend if not specified
    if backend is None:
        if ollama_model:
            backend = "ollama"
        elif llama_model:
            backend = "llama_cpp"

    if backend == "ollama" and ollama_model:
        return _try_ollama(text, ollama_model, ollama_host)
    if backend == "llama_cpp":
        # Optionally provision a model if needed
        if not llama_model and auto_download_model:
            try:
                from .models import ensure_model

                llama_model = ensure_model(model_key, auto_download=True, custom_url=custom_model_url)
            except Exception:
                llama_model = None
        if llama_model:
            return _try_llama_cpp(text, llama_model)

    return None
