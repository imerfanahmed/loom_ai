#!/usr/bin/env python3
"""
Loom CLI — Entry Point
Wires together config, AI engine, mock driver, and the interactive CLI.

Usage:
    python main.py
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path so packages resolve correctly
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from config import settings
from models import Device
from ai import GeminiEngine
from network import NetmikoDriver
from cli import LoomCLI


def main() -> None:
    # 1. Build the default device from config
    device = Device.from_dict(settings.DEFAULT_DEVICE)

    # 2. Initialise the AI engine
    engine = GeminiEngine()

    # 3. Create the network driver
    driver = NetmikoDriver(device)

    # 4. Launch the CLI
    app = LoomCLI(engine=engine, driver=driver, device=device)
    app.run()


if __name__ == "__main__":
    main()
