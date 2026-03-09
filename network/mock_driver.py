"""
Loom CLI — Mock Network Driver
Simulates pushing commands to a Cisco device without any real connection.
Used for prototyping and demonstrations.
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import List

from models import Device, CommandResult
from network.base import NetworkDriver


class MockDriver(NetworkDriver):
    """Simulates a Cisco IOS SSH session for demo purposes."""

    def __init__(self, device: Device) -> None:
        super().__init__(device)
        self._log: List[CommandResult] = []

    # ── Connection lifecycle ──────────────────────────────────────────────

    def connect(self) -> None:
        time.sleep(0.3)  # simulate handshake
        self._connected = True

    def disconnect(self) -> None:
        self._connected = False

    # ── Command execution ─────────────────────────────────────────────────

    def send_commands(self, commands: List[str]) -> CommandResult:
        if not self._connected:
            self.connect()

        output_lines: List[str] = []
        prompt = f"{self.device.hostname}#"
        config_prompt = f"{self.device.hostname}(config)#"

        in_config = False

        for cmd in commands:
            time.sleep(0.08)  # simulate per-command latency

            stripped = cmd.strip()

            if stripped.lower() == "configure terminal":
                in_config = True
                output_lines.append(f"{prompt} {stripped}")
                output_lines.append("Enter configuration commands, one per line. End with CNTL/Z.")
                continue

            if stripped.lower() == "end":
                in_config = False
                output_lines.append(f"{config_prompt} {stripped}")
                output_lines.append(prompt)
                continue

            # Sub-mode prompts
            current_prompt = config_prompt if in_config else prompt

            if stripped.startswith("interface "):
                iface = stripped.split(" ", 1)[1]
                current_prompt = f"{self.device.hostname}(config-if:{iface})#"
                in_config = True
            elif stripped.startswith("router "):
                proto = stripped.split(" ", 1)[1]
                current_prompt = f"{self.device.hostname}(config-router:{proto})#"
                in_config = True
            elif stripped.startswith("vlan "):
                vid = stripped.split(" ", 1)[1]
                current_prompt = f"{self.device.hostname}(config-vlan:{vid})#"
                in_config = True
            elif stripped.startswith("ip access-list"):
                acl_name = stripped.rsplit(" ", 1)[-1]
                current_prompt = f"{self.device.hostname}(config-ext-nacl:{acl_name})#"
                in_config = True
            elif stripped.startswith("line "):
                line = stripped.split(" ", 1)[1]
                current_prompt = f"{self.device.hostname}(config-line:{line})#"
                in_config = True

            output_lines.append(f"{current_prompt} {stripped}")

        output = "\n".join(output_lines)
        result = CommandResult(
            device=self.device,
            commands=commands,
            output=output,
            success=True,
            timestamp=datetime.now(),
        )
        self._log.append(result)
        return result

    # ── History ───────────────────────────────────────────────────────────

    @property
    def history(self) -> List[CommandResult]:
        return list(self._log)
