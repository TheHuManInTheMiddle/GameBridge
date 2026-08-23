# -*- coding: utf-8 -*-
"""
CONNECTIONS:
 - FETCHES FROM: Isolated system memory layout.
 - CALLED BY: main/main.py, interface/client_gui.py, and any background core thread.
"""

import queue
from typing import Callable

class UIEventQueue:
    def __init__(self):
        # Thread-safe FIFO queue for executing UI updates on the main execution thread
        self._queue = queue.Queue()

    def dispatch(self, callback: Callable[[], None]) -> None:
        """Enqueues a specific UI execution task from any background worker thread."""
        self._queue.put(callback)

    def process_next_batch(self) -> None:
        """Consumes all currently available thread tasks transactionally. Must be bound to gui.after()."""
        try:
            while True:
                callback = self._queue.get_nowait()
                try:
                    callback()
                except Exception as e:
                    print(f"[UI-QUEUE-ERROR] Failed to execute safe GUI callback function: {e}")
        except queue.Empty:
            pass

