from __future__ import annotations

import sys
import os
import tkinter as tk
from tkinter import ttk

import pyperclip

from .converter import deasciify
from .llm import deasciify_via_llm
from .models import ensure_model


def run() -> None:
    root = tk.Tk()
    root.title("Turkify – Turkish Deasciifier")

    # Sizing
    root.geometry("640x360")

    main = ttk.Frame(root, padding=12)
    main.pack(fill=tk.BOTH, expand=True)

    # Input
    lbl_in = ttk.Label(main, text="Input (ASCII Turkish)")
    lbl_in.pack(anchor="w")

    txt_in = tk.Text(main, height=8, wrap=tk.WORD)
    txt_in.pack(fill=tk.BOTH, expand=True)

    # Output
    lbl_out = ttk.Label(main, text="Output (Türkçe)")
    lbl_out.pack(anchor="w", pady=(8, 0))

    txt_out = tk.Text(main, height=8, wrap=tk.WORD)
    txt_out.pack(fill=tk.BOTH, expand=True)

    # Actions
    btns = ttk.Frame(main)
    btns.pack(fill=tk.X, pady=(8, 0))

    # LLM toggle via env to keep UI minimal
    # LLM is default; disable with TURKIFY_USE_LLM=0/false/no/off
    env_val = os.environ.get("TURKIFY_USE_LLM", "1").strip().lower()
    use_llm = env_val not in ("0", "false", "no", "off", "")
    if use_llm:
        # Prefetch model on initial start (first launch)
        try:
            model_key = os.environ.get("TURKIFY_MODEL_NAME", "qwen2.5-0.5b-instruct-q4_k_m")
            custom_url = os.environ.get("TURKIFY_MODEL_URL")
            ensure_model(model_key, auto_download=True, custom_url=custom_url)
        except Exception:
            pass

    def do_convert(event=None):
        text = txt_in.get("1.0", tk.END).rstrip("\n")
        txt_out.delete("1.0", tk.END)
        out = None
        if use_llm:
            out = deasciify_via_llm(
                text,
                auto_download_model=True,
                model_key=os.environ.get("TURKIFY_MODEL_NAME", "qwen2.5-0.5b-instruct-q4_k_m"),
                custom_model_url=os.environ.get("TURKIFY_MODEL_URL"),
            )
        txt_out.insert("1.0", out or deasciify(text))

    def do_copy_out():
        pyperclip.copy(txt_out.get("1.0", tk.END).rstrip("\n"))

    def do_paste_in():
        txt_in.delete("1.0", tk.END)
        txt_in.insert("1.0", pyperclip.paste())

    def do_swap():
        src = txt_out.get("1.0", tk.END)
        txt_in.delete("1.0", tk.END)
        txt_in.insert("1.0", src)
        do_convert()

    ttk.Button(btns, text="Paste", command=do_paste_in).pack(side=tk.LEFT)
    ttk.Button(btns, text="Convert", command=do_convert).pack(side=tk.LEFT, padx=6)
    ttk.Button(btns, text="Copy Output", command=do_copy_out).pack(side=tk.LEFT)
    ttk.Button(btns, text="Swap", command=do_swap).pack(side=tk.RIGHT)

    # Keybindings
    root.bind("<Control-Return>", do_convert)
    if sys.platform == "darwin":
        root.bind("<Command-Return>", do_convert)

    # Autofocus
    txt_in.focus_set()
    root.mainloop()


if __name__ == "__main__":
    run()
