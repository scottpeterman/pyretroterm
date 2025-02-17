import sys
import os
import asyncio
import traceback
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtCore import QUrl, pyqtSlot, QObject
from qasync import QEventLoop

from termtel.backend.message_router import MessageRouter


class ZoomController(QObject):
    def __init__(self, web_view):
        super().__init__()
        self.web_view = web_view
        self.zoom_factor = 1.0

    @pyqtSlot()
    def zoom_in(self):
        self.zoom_factor = min(self.zoom_factor + 0.1, 5.0)  # max 500%
        self.web_view.setZoomFactor(self.zoom_factor)

    @pyqtSlot()
    def zoom_out(self):
        self.zoom_factor = max(self.zoom_factor - 0.1, 0.25)  # min 25%
        self.web_view.setZoomFactor(self.zoom_factor)


class MainWindow(QWebEngineView):
    def __init__(self, parent=None):
        super().__init__(parent)  # Pass parent to QWebEngineView
        self.base_path = self.resolve_base_path()
        self.setWindowTitle("Terminal Telemetry")
        self.zoom_controller = ZoomController(self)
        self._cleanup_done = False
        self.setup_ui()

    def resolve_base_path(self):
        """Resolve the base path for frontend files"""
        current_dir = Path(__file__).parent.parent
        return current_dir / 'frontend'

    def setup_ui(self):
        try:
            self.channel = QWebChannel()
        except:
            traceback.print_exc()

        self.message_router = MessageRouter(parent=self)
        self.channel.registerObject("messageRouter", self.message_router)
        self.channel.registerObject("zoomController", self.zoom_controller)

        try:
            self.page().setWebChannel(self.channel)
        except:
            traceback.print_exc()
            return

        # Load the frontend using resolved path
        frontend_path = self.base_path / 'index.html'
        if not frontend_path.exists():
            raise FileNotFoundError(f"Frontend file not found at: {frontend_path}")

        url = QUrl.fromLocalFile(str(frontend_path.absolute()))
        print(f"Loading frontend from: {url.toString()}")
        self.setUrl(url)

    async def cleanup(self):
        """Perform cleanup operations"""
        if self._cleanup_done:
            return

        try:
            await self.message_router.cleanup()
            self._cleanup_done = True
        except Exception as e:
            print(f"Error during cleanup: {e}")
            traceback.print_exc()

    def closeEvent(self, event):
        """Handle window close event"""
        try:
            # Get the running event loop
            loop = asyncio.get_event_loop()

            # Create the cleanup task
            cleanup_future = asyncio.ensure_future(self.cleanup())

            # Add a callback to destroy the window after cleanup
            def cleanup_complete(_):
                self.deleteLater()

            cleanup_future.add_done_callback(cleanup_complete)

        except Exception as e:
            print(f"Error setting up cleanup: {e}")
            traceback.print_exc()

        event.accept()

def main():
    app = QApplication(sys.argv)

    # Set up async event loop
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    # Create and show window
    window = MainWindow()
    window.resize(1200, 800)
    window.show()

    # Run event loop
    with loop:
        try:
            loop.run_forever()
        except Exception as e:
            print(f"Error in main loop: {e}")
            traceback.print_exc()


if __name__ == "__main__":
    main()