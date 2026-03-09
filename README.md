# 🧵 Loom CLI — Cisco AI Agent

> A conversational CLI tool that translates plain English into Cisco IOS commands using **Gemini AI**, and pushes them to devices via **Netmiko**.

![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![Prototype](https://img.shields.io/badge/status-prototype-yellow)

---

## ✨ Features

- 🤖 **AI-Powered** — Describe what you want in English; Gemini generates the exact Cisco IOS commands
- 📡 **Netmiko Ready** — Mock driver for prototyping, real Netmiko driver ready for production
- 🎨 **Beautiful CLI** — Rich-powered terminal UI with syntax highlighting, panels, and spinners
- 📜 **Command History** — Track every push in the current session
- 🔒 **Offline Demo** — Works without an API key using built-in demo responses

---

## 🚀 Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure (optional)

```bash
cp .env.example .env
# Edit .env and add your Gemini API key
```

### 3. Run

```bash
python main.py
```

---

## 🗂 Project Structure

```
cisco_cli/
├── main.py              # Entry point
├── config/              # Settings & .env loading
├── models/              # Device & CommandResult dataclasses
├── ai/                  # Gemini API integration
├── network/             # Network drivers (Mock + Netmiko)
└── cli/                 # Rich interactive CLI
```

---

## 💬 Usage Examples

Once running, type natural-language requests:

```
🔧 What would you like to configure? Configure VLAN 10 on GigabitEthernet0/1

📋 Generated Commands:
  1 │ vlan 10
  2 │  name SALES
  3 │ interface GigabitEthernet0/1
  4 │  switchport mode access
  5 │  switchport access vlan 10
  6 │  no shutdown
  7 │ end

⚡ Push these commands to the device? [Y/n]: y
✅ Success — 7 command(s) pushed to Router-1
```

### Built-in commands

| Command   | Description              |
|-----------|--------------------------|
| `help`    | Show help & examples     |
| `devices` | Show active device info  |
| `history` | Show push history        |
| `clear`   | Clear the screen         |
| `exit`    | Quit Loom CLI            |

---

## 🔑 Environment Variables

| Variable        | Default             | Description                |
|-----------------|---------------------|----------------------------|
| `GEMINI_API_KEY` | *(none)*           | Google Gemini API key      |
| `GEMINI_MODEL`   | `gemini-2.0-flash` | Gemini model to use        |
| `LOG_LEVEL`      | `INFO`             | Logging verbosity          |

---

## 📌 Roadmap

- [ ] Connect to real Cisco devices via Netmiko
- [ ] Multi-device support and device inventory
- [ ] Command rollback / undo
- [ ] Configuration templates
- [ ] Session logging to file
