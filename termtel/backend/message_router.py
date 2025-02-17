# backend/message_router.py
import asyncio
import traceback

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
import json
import logging
from termtel.backend.sessions import SSHSession, TelemetrySession, UISession

logger = logging.getLogger(__name__)


class MessageRouter(QObject):
    """
    Central message routing system that manages all sessions and message dispatch
    """
    message_to_frontend = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        # Initialize our sessions
        self.sessions = {
            "terminal": SSHSession("terminal"),
            "telemetry": TelemetrySession("telemetry"),
            "ui_state": UISession("ui_state")
        }

        # Connect each session's message_ready signal to our frontend relay
        for session in self.sessions.values():
            session.message_ready.connect(self._relay_to_frontend)

        logger.info("MessageRouter initialized with sessions")

    @pyqtSlot(str)
    def handle_frontend_message(self, message_json: str):
        """Entry point for all messages from frontend"""
        try:
            message = json.loads(message_json)
            session_id = message.get("session_id")

            if session_id not in self.sessions:
                logger.error(f"Unknown session ID: {session_id}")
                return

            session = self.sessions[session_id]
            action = message.get("action")
            payload = message.get("payload", {})

            # Create task for async operations
            asyncio.create_task(self._handle_message_async(session, action, payload))

        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received: {message_json}")
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            self._send_error("system", str(e))

    async def _handle_message_async(self, session, action, payload):
        """Handle async message processing"""
        print(f"session: {session} action: {action} payload: {payload}")
        try:
            if action == "connect":
                await session.connect(**payload)
            elif action == "disconnect":
                await session.disconnect()
            elif action == "data":
                # Explicitly handle terminal data
                await session.handle_data(payload)
            elif action == "resize":
                # Explicitly handle terminal resize
                await session.handle_resize(payload)
            elif action == "set_theme":
                await session.set_theme(payload.get("theme"))
            elif action == "get_device_info":  # New telemetry specific action
                try:
                    await session.get_device_info()
                except:
                    pass # will retry
            elif action == "get_environment":
                try:
                    await session.get_environment_data()
                except:
                    traceback.print_exc()
                    # will retry
                    pass
                # await session.get_environment_data()
            elif action == "start_monitoring" and isinstance(session, SSHSession):
                # Only allow start_monitoring for SSH sessions
                print("start_monitoring not yet implemented")
                # await session.start_monitoring()
            elif action == "zoom_in":
                # Access the main window through the view
                view = self.parent
                if hasattr(view, 'page'):
                    current_factor = view.zoomFactor()
                    view.setZoomFactor(min(current_factor + 0.1, 5.0))
            elif action == "zoom_out":
                view = self.parent
                if hasattr(view, 'page'):
                    current_factor = view.zoomFactor()
                    view.setZoomFactor(max(current_factor - 0.1, 0.25))
            else:
                # Default message handling for other actions
                if hasattr(session, f"handle_{action}"):
                    method = getattr(session, f"handle_{action}")
                    await method(payload)
                else:
                    logger.warning(f"Unknown action {action} for session {session.session_id}")
        except Exception as e:
            traceback.print_exc()
            logger.error(f"Error in async message handling: {e}")
            self._send_error(session.session_id, str(e))

    def _relay_to_frontend(self, message: str):
        """Relay messages from sessions to frontend"""
        self.message_to_frontend.emit(message)

    def _send_error(self, session_id: str, error_message: str):
        """Utility method to send error messages to frontend"""
        error = {
            "session_id": session_id,
            "action": "error",
            "payload": {"message": error_message}
        }
        self.message_to_frontend.emit(json.dumps(error))

    async def cleanup(self):
        """Cleanup all sessions"""
        for session in self.sessions.values():
            try:
                if hasattr(session, 'stop'):
                    await session.stop()
            except Exception as e:
                logger.error(f"Error stopping session: {e}")
