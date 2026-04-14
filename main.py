import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

# Ensure project root is on sys.path so packages resolve correctly
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from config import settings
from models import Device
from ai import GeminiEngine
from network import NetmikoDriver
from cli import LoomCLI
from cli.utils import get_masked_input

console = Console()

def main() -> None:
    console.print(Panel.fit(
        "[bold cyan]Loom CLI — Network Automation Engine[/bold cyan]\n"
        "[dim]Initializing interactive login sequence...[/dim]",
        border_style="cyan"
    ))

    try:
        # 1. Prompt for credentials
        ip = input("Enter Cisco Device IP: ").strip()
        if not ip:
            console.print("[red]Error: IP address is required.[/red]")
            return

        username = input("Enter Username: ").strip()
        if not username:
            username = "admin" # Default

        password = get_masked_input(f"Enter Password for {username}: ")

        # 2. Build the device model
        device = Device(
            hostname="Cisco-Device", # Placeholder hostname until connected
            ip=ip,
            username=username,
            password=password
        )

        # 3. Initialise the AI engine
        engine = GeminiEngine()

        # 4. Create the network driver
        driver = NetmikoDriver(device)

        # 5. Verify connection
        console.print(f"[yellow]Attempting to connect to {ip}...[/yellow]")
        driver.connect()
        console.print("[green]✓ Connection successful![/green]")

        # 6. Launch the CLI
        app = LoomCLI(engine=engine, driver=driver, device=device)
        app.run()

    except KeyboardInterrupt:
        console.print("\n[yellow]Exiting Loom CLI...[/yellow]")
    except Exception as e:
        console.print(f"\n[bold red]Connection Failed:[/bold red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
