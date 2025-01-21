# pyRetroTerm

A modern terminal emulator built with PyQt6, featuring retro-themed visuals and advanced terminal capabilities.
![Screenshot](https://raw.githubusercontent.com/scottpeterman/pyretroterm/main/screenshots/slides1.gif)
![License](https://img.shields.io/badge/license-GPL--3.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)

## Features

-  Retro-themed UI with customizable themes (CRT Green and Amber, Dark/Light etc)
-  Multi-tabbed terminal interface
-  Secure encrypted credential management
-  Portable session management with YAML configuration
- ️ Split-pane interface with adjustable layouts
-  SSH connectivity with full terminal emulation
-  Netbox integration, export netbox devices into a local sessions YAML file

## Installation

### Via pip

```bash
pip install pyretroterm
pyretroterm
```

### From source

```bash
git clone https://github.com/scottpeterman/pyretroterm.git
cd pyretroterm
pip install -r requirements.txt
python -m pyretroterm.pyretroterm
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

Themes can be switched via the View menu.

## Requirements

- Python 3.8 or higher
- PyQt6
- Additional dependencies listed in requirements.txt

## Security Features

- Encrypted credential storage
- Master password protection
- Secure session management


## License

This project is licensed under the GNU General Public License v3 (GPLv3) - see the [LICENSE](LICENSE) file for details.

## Author

Scott Peterman (scottpeterman@gmail.com)

## Acknowledgments

- Thanks to the PyQt6 team for the excellent GUI framework
