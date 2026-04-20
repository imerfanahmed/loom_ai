# AI-Driven Network Automation: An Intelligent CLI Agent for Cisco IOS Configuration Using Python and Netmiko

## 1. Introduction

The acceleration of digital transformation within small-to-medium enterprises (SMEs) has placed increasing demand on network engineers to configure, secure, and maintain infrastructure at speed and scale (Cisco, 2024). Manual command-line configuration of Cisco routers and switches remains error-prone and time-consuming, particularly when repetitive tasks span multiple devices across geographically distributed sites. A single misconfigured access control list or an incorrect routing advertisement can result in prolonged outages, security breaches, or data loss. Network automation addresses these challenges by replacing human-driven, device-by-device workflows with programmable, repeatable scripts that enforce consistency and reduce operational risk (Edelman, Lenz and Osvaldo, 2018).

A number of established tools already provide network automation capabilities — including Ansible, Terraform, Nornir, NAPALM, SaltStack, and Puppet — each operating across different layers of abstraction from low-level SSH libraries (Paramiko) to full infrastructure-as-code platforms (Red Hat, 2024; HashiCorp, 2024). However, these tools share a common limitation: they require the engineer to specify the exact device commands or declarative state definitions in advance, using domain-specific languages such as YAML, HCL, or Puppet DSL. None provides an interactive, conversational interface where an engineer can describe a configuration goal in plain English and receive ready-to-deploy Cisco IOS commands in real time.

This report presents **Loom CLI**, a Python-based interactive command-line agent that combines the Netmiko SSH automation library with Google's Gemini large language model (LLM) to deliver an intelligent, conversational interface for Cisco IOS device management. Unlike existing tools, Loom CLI occupies a unique position in the automation landscape by integrating natural-language processing with a human-in-the-loop command editor, allowing engineers to describe *what* they want — such as "harden SSH on this router" or "configure OSPF area 0" — while the AI generates the *how*. The tool falls within the scope of **Management Plane Security**, as it automates secure SSH-based device access, configuration backup, session auditing, and controlled command deployment. Key terminology includes: *management plane* — the functions used to manage and monitor network devices; *privileged EXEC mode* — the elevated Cisco IOS mode permitting configuration changes; and *Netmiko* — an open-source Python library simplifying SSH connections to multi-vendor devices. The aims and objectives are:

- **Aim:** To develop a modular, AI-augmented Python automation tool that simplifies Cisco IOS configuration via natural-language input while maintaining secure, auditable SSH sessions.
- **Objectives:** (1) Establish secure SSH connectivity to Cisco IOS devices using Netmiko, operating in privileged EXEC mode by default; (2) Translate plain-English user requests into valid Cisco IOS commands via the Gemini API; (3) Provide an interactive command editor enabling engineers to review, modify, and approve commands before deployment; (4) Implement session logging and configuration backup for auditability.

The remainder of this report reviews relevant literature, compares eight existing automation systems against Loom CLI's capabilities, justifies the architectural decisions behind the tool, provides a comprehensive feature matrix, demonstrates functionality with supporting evidence across ten real-world use cases spanning OSPF routing, security hardening, VLAN provisioning, NAT, ACLs, and compliance auditing, and critically evaluates its contribution to the field of network automation.

## 2. Main Body

### 2.1 Literature Review and Industry Standards

The management plane of a network device encompasses the protocols and services used for administrative access — SSH, SNMP, AAA, and logging (NIST, 2023). The National Institute of Standards and Technology (NIST) Special Publication 800-53 recommends enforcing encrypted management sessions, role-based access control, and comprehensive audit trails for all administrative actions (NIST, 2023). Cisco's own IOS Hardening Guide prescribes disabling Telnet in favour of SSHv2, implementing login banners, and restricting VTY access through access control lists (Cisco, 2024). These recommendations form the security baseline upon which this automation tool operates.

#### Existing Network Automation Tools

A range of open-source and commercial tools currently address network automation, each with different design philosophies, strengths, and limitations. The following discusses the most prominent solutions and evaluates their suitability for the interactive, AI-assisted workflow that Loom CLI aims to deliver.

**Paramiko** is a low-level Python library that implements the SSHv2 protocol, providing raw transport, channel, and SFTP capabilities (Paramiko, 2024). While it offers maximum flexibility, Paramiko requires the developer to manually handle prompt detection, privilege escalation (`enable`), error parsing, and timeout management for every vendor. Building an interactive Cisco CLI tool with Paramiko alone would involve significant boilerplate code to handle IOS-specific patterns such as `--More--` pagination, `%` error messages, and the distinction between user EXEC, privileged EXEC, and global configuration modes. Paramiko is best suited as a foundation library rather than a direct tool for network automation.

**Netmiko**, built on top of Paramiko, abstracts vendor-specific SSH nuances and provides high-level methods such as `send_command()`, `send_config_set()`, and `enable()` that map directly onto Cisco's privilege levels (Byers, 2023). Netmiko currently supports over 70 device types across vendors including Cisco, Juniper, Arista, and HP. Its imperative, session-oriented model makes it ideal for interactive, real-time command execution where the engineer needs immediate feedback. However, Netmiko operates at the device level — it does not natively provide inventory management, parallel execution, or configuration compliance features.

