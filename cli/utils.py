"""
Loom CLI — Utilities
General helper functions for CLI interaction.
"""

import sys
import tty
import termios
from rich.console import Console

console = Console()

def get_masked_input(prompt: str) -> str:
    """
    Prompts the user for input while masking the typed characters with asterisks.
    Specifically designed for Linux/Unix environments.
    """
    sys.stdout.write(prompt)
    sys.stdout.flush()
    
    password = ""
    while True:
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            # Read 1 character
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        
        if ch == "\r" or ch == "\n":
            sys.stdout.write("\n")
            sys.stdout.flush()
            break
        elif ch == "\x7f":  # Backspace
            if len(password) > 0:
                password = password[:-1]
                sys.stdout.write("\b \b")
                sys.stdout.flush()
        elif ch == "\x03":  # Ctrl+C
            sys.stdout.write("\n")
            raise KeyboardInterrupt
        else:
            password += ch
            sys.stdout.write("*")
            sys.stdout.flush()
            
    return password
