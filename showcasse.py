from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QLineEdit, QPushButton, QTextEdit,
    QFrame, QTreeWidget, QTreeWidgetItem, QGroupBox, QSplitter
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEngineSettings
import sys
from pathlib import Path
import os
import json

from pyretroterm.themes3 import ThemeLibrary, ThemeColors


class HUDFrame(QFrame):
    """A frame with a HUD-like border effect"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                border: 1px solid;
                background-color: transparent;
                padding: 10px;
            }
        """)


class TerminalPreview(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create the web view
        self.view = QWebEngineView(self)
        layout.addWidget(self.view)

        # Store page reference for theme manager
        self.page = self.view.page()

        # Configure web settings
        settings = self.page.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)

        # Set up console message handling
        self.page.javaScriptConsoleMessage = self.handle_console_message

        self.view.setHtml("""
        <!DOCTYPE html>
        <html>
        <head>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/xterm/3.14.5/xterm.css" />
            <script src="https://cdnjs.cloudflare.com/ajax/libs/xterm/3.14.5/xterm.js"></script>
            <script>
                window.onerror = function(msg, url, line) {
                    console.error('JavaScript error:', msg, 'at', url, ':', line);
                    return false;
                };

                let term;

                function initTerminal() {
                    try {
                        console.log('Initializing terminal...');
                        term = new Terminal({
                            cursorBlink: true,
                            fontSize: 14,
                            fontFamily: 'Courier New',
                            rows: 15
                        });

                        console.log('Opening terminal...');
                        term.open(document.getElementById('terminal'));

                        // Add test content showing various colors
                        term.writeln('\\x1b[1;37m=== Terminal Theme Preview ===\\x1b[0m');
                        term.writeln('');
                        term.writeln('\\x1b[34mDirectory listing:\\x1b[0m');
                        term.writeln('\\x1b[33mthemes/\\x1b[0m');
                        term.writeln('  \\x1b[32mborland.json\\x1b[0m');
                        term.writeln('  \\x1b[32mcyberpunk.json\\x1b[0m');
                        term.writeln('');
                        term.write('$ ');

                        console.log('Terminal initialization complete');
                    } catch (e) {
                        console.error('Terminal initialization error:', e);
                    }
                }

                document.addEventListener('DOMContentLoaded', initTerminal);
            </script>
            <style>
                body { 
                    margin: 0; 
                    padding: 0; 
                    height: 100vh; 
                }
                #terminal { 
                    height: 100%;
                }
                .xterm-viewport::-webkit-scrollbar {
                    width: 12px;
                }
            </style>
        </head>
        <body>
            <div id="terminal"></div>
        </body>
        </html>
        """)
        self.view.setMinimumHeight(300)

    def handle_console_message(self, level, message, line, source_id):
        print(f"Console: [{level}] {message} (line {line}, source: {source_id})")