**Ansible** is a widely adopted agentless automation framework that uses YAML playbooks with dedicated Cisco IOS modules such as `ios_config`, `ios_command`, and `ios_facts` (Red Hat, 2024). Ansible's declarative syntax lowers the barrier to entry and its idempotent execution model ensures that re-running a playbook does not introduce duplicate configurations. However, Ansible's playbook model assumes pre-defined, static tasks — it does not natively support dynamic, context-sensitive command generation or real-time conversational interaction. An engineer must write the exact IOS commands into the playbook before execution, eliminating the possibility of on-the-fly, AI-assisted configuration.

**NAPALM** (Network Automation and Programmability Abstraction Layer with Multivendor support) provides a vendor-agnostic API for configuration management and operational data retrieval (NAPALM, 2024). Its standout feature is `compare_config()`, which performs a formal diff between the candidate and running configurations before committing changes. NAPALM supports a `merge` and `replace` workflow that aligns with infrastructure-as-code principles. However, NAPALM focuses on batch configuration deployment rather than interactive, command-by-command execution — it does not offer a conversational interface or real-time command editing, and its Cisco IOS support is limited compared to IOS-XE and NX-OS.

**Nornir** is a Python-native automation framework that provides multi-threaded, inventory-driven task execution across large device fleets (Ulinic, 2023). Unlike Ansible, Nornir uses pure Python rather than YAML, giving engineers programmatic control over task execution, filtering, and error handling. Nornir's plugin architecture supports both Netmiko and NAPALM as connection backends. Its strength lies in parallel execution across hundreds of devices, but it is designed for batch-oriented workflows rather than interactive, single-device sessions.

**Terraform** (HashiCorp, 2024) extends infrastructure-as-code to network devices through providers such as the Cisco IOS provider. Terraform excels at declarative state management — the engineer defines the desired end state, and Terraform calculates the necessary changes. However, Terraform's plan-apply workflow is designed for scheduled, version-controlled deployments rather than ad-hoc, real-time configuration changes. It also requires the engineer to learn HashiCorp Configuration Language (HCL) and does not support natural-language input.

**SaltStack** uses a master-minion architecture with support for network automation through proxy minions and the NAPALM integration module (Salt Project, 2024). SaltStack's event-driven reactor system is well-suited to automated remediation — for example, automatically reconfiguring a failover route when a link goes down. However, SaltStack requires a persistent infrastructure (Salt master, minion daemons), making it heavier to deploy than a standalone Python script. Its configuration is defined in YAML and Jinja2 templates, not natural language.

**Puppet** is an agent-based configuration management tool that uses its own declarative language (Puppet DSL) to define resource states (Puppet, 2024). The `cisco_ios` module enables management of Cisco devices through a Puppet agent running on a proxy. Puppet is well-suited to enforcing compliance at scale across large enterprise environments, but its agent-based architecture, steep learning curve, and lack of interactive capabilities make it unsuitable for the ad-hoc, engineer-driven use case that Loom CLI addresses.

#### Comparison of Existing Systems

The table below compares the key characteristics of each tool against the requirements of an interactive, AI-assisted network automation agent.

| Criteria | Paramiko | Netmiko | Ansible | NAPALM | Nornir | Terraform | SaltStack | Puppet | **Loom CLI** |
|----------|----------|---------|---------|--------|--------|-----------|-----------|--------|--------------|
| **Interactive CLI** | ⬜ No | ⬜ No | ⬜ No | ⬜ No | ⬜ No | ⬜ No | ⬜ No | ⬜ No | ✅ Yes |
| **Natural-Language Input** | ⬜ No | ⬜ No | ⬜ No | ⬜ No | ⬜ No | ⬜ No | ⬜ No | ⬜ No | ✅ Yes |
| **AI-Powered Command Gen.** | ⬜ No | ⬜ No | ⬜ No | ⬜ No | ⬜ No | ⬜ No | ⬜ No | ⬜ No | ✅ Yes |
| **Pre-Push Command Editing** | ⬜ No | ⬜ No | ⬜ No | ⬜ No | ⬜ No | ⬜ No | ⬜ No | ⬜ No | ✅ Yes |
| **Real-Time Execution** | ✅ Yes | ✅ Yes | ⬜ No | ⬜ No | ⬜ No | ⬜ No | ✅ Yes | ⬜ No | ✅ Yes |
| **Cisco IOS Support** | ✅ Yes | ✅ Yes | ✅ Yes | ⚠️ Partial | ✅ Yes | ⚠️ Partial | ✅ Yes | ✅ Yes | ✅ Yes |
| **Multi-Vendor Support** | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ⬜ Cisco Only |
| **Multi-Device Parallel** | ⬜ No | ⬜ No | ✅ Yes | ⬜ No | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ⬜ No |
| **Config Backup** | ⬜ Manual | ⬜ Manual | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| **Config Compliance/Diff** | ⬜ No | ⬜ No | ⬜ No | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ⬜ No |
| **Session Audit Logging** | ⬜ Manual | ⬜ Manual | ✅ Yes | ⬜ No | ⬜ Manual | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| **No Infrastructure Required** | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ⬜ No | ⬜ No | ⬜ No | ✅ Yes |
| **Learning Curve** | High | Low | Medium | Medium | Medium | High | High | High | Low |
| **Primary Use Case** | Low-level SSH | Device scripting | Batch playbooks | Compliance | Fleet tasks | IaC state mgmt | Event-driven | Enforcement | Interactive AI agent |

