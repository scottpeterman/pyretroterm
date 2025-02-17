"""
Termtel - UI Setup Module
Handles menu system and dialog setup
"""
import sys

import yaml
from PyQt6.QtGui import QActionGroup, QAction, QDesktopServices
from PyQt6.QtWidgets import (
    QMenuBar, QMenu, QFileDialog, QDialog,
    QVBoxLayout, QLabel, QWidget, QGroupBox, QPushButton, QMessageBox
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl, Qt, QProcess, QProcessEnvironment
import logging
import os

from pyretroterm.widgets.credential_manager import CredentialManagerDialog
from pyretroterm.widgets.lmtosession import LMDownloader
from pyretroterm.widgets.nbtosession import App as NetboxExporter

logger = logging.getLogger('pyretroterm.setup')


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About pyRetro")
        self.setMinimumSize(800, 600)

        # Get theme colors from parent window's theme manager
        theme_name = parent.theme if hasattr(parent, 'theme') else 'cyberpunk'
        theme_colors = parent.theme_manager.get_colors(theme_name) if hasattr(parent, 'theme_manager') else None

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        web_view = QWebEngineView()

        # Define colors based on theme or fallback to defaults
        if theme_colors:
            bg_color = theme_colors['background']
            text_color = theme_colors['text']
            highlight_color = theme_colors['primary']
            secondary_color = theme_colors['border']
            border_color = theme_colors['border']
        else:
            bg_color = "#1e1e1e"
            text_color = "#ffffff"
            highlight_color = "#0affff"
            secondary_color = "#888888"
            border_color = "#444444"

        about_html = f"""
        <html>
        <head>
            <style>
                body {{
                    background-color: {bg_color};
                    color: {text_color};
                    font-family: 'Segoe UI', Arial, sans-serif;
                    line-height: 1.6;
                    margin: 0;
                    padding: 20px 40px;
                }}
                .container {{
                    max-width: 800px;
                    margin: 0 auto;
                }}
                h1 {{
                    color: {text_color};
                    text-align: center;
                    font-size: 2.5em;
                    margin-bottom: 10px;
                }}
                h2 {{
                    color: {text_color};
                    margin-top: 25px;
                }}
                h3 {{
                    color: {text_color};
                    margin-top: 20px;
                    font-size: 1.2em;
                }}
                .subtitle {{
                    color: {text_color};
                    text-align: center;
                    font-size: 1.1em;
                    margin-bottom: 30px;
                }}
                .feature-list {{
                    list-style-type: none;
                    padding: 0;
                }}
                .feature-list li {{
                    margin: 10px 0;
                    padding-left: 25px;
                    position: relative;
                }}
                .feature-list li:before {{
                    content: "✓";
                    color: {text_color};
                    position: absolute;
                    left: 0;
                }}
                .highlight {{
                    color: {text_color};
                }}
                .footer {{
                    margin-top: 40px;
                    text-align: center;
                    color: {secondary_color};
                    border-top: 1px solid {border_color};
                    padding-top: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>pyRetroTerm</h1>
                <div class="subtitle">A minimalist, retro-inspired terminal emulator with modern features</div>

                <h2>Key Features</h2>
                <div class="feature-list">
                    <h3>Modern Terminal Emulator</h3>
                    <ul>
                        <li>Multi-session support with tabbed interface</li>
                        <li>Customizable themes (Cyberpunk, Dark Mode, Light Mode, Retro Green, Retro Amber, Neon Blue)</li>
                        <li>Session management and quick connect functionality</li>
                        <li>Secure credential storage</li>
                    </ul>

                     <h3>Theme System</h3>
                    <ul>
                        <li>Dynamic JSON-based themes</li>
                        <li>Live theme preview and hot-reload</li>
                        <li>Custom theme creation support</li>
                    </ul>
                    <div class="code">
                    To install themes:
                    1. Download themes.zip from View > Theme > Download Themes
                    2. Extract to 'themes' directory
                    3. Click View > Theme > Reload Themes
                    </div>

                    <h3>Security Features</h3>
                    <ul>
                        <li>PBKDF2-HMAC-SHA256 key derivation (480,000 iterations)</li>
                        <li>Fernet (AES-128-CBC) encryption with HMAC authentication</li>
                        <li>Platform-specific secure storage locations</li>
                        <li>Machine-specific binding</li>
                        <li>Rate-limited authentication</li>
                        <li>Cross-platform secure credential management</li>
                        <li>Zero plaintext storage of sensitive data</li>
                    </ul>
                </div>

                <div class="footer">
                    <p>Author: Scott Peterman (github.com/scottpeterman)</p>
                    <p>Licensed under GNU General Public License v3 (GPLv3)</p>
                </div>
            </div>
        </body>
        </html>
        """
        web_view.setHtml(about_html)
        layout.addWidget(web_view)
        self.setLayout(layout)

        # Apply the parent's theme to the dialog
        if hasattr(parent, 'theme_manager'):
            parent.theme_manager.apply_theme(self, theme_name)


class TelemetryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Telemetry Settings")
        self.setMinimumSize(500, 400)

        layout = QVBoxLayout()

        # Data Collection Group
        collection_group = QGroupBox("Data Collection")
        collection_layout = QVBoxLayout()
        # TODO: Add data collection settings
        collection_group.setLayout(collection_layout)

        # Export Group
        export_group = QGroupBox("Data Export")
        export_layout = QVBoxLayout()
        export_btn = QPushButton("Export Telemetry Data")
        export_btn.clicked.connect(self.export_telemetry)
        export_layout.addWidget(export_btn)
        export_group.setLayout(export_layout)

        layout.addWidget(collection_group)
        layout.addWidget(export_group)
        self.setLayout(layout)

    def export_telemetry(self):
        # TODO: Implement telemetry export
        logger.info("Telemetry export requested")
        pass


def setup_menus(window):
    """Setup menu system for the main window"""
    menubar = window.menuBar()

    # File Menu
    file_menu = menubar.addMenu("&File")
    open_action = file_menu.addAction("&Open Sessions...")
    open_action.triggered.connect(lambda: handle_open_sessions(window))
    file_menu.addSeparator()
    exit_action = file_menu.addAction("E&xit")
    exit_action.triggered.connect(window.close)

    # View Menu
    view_menu = menubar.addMenu("&View")

    # Create Themes submenu with dynamic theme loading
    themes_menu = view_menu.addMenu("Theme")
    theme_group = QActionGroup(window)
    theme_group.setExclusive(True)

    # Get available themes from ThemeLibrary
    available_themes = window.theme_manager.get_theme_names()

    # Create theme actions
    for theme_name in available_themes:
        # Convert theme name to display name (e.g., "dark_mode" -> "Dark Mode")
        display_name = theme_name.replace('_', ' ').title()

        theme_action = QAction(display_name, window)
        theme_action.setCheckable(True)
        theme_action.setChecked(theme_name == window.theme)
        theme_action.triggered.connect(
            lambda checked, t=theme_name: window.switch_theme(t)
        )
        theme_group.addAction(theme_action)
        themes_menu.addAction(theme_action)

    # Add theme reload action
    themes_menu.addSeparator()
    reload_themes = themes_menu.addAction("Reload Themes")
    reload_themes.triggered.connect(lambda: reload_theme_menu(window, themes_menu, theme_group))
    download_themes = themes_menu.addAction("Download Themes")
    download_themes.triggered.connect(
        lambda: QDesktopServices.openUrl(
            QUrl("https://raw.githubusercontent.com/scottpeterman/pyretroterm/main/themes.zip")
        )
    )
    credentials_action = view_menu.addAction("&Credentials")
    credentials_action.triggered.connect(lambda: show_credentials_dialog(window))

    # Tools Menu
    tools_menu = menubar.addMenu("&Tools")

    netbox_action = tools_menu.addAction("&Netbox Import")
    netbox_action.triggered.connect(lambda: show_netbox_importer(window))

    lm_action = tools_menu.addAction("&LogicMonitor Import")
    lm_action.triggered.connect(lambda: show_logicmonitor_importer(window))

    telemetry_action = tools_menu.addAction('Telemetry')
    telemetry_action.triggered.connect(lambda: launch_telemetry(window))

    manage_sessions_action = tools_menu.addAction('Manage Sessions')
    manage_sessions_action.triggered.connect(lambda: show_session_manager(window))

    # Add separator before distractions menu
    tools_menu.addSeparator()

    # Add Distractions submenu
    distractions_menu = tools_menu.addMenu("Distractions")
    distractions_menu.setObjectName("menu_distractions")

    # Add Notepad action
    notepad_action = distractions_menu.addAction("Notepad")
    notepad_action.triggered.connect(
        lambda: window.terminal_tabs.create_text_editor_tab("Notepad")
    )

    space_debris = distractions_menu.addAction("Space Debris")
    space_debris.triggered.connect(
        lambda: window.terminal_tabs.create_game_tab("Space Debris")
    )

    doom_action = distractions_menu.addAction("Doom")
    doom_action.triggered.connect(
        lambda: window.terminal_tabs.create_doom_tab("Doom")
    )

    # Help Menu
    help_menu = menubar.addMenu("&Help")

    about_action = help_menu.addAction("&About")
    about_action.triggered.connect(lambda: show_about_dialog(window))

def reload_theme_menu(window, themes_menu, theme_group):
    """Reload the themes menu with current themes from ThemeLibrary"""
    # Clear existing theme actions
    for action in theme_group.actions():
        themes_menu.removeAction(action)
        theme_group.removeAction(action)

    # Reload themes from library
    window.theme_manager._load_custom_themes()

    # Add new theme actions
    available_themes = window.theme_manager.get_theme_names()
    for theme_name in available_themes:
        display_name = theme_name.replace('_', ' ').title()
        theme_action = QAction(display_name, window)
        theme_action.setCheckable(True)
        theme_action.setChecked(theme_name == window.theme)
        theme_action.triggered.connect(
            lambda checked, t=theme_name: window.switch_theme(t)
        )
        theme_group.addAction(theme_action)
        themes_menu.insertAction(themes_menu.actions()[-2], theme_action)  # Insert before separator

# Remove TelemetryDialog and show_telemetry_dialog since they're not needed anymore
def toggle_telemetry(window, telemetry_action):
    """Toggle telemetry frame visibility and save state"""
    is_visible = telemetry_action.isChecked()
    window.telemetry_frame.setVisible(is_visible)
    # Save state to settings
    window.settings_manager.set_view_setting('telemetry_visible', is_visible)
def show_session_manager(window):
    """Launch the session manager dialog"""
    from pyretroterm.widgets.session_editor import SessionEditorDialog

    dialog = SessionEditorDialog(window, session_file=window.session_file_with_path)
    if dialog.exec() == dialog.DialogCode.Accepted:
        # Reload the sessions after editing
        # window.load_sessions(window, window.session_file_with_path)
        try:
            with open(window.session_file_with_path) as f:
                sessions_data = yaml.safe_load(f)
                window.session_navigator.load_sessions(file_content_to_load=sessions_data)

        except Exception as e:
            logger.error(f"Failed to load sessions: {str(e)}")



def show_netbox_importer(window):
    """Show the Netbox to Session importer"""
    try:
        dialog = NetboxExporter(window)
        dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        dialog.show()
    except Exception as e:
        logger.error(f"Error showing Netbox importer: {e}")

def handle_open_sessions(window):
    """Handle opening a new sessions file"""
    try:
        file_name, _ = QFileDialog.getOpenFileName(
            window,
            "Open Sessions File",
            "",
            "YAML Files (*.yaml);;All Files (*)"
        )
        if file_name:
            logger.info(f"Opening sessions file: {file_name}")
            window.session_file = file_name
            window.load_sessions()
    except Exception as e:
        logger.error(f"Error opening sessions file: {e}")


def show_credentials_dialog(window):
    """Show the credentials management dialog"""
    try:
        dialog = CredentialManagerDialog(window)
        dialog.credentials_updated.connect(window.session_navigator.load_sessions)
        dialog.exec()
    except Exception as e:
        logger.error(f"Error showing credentials dialog: {e}")


def show_telemetry_dialog(window):
    """Show the telemetry settings dialog"""
    try:
        window.launch_telemetry()
    except Exception as e:
        logger.error(f"Error showing telemetry dialog: {e}")


def show_about_dialog(window):
    """Show the about dialog"""
    try:
        dialog = AboutDialog(window)
        dialog.exec()
    except Exception as e:
        logger.error(f"Error showing about dialog: {e}")

def show_logicmonitor_importer(window):
    """Show the LogicMonitor to Session importer"""
    try:
        window.lmdialog = LMDownloader(window)
        window.lmdialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        window.lmdialog.show()
    except Exception as e:
        logger.error(f"Error showing LogicMonitor importer: {e}")


def launch_telemetry(window):
    """
    Launch the telemetry backend using the current Python interpreter.
    Handles process management and error cases.

    Args:
        window: The main application window instance
    """
    try:
        # Create a QProcess instance
        process = QProcess(window)

        # Set up environment
        env = QProcessEnvironment.systemEnvironment()
        process.setProcessEnvironment(env)

        # Set up the command and arguments
        python_path = sys.executable
        args = ['-m', 'termtel.backend.launcher']

        # Optional: Log the command being executed
        print(f"Launching telemetry with: {python_path} {' '.join(args)}")

        # Connect signals for monitoring
        process.errorOccurred.connect(lambda error: _handle_error(window, error))
        process.finished.connect(lambda code, status: _handle_finish(window, code, status))
        process.readyReadStandardError.connect(lambda: _handle_stderr(process))
        process.readyReadStandardOutput.connect(lambda: _handle_stdout(process))

        # Start the process
        process.start(python_path, args)

        # Store process reference if needed later
        window.telemetry_process = process

    except Exception as e:
        QMessageBox.critical(
            window,
            "Telemetry Launch Error",
            f"Failed to start telemetry process: {str(e)}"
        )


def _handle_error(window, error):
    """Handle QProcess errors"""
    error_messages = {
        QProcess.ProcessError.FailedToStart: "The process failed to start",
        QProcess.ProcessError.Crashed: "The process crashed",
        QProcess.ProcessError.Timedout: "The process timed out",
        QProcess.ProcessError.WriteError: "Write error occurred",
        QProcess.ProcessError.ReadError: "Read error occurred",
        QProcess.ProcessError.UnknownError: "Unknown error occurred"
    }

    error_msg = error_messages.get(error, "An unknown error occurred")
    # QMessageBox.critical(
    #     window,
    #     "Telemetry Error",
    #     f"Telemetry process error: {error_msg}"
    # )


def _handle_finish(window, exit_code, exit_status):
    """Handle process completion"""
    pass
    # if exit_code != 0:
    #     QMessageBox.warning(
    #         window,
    #         "Telemetry Warning",
    #         f"Telemetry process exited with code {exit_code}"
    #     )

    # Clean up process reference
    if hasattr(window, 'telemetry_process'):
        delattr(window, 'telemetry_process')


def _handle_stdout(process):
    """Handle process standard output"""
    data = process.readAllStandardOutput()
    stdout = bytes(data).decode('utf8')
    print(f"Telemetry stdout: {stdout}")


def _handle_stderr(process):
    """Handle process standard error"""
    data = process.readAllStandardError()
    stderr = bytes(data).decode('utf8')
    print(f"Telemetry stderr: {stderr}")