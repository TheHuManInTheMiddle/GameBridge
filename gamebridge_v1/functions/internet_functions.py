# -*- coding: utf-8 -*-
"""
KOPPLINGAR:
 - HÄMTAR FRÅN: Pythons standardbibliotek (webbrowser)
 - ANROPAS AV: functions/router_functions.py
"""
import webbrowser
import threading

def function_open_browser_link(url_str: str):
    """Asynchronously dispatches a clean URL string to the host OS standard browser execution layer."""
    if not url_str:
        return
        
    def browser_worker():
        try:
            # Rensa eventuellt brus från strängen och öppna i standardwebbläsaren
            clean_url = url_str.strip().strip('"').strip("'")
            # Enforce strict web protocol prefixes if missing
            if not clean_url.startswith(("http://", "https://")):
                clean_url = "https://" + clean_url
                
            print(f"[INTERNET-BRIDGE] Launching default OS browser layer for payload: {clean_url}")
            webbrowser.open(clean_url, new=2) # new=2 opens in a new tab if browser is alive
        except Exception as e:
            print(f"[INTERNET-BRIDGE-ERROR] Failed to dispatch browser thread: {e}")

    threading.Thread(target=browser_worker, daemon=True).start()
