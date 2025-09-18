from __future__ import annotations

import hashlib
import os
import sys
from dataclasses import dataclass
from typing import Optional


def _home() -> str:
    return os.path.expanduser("~")


def cache_dir() -> str:
    # Cross-platform cache base
    if sys.platform == "win32":
        base = os.getenv("LOCALAPPDATA", os.path.join(_home(), "AppData", "Local"))
        path = os.path.join(base, "turkify", "models")
    elif sys.platform == "darwin":
        path = os.path.join(_home(), "Library", "Caches", "turkify", "models")
    else:
        path = os.path.join(_home(), ".cache", "turkify", "models")
    os.makedirs(path, exist_ok=True)
    return path


@dataclass
class ModelSpec:
    name: str
    filename: str
    url: str
    sha256: Optional[str] = None


DEFAULT_MODELS = {
    # Good multilingual tiny instruct model (~220–260MB depending on quant)
    "qwen2.5-0.5b-instruct-q4_k_m": ModelSpec(
        name="Qwen2.5-0.5B-Instruct Q4_K_M",
        filename="qwen2.5-0.5b-instruct-q4_k_m.gguf",
        url=(
            "https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/"
            "qwen2.5-0.5b-instruct-q4_k_m.gguf?download=true"
        ),
        sha256=None,  # Optional; may change across mirrors
    ),
    # Alternative: Phi-2 (English-focused; larger ~1.7GB in some quants)
    "phi-2-q4_k_m": ModelSpec(
        name="Phi-2 Q4_K_M",
        filename="phi-2.Q4_K_M.gguf",
        url=(
            "https://huggingface.co/TheBloke/phi-2-GGUF/resolve/main/phi-2.Q4_K_M.gguf"
        ),
        sha256=None,
    ),
}


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url: str, dest_path: str, sha256: Optional[str] = None) -> str:
    import requests  # lazy import
    try:
        from tqdm import tqdm  # type: ignore
    except Exception:
        tqdm = None

    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        if tqdm:
            bar = tqdm(total=total, unit="B", unit_scale=True, desc=os.path.basename(dest_path))
        else:
            bar = None
        tmp = dest_path + ".part"
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
                    if bar:
                        bar.update(len(chunk))
        if bar:
            bar.close()
        os.replace(tmp, dest_path)

    if sha256:
        digest = _sha256_file(dest_path)
        if digest.lower() != sha256.lower():
            raise RuntimeError("Downloaded file checksum mismatch")
    return dest_path


def ensure_model(
    model_key: str = "qwen2.5-0.5b-instruct-q4_k_m",
    *,
    auto_download: bool = False,
    custom_url: Optional[str] = None,
) -> Optional[str]:
    """Return a local GGUF path; download to cache if missing and allowed.

    When auto_download is False and the file is missing, returns None.
    """
    spec = DEFAULT_MODELS.get(model_key)
    if spec is None and not custom_url:
        raise ValueError(f"Unknown model key: {model_key}")

    cdir = cache_dir()
    filename = spec.filename if spec else os.path.basename(custom_url)  # type: ignore[arg-type]
    dest = os.path.join(cdir, filename)
    if os.path.isfile(dest):
        return dest
    if not auto_download:
        return None

    url = custom_url or spec.url  # type: ignore[union-attr]
    sha = spec.sha256 if spec else None
    return download(url, dest, sha)