As the comparison demonstrates, no existing tool combines interactive CLI interaction, natural-language input, and AI-powered command generation with a human-in-the-loop editor. Tools such as Ansible, Nornir, and Terraform excel at batch, fleet-wide automation but assume the engineer has already determined the exact commands to deploy. Paramiko and Netmiko provide the programmatic SSH primitives but offer no interface or intelligence layer. Loom CLI occupies a unique position by combining Netmiko's proven SSH automation with Gemini's natural-language understanding, specifically targeting the ad-hoc, engineer-driven configuration workflow where the engineer describes *what* they want rather than specifying *how* to achieve it.

#### Large Language Models in Network Operations

Recent literature highlights the emergence of large language models in network operations. Studies such as those by Chen et al. (2024) demonstrate that LLMs can be fine-tuned to produce syntactically valid network configurations from natural-language prompts, reducing cognitive load on engineers. Loom CLI integrates this concept by employing the Gemini API as a command-generation engine constrained by a system prompt that enforces Cisco IOS syntax rules, mode awareness, and error boundaries. The key differentiator is the **human-in-the-loop editor** — unlike a fully autonomous system, Loom CLI ensures that every AI-generated command is reviewed and approved by a qualified engineer before reaching production infrastructure, addressing the trust and safety concerns raised in the literature around AI-generated network configurations.

### 2.2 Rationale for Features and Architecture

The script is architected as a modular Python application with five packages: `config`, `models`, `ai`, `network`, and `cli`. This separation of concerns follows established software engineering principles, enabling each component to be tested and replaced independently (Martin, 2017). The `NetworkDriver` base class is defined as a Python Abstract Base Class (ABC), meaning alternative drivers — such as one using NAPALM or Paramiko — could be substituted without modifying the CLI or AI layers. Figure 1 illustrates the system architecture.

*[INSERT SCREENSHOT: Figure 1 — Loom CLI System Architecture Diagram showing the five modular packages and their interactions]*

### 2.3 Feature Matrix

The table below provides a comprehensive overview of all features implemented in Loom CLI, with their current implementation status.

| # | Feature | Status | Description |
|---|---------|--------|-------------|
| 1 | Secure SSH Connectivity | ✅ Implemented | Establishes encrypted SSH sessions to Cisco IOS devices using Netmiko's `ConnectHandler` with `cisco_ios` device type |
| 2 | Enable Mode Escalation | ✅ Implemented | Automatically escalates to privileged EXEC mode via `self._connection.enable()` upon connection |
| 3 | AI Command Generation (Gemini) | ✅ Implemented | Translates plain-English requests into valid Cisco IOS commands via the Gemini 2.0 Flash API |
| 4 | Constrained System Prompt | ✅ Implemented | AI responses are bounded by a system prompt enforcing IOS syntax, mode awareness (`config t`/`end`), and error handling |
| 5 | Offline Demo Fallback | ✅ Implemented | Hardcoded demo responses for VLANs, OSPF, ACLs, SSH, NAT, interfaces, and show commands when no API key is available |
| 6 | Dual-Path Command Execution | ✅ Implemented | Automatically detects config vs. exec commands — uses `send_config_set()` for configuration blocks and `send_command()` for show/exec commands |
| 7 | Interactive Command Editor | ✅ Implemented | Pre-push review editor with `edit`, `add`, `insert`, `delete`, `swap`, `reset`, `show`, `push`, and `discard` operations |
| 8 | Syntax-Highlighted Output | ✅ Implemented | Rich-powered Monokai syntax highlighting for all command panels and device output |
| 9 | Configuration Backup | ✅ Implemented | Fetches `show running-config` and saves to timestamped file (e.g., `Router-1_20260414_110215.cfg`) in `storage/` directory |
| 10 | Session Audit Logging | ✅ Implemented | Generates session summary with user identity (`getpass.getuser()`), timestamps, and all pushed commands; persists to `session_summary.log` |
| 11 | Device Information Retrieval | ✅ Implemented | Parses `show version` output to extract hostname, hardware model, OS version, and uptime |
| 12 | Live/Demo Mode Indicator | ✅ Implemented | Visual banner indicator showing `● LIVE (Gemini API)` or `● DEMO (offline fallback)` status |
| 13 | Masked Password Input | ✅ Implemented | Secure credential entry with masked password and enable secret prompts during login |
| 14 | Rich CLI Interface | ✅ Implemented | Full Rich library integration with panels, tables, spinners, Markdown rendering, and colour-coded status indicators |
| 15 | Persistent Chat Context | ✅ Implemented | Gemini chat session maintains conversation history, allowing follow-up context-aware requests |
| 16 | Netmiko Session Logging | ✅ Implemented | Raw SSH session saved to `netmiko_session.log` for low-level debugging and protocol analysis |
| 17 | Graceful Error Handling | ✅ Implemented | Non-crashing error capture for SSH failures, API timeouts, and invalid commands with user-friendly error panels |
| 18 | Modular Driver Architecture | ✅ Implemented | Abstract Base Class (`NetworkDriver`) allows swappable drivers (Netmiko, Paramiko, NAPALM) without changing other layers |
| 19 | Environment Variable Config | ✅ Implemented | Settings loaded from `.env` via `python-dotenv` — supports `GEMINI_API_KEY`, `GEMINI_MODEL`, and `LOG_LEVEL` |
| 20 | Command History Tracking | ✅ Implemented | In-session history table displaying request, commands pushed, success/failure status, and timestamps |
| 21 | Multi-Device Support | ⬜ Planned | Batch operations across an inventory of devices using Nornir integration |
| 22 | Configuration Compliance | ⬜ Planned | NAPALM `compare_config()` for formal diff between intended and running configuration |
| 23 | Role-Based Access Control | ⬜ Planned | Restrict command categories by engineer seniority level within the CLI |
| 24 | Git-Based Config Versioning | ⬜ Planned | Automatic commit of configuration backups to a Git repository for version control |
| 25 | Scheduled Task Automation | ⬜ Planned | Cron-like scheduling for periodic configuration audits and compliance checks |

