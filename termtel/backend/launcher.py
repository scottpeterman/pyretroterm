from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QLineEdit, QPushButton, QFormLayout, QComboBox,
                             QCheckBox, QHBoxLayout)
from PyQt6.QtCore import QObject, pyqtSlot, QSettings
from PyQt6.QtWebEngineWidgets import QWebEngineView
from qasync import QEventLoop
import asyncio
import sys
from pathlib import Path

from termtel.backend.main import MainWindow


class EditableComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.setMaxCount(10)
        self.setMaxVisibleItems(10)
        self.setInsertPolicy(QComboBox.InsertPolicy.InsertAtTop)


class TelemetryLauncher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Telemetry Launcher")
        self.telemetry_window = None

        # Initialize settings
        self.settings = QSettings('YourCompany', 'TelemetryLauncher')

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        form_layout = QFormLayout()

        # Create ComboBox for host with history
        self.host_input = EditableComboBox()
        saved_hosts = self.settings.value('hosts', [])
        if saved_hosts:
            self.host_input.addItems(saved_hosts)
            last_host = self.settings.value('last_host', '')
            if last_host:
                self.host_input.setEditText(last_host)

        # Create ComboBox for username with history
        self.username_input = EditableComboBox()
        saved_usernames = self.settings.value('usernames', [])
        if saved_usernames:
            self.username_input.addItems(saved_usernames)
            last_username = self.settings.value('last_username', '')
            if last_username:
                self.username_input.setEditText(last_username)

        # Password field
        self.password_input = QLineEdit("")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        # Driver type combo box with saved state
        self.driver_select = QComboBox()
        self.driver_select.addItems(["linux", "ios", "eos", "nxos_ssh", "junos"])
        last_driver = self.settings.value('last_driver', '')
        if last_driver:
            index = self.driver_select.findText(last_driver)
            if index >= 0:
                self.driver_select.setCurrentIndex(index)

        # Telemetry checkbox with saved state
        self.telemetry_checkbox = QCheckBox("Telemetry")
        telemetry_state = self.settings.value('telemetry_enabled', True, type=bool)
        self.telemetry_checkbox.setChecked(telemetry_state)

        # Add fields to form
        form_layout.addRow("Host:", self.host_input)
        form_layout.addRow("Username:", self.username_input)
        form_layout.addRow("Password:", self.password_input)
        form_layout.addRow("Driver Type:", self.driver_select)
        form_layout.addRow("", self.telemetry_checkbox)

        # Create buttons
        button_layout = QHBoxLayout()
        launch_btn = QPushButton("Launch")
        launch_btn.clicked.connect(self.launch_telemetry)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.close)
        button_layout.addWidget(launch_btn)
        button_layout.addWidget(cancel_btn)

        # Add layouts to main layout
        layout.addLayout(form_layout)
        layout.addLayout(button_layout)

        # Set fixed size for the window
        self.setFixedSize(300, 250)

        # Apply dark theme styling
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #1a1a1a;
                color: #ffffff;
            }
            QLineEdit, QComboBox {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                padding: 5px;
                color: #ffffff;
                min-width: 200px;
                selection-background-color: #4d4d4d;
            }
            QComboBox::drop-down {
                border: 1px solid #3d3d3d;
                border-left: 1px solid #3d3d3d;
                width: 20px;
                background-color: #2d2d2d;
            }
            QComboBox::down-arrow {
                width: 8px;
                height: 8px;
                background: #ffffff;
                clip-path: polygon(0 0, 100% 0, 50% 100%);
            }
            QComboBox QAbstractItemView {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                color: #ffffff;
                selection-background-color: #4d4d4d;
            }
            QPushButton {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                padding: 8px 16px;
                color: #ffffff;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
            }
            QCheckBox {
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
            }
            QCheckBox::indicator:checked {
                background-color: #4d4d4d;
            }
        """)

    def save_settings(self):
        """Save current values to settings"""
        # Save current host
        current_host = self.host_input.currentText()
        hosts = [self.host_input.itemText(i) for i in range(self.host_input.count())]
        if current_host and current_host not in hosts:
            self.host_input.insertItem(0, current_host)
            while self.host_input.count() > 10:
                self.host_input.removeItem(self.host_input.count() - 1)
            hosts = [self.host_input.itemText(i) for i in range(self.host_input.count())]
        self.settings.setValue('hosts', hosts)
        self.settings.setValue('last_host', current_host)

        # Save current username
        current_username = self.username_input.currentText()
        usernames = [self.username_input.itemText(i) for i in range(self.username_input.count())]
        if current_username and current_username not in usernames:
            self.username_input.insertItem(0, current_username)
            while self.username_input.count() > 10:
                self.username_input.removeItem(self.username_input.count() - 1)
            usernames = [self.username_input.itemText(i) for i in range(self.username_input.count())]
        self.settings.setValue('usernames', usernames)
        self.settings.setValue('last_username', current_username)

        # Save driver and telemetry settings
        self.settings.setValue('last_driver', self.driver_select.currentText())
        self.settings.setValue('telemetry_enabled', self.telemetry_checkbox.isChecked())

    def launch_telemetry(self):
        self.save_settings()
        loop = asyncio.get_event_loop()
        loop.create_task(self.launch_telemetry_async())

    async def launch_telemetry_async(self):
        print("Launching telemetry window...")
        self.telemetry_window = MainWindow()  # Create without parent for independent window
        print("MainWindow instance created")

        await asyncio.sleep(0.1)

        self.telemetry_window.page().loadFinished.connect(self.on_page_loaded)
        print("Connected loadFinished signal")

        self.telemetry_window.resize(1200, 800)
        self.telemetry_window.show()
        print("Window shown")
    def on_page_loaded(self, ok):
        if not ok:
            print("Page failed to load")
            return

        print("Page loaded successfully")
        credentials = {
            'host': self.host_input.currentText(),
            'username': self.username_input.currentText(),
            'password': self.password_input.text(),
            'driver_type': self.driver_select.currentText(),
            'telemetry_enabled': self.telemetry_checkbox.isChecked()
        }

        # Convert credentials to JavaScript object
        creds_js = (f"({{ "
                    f"host: '{credentials['host']}', "
                    f"username: '{credentials['username']}', "
                    f"password: '{credentials['password']}', "
                    f"driver_type: '{credentials['driver_type']}' "
                    f"}})")

        # First establish terminal connection
        js_code = f"""
                if (window.sessionManager && window.sessionManager.sessions.terminal) {{
                    console.log('Starting terminal connection');
                    const connectionInfo = {{
                        host: '{credentials["host"]}',
                        username: '{credentials["username"]}',
                        password: '{credentials["password"]}'
                    }};
                    window.sessionManager.sessions.terminal.connect(connectionInfo);
                }}
                """
        self.telemetry_window.page().runJavaScript(js_code)

        # Execute connection sequence via JavaScript
        js_code = f"""
        const driverSelect = document.getElementById('driver-select');
        if (driverSelect) {{
            driverSelect.value = '{credentials['driver_type']}';
        }}

        const telemetryCheckbox = document.getElementById('useTelemetry');
        if (telemetryCheckbox) {{
            telemetryCheckbox.checked = {str(credentials['telemetry_enabled']).lower()};
        }}

        if (window.sessionManager && window.sessionManager.sessions.telemetry) {{
            console.log('Connecting with credentials:', {creds_js});
            window.sessionManager.sessions.telemetry.connect({creds_js});
        }} else {{
            console.error('Session manager not ready');
        }}
        """

        self.telemetry_window.page().runJavaScript(js_code)

    def closeEvent(self, event):
        """Handle launcher window close event"""
        if self.telemetry_window:
            self.telemetry_window.close()
        self.save_settings()
        event.accept()


def main():
    app = QApplication(sys.argv)

    # Set up async event loop
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    # Create and show launcher
    launcher = TelemetryLauncher()
    launcher.show()

    # Run event loop
    with loop:
        loop.run_forever()


if __name__ == "__main__":
    main()