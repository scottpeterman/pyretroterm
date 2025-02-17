import traceback

import napalm
from PyQt6.QtCore import QObject, pyqtSignal, QThread
import asyncio
import json
import logging
import paramiko
import os
from termtel.backend.linux_driver import LinuxDriver

logger = logging.getLogger(__name__)


class TelemetryCollector(QThread):
    telemetry_ready = pyqtSignal(dict)
    error_signal = pyqtSignal(str)

    def __init__(self, device, parent=None):
        super().__init__(parent)
        self.device = device
        self._is_running = False

    def run(self):
        self._is_running = True
        while self._is_running:
            try:
                # Get device info first with retry mechanism
                device_info = None
                for attempt in range(6):  # max_retries = 6
                    try:
                        print(f"\nAttempting to get device info (attempt {attempt + 1}/6)...")
                        facts = self.device.get_facts()

                        if "unknown" in facts.get('hostname', 'unknown'):
                            raise ValueError('not enough values to unpack')

                        uptime_seconds = facts.get("uptime", 0)
                        days = int(uptime_seconds // 86400)
                        hours = int((uptime_seconds % 86400) // 3600)
                        minutes = int((uptime_seconds % 3600) // 60)

                        device_info = {
                            "hostname": facts.get("hostname"),
                            "model": facts.get("model"),
                            "serial": facts.get("serial_number"),
                            "os_version": facts.get("os_version"),
                            "uptime": f"{days}d {hours}h {minutes}m"
                        }
                        print("Successfully got device info!")
                        break  # Success, exit retry loop

                    except ValueError as e:
                        if "not enough values to unpack" in str(e):
                            print(f"\nSession confusion detected on attempt {attempt + 1}: {e}")
                            if attempt < 5:  # max_retries - 1
                                delay = 1 * (2 ** attempt)  # Exponential backoff
                                print(f"Waiting {delay} seconds before next attempt...")
                                self.sleep(delay)
                        else:
                            print(f"\nValue error on attempt {attempt + 1}: {e}")

                    except Exception as e:
                        print(f"\nError on attempt {attempt + 1}: {e}")
                        if attempt < 5:
                            delay = 1 * (2 ** attempt)
                            print(f"Waiting {delay} seconds before next attempt...")
                            self.sleep(delay)

                if not device_info:
                    raise Exception("Failed to get device info after max retries")

                # Get interfaces
                print("retrieving interfaces via cli")
                interfaces = self.device.get_interfaces()
                processed_interfaces = [
                    {
                        "name": name,
                        "status": "UP" if details.get("is_up") else "DOWN"
                    }
                    for name, details in interfaces.items()
                ]

                # Get neighbors
                try:
                    neighbors = self.device.get_lldp_neighbors_detail()
                except:
                    neighbors = []
                processed_neighbors = [
                    {
                        "local_port": port,
                        "neighbor": neighbor.get("remote_system_name", "Unknown"),
                        "remote_port": neighbor.get("remote_port", "Unknown")
                    }
                    for port, port_neighbors in neighbors.items()
                    for neighbor in port_neighbors
                ]

                # Get routes
                route_details = self.device.get_route_to(destination="0.0.0.0/0")
                routes = []
                try:
                    for protocol_details in route_details.values():
                        for route in protocol_details:
                            routes.append({
                                "network": route.get("destination", "0.0.0.0"),
                                "mask": route.get("prefix_length", "0"),
                                "next_hop": route.get("next_hop", "")
                            })
                except:
                    routes = []

                # Get environment data
                environment = self.device.get_environment()
                processed_env = {}
                if environment:
                    # Process CPU data
                    cpu_info = {}
                    if 'cpu' in environment:
                        cpu_data = environment['cpu']
                        if isinstance(cpu_data, dict):
                            cpu_usages = [cpu['%usage'] for cpu in cpu_data.values() if '%usage' in cpu]
                            if cpu_usages:
                                cpu_info['average_usage'] = sum(cpu_usages) / len(cpu_usages)
                                cpu_info['num_cpus'] = len(cpu_usages)

                    # Process Memory data
                    memory_info = {}
                    if 'memory' in environment:
                        mem = environment['memory']
                        memory_info['total'] = mem.get('available_ram', 0)
                        memory_info['used'] = mem.get('used_ram', 0)
                        if memory_info['total'] > 0:
                            memory_info['usage_percent'] = (memory_info['used'] / memory_info['total']) * 100

                    processed_env = {
                        'cpu': cpu_info,
                        'memory': memory_info,
                        'temperature': [
                            {
                                'location': loc,
                                'temperature': data.get('temperature', 0),
                                'alert': data.get('is_alert', False),
                                'critical': data.get('is_critical', False)
                            }
                            for loc, data in environment.get('temperature', {}).items()
                        ],
                        'power': [
                            {
                                'id': psu_id,
                                'status': data.get('status', False),
                                'capacity': data.get('capacity', 0),
                                'output': data.get('output', 0)
                            }
                            for psu_id, data in environment.get('power', {}).items()
                        ],
                        'fans': [
                            {
                                'location': loc,
                                'status': data.get('status', False)
                            }
                            for loc, data in environment.get('fans', {}).items()
                        ]
                    }

                # Emit collected data
                update_data = {
                    "device_info": device_info,  # Include device info in update
                    "interfaces": processed_interfaces,
                    "neighbors": processed_neighbors,
                    "routing_table": routes,
                    "environment": processed_env
                }
                self.telemetry_ready.emit(update_data)

            except Exception as e:
                traceback.print_exc()
                self.error_signal.emit(f"Error collecting telemetry: {str(e)}")

            # Sleep for 30 seconds before next collection
            if self._is_running:
                print("\nWaiting 30 seconds before next telemetry collection...")
                self.sleep(30)

class BaseSession(QObject):
    """Base class for all session types"""
    message_ready = pyqtSignal(str)

    def __init__(self, session_id):
        super().__init__()
        self.session_id = session_id
        self.queue = asyncio.Queue()
        self._active = False

    def send_message(self, action: str, payload: dict):
        message = {
            "session_id": self.session_id,
            "action": action,
            "payload": payload
        }
        print(message)
        self.message_ready.emit(json.dumps(message))


import paramiko
import asyncio
import logging
from typing import Optional, Dict, Any



class SSHSession(BaseSession):
    """Handles SSH terminal sessions with support for legacy cipher suites"""

    def __init__(self, session_id: str):
        super().__init__(session_id)
        self.client = None
        self.channel = None
        self.session_id = session_id
        self._active = False

        # Configure Paramiko's preferred algorithms
        paramiko.Transport._preferred_kex = (
            "diffie-hellman-group14-sha1",
            "diffie-hellman-group-exchange-sha1",
            "diffie-hellman-group-exchange-sha256",
            "diffie-hellman-group1-sha1",
            "ecdh-sha2-nistp256",
            "ecdh-sha2-nistp384",
            "ecdh-sha2-nistp521",
            "curve25519-sha256",
            "curve25519-sha256@libssh.org",
            "diffie-hellman-group16-sha512",
            "diffie-hellman-group18-sha512"
        )

        paramiko.Transport._preferred_ciphers = (
            "aes128-cbc",
            "aes128-ctr",
            "aes192-ctr",
            "aes256-ctr",
            "aes256-cbc",
            "3des-cbc",
            "aes192-cbc",
            "aes256-gcm@openssh.com",
            "aes128-gcm@openssh.com",
            "chacha20-poly1305@openssh.com",
            "aes256-gcm",
            "aes128-gcm"
        )

        paramiko.Transport._preferred_keys = (
            "ssh-rsa",
            "ssh-dss",
            "ecdsa-sha2-nistp256",
            "ecdsa-sha2-nistp384",
            "ecdsa-sha2-nistp521",
            "ssh-ed25519",
            "rsa-sha2-256",
            "rsa-sha2-512"
        )

    async def connect(self, host: str, username: str,
                      password: Optional[str] = None,
                      key_path: Optional[str] = None) -> None:
        """Establish SSH connection with legacy cipher support"""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Connect with modified defaults and disabled key searching
            await asyncio.to_thread(
                self.client.connect,
                hostname=host,
                username=username,
                password=password,
                key_filename=key_path if key_path else None,
                look_for_keys=False,
                allow_agent=False,
                timeout=30
            )

            # Request a PTY terminal
            self.channel = self.client.invoke_shell(term='xterm')
            self.channel.set_combine_stderr(True)

            # Set active flag for read loop
            self._active = True
            print(f"ssh session connected - terminal")
            self.send_message("connected", {"status": "success"})

            # Start reading output
            await asyncio.create_task(self._read_output())


        except Exception as e:
            logger.error(f"Connection error: {e}")
            self.send_message("error", {"message": str(e)})
            raise

    async def handle_data(self, payload: Dict[str, Any]) -> None:
        """Handle incoming terminal data"""
        if self.channel and self.channel.active:
            try:
                text = payload.get("text", "")
                self.channel.send(text)
            except Exception as e:
                logger.error(f"Failed to send data: {e}")
                self.send_message("error", {"message": str(e)})

    async def handle_resize(self, payload: Dict[str, Any]) -> None:
        """Handle terminal resize events"""
        print(f"handle_resize: {payload}")
        if self.channel and self.channel.active:
            try:
                cols = payload.get('cols', 80)
                rows = payload.get('rows', 24)
                self.channel.resize_pty(width=cols - 4, height=rows)
            except Exception as e:
                logger.error(f"Failed to resize PTY: {e}")

    async def _read_output(self) -> None:
        """Read and forward SSH output"""
        while self._active and self.channel:
            try:
                data = await asyncio.to_thread(self.channel.recv, 1024)
                if not data:  # Connection closed
                    break
                self.send_message("data", {"text": data.decode()})
            except Exception as e:
                logger.error(f"Read error: {e}")
                break

        # If we break out of the loop and were still active, there was an error
        if self._active:
            await self.disconnect()

    async def disconnect(self) -> None:
        """Disconnect SSH session"""
        self._active = False
        if self.channel:
            self.channel.close()
        if self.client:
            self.client.close()
        self.send_message("disconnected", {"status": "success"})

    async def stop(self) -> None:
        """Stop the session"""
        await self.disconnect()


class TelemetrySession(BaseSession):
    def __init__(self, session_id):
        super().__init__(session_id)
        self.device = None
        self._active = False
        self.refresh_rate = 30  # seconds
        self.collector = None  # Track collector instance

    async def connect(self, host, username, password=None, driver_type="linux"):
        """Establish Napalm connection to device"""
        try:
            # Configure logging for Netmiko to reduce noise
            logging.getLogger('netmiko').setLevel(logging.WARNING)
            logging.getLogger('paramiko').setLevel(logging.WARNING)

            # Get the appropriate Napalm driver
            driver_map = {
                "ios": napalm.get_network_driver("ios"),
                "eos": napalm.get_network_driver("eos"),
                "nxos_ssh": napalm.get_network_driver("nxos_ssh"),
                "junos": napalm.get_network_driver("junos"),
                "linux": LinuxDriver
            }

            if driver_type not in driver_map:
                raise ValueError(f"Unsupported driver type: {driver_type}")

            driver = driver_map[driver_type]

            # Define base optional arguments with adjusted timeouts
            optional_args = {
                'port': 22,
                'timeout': 120,  # Increased global timeout
                'keepalive': 30,
                'auto_rollback_on_error': True,
                'netmiko_options': {
                    'timeout': 120,  # Connection timeout
                    'global_delay_factor': 2,  # Multiplier for all delays
                    'read_timeout_override': 90,  # Override for read operations
                    'fast_cli': False,  # Disable fast_cli for reliability
                    'session_timeout': 120,  # Session timeout
                    'session_log': None,
                    'conn_timeout': 60,  # Connection establishment timeout
                }
            }

            # Platform-specific configurations
            if driver_type == "eos":
                optional_args.update({
                    'transport': 'ssh',
                    'port': 22,
                    'allow_agent': False,
                    'enable_mode': True,
                    'use_keys': False,
                    'key_file': None,
                    'netmiko_options': {
                        'global_delay_factor': 2,
                        'read_timeout_override': 120,
                        'expect_string': r'[>#]',  # More permissive prompt pattern
                        'fast_cli': False
                    }
                })
            elif driver_type == "nxos_ssh":
                optional_args['netmiko_options'].update({
                    'global_delay_factor': 3,
                    'read_timeout_override': 120
                })
            elif driver_type == "ios":
                optional_args['netmiko_options'].update({
                    'global_delay_factor': 3,
                    'command_timeout': 90
                })

            self.device = driver(
                hostname=host,
                username=username,
                password=password,
                optional_args=optional_args
            )

            print(f"napalm session connected - {driver_type}")

            # Open connection in a separate thread to avoid blocking
            await asyncio.to_thread(self.device.open)

            self._active = True
            self.send_message("connected", {"status": "success"})

            # Start monitoring after successful connection
            await self.collect_all_telemetry()

        except Exception as e:
            error_msg = f"Napalm connection failed: {str(e)}"
            print(error_msg)
            self.send_message("error", {"message": error_msg})
            if self.device:
                try:
                    await asyncio.to_thread(self.device.close)
                except Exception:
                    pass
                self.device = None
    async def collect_all_telemetry(self):
        """Collect and send all telemetry data in sequence"""
        try:
            # Get device info first in the main thread

            # Only start a new collector if one isn't already running
            if self.collector is None or not self.collector.isRunning():
                if self.collector is not None:
                    # Clean up any previous collector
                    self.collector.telemetry_ready.disconnect()
                    self.collector.error_signal.disconnect()
                    self.collector = None

                # Create and start new collector
                self.collector = TelemetryCollector(self.device)
                self.collector.telemetry_ready.connect(self._handle_telemetry_data)
                self.collector.error_signal.connect(self._handle_telemetry_error)
                self.collector.start()
            else:
                logger.debug("Telemetry collector already running")

        except Exception as e:
            error_msg = f"Error collecting telemetry: {str(e)}"
            logger.error(error_msg)
            self.send_message("error", {"message": error_msg})

    async def disconnect(self):
        """Disconnect from device"""
        self._active = False

        # Clean up collector if it exists
        if self.collector is not None:
            if self.collector.isRunning():
                self.collector.quit()
                self.collector.wait()
            self.collector.telemetry_ready.disconnect()
            self.collector.error_signal.disconnect()
            self.collector = None

        if self.device:
            try:
                await asyncio.to_thread(self.device.close)
            except Exception as e:
                logger.error(f"Error disconnecting: {e}")
            self.device = None
        self.send_message("disconnected", {"status": "success"})

    def _handle_telemetry_data(self, data):
        """Handle telemetry data from collector"""
        if self._active:  # Only process data if session is still active
            self.send_message("telemetry_update", data)

    def _handle_telemetry_error(self, error_msg):
        """Handle telemetry error from collector"""
        if self._active:  # Only process errors if session is still active
            logger.error(error_msg)
            self.send_message("error", {"message": error_msg})

class UISession(BaseSession):
    """Handles UI state and theme management"""

    def __init__(self, session_id):
        super().__init__(session_id)
        self.session_id = session_id
        self.current_theme = self.load_saved_theme()
        # Send initial theme to frontend immediately after initialization
        self.send_message("theme_changed", {"theme": self.current_theme})

    def load_saved_theme(self):
        """Load theme from persistent storage"""
        try:
            with open('theme_settings.json', 'r') as f:
                settings = json.load(f)
                return settings.get('theme', 'cyber')
        except (FileNotFoundError, json.JSONDecodeError):
            return 'cyber'  # Default theme

    def save_theme(self, theme_name):
        """Save theme to persistent storage"""
        try:
            with open('theme_settings.json', 'w') as f:
                json.dump({'theme': theme_name}, f)
        except Exception as e:
            logger.error(f"Error saving theme: {e}")

    async def handle_get_theme(self, payload):
        """Handle request for current theme"""
        self.send_message("theme_changed", {"theme": self.current_theme})

    async def handle_set_theme(self, payload):
        """Handle theme change request"""
        theme_name = payload.get('theme')
        if theme_name:
            self.current_theme = theme_name
            self.save_theme(theme_name)
            self.send_message("theme_changed", {"theme": theme_name})

    async def set_theme(self, theme_name):
        """Set theme and notify frontend"""
        self.current_theme = theme_name
        self.save_theme(theme_name)
        self.send_message("theme_changed", {"theme": theme_name})