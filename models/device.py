"""
Loom CLI — Data Models
Dataclasses for network devices and command execution results.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List


@dataclass
class Device:
    """Represents a Cisco network device."""

    hostname: str
    ip: str
    device_type: str = "cisco_ios"
    username: str = "admin"
    password: str = "admin123"
    secret: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> "Device":
        return cls(**data)

    def __str__(self) -> str:
        return f"{self.hostname} ({self.ip}) [{self.device_type}]"


@dataclass
class CommandResult:
    """Result of a command push to a device."""

    device: Device
    commands: List[str] = field(default_factory=list)
    output: str = ""
    success: bool = True
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def summary(self) -> str:
        status = "✅ Success" if self.success else "❌ Failed"
        return (
            f"{status} — {len(self.commands)} command(s) "
            f"pushed to {self.device.hostname} at {self.timestamp:%H:%M:%S}"
        )
