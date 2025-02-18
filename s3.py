from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QLineEdit, QPushButton, QTextEdit,
    QFrame, QTreeWidget, QTreeWidgetItem, QGroupBox, QSplitter,
    QScrollArea
)
from PyQt6.QtCore import Qt, QUrl, QSettings, QTimer
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEngineSettings
import sys
from pathlib import Path
import os
import json

from pyretroterm.themes3 import ThemeLibrary, ThemeColors


class ScrollableGroupBox(QGroupBox):
    """A scrollable group box for containing widgets"""

    def __init__(self, title, parent=None):
        super().__init__(title, parent)
        self.scroll_layout = QVBoxLayout(self)

        # Create scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Create container widget for scroll area
        self.scroll_widget = QWidget()
        self.layout = QVBoxLayout(self.scroll_widget)

        # Set up scroll area
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_layout.addWidget(self.scroll_area)

    def addWidget(self, widget):
        """Add a widget to the scrollable container"""
        self.layout.addWidget(widget)


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
    """Terminal preview widget using xterm.js"""

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
                            rows: 15,
                            theme: window.terminal_theme || {
                                foreground: '#000000',
                                background: '#F5E6D3',
                                cursor: '#000000',
                                cursorAccent: '#F5E6D3',
                                selection: '#A1A1A1',
                                selectionForeground: '#FFFFFF',
                                black: '#000000',
                                red: '#CC0000',
                                green: '#008800',
                                yellow: '#CC6600',
                                blue: '#0000CC',
                                magenta: '#CC00CC',
                                cyan: '#008888',
                                white: '#808080',
                                brightBlack: '#666666',
                                brightRed: '#FF0000',
                                brightGreen: '#00CC00',
                                brightYellow: '#FFCC00',
                                brightBlue: '#0000FF',
                                brightMagenta: '#FF00FF',
                                brightCyan: '#00CCCC',
                                brightWhite: '#FFFFFF'
                            }
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

                // Global function to update terminal theme
                window.updateTerminalTheme = function(newTheme) {
                    window.terminal_theme = newTheme;
                    if (term && term.setOption) {
                        console.log('Applying theme:', newTheme);
                        term.setOption('theme', newTheme);
                    } else {
                        console.log('Terminal not ready for theme update');
                    }
                };

                // Initialize terminal with retry mechanism
                function initTerminalWithRetry(maxAttempts = 5) {
                    let attempts = 0;

                    function tryInit() {
                        try {
                            if (attempts >= maxAttempts) {
                                console.error('Failed to initialize terminal after', attempts, 'attempts');
                                return;
                            }

                            attempts++;
                            console.log('Initializing terminal, attempt', attempts);

                            if (window.term) {
                                console.log('Terminal already exists, disposing');
                                window.term.dispose();
                            }

                            term = new Terminal({
                                cursorBlink: true,
                                fontSize: 14,
                                fontFamily: 'Courier New',
                                rows: 15,
                                theme: window.terminal_theme || {}
                            });

                            window.term = term;  // Store reference globally

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

                            // If we have a theme waiting, apply it
                            if (window.terminal_theme) {
                                window.updateTerminalTheme(window.terminal_theme);
                            }

                            console.log('Terminal initialization complete');
                        } catch (e) {
                            console.error('Terminal initialization error:', e);
                            setTimeout(tryInit, 100);  // Retry after 100ms
                        }
                    }

                    tryInit();
                }

                document.addEventListener('DOMContentLoaded', () => initTerminalWithRetry());
            </script>
            <style>
                body { 
                    margin: 0; 
                    padding: 0;
                    height: 100vh;
                    background: transparent;
                }
                #terminal { 
                    height: 100%;
                    background: inherit;
                }
                .xterm-viewport::-webkit-scrollbar {
                    width: 12px;
                }
                .xterm-viewport::-webkit-scrollbar-track {
                    background: var(--scrollbar-bg, #F5E6D3);
                }
                .xterm-viewport::-webkit-scrollbar-thumb {
                    background: var(--scrollbar-thumb, #666666);
                }
                .xterm-viewport::-webkit-scrollbar-thumb:hover {
                    background: var(--scrollbar-thumb-hover, #999999);
                }
                .terminal.xterm {
                    padding: 8px;
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
        self.settings = QSettings('PyRetroTerm', 'ThemeShowcase')

        # Set up UI first
        self.setup_ui()

        # Load themes
        self.load_themes()

        # Apply last used theme after a delay
        QTimer.singleShot(1000, self.apply_saved_theme)

    def apply_saved_theme(self):
        """Apply the last used theme or default"""
        last_theme = self.settings.value('last_theme', 'borland', str)
        print(f"Loading saved theme: {last_theme}")

        # Find theme in combo box
        index = self.theme_combo.findText(last_theme)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)
        else:
            print(f"Saved theme {last_theme} not found, using first available")
            self.theme_combo.setCurrentIndex(0)

        # Force theme application
        self.change_theme(self.theme_combo.currentText())

    def load_themes(self):
        """Load themes and populate combo box"""
        self.theme_combo.clear()
        theme_names = self.theme_manager.get_theme_names()
        self.theme_combo.addItems(theme_names)

        # Select last used theme
        last_theme = self.settings.value('last_theme', 'borland')
        index = self.theme_combo.findText(last_theme)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)

    def setup_ui(self):
        self.setWindowTitle("Theme Showcase")
        self.resize(1200, 800)

        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        # Left panel (controls and inputs)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # Make left panel scrollable
        left_scroll = QScrollArea()
        left_scroll.setWidget(left_panel)
        left_scroll.setWidgetResizable(True)
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        left_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

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
        left_layout.addWidget(selector_frame)

        # Input showcase section (now in a scrollable group box)
        input_showcase = ScrollableGroupBox("Input Elements")

        # Text input group
        text_group = QGroupBox("Text Input Elements")
        text_layout = QVBoxLayout(text_group)

        line_edit = QLineEdit("Sample text input")
        text_edit = QTextEdit("Multi-line\ntext area\nwith multiple lines of content")
        text_edit.setMaximumHeight(100)

        text_layout.addWidget(line_edit)
        text_layout.addWidget(text_edit)
        input_showcase.addWidget(text_group)

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

        input_showcase.addWidget(button_group)

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
        input_showcase.addWidget(tree_group)

        left_layout.addWidget(input_showcase)
        main_layout.addWidget(left_scroll, 1)

        # Right panel (terminal and theme info)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # Make right panel scrollable
        right_scroll = QScrollArea()
        right_scroll.setWidget(right_panel)
        right_scroll.setWidgetResizable(True)
        right_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        right_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Terminal preview
        terminal_frame = HUDFrame()
        terminal_layout = QVBoxLayout(terminal_frame)
        terminal_layout.addWidget(QLabel("Terminal Preview:"))
        self.terminal = TerminalPreview()
        terminal_layout.addWidget(self.terminal)
        right_layout.addWidget(terminal_frame)

        # Theme info
        info_frame = HUDFrame()
        info_layout = QVBoxLayout(info_frame)
        info_layout.addWidget(QLabel("Theme Information:"))
        self.theme_info = QTextEdit()
        self.theme_info.setReadOnly(True)
        info_layout.addWidget(self.theme_info)
        right_layout.addWidget(info_frame)

        main_layout.addWidget(right_scroll, 2)

    def change_theme(self, theme_name):
        """Apply the selected theme, update theme info, and save selection"""
        theme = self.theme_manager.get_theme(theme_name)
        if theme:
            # Apply theme to PyQt widgets
            self.theme_manager.apply_theme(self, theme_name)

            # Apply theme to terminal
            theme_data = theme.to_dict()
            if 'terminal' in theme_data and 'theme' in theme_data['terminal']:
                terminal_theme = theme_data['terminal']['theme']

                # Apply scrollbar colors if present
                scrollbar_style = ""
                if 'scrollbar' in terminal_theme:
                    scrollbar = terminal_theme['scrollbar']
                    scrollbar_style = f"""
                        :root {{
                            --scrollbar-bg: {scrollbar.get('background', '#F5E6D3')};
                            --scrollbar-thumb: {scrollbar.get('thumb', '#666666')};
                            --scrollbar-thumb-hover: {scrollbar.get('thumb_hover', '#999999')};
                        }}
                    """

                # Inject theme into terminal
                script = f"""
                    const style = document.createElement('style');
                    style.textContent = `{scrollbar_style}`;
                    document.head.appendChild(style);

                    if (window.updateTerminalTheme) {{
                        window.updateTerminalTheme({json.dumps(terminal_theme)});
                    }} else {{
                        // Store theme for when terminal initializes
                        window.terminal_theme = {json.dumps(terminal_theme)};
                        console.log('Stored theme for later application');
                    }}
                """
                self.terminal.page.runJavaScript(script)

            # Update theme info display
            theme_dict = theme.to_dict()
            info_text = "Theme Colors:\n\n"

            # Format theme information
            for key, value in theme_dict.items():
                if key != 'terminal':
                    info_text += f"{key}: {value}\n"
                else:
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

            # Save the selected theme
            self.settings.setValue('last_theme', theme_name)


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