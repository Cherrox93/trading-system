"""
WebSocket handler dla real-time aktualizacji dashboardu.
STUB — zaimplementuj w następnych promptach.
"""
from fastapi import WebSocket
import logging

logger = logging.getLogger(__name__)


async def ws_handler(websocket: WebSocket):
    """Obsługuje połączenia WebSocket od klientów dashboardu."""
    await websocket.accept()
    # TODO: Zaimplementuj broadcast aktualizacji stanu
    await websocket.close()
