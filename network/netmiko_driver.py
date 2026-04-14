"""
Loom CLI — Netmiko Network Driver
Real implementation using Netmiko for future use with actual devices.
Production SSH driver using Netmiko.
"""

from __future__ import annotations

from datetime import datetime
from typing import List

from models import Device, CommandResult
from network.base import NetworkDriver


class NetmikoDriver(NetworkDriver):
    """
    Real Netmiko-based driver for pushing commands to Cisco devices.
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
            secret=self.device.password,
        )
        self._connection.enable()
        self._connected = True

    def send_commands(self, commands: List[str]) -> CommandResult:
        if not self._connected or self._connection is None:
            self.connect()

        try:
            # Check if this is a configuration block
            has_config_start = any(cmd.strip() in ("config t", "configure terminal") for cmd in commands)
            
            if has_config_start:
                # Filter out the explicit mode entry/exit commands since send_config_set handles it automatically
                config_cmds = [cmd for cmd in commands if cmd.strip() not in ("config t", "configure terminal", "end", "exit")]
                output = self._connection.send_config_set(config_cmds)
            else:
                # Execute exec mode commands sequentially
                outputs = []
                for cmd in commands:
                    out = self._connection.send_command(cmd)
                    outputs.append(f"{self._connection.find_prompt()}{cmd}\n{out}")
                output = "\n".join(outputs)
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

    def get_running_config(self) -> str:
        if not self._connected or self._connection is None:
            self.connect()

        try:
            return self._connection.send_command("show running-config")
        except Exception as exc:
            return f"Error Retrieving Configuration: {exc}"