class ThemeShowcase(QMainWindow):
    def __init__(self):
        super().__init__()
        self.theme_manager = ThemeLibrary()
        self.setup_ui()
        self.load_themes()

        # Apply default theme
        self.change_theme("borland")  # Changed default to borland

    def load_themes(self):
        """Load themes and populate combo box"""
        self.theme_combo.clear()
        theme_names = self.theme_manager.get_theme_names()
        self.theme_combo.addItems(theme_names)

        # If borland theme exists, select it
        borland_index = self.theme_combo.findText("borland")
        if borland_index >= 0:
            self.theme_combo.setCurrentIndex(borland_index)

    def setup_ui(self):
        self.setWindowTitle("Theme Showcase")
        self.resize(1200, 900)

        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # Create splitter for main content
        splitter = QSplitter(Qt.Orientation.Vertical)
        layout.addWidget(splitter)

        # Top section
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)

        # Theme selector section
        selector_frame = HUDFrame()
        selector_layout = QVBoxLayout(selector_frame)

        theme_label = QLabel("Select Theme:")
        self.theme_combo = QComboBox()
        self.theme_combo.currentTextChanged.connect(self.change_theme)

        reload_button = QPushButton("Reload Themes")
        reload_button.clicked.connect(self.load_themes)

        selector_layout.addWidget(theme_label)
        selector_layout.addWidget(self.theme_combo)
        selector_layout.addWidget(reload_button)
        top_layout.addWidget(selector_frame)

        # Input showcase section
        input_frame = HUDFrame()
        input_layout = QVBoxLayout(input_frame)

        # Text input group
        text_group = QGroupBox("Text Input Elements")
        text_layout = QVBoxLayout(text_group)

        line_edit = QLineEdit("Sample text input")
        text_edit = QTextEdit("Multi-line\ntext area\nwith multiple lines of content")
        text_edit.setMaximumHeight(100)

        text_layout.addWidget(line_edit)
        text_layout.addWidget(text_edit)
        input_layout.addWidget(text_group)

        # Buttons group
        button_group = QGroupBox("Buttons")
        button_layout = QHBoxLayout(button_group)

        buttons = [
            QPushButton("Normal Button"),
            QPushButton("Hover Me"),
            QPushButton("Click Me")
        ]
        for btn in buttons:
            button_layout.addWidget(btn)

        input_layout.addWidget(button_group)

        # Tree view
        tree_group = QGroupBox("Tree View")
        tree_layout = QVBoxLayout(tree_group)

        tree = QTreeWidget()
        tree.setHeaderLabels(["Item", "Value"])
        root = QTreeWidgetItem(tree, ["Root Item", "Root Value"])
        child1 = QTreeWidgetItem(root, ["Child 1", "Value 1"])
        child2 = QTreeWidgetItem(root, ["Child 2", "Value 2"])
        root.addChild(QTreeWidgetItem(["Child 3", "Value 3"]))
        root.setExpanded(True)

        tree_layout.addWidget(tree)
        input_layout.addWidget(tree_group)

        top_layout.addWidget(input_frame)
        splitter.addWidget(top_widget)

        # Bottom section (terminal and theme info)
        bottom_widget = QWidget()
        bottom_layout = QHBoxLayout(bottom_widget)

        # Terminal preview
        terminal_frame = HUDFrame()
        terminal_layout = QVBoxLayout(terminal_frame)
        terminal_layout.addWidget(QLabel("Terminal Preview:"))
        self.terminal = TerminalPreview()
        terminal_layout.addWidget(self.terminal)
        bottom_layout.addWidget(terminal_frame)

        # Theme info
        info_frame = HUDFrame()
        info_layout = QVBoxLayout(info_frame)
        info_layout.addWidget(QLabel("Theme Information:"))
        self.theme_info = QTextEdit()
        self.theme_info.setReadOnly(True)
        info_layout.addWidget(self.theme_info)
        bottom_layout.addWidget(info_frame)

        splitter.addWidget(bottom_widget)

    def change_theme(self, theme_name):
        """Apply the selected theme and update theme info"""
        theme = self.theme_manager.get_theme(theme_name)
        if theme:
            # Apply theme to PyQt widgets
            self.theme_manager.apply_theme(self, theme_name)

            # Apply theme to terminal
            self.theme_manager.apply_theme_to_terminal(self.terminal, theme_name)

            # Update theme info display
            theme_dict = theme.to_dict()
            info_text = "Theme Colors:\n\n"

            # Format theme information
            for key, value in theme_dict.items():
                if key != 'terminal':  # Handle regular theme properties
                    info_text += f"{key}: {value}\n"
                else:  # Handle terminal theme section
                    info_text += "\nTerminal Theme:\n"
                    if isinstance(value, dict) and 'theme' in value:
                        for tk, tv in value['theme'].items():
                            if isinstance(tv, dict):
                                info_text += f"  {tk}:\n"
                                for sk, sv in tv.items():
                                    info_text += f"    {sk}: {sv}\n"
                            else:
                                info_text += f"  {tk}: {tv}\n"

            self.theme_info.setText(info_text)


def main():
    try:
        app = QApplication(sys.argv)
        print("Setting up web profile...")
        profile = QWebEngineProfile.defaultProfile()

        print("Creating main window...")
        window = ThemeShowcase()

        print("Showing window...")
        window.show()

        print("Entering event loop...")
        sys.exit(app.exec())
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()