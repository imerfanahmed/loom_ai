"""
Loom CLI — Interactive CLI Application
Rich-powered conversational interface for Cisco device configuration.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from typing import List
import getpass

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from rich.prompt import Prompt, Confirm
from rich.markdown import Markdown
from rich import box

from ai import GeminiEngine
from network.base import NetworkDriver
from models import Device, CommandResult


# ── Banner ────────────────────────────────────────────────────────────────────

_BANNER = r"""
  ██╗      ██████╗  ██████╗ ███╗   ███╗
  ██║     ██╔═══██╗██╔═══██╗████╗ ████║
  ██║     ██║   ██║██║   ██║██╔████╔██║
  ██║     ██║   ██║██║   ██║██║╚██╔╝██║
  ███████╗╚██████╔╝╚██████╔╝██║ ╚═╝ ██║
  ╚══════╝ ╚═════╝  ╚═════╝ ╚═╝     ╚═╝
       C I S C O   C L I   A G E N T
"""


class LoomCLI:
    """Interactive CLI application for Loom — the Cisco AI agent."""

    def __init__(
        self,
        engine: GeminiEngine,
        driver: NetworkDriver,
        device: Device,
    ) -> None:
        self.console = Console()
        self.engine = engine
        self.driver = driver
        self.device = device
        self._history: List[dict] = []

    # ── Main loop ─────────────────────────────────────────────────────────

    def run(self) -> None:
        """Launch the interactive CLI session."""
        self._show_banner()
        self._show_device_info()
        self._show_help_hint()

        while True:
            try:
                user_input = Prompt.ask(
                    "\n[bold cyan]🔧 What would you like to configure?[/]"
                )
            except (KeyboardInterrupt, EOFError):
                self._exit()
                return

            stripped = user_input.strip().lower()

            if not stripped:
                continue
            if stripped in ("exit", "quit", "q"):
                self._exit()
                return
            if stripped == "help":
                self._show_help()
                continue
            if stripped == "devices":
                self._show_device_info()
                continue
            if stripped == "history":
                self._show_history()
                continue
            if stripped == "clear":
                self.console.clear()
                self._show_banner()
                continue
            if stripped in ("save", "backup"):
                self._save_config()
                continue

            # ── AI generates commands ─────────────────────────────────
            self._handle_request(user_input.strip())

    # ── Request handling ──────────────────────────────────────────────────

    def _save_config(self) -> None:
        """Fetch running config and save it to storage."""
        self.console.print("\n[dim]Connecting to device to fetch running configuration...[/]")
        with self.console.status(
            f"[bold cyan]📡 Retrieving from {self.device.hostname}…[/]",
            spinner="dots",
        ):
            config = self.driver.get_running_config()
            
        if config.startswith("Error"):
            self.console.print(f"[bold red]❌ {config}[/]")
            return
            
        # Create storage directory at project root
        project_root = Path(__file__).resolve().parent.parent
        storage_dir = project_root / "storage"
        storage_dir.mkdir(exist_ok=True)
        
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.device.hostname}_{timestamp}.cfg"
        file_path = storage_dir / filename
        
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(config)
            self.console.print(f"[bold green]✅ Running config saved to [white]{file_path}[/][/]\n")
        except Exception as e:
            self.console.print(f"[bold red]❌ Failed to save config: {e}[/]\n")

    def _handle_request(self, user_prompt: str) -> None:
        """Send prompt to AI, open editor, then optionally push."""

        with self.console.status(
            "[bold yellow]🤖 Thinking… generating Cisco commands…[/]",
            spinner="dots",
        ):
            commands = self.engine.generate_commands(
                user_prompt, self.device.hostname
            )

        # Check for errors
        if commands and commands[0].startswith("ERROR:"):
            self.console.print(
                Panel(
                    commands[0],
                    title="⚠️  Error",
                    border_style="red",
                    box=box.ROUNDED,
                )
            )
            return

        # Enter the interactive editor
        final_commands = self._command_editor(commands)

        if final_commands is None:
            self.console.print("[dim]↩ Commands discarded.[/]")
            return

        # Push commands via driver
        with self.console.status(
            f"[bold cyan]📡 Pushing to {self.device.hostname}…[/]",
            spinner="dots",
        ):
            result = self.driver.send_commands(final_commands)

        self._display_result(result)
        self._history.append(
            {"prompt": user_prompt, "commands": final_commands, "result": result}
        )

    # ── Mini Command Editor ───────────────────────────────────────────────

    def _render_commands(self, commands: List[str], title: str = "📋 Commands") -> None:
        """Render the command list as a numbered, syntax-highlighted panel."""
        cmd_text = "\n".join(commands)
        syntax = Syntax(
            cmd_text,
            "cisco",
            theme="monokai",
            line_numbers=True,
            padding=1,
        )
        self.console.print(
            Panel(
                syntax,
                title=title,
                subtitle=f"Target: {self.device.hostname} ({self.device.ip})",
                border_style="green",
                box=box.DOUBLE,
            )
        )

    def _show_editor_help(self) -> None:
        """Print the editor command reference."""
        help_table = Table(
            title="✏️  Editor Commands",
            box=box.SIMPLE_HEAVY,
            border_style="yellow",
            title_style="bold yellow",
            show_edge=False,
            pad_edge=False,
        )
        help_table.add_column("Command", style="bold cyan", no_wrap=True)
        help_table.add_column("Description", style="white")

        help_table.add_row("edit [N]",      "Edit line N")
        help_table.add_row("add",           "Append a new line at the end")
        help_table.add_row("insert [N]",    "Insert a new line before line N")
        help_table.add_row("del [N]",       "Delete line N")
        help_table.add_row("swap [N] [M]",  "Swap lines N and M")
        help_table.add_row("show",          "Redisplay the command list")
        help_table.add_row("reset",         "Restore original AI-generated commands")
        help_table.add_row("push",          "Accept & push commands to device")
        help_table.add_row("discard",       "Discard all and return to prompt")

        self.console.print(help_table)

    def _command_editor(self, original_commands: List[str]) -> List[str] | None:
        """
        Interactive mini editor for the generated command list.

        Returns the final command list to push, or None if discarded.
        """
        commands = list(original_commands)  # work on a copy

        self.console.print()
        self._render_commands(commands, "📋 Generated Commands")
        self.console.print(
            "\n[bold yellow]✏️  Editor mode[/] — "
            "modify commands before pushing. Type [bold]help[/] for commands.\n"
        )

        while True:
            try:
                raw = Prompt.ask("[bold yellow]  editor>[/]")
            except (KeyboardInterrupt, EOFError):
                return None

            parts = raw.strip().split()
            if not parts:
                continue

            cmd = parts[0].lower()

            # ── push ──────────────────────────────────────────────
            if cmd == "push":
                if not commands:
                    self.console.print("[red]  ✖ Nothing to push — list is empty.[/]")
                    continue
                return commands

            # ── discard ───────────────────────────────────────────
            if cmd in ("discard", "quit", "q"):
                return None

            # ── help ──────────────────────────────────────────────
            if cmd == "help":
                self._show_editor_help()
                continue

            # ── show ──────────────────────────────────────────────
            if cmd == "show":
                if commands:
                    self._render_commands(commands)
                else:
                    self.console.print("[dim]  (empty list)[/]")
                continue

            # ── reset ─────────────────────────────────────────────
            if cmd == "reset":
                commands = list(original_commands)
                self.console.print("[green]  ↺ Restored original commands.[/]")
                self._render_commands(commands)
                continue

            # ── add ───────────────────────────────────────────────
            if cmd == "add":
                new_line = Prompt.ask("[cyan]  new command[/]")
                if new_line.strip():
                    commands.append(new_line)
                    self.console.print(
                        f"[green]  ✔ Added line {len(commands)}:[/] "
                        f"[white]{new_line}[/]"
                    )
                continue

            # ── edit N ────────────────────────────────────────────
            if cmd == "edit":
                idx = self._parse_line_number(parts, commands)
                if idx is None:
                    continue
                self.console.print(
                    f"[dim]  Current line {idx + 1}:[/] "
                    f"[white]{commands[idx]}[/]"
                )
                new_line = Prompt.ask("[cyan]  replace with[/]")
                if new_line.strip():
                    commands[idx] = new_line
                    self.console.print(
                        f"[green]  ✔ Line {idx + 1} updated.[/]"
                    )
                continue

            # ── insert N ──────────────────────────────────────────
            if cmd == "insert":
                idx = self._parse_line_number(parts, commands)
                if idx is None:
                    continue
                new_line = Prompt.ask("[cyan]  new command[/]")
                if new_line.strip():
                    commands.insert(idx, new_line)
                    self.console.print(
                        f"[green]  ✔ Inserted at line {idx + 1}:[/] "
                        f"[white]{new_line}[/]"
                    )
                continue

            # ── del N ─────────────────────────────────────────────
            if cmd in ("del", "delete", "rm"):
                idx = self._parse_line_number(parts, commands)
                if idx is None:
                    continue
                removed = commands.pop(idx)
                self.console.print(
                    f"[red]  ✖ Deleted line {idx + 1}:[/] "
                    f"[dim]{removed}[/]"
                )
                continue

            # ── swap N M ──────────────────────────────────────────
            if cmd == "swap":
                if len(parts) < 3:
                    self.console.print(
                        "[red]  Usage: swap [N] [M][/]"
                    )
                    continue
                try:
                    a, b = int(parts[1]) - 1, int(parts[2]) - 1
                except ValueError:
                    self.console.print("[red]  ✖ Line numbers must be integers.[/]")
                    continue
                if not (0 <= a < len(commands) and 0 <= b < len(commands)):
                    self.console.print(
                        f"[red]  ✖ Line numbers must be 1–{len(commands)}.[/]"
                    )
                    continue
                commands[a], commands[b] = commands[b], commands[a]
                self.console.print(
                    f"[green]  ✔ Swapped lines {a + 1} and {b + 1}.[/]"
                )
                continue

            # ── unknown ───────────────────────────────────────────
            self.console.print(
                f"[red]  ✖ Unknown editor command:[/] [bold]{cmd}[/]  "
                "[dim](type [bold]help[/dim] for commands)[/]"
            )

    @staticmethod
    def _parse_line_number(parts: List[str], commands: List[str]) -> int | None:
        """Parse and validate a 1-based line number from command parts."""
        if len(parts) < 2:
            return None  # will print nothing — let caller handle
        try:
            n = int(parts[1])
        except ValueError:
            return None
        idx = n - 1
        if idx < 0 or idx >= len(commands):
            return None
        return idx

    # ── Display helpers ───────────────────────────────────────────────────

    def _show_banner(self) -> None:
        mode_label = (
            "[bold green]● LIVE[/] (Gemini API)"
            if self.engine.is_live
            else "[bold yellow]● DEMO[/] (offline fallback)"
        )
        self.console.print(
            Panel(
                Text.from_ansi(_BANNER)
                if "\033" in _BANNER
                else Text(_BANNER, style="bold cyan"),
                subtitle=mode_label,
                border_style="bright_blue",
                box=box.DOUBLE,
                padding=(0, 2),
            )
        )

    def _show_device_info(self) -> None:
        table = Table(
            title="🖥  Active Device",
            box=box.ROUNDED,
            border_style="bright_blue",
            title_style="bold",
        )
        table.add_column("Property", style="cyan", no_wrap=True)
        table.add_column("Value", style="white")

        table.add_row("Hostname", self.device.hostname)
        table.add_row("IP Address", self.device.ip)
        table.add_row("Type", self.device.device_type)
        table.add_row("Username", self.device.username)
        table.add_row("Status", "[bold green]Live (SSH)[/]")
        self.console.print(table)

    def _show_help_hint(self) -> None:
        self.console.print(
            "\n[dim]Type your configuration request in plain English, "
            "or use:[/] [bold]help[/] [dim]|[/] [bold]devices[/] [dim]|[/] "
            "[bold]history[/] [dim]|[/] [bold]save[/] [dim]|[/] [bold]clear[/] [dim]|[/] [bold]exit[/]\n"
        )

    def _show_help(self) -> None:
        help_md = """\
