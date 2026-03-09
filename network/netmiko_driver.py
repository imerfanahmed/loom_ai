"""
Loom CLI — Netmiko Network Driver
Real implementation using Netmiko for future use with actual devices.
Not used in the prototype — all interactions go through MockDriver.
"""

from __future__ import annotations

from datetime import datetime
from typing import List

from models import Device, CommandResult
from network.base import NetworkDriver


class NetmikoDriver(NetworkDriver):
    """
    Real Netmiko-based driver for pushing commands to Cisco devices.

    This driver is provided for future use when real routers / switches
    are available.  It is NOT instantiated in the current prototype.
    """

    def __init__(self, device: Device) -> None:
        super().__init__(device)
        self._connection = None

    def connect(self) -> None:
        from netmiko import ConnectHandler

        self._connection = ConnectHandler(
            device_type=self.device.device_type,
            host=self.device.ip,
            username=self.device.username,
            password=self.device.password,
        )
        self._connected = True

    def send_commands(self, commands: List[str]) -> CommandResult:
        if not self._connected or self._connection is None:
            self.connect()

        try:
            output = self._connection.send_config_set(commands)
            return CommandResult(
                device=self.device,
                commands=commands,
                output=output,
                success=True,
                timestamp=datetime.now(),
            )
        except Exception as exc:
            return CommandResult(
                device=self.device,
                commands=commands,
                output=str(exc),
                success=False,
                timestamp=datetime.now(),
            )

    def disconnect(self) -> None:
        if self._connection:
            self._connection.disconnect()
        self._connected = False
