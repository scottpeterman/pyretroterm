# pyRetroTerm

A modern terminal emulator built with PyQt6, featuring retro-themed visuals and advanced terminal capabilities.
![Screenshot](https://raw.githubusercontent.com/scottpeterman/pyretroterm/main/screenshots/amber_screen.png)
![License](https://img.shields.io/badge/license-GPL--3.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)

## Features

- 🎨 Retro-themed UI with customizable themes (including Cyberpunk default theme)
- 📑 Multi-tabbed terminal interface
- 🔒 Secure credential management
- 📁 Portable session management with YAML configuration
- 🖥️ Split-pane interface with adjustable layouts
- 🌓 Light and dark mode support
- 🔌 SSH connectivity
- 📊 Built-in telemetry support

## Installation

### Via pip

```bash
pip install pyretroterm
```

### From source

```bash
git clone https://github.com/scottpeterman/pyretroterm.git
cd pyretroterm
pip install -r requirements.txt
python setup.py install
```

## Quick Start

1. Launch the application:
```bash
pyretroterm
```

2. For console mode:
```bash
pyretroterm-con
```

3. On first launch:
   - Set up a master password for credential management
   - Configure your session settings (default configuration will be created)
   - Choose your preferred theme

## Configuration

### Sessions

Sessions are configured via YAML files in the `sessions` directory. A default configuration will be created on first launch:

```yaml
- folder_name: Example
  sessions:
  - DeviceType: linux
    Model: vm 
    SerialNumber: ''
    SoftwareVersion: ''
    Vendor: ubuntu
    credsid: '1'
    display_name: T1000
    host: 10.0.0.104
    port: '22'
```

### Themes

pyRetroTerm comes with several built-in themes:
- Cyberpunk (default)
- Light Mode
- Dark Mode
- Additional retro themes - green and amber

Themes can be switched via the View menu or keyboard shortcuts.

## Requirements

- Python 3.8 or higher
- PyQt6
- Additional dependencies listed in requirements.txt

## Security Features

- Encrypted credential storage
- Master password protection
- Secure session management

## Development

### Building from Source

```bash
git clone https://github.com/scottpeterman/pyretroterm.git
cd pyretroterm
pip install -r requirements.txt
```


## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the GNU General Public License v3 (GPLv3) - see the [LICENSE](LICENSE) file for details.

## Author

Scott Peterman (scottpeterman@gmail.com)

## Acknowledgments

- Thanks to the PyQt6 team for the excellent GUI framework
