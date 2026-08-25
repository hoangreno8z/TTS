#!/usr/bin/env python3
"""Bulletproof Launcher script for LAPQUE Personal Vietnamese TTS Studio.
Ensures single-process stability, auto-opens the browser, and handles port resolution.
"""
import os
import sys
import socket
import webbrowser
import time
import threading

def find_available_port(start_port=8000):
    for port in [8000, 8001, 8080, 8888, 5000]:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('127.0.0.1', port))
                return port
            except OSError:
                continue
    return start_port

def start_server():
    project_root = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(project_root, "backend")

    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)

    os.chdir(project_root)

    port = find_available_port(8000)
    server_url = f"http://127.0.0.1:{port}"

    def open_browser():
        time.sleep(1.0)
        print(f"\n[OK] Dang mo trinh duyet Studio: {server_url}\n")
        try:
            webbrowser.open(server_url)
        except Exception:
            pass

    threading.Thread(target=open_browser, daemon=True).start()

    import uvicorn
    print("=" * 65)
    print("   LAPQUE PERSONAL VIETNAMESE TTS STUDIO — SERVER RUNNING")
    print("=" * 65)
    print(f"Thu muc du an   : {project_root}")
    print(f"Dia chi Studio  : {server_url}")
    print("Trang thai       : REAL VIETNAMESE VOICE ACTIVE (0 DONG)")
    print("Nhan Ctrl+C de dung may chu.")
    print("=" * 65 + "\n")

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=port,
        reload=False,
        app_dir=backend_dir,
        log_level="info"
    )

if __name__ == "__main__":
    start_server()