### 2.4 Core Feature Descriptions

**Secure SSH Connectivity with Netmiko.** The `NetmikoDriver` class establishes connections using `ConnectHandler` with the `cisco_ios` device type and immediately escalates to privileged EXEC mode via `self._connection.enable()`, aligning with Cisco best practices (Cisco, 2024). The driver detects whether incoming commands include `configure terminal` — if present, it invokes `send_config_set()` which handles mode entry, execution, and automatic exit back to enable mode; if absent, it iterates commands through `send_command()` for exec-level operations. This dual-path approach prevents a common automation error where commands fail due to incorrect privilege levels. The connection is configured with a 120-second timeout, a global delay factor of 2 for slower devices, and a read timeout override of 90 seconds to accommodate large configuration outputs.

**AI-Powered Command Generation.** The `GeminiEngine` class interfaces with the Gemini API via a persistent chat session initialised with a constrained system prompt. This prompt enforces mode separation: configuration tasks must include `config t` and `end`, whilst show commands remain in exec mode. The response parser strips residual markdown formatting, ensuring only clean command strings reach the network driver — eliminating the risk of ambiguous output that conflates privilege levels (Chen et al., 2024). The engine includes a comprehensive offline fallback with hardcoded demo responses covering VLANs, OSPF, ACLs, SSH, NAT, hostname/banner, interface configuration, show commands, and troubleshooting (ping/traceroute), ensuring the tool remains functional without an API key.

**Interactive Command Editor.** Before commands are pushed to a live device, Loom CLI presents them in a syntax-highlighted panel and enters an interactive editor mode. The engineer can `edit`, `add`, `insert`, `delete`, or `swap` individual lines, `reset` to the original AI-generated set, or `discard` entirely. This human-in-the-loop safeguard ensures that machine-generated configurations are validated by a qualified engineer before deployment to production infrastructure (Edelman, Lenz and Osvaldo, 2018).

**Device Information Retrieval.** Upon successful SSH connection, the tool automatically runs `show version` and parses the output using regular expressions to extract the device hostname, hardware model, IOS version, and system uptime. This information is displayed in a formatted table, providing the engineer with immediate context about the target device before any configuration changes are made.

**Configuration Backup.** The `save` command fetches the running configuration via `show running-config` over SSH and writes it to a timestamped file (e.g., `Router-1_20260414_110215.cfg`) in a local `storage/` directory. The timestamped naming convention ensures multiple backups coexist without overwriting previous versions, aligned with NIST's recommendation for maintaining configuration baselines (NIST, 2023).

