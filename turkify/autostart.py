from __future__ import annotations

import json
import os
import shutil
import sys
from typing import Optional


APP_ID = "com.turkify.watch"


def _python_execs():
    py = sys.executable
    pyw = None
    if sys.platform == "win32" and py.lower().endswith("python.exe"):
        candidate = py[:-10] + "pythonw.exe"
        if os.path.isfile(candidate):
            pyw = candidate
    return py, pyw


def _watch_command(mode: str, hotkey: Optional[str]) -> list[str]:
    # Prefer running module to avoid relying on entrypoints on PATH
    # mode: "llm" or "heuristic"
    py, pyw = _python_execs()
    argv = [py]
    if sys.platform == "win32" and pyw:
        argv = [pyw]
    argv += ["-m", "turkify.cli"]
    if mode == "llm":
        argv += ["--llm", "--watch-hotkey"]
    else:
        argv += ["--watch-hotkey"]
    if hotkey:
        argv[-1:] = [hotkey]
    return argv


def _tray_command(tray_mode: str) -> tuple[list[str], dict[str, str]]:
    # tray_mode: 'tray-llm' or 'tray-heuristic'
    py, pyw = _python_execs()
    argv = [pyw or py, "-m", "turkify.tray"]
    env = {}
    if tray_mode == "tray-llm":
        env["TURKIFY_USE_LLM"] = "1"
    return argv, env


def install_autostart(mode: str = "llm", hotkey: Optional[str] = None) -> str:
    """Install user-level autostart. Returns the path of the installed file.

    mode: "llm" (default) or "heuristic"
    hotkey: optional hotkey string (e.g., "<cmd>+<alt>+t" on macOS)
    """
    mode = mode.lower()
    if mode not in {"llm", "heuristic", "tray-llm", "tray-heuristic"}:
        raise ValueError("mode must be 'llm', 'heuristic', 'tray-llm' or 'tray-heuristic'")

    tray_mode = mode in {"tray-llm", "tray-heuristic"}
    if tray_mode:
        cmd, extra_env = _tray_command(mode)
    else:
        cmd = _watch_command(mode, hotkey)
        extra_env = {}

    if sys.platform == "darwin":
        launch_dir = os.path.join(os.path.expanduser("~"), "Library", "LaunchAgents")
        os.makedirs(launch_dir, exist_ok=True)
        plist_path = os.path.join(launch_dir, f"{APP_ID}.plist")
        env_xml = ""
        if extra_env:
            env_items = "".join(f"\n        <key>{k}</key><string>{v}</string>" for k, v in extra_env.items())
            env_xml = f"\n    <key>EnvironmentVariables</key>\n    <dict>{env_items}\n    </dict>\n"
        plist = f"""
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{APP_ID}</string>
    <key>ProgramArguments</key>
    <array>
{os.linesep.join(f'        <string>{x}</string>' for x in cmd)}
    </array>
{env_xml}    
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
""".strip()
        with open(plist_path, "w", encoding="utf-8") as f:
            f.write(plist)
        return plist_path

    if sys.platform == "win32":
        startup_dir = os.path.join(os.environ.get("APPDATA", ""), "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
        if not startup_dir:
            raise RuntimeError("Cannot locate Startup folder")
        os.makedirs(startup_dir, exist_ok=True)
        bat_path = os.path.join(startup_dir, "turkify-watch.bat")
        line = " ".join(f'"{arg}"' if " " in arg or arg.startswith("-") else arg for arg in cmd)
        # Use start to detach; window minimized if pythonw used
        env_lines = "".join(f"set {k}={v}\n" for k, v in extra_env.items())
        contents = f"@echo off\n{env_lines}start "" {line}\n"
        with open(bat_path, "w", encoding="utf-8") as f:
            f.write(contents)
        return bat_path

    # Linux / others with XDG autostart
    autostart_dir = os.path.join(os.path.expanduser("~"), ".config", "autostart")
    os.makedirs(autostart_dir, exist_ok=True)
    desktop_path = os.path.join(autostart_dir, "turkify.desktop")
    prefix = "" if not extra_env else ("env " + " ".join(f"{k}={shlex_quote(v)}" for k, v in extra_env.items()) + " ")
    exec_line = prefix + " ".join(shlex_quote(x) for x in cmd)
    desktop = f"""
[Desktop Entry]
Type=Application
Name=Turkify Watcher
Exec={exec_line}
X-GNOME-Autostart-enabled=true
Terminal=false
""".strip()
    with open(desktop_path, "w", encoding="utf-8") as f:
        f.write(desktop)
    return desktop_path


def uninstall_autostart() -> bool:
    removed = False
    if sys.platform == "darwin":
        path = os.path.join(os.path.expanduser("~"), "Library", "LaunchAgents", f"{APP_ID}.plist")
        if os.path.isfile(path):
            os.remove(path)
            removed = True
    elif sys.platform == "win32":
        startup_dir = os.path.join(os.environ.get("APPDATA", ""), "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
        path = os.path.join(startup_dir, "turkify-watch.bat")
        if os.path.isfile(path):
            os.remove(path)
            removed = True
    else:
        path = os.path.join(os.path.expanduser("~"), ".config", "autostart", "turkify.desktop")
        if os.path.isfile(path):
            os.remove(path)
            removed = True
    return removed


def shlex_quote(s: str) -> str:
    # Minimal portable quoting for .desktop Exec field
    if not s:
        return "''"
    if any(c in s for c in " \t\n\"'`$&|;<>(){}[]*?~\\"):
        return "'" + s.replace("'", "'\''") + "'"
    return s
