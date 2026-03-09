"""
Loom CLI — Abstract Network Driver
Defines the interface that all network drivers must implement.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from models import Device, CommandResult


class NetworkDriver(ABC):
    """Base class for network device drivers."""

    def __init__(self, device: Device) -> None:
        self.device = device
        self._connected = False

    @property
    def connected(self) -> bool:
        return self._connected

    @abstractmethod
    def connect(self) -> None:
        """Establish a connection to the device."""
        ...

    @abstractmethod
    def send_commands(self, commands: List[str]) -> CommandResult:
        """
        Send a list of configuration commands to the device.

        Parameters
        ----------
        commands : list[str]
            Cisco IOS commands to push.

        Returns
        -------
        CommandResult
            Result of the push operation.
        """
        ...

    @abstractmethod
    def disconnect(self) -> None:
        """Close the connection to the device."""
        ...

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *_):
        self.disconnect()