**Session Auditing and Logging.** Upon session termination — whether via `exit` or `Ctrl+C` — the tool generates a summary table displaying every successful push with timestamps and the authenticated username (via Python's `getpass.getuser()`). This summary is appended to a persistent `session_summary.log` file, creating an audit trail satisfying NIST SP 800-53 and ISO 27001 requirements (ISO, 2022). Additionally, a raw Netmiko session log (`netmiko_session.log`) captures every byte transmitted and received over SSH, enabling low-level protocol debugging.

**Masked Credential Input.** The login sequence uses a custom `get_masked_input()` utility to securely prompt for the device password and enable secret. Characters are replaced with asterisks during typing, preventing shoulder-surfing in shared environments. If the user presses Enter without providing an enable secret (indicating a privilege-15 account), the tool defaults to using the login password as the enable secret.

### 2.5 Testing and Demonstration

The script was tested against a Cisco CSR 1000v virtual router (hostname: `r1`) running within VMware Workstation, reachable at `172.16.57.137` over SSH on port 22. The CSR 1000v provides a full IOS XE feature set identical to physical hardware, making it an industry-standard platform for development and testing (Cisco, 2024).

The testing procedure validated the following scenarios, each supported by the screen captures below.

---

**Test 1 — Login and SSH Connection**

Upon launching `python main.py`, the user is prompted for the device IP, username, password, and enable secret. The CLI establishes an SSH connection, escalates to enable mode, and displays a Device Information table with hostname, hardware, OS version, and uptime parsed from `show version`.

*[INSERT SCREENSHOT: Terminal showing the login prompts (IP, username, masked password, masked enable secret) followed by the "Connection successful" message]*

*[INSERT SCREENSHOT: Terminal showing the Device Information table with Hostname, Hardware, OS Version, and Uptime fields populated]*

---

**Test 2 — Banner and Active Device Display**

After successful login, the Loom CLI ASCII banner is displayed with the Gemini API status indicator (LIVE or DEMO), followed by the Active Device panel showing hostname, IP, device type, username, and live SSH status.

*[INSERT SCREENSHOT: Terminal showing the Loom CLI ASCII art banner with "● LIVE (Gemini API)" subtitle]*

*[INSERT SCREENSHOT: Terminal showing the "Active Device" table with hostname, IP, type, username, and "Live (SSH)" status]*

---

**Test 3 — AI Command Generation**

Entering a natural-language request such as "configure ospf area 0 on 10.0.0.0/24" triggers the Gemini engine. The AI returns syntactically valid Cisco IOS commands, which are displayed in a syntax-highlighted "Generated Commands" panel with line numbers and the target device name.

*[INSERT SCREENSHOT: Terminal showing the "🤖 Thinking… generating Cisco commands…" spinner]*

*[INSERT SCREENSHOT: Terminal showing the "Generated Commands" panel with OSPF configuration commands and the editor prompt]*

---

**Test 4 — Interactive Command Editor**

From the editor prompt, the engineer can modify AI-generated commands before pushing. This test demonstrates the `edit`, `add`, `delete`, and `show` operations within the editor, including modifying an OSPF network statement and adding a `network` command.

*[INSERT SCREENSHOT: Terminal showing the editor command reference table (help output) with all available operations]*

*[INSERT SCREENSHOT: Terminal showing an edit operation — modifying a line's content and receiving the "Line updated" confirmation]*

---

**Test 5 — Configuration Deployment (Push)**

After reviewing and editing, typing `push` sends the commands to the router via `send_config_set()`. The output panel displays the router's response showing successful configuration mode entry, command execution, and return to enable mode.

*[INSERT SCREENSHOT: Terminal showing the green "✅ Success" panel with router output including config mode transitions and command acknowledgements]*

---

**Test 6 — Show/Exec Command Execution**

Entering "show ip route" or "show me the running config" uses `send_command()` in exec mode (bypassing `config t`). The full device output is displayed in a formatted panel.

*[INSERT SCREENSHOT: Terminal showing the output of "show ip route" with the routing table displayed in a panel]*

*[INSERT SCREENSHOT: Terminal showing the output of "show running-config" with the full device configuration]*

---

**Test 7 — Configuration Backup (Save)**

The `save` command fetches the running configuration and writes it to a timestamped backup file.

*[INSERT SCREENSHOT: Terminal showing "📡 Retrieving from r1…" spinner]*

*[INSERT SCREENSHOT: Terminal showing "✅ Running config saved to storage/r1_20260414_110215.cfg" success message]*

---

**Test 8 — Command History**

The `history` command displays a table of all pushed commands during the current session, including the original request, commands sent, success/failure status, and timestamps.

*[INSERT SCREENSHOT: Terminal showing the "📜 Command History" table with multiple entries showing request, commands, status, and time columns]*

---

**Test 9 — Session Summary and Audit Log**

Upon pressing `Ctrl+C` or typing `exit`, the session summary is displayed with all successful pushes, user identity, timestamps, and commands. The same data is persisted to `session_summary.log`.

*[INSERT SCREENSHOT: Terminal showing the "📝 Session Summary of Changes" table with user, time, prompt/action, commands pushed, and output columns]*

*[INSERT SCREENSHOT: Contents of session_summary.log file showing the persisted audit trail]*

---

**Test 10 — Offline Demo Mode**

When no `GEMINI_API_KEY` is configured, the tool gracefully falls back to demo mode with hardcoded responses. The banner displays `● DEMO (offline fallback)` and commands are generated from the built-in response library.

*[INSERT SCREENSHOT: Terminal showing the Loom CLI banner with "● DEMO (offline fallback)" subtitle]*

*[INSERT SCREENSHOT: Terminal showing demo-generated commands for a VLAN configuration request]*

---

**Test 11 — Error Handling**

Testing with an unreachable device IP to verify graceful error handling. The tool displays a formatted error panel without crashing.

*[INSERT SCREENSHOT: Terminal showing the "Connection Failed:" error message with a descriptive SSH timeout error]*

---

All tests confirmed that the script correctly distinguishes between configuration mode and privileged EXEC mode, handles errors gracefully, and maintains a complete audit trail.

### 2.6 Real-World Use Case Scenarios

The following scenarios demonstrate how Loom CLI can be applied to common network engineering tasks across different operational domains. Each use case shows the natural-language input, the AI-generated commands, and the expected outcome.

---

#### Use Case 1: OSPF Routing Configuration

**Scenario:** A network engineer needs to enable OSPF on a branch office router, advertising the LAN subnet (192.168.10.0/24) and WAN link (10.0.0.0/30) into Area 0, with a custom router ID and passive interface on the LAN side.

**Natural-language input:**
> "Set up OSPF process 1 with router-id 1.1.1.1, advertise 192.168.10.0/24 and 10.0.0.0/30 into area 0, make GigabitEthernet0/0 passive"

**Expected AI-generated commands:**
```
config t
router ospf 1
 router-id 1.1.1.1
 network 192.168.10.0 0.0.0.255 area 0
 network 10.0.0.0 0.0.0.3 area 0
 passive-interface GigabitEthernet0/0
end
```

**Outcome:** The engineer reviews the commands in the editor, confirms the wildcard masks are correct, pushes to the device, then verifies with "show ip ospf neighbor" to confirm adjacency formation.

*[INSERT SCREENSHOT: Terminal showing the OSPF configuration commands in the editor panel]*

*[INSERT SCREENSHOT: Terminal showing the "show ip ospf neighbor" output confirming adjacency]*

---

#### Use Case 2: Security Hardening — SSH and VTY Line Lockdown

**Scenario:** A security audit has identified that the router still permits Telnet access and lacks SSH hardening. The engineer must disable Telnet, enforce SSHv2, configure a login banner, set VTY timeouts, and restrict management access to the IT subnet only.

**Natural-language input:**
> "Harden SSH on this router: set hostname to CORE-RTR-01, set domain name to corp.local, generate 2048-bit RSA keys, enable SSH version 2 only, create local user 'netadmin' with privilege 15, restrict VTY lines 0-4 to SSH only with a 5-minute timeout, add an access-class to only allow 10.10.10.0/24, and set a warning banner"

**Expected AI-generated commands:**
```
config t
hostname CORE-RTR-01
ip domain-name corp.local
crypto key generate rsa modulus 2048
ip ssh version 2
ip ssh time-out 60
ip ssh authentication-retries 3
username netadmin privilege 15 secret SecureP@ss123
line vty 0 4
 transport input ssh
 login local
 exec-timeout 5 0
 access-class 10 in
access-list 10 permit 10.10.10.0 0.0.0.255
access-list 10 deny any log
banner motd # WARNING: Authorized Access Only. All sessions are monitored and logged. #
no ip http server
no ip http secure-server
end
```

**Outcome:** The engineer uses the editor to change the username password to a company-standard credential, removes the HTTP server lines if already configured, and pushes. Session logging records the change for the compliance audit.

*[INSERT SCREENSHOT: Terminal showing the security hardening commands in the editor]*

*[INSERT SCREENSHOT: Terminal showing the "show ip ssh" output confirming SSHv2 is active]*

---

#### Use Case 3: VLAN Provisioning and Trunk Configuration

**Scenario:** A new department is being provisioned and requires VLAN 50 (HR), VLAN 60 (Finance), and VLAN 70 (Guest). The uplink port (GigabitEthernet0/1) must be configured as a trunk carrying all three VLANs, and access ports must be assigned accordingly.

**Natural-language input:**
> "Create VLANs 50, 60, and 70 named HR, Finance, and Guest. Set Gi0/2 as access port on VLAN 50, Gi0/3 as access on VLAN 60, Gi0/4 as access on VLAN 70. Make Gi0/1 a trunk carrying VLANs 50, 60, and 70 only"

**Expected AI-generated commands:**
```
config t
vlan 50
 name HR
vlan 60
 name Finance
vlan 70
 name Guest
interface GigabitEthernet0/2
 switchport mode access
 switchport access vlan 50
 no shutdown
interface GigabitEthernet0/3
 switchport mode access
 switchport access vlan 60
 no shutdown
interface GigabitEthernet0/4
 switchport mode access
 switchport access vlan 70
 no shutdown
interface GigabitEthernet0/1
 switchport trunk encapsulation dot1q
 switchport mode trunk
 switchport trunk allowed vlan 50,60,70
 no shutdown
end
```

**Outcome:** The engineer pushes the commands, then verifies with "show vlan brief" and "show interfaces trunk" to confirm proper VLAN assignments and trunk status.

*[INSERT SCREENSHOT: Terminal showing VLAN provisioning commands in the editor]*

*[INSERT SCREENSHOT: Terminal showing "show vlan brief" output with VLANs 50, 60, 70 listed]*

---

#### Use Case 4: NAT Overload (PAT) for Internet Access

**Scenario:** The internal LAN (192.168.1.0/24) requires internet access via PAT through the WAN interface. The engineer must configure inside/outside NAT interfaces, the overload rule, and a corresponding access list.

**Natural-language input:**
> "Configure NAT overload so that 192.168.1.0/24 on GigabitEthernet0/0 can access the internet through GigabitEthernet0/1 using PAT"

**Expected AI-generated commands:**
```
config t
interface GigabitEthernet0/0
 ip nat inside
interface GigabitEthernet0/1
 ip nat outside
access-list 1 permit 192.168.1.0 0.0.0.255
ip nat inside source list 1 interface GigabitEthernet0/1 overload
end
```

**Outcome:** The engineer verifies NAT translations with "show ip nat translations" and tests with a ping from an internal host.

*[INSERT SCREENSHOT: Terminal showing NAT configuration commands in the editor]*

*[INSERT SCREENSHOT: Terminal showing "show ip nat translations" output confirming active translations]*

---

#### Use Case 5: Extended ACL for Traffic Filtering

**Scenario:** The security team requires blocking all inbound Telnet (TCP 23) and FTP (TCP 20-21) traffic on the external interface while permitting all other traffic. The ACL must be applied inbound on the WAN-facing interface.

**Natural-language input:**
> "Create an extended ACL called WAN_INBOUND that blocks Telnet and FTP from any source, permits everything else, and apply it inbound on GigabitEthernet0/1"

**Expected AI-generated commands:**
```
config t
ip access-list extended WAN_INBOUND
 deny tcp any any eq 23 log
 deny tcp any any eq 21 log
 deny tcp any any eq 20 log
 permit ip any any
interface GigabitEthernet0/1
 ip access-group WAN_INBOUND in
end
```

**Outcome:** The engineer adds a `log` keyword to the deny statements via the editor for audit purposes, pushes, and verifies with "show access-lists".

*[INSERT SCREENSHOT: Terminal showing ACL commands in the editor with deny and permit statements]*

*[INSERT SCREENSHOT: Terminal showing "show access-lists" output confirming the ACL is applied]*

---

#### Use Case 6: Disaster Recovery — Configuration Backup and Restore

**Scenario:** Before a major firmware upgrade, the engineer must create a full configuration backup. If the upgrade fails, the backup can be referenced to manually restore the configuration.

**Step 1 — Pre-upgrade backup:**

The engineer uses the `save` command to back up the current running configuration.

*[INSERT SCREENSHOT: Terminal showing the "save" command executing and confirming the backup file path]*

**Step 2 — Verify backup contents:**

The engineer checks the saved file in the `storage/` directory to confirm it contains the complete running configuration.

*[INSERT SCREENSHOT: File explorer or terminal showing the contents of the backup .cfg file]*

**Step 3 — Post-failure reference:**

After a failed upgrade, the engineer opens Loom CLI, connects to the device, and manually reviews the saved backup to identify which configuration sections need to be restored.

*[INSERT SCREENSHOT: Terminal showing the session summary log with the backup operation recorded]*

---

#### Use Case 7: Troubleshooting — Network Connectivity Diagnostics

**Scenario:** Users report intermittent connectivity to a remote branch. The engineer uses Loom CLI to run a series of diagnostic commands without manually typing each one.

**Natural-language input:**
> "Show me the routing table, interface status, and OSPF neighbors"

**Expected AI-generated commands:**
```
show ip route
show ip interface brief
show ip ospf neighbor
```

**Outcome:** The tool executes each command via `send_command()` in exec mode (no `config t` involved) and displays the consolidated output. The engineer spots a missing OSPF adjacency and investigates further.

*[INSERT SCREENSHOT: Terminal showing the consolidated output of routing table, interface status, and OSPF neighbor information]*

---

#### Use Case 8: Interface Configuration and IP Addressing

**Scenario:** A new WAN link has been provisioned. The engineer must configure the physical interface with an IP address, description, and bring it up.

**Natural-language input:**
> "Configure GigabitEthernet0/2 with IP 203.0.113.1/30, description 'WAN Link to ISP', and enable the interface"

**Expected AI-generated commands:**
```
config t
interface GigabitEthernet0/2
 description WAN Link to ISP
 ip address 203.0.113.1 255.255.255.252
 no shutdown
end
```

**Outcome:** The engineer verifies the configuration with "show ip interface brief" confirming the interface is up/up with the correct IP address.

*[INSERT SCREENSHOT: Terminal showing the interface configuration commands in the editor]*

*[INSERT SCREENSHOT: Terminal showing "show ip interface brief" output with the new interface active]*

---

#### Use Case 9: Logging and SNMP Configuration for Monitoring

**Scenario:** The NOC team requires syslog and SNMP to be configured on all core routers for centralised monitoring. The engineer uses Loom CLI to generate the configuration.

**Natural-language input:**
> "Configure syslog to send logs to 10.10.10.100, set logging level to informational, enable SNMP v2c with community string 'N0CMonitor' read-only, and set the SNMP contact and location"

**Expected AI-generated commands:**
```
config t
logging host 10.10.10.100
logging trap informational
logging buffered 16384
snmp-server community N0CMonitor RO
snmp-server location London-DC-Rack12
snmp-server contact noc@company.com
end
```

**Outcome:** The engineer uses the editor to change the SNMP community string to match the company standard, pushes, and verifies with "show logging" and "show snmp".

*[INSERT SCREENSHOT: Terminal showing the logging and SNMP commands in the editor]*

---

#### Use Case 10: Compliance Audit — Verifying Security Baselines

**Scenario:** Before a quarterly compliance review, the engineer must verify that key security controls are in place: SSH is the only transport on VTY lines, Telnet is disabled, a banner is configured, and password encryption is enabled.

**Natural-language input sequence:**

1. "Show the running config for VTY lines"
2. "Show the banner configuration"
3. "Show if service password-encryption is enabled"

The engineer executes each verification command through Loom CLI, and the session summary log provides a timestamped audit record of every command executed, which can be submitted as evidence for the compliance review.

*[INSERT SCREENSHOT: Terminal showing the running config section for VTY lines]*

*[INSERT SCREENSHOT: Terminal showing the session summary used as an audit evidence trail]*

---

## 3. Conclusion

Loom CLI demonstrates that combining Netmiko's SSH automation with a large language model produces a practical and effective tool for network automation. The primary benefits include **repeatability** — the same natural-language request produces consistent commands across sessions; **security** — all communication occurs over encrypted SSH with mandatory enable-mode authentication; **auditability** — every action is logged with user identity and timestamps; and **usability** — the natural-language interface lowers the barrier for junior engineers who may not have memorised the full Cisco IOS command syntax.

The feature matrix in Section 2.3 confirms that twenty core features have been implemented, covering connectivity, AI integration, command editing, backup, logging, and error handling. The ten real-world use cases demonstrate the tool's versatility across routing (OSPF), security hardening (SSH, ACLs), switching (VLANs), NAT, monitoring (SNMP/syslog), and troubleshooting, validating its applicability to the daily workflow of a network engineer.

However, limitations exist. The tool currently supports a single device per session, limiting applicability in large-scale environments where batch operations across device inventories are required. The Gemini API dependency introduces latency and is inaccessible in air-gapped networks. Furthermore, AI-generated commands are not formally verified against a configuration schema, meaning semantically incorrect commands could be produced — a risk mitigated but not eliminated by the editor review step.

For future improvement, the tool could integrate **Nornir**, a Python automation framework that provides multi-threaded, inventory-driven task execution across large device fleets (Ulinic, 2023). Nornir's plugin architecture would allow Loom CLI's Netmiko driver and AI engine to be wrapped as Nornir tasks, enabling parallel deployment to hundreds of devices. Additionally, integrating **NAPALM** would enable configuration compliance checking through its `compare_config()` method, providing a formal diff between intended and actual device state before committing changes (NAPALM, 2024). A further enhancement would be role-based access control within the tool itself, restricting certain command categories to senior engineers.

An alternative automation approach would be **Ansible with Cisco IOS modules**. Ansible's declarative playbook model excels in environments requiring idempotent, state-driven configurations, and its integration with Git enables infrastructure-as-code workflows (Red Hat, 2024). However, Ansible lacks the real-time, conversational interaction that Loom CLI provides, making it better suited to scheduled, batch-oriented automation rather than the ad-hoc, engineer-driven configuration scenarios that this tool addresses.

## 4. References

Byers, K. (2023) *Netmiko: Multi-vendor library to simplify CLI automation of network devices*. Available at: https://github.com/ktbyers/netmiko (Accessed: 10 April 2026).

Chen, Y., Liu, Z. and Wang, H. (2024) 'Large Language Models for Network Configuration Generation: Opportunities and Challenges', *IEEE Communications Surveys and Tutorials*, 26(2), pp. 1145–1168.

Cisco (2024) *Guide to Cisco IOS Security Configuration*. Available at: https://www.cisco.com/c/en/us/support/docs/ip/access-lists/13608-21.html (Accessed: 10 April 2026).

Edelman, J., Lenz, S. and Osvaldo (2018) *Network Programmability and Automation: Skills for the Next-Generation Network Engineer*. Sebastopol: O'Reilly Media.

HashiCorp (2024) *Terraform: Infrastructure as Code*. Available at: https://www.terraform.io (Accessed: 14 April 2026).

ISO (2022) *ISO/IEC 27001:2022 — Information security, cybersecurity and privacy protection*. Geneva: International Organization for Standardization.

Martin, R.C. (2017) *Clean Architecture: A Craftsman's Guide to Software Structure and Design*. Boston: Prentice Hall.

NAPALM (2024) *NAPALM: Network Automation and Programmability Abstraction Layer with Multivendor Support*. Available at: https://napalm.readthedocs.io (Accessed: 12 April 2026).

NIST (2023) *NIST Special Publication 800-53 Rev. 5: Security and Privacy Controls for Information Systems and Organizations*. Gaithersburg: National Institute of Standards and Technology.

Paramiko (2024) *Paramiko: A Python implementation of SSHv2*. Available at: https://www.paramiko.org (Accessed: 14 April 2026).

Puppet (2024) *Puppet: Infrastructure automation and compliance*. Available at: https://www.puppet.com (Accessed: 14 April 2026).

Red Hat (2024) *Ansible Network Automation*. Available at: https://docs.ansible.com/ansible/latest/network/index.html (Accessed: 11 April 2026).

Salt Project (2024) *SaltStack: Event-driven infrastructure automation*. Available at: https://saltproject.io (Accessed: 14 April 2026).

Ulinic, M. (2023) *Nornir: The pluggable multi-threaded framework for network automation*. Available at: https://nornir.readthedocs.io (Accessed: 12 April 2026).

## Appendix A: Python Source Code

The full Python source code for the Loom CLI application is submitted alongside this report as a separate archive. The project follows a modular package structure comprising eight key files:

| File | Purpose |
|------|---------|
| `main.py` | Application entry point; wires together all components, handles login sequence and device info retrieval |
| `config/settings.py` | Centralised settings loaded from environment variables via `python-dotenv` |
| `models/device.py` | `Device` and `CommandResult` dataclasses with typed fields and summary properties |
| `network/base.py` | Abstract `NetworkDriver` base class (ABC) defining the driver interface with context manager support |
| `network/netmiko_driver.py` | Production SSH driver using Netmiko's `ConnectHandler` with enable-mode escalation and device info parsing |
| `ai/gemini_engine.py` | Gemini LLM integration with constrained system prompt, response parsing, and offline demo fallback |
| `cli/app.py` | Rich-powered interactive CLI with command editor, session logging, history tracking, and config backup |
| `cli/utils.py` | Utility functions including masked password input (`get_masked_input()`) |

All source files are fully commented and documented with Python docstrings. The code is organised to allow each module to be independently tested, replaced, or extended without affecting other components.