## Loom CLI Commands

| Command     | Description                                |
|-------------|--------------------------------------------|
| `help`      | Show this help message                     |
| `devices`   | Show active device information             |
| `history`   | Show command push history                  |
| `save`      | Save running config to storage directory   |
| `clear`     | Clear the screen                           |
| `exit`      | Quit Loom CLI                              |

**Anything else** is treated as a configuration request and sent to the AI engine.

### Example requests
- *"Configure VLAN 10 on interface Gi0/1"*
- *"Set up OSPF with area 0 on 10.0.0.0/24"*
- *"Create an ACL to block Telnet"*
- *"Enable SSH on the router"*
- *"Configure NAT overload on Gi0/1"*
"""
        self.console.print(Markdown(help_md))

    def _show_history(self) -> None:
        if not self._history:
            self.console.print("[dim]No commands have been pushed yet.[/]")
            return

        table = Table(
            title="📜 Command History",
            box=box.ROUNDED,
            border_style="bright_magenta",
            title_style="bold",
        )
        table.add_column("#", style="dim", width=4)
        table.add_column("Request", style="cyan")
        table.add_column("Commands", style="white", max_width=40)
        table.add_column("Status", style="green")
        table.add_column("Time", style="dim")

        for i, entry in enumerate(self._history, 1):
            r: CommandResult = entry["result"]
            cmds_preview = ", ".join(entry["commands"][:3])
            if len(entry["commands"]) > 3:
                cmds_preview += "…"
            table.add_row(
                str(i),
                entry["prompt"][:50],
                cmds_preview,
                "✅" if r.success else "❌",
                r.timestamp.strftime("%H:%M:%S"),
            )

        self.console.print(table)

    def _display_result(self, result: CommandResult) -> None:
        output_syntax = Syntax(
            result.output,
            "text",
            theme="monokai",
            line_numbers=False,
            padding=1,
        )
        border = "green" if result.success else "red"
        self.console.print(
            Panel(
                output_syntax,
                title=result.summary,
                border_style=border,
                box=box.ROUNDED,
            )
        )

    def _show_exit_summary(self) -> None:
        user = getpass.getuser()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        successful = [entry for entry in self._history if entry["result"].success]
        if not successful:
            self.console.print("\n[dim]No changes were pushed during this session.[/]")
            return

        table = Table(
            title="📝 Session Summary of Changes",
            caption=f"Executed by: {user} | Session closed at: {now}",
            box=box.ROUNDED,
            border_style="green",
            title_style="bold",
        )
        table.add_column("Time", style="dim", width=10)
        table.add_column("User", style="magenta")
        table.add_column("Prompt/Action", style="cyan")
        table.add_column("Commands Pushed", style="white")

        log_content = f"--- Session Summary: {now} ---\nUser: {user}\n"

        for entry in successful:
            cmds = "\n".join(entry["commands"])
            time_str = entry["result"].timestamp.strftime("%H:%M:%S")
            table.add_row(time_str, user, entry["prompt"], cmds)

            log_content += f"[{time_str}] Action: {entry['prompt']}\nCommands:\n{cmds}\n"

        log_content += "-" * 50 + "\n\n"

        self.console.print()
        self.console.print(table)

        # Append to log file
        try:
            log_path = Path(__file__).resolve().parent.parent / "session_summary.log"
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(log_content)
        except Exception as e:
            self.console.print(f"[dim red]Failed to write to session log: {e}[/]")

    def _exit(self) -> None:
        self._show_exit_summary()
        self.driver.disconnect()
        self.console.print(
            "\n[bold bright_blue]👋 Goodbye from Loom CLI![/]\n"
        )
