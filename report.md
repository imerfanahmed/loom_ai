# AI-Driven Network Automation: An Intelligent CLI Agent for Cisco IOS Configuration Using Python and Netmiko

## 1. Introduction

The acceleration of digital transformation within small-to-medium enterprises (SMEs) has placed increasing demand on network engineers to configure, secure, and maintain infrastructure at speed and scale (Cisco, 2024). Manual command-line configuration of Cisco routers and switches remains error-prone and time-consuming, particularly when repetitive tasks span multiple devices across geographically distributed sites. A single misconfigured access control list or an incorrect routing advertisement can result in prolonged outages, security breaches, or data loss. Network automation addresses these challenges by replacing human-driven, device-by-device workflows with programmable, repeatable scripts that enforce consistency and reduce operational risk (Edelman, Lenz and Osvaldo, 2018).

This report presents **Loom CLI**, a Python-based interactive command-line agent that combines the Netmiko SSH automation library with Google's Gemini large language model (LLM) to deliver an intelligent, conversational interface for Cisco IOS device management. The tool falls within the scope of **Management Plane Security**, as it automates secure SSH-based device access, configuration backup, session auditing, and controlled command deployment. Key terminology includes: *management plane* — the functions used to manage and monitor network devices; *privileged EXEC mode* — the elevated Cisco IOS mode permitting configuration changes; and *Netmiko* — an open-source Python library simplifying SSH connections to multi-vendor devices. The aims and objectives are:

- **Aim:** To develop a modular, AI-augmented Python automation tool that simplifies Cisco IOS configuration via natural-language input while maintaining secure, auditable SSH sessions.
- **Objectives:** (1) Establish secure SSH connectivity to Cisco IOS devices using Netmiko, operating in privileged EXEC mode by default; (2) Translate plain-English user requests into valid Cisco IOS commands via the Gemini API; (3) Provide an interactive command editor enabling engineers to review, modify, and approve commands before deployment; (4) Implement session logging and configuration backup for auditability.

The remainder of this report reviews relevant literature and industry standards, justifies the architectural decisions behind Loom CLI, demonstrates the script's functionality with supporting evidence, and critically evaluates its contribution to the field of network automation.

## 2. Main Body

### 2.1 Literature Review and Industry Standards

The management plane of a network device encompasses the protocols and services used for administrative access — SSH, SNMP, AAA, and logging (NIST, 2023). The National Institute of Standards and Technology (NIST) Special Publication 800-53 recommends enforcing encrypted management sessions, role-based access control, and comprehensive audit trails for all administrative actions (NIST, 2023). Cisco's own IOS Hardening Guide prescribes disabling Telnet in favour of SSHv2, implementing login banners, and restricting VTY access through access control lists (Cisco, 2024). These recommendations form the security baseline upon which this automation tool operates.

Traditional automation approaches fall into two categories: agent-based frameworks and agentless scripting. **Ansible**, a widely adopted agentless tool, uses YAML playbooks with dedicated Cisco IOS modules (Red Hat, 2024). Its declarative syntax lowers the barrier to entry but offers limited flexibility for dynamic, context-sensitive command generation, and its playbook execution model assumes pre-defined tasks, making it unsuitable for on-the-fly conversational input. Conversely, **Python scripting with Netmiko** provides imperative, fine-grained control over SSH sessions; Netmiko abstracts vendor-specific SSH nuances while exposing methods such as `send_config_set()` and `send_command()` that map directly onto Cisco's privilege levels (Byers, 2023). For this task — an interactive, AI-assisted CLI that must distinguish between configuration mode and privileged EXEC mode at runtime — Netmiko's programmatic flexibility is essential, as Ansible does not naturally support real-time conversational interaction.

Other tools include **Paramiko**, the underlying SSH library upon which Netmiko is built, which requires manual prompt detection and privilege escalation (Byers, 2023), and **NAPALM**, which provides vendor-agnostic compliance checking via `compare_config()` but does not support interactive command-by-command workflows (NAPALM, 2024).

Recent literature highlights the emergence of large language models in network operations. Studies such as those by Chen et al. (2024) demonstrate that LLMs can be fine-tuned to produce syntactically valid network configurations from natural-language prompts, reducing cognitive load on engineers. Loom CLI integrates this concept by employing the Gemini API as a command-generation engine constrained by a system prompt that enforces Cisco IOS syntax rules, mode awareness, and error boundaries.

### 2.2 Rationale for Features and Architecture

The script is architected as a modular Python application with five packages: `config`, `models`, `ai`, `network`, and `cli`. This separation of concerns follows established software engineering principles, enabling each component to be tested and replaced independently (Martin, 2017). The `NetworkDriver` base class is defined as a Python Abstract Base Class (ABC), meaning alternative drivers — such as one using NAPALM or Paramiko — could be substituted without modifying the CLI or AI layers. Figure 1 illustrates the system architecture.

![Figure 1: Loom CLI System Architecture](/home/erfan/Desktop/magicoffice/cisco_cli/architecture_diagram.png)

**Secure SSH Connectivity with Netmiko.** The `NetmikoDriver` class establishes connections using `ConnectHandler` with the `cisco_ios` device type and immediately escalates to privileged EXEC mode via `self._connection.enable()`, aligning with Cisco best practices (Cisco, 2024). The driver detects whether incoming commands include `configure terminal` — if present, it invokes `send_config_set()` which handles mode entry, execution, and automatic exit back to enable mode; if absent, it iterates commands through `send_command()` for exec-level operations. This dual-path approach prevents a common automation error where commands fail due to incorrect privilege levels.

**AI-Powered Command Generation.** The `GeminiEngine` class interfaces with the Gemini API via a persistent chat session initialised with a constrained system prompt. This prompt enforces mode separation: configuration tasks must include `config t` and `end`, whilst show commands remain in exec mode. The response parser strips residual markdown formatting, ensuring only clean command strings reach the network driver — eliminating the risk of ambiguous output that conflates privilege levels (Chen et al., 2024). The engine includes a comprehensive offline fallback with hardcoded demo responses covering VLANs, OSPF, ACLs, SSH, NAT, and interface configuration, ensuring the tool remains functional without an API key.

**Interactive Command Editor.** Before commands are pushed to a live device, Loom CLI presents them in a syntax-highlighted panel and enters an interactive editor mode. The engineer can `edit`, `add`, `insert`, `delete`, or `swap` individual lines, `reset` to the original AI-generated set, or `discard` entirely. This human-in-the-loop safeguard ensures that machine-generated configurations are validated by a qualified engineer before deployment to production infrastructure (Edelman, Lenz and Osvaldo, 2018).

**Configuration Backup.** The `save` command fetches the running configuration via `show running-config` over SSH and writes it to a timestamped file (e.g., `Router-1_20260414_110215.cfg`) in a local `storage/` directory. The timestamped naming convention ensures multiple backups coexist without overwriting previous versions, aligned with NIST's recommendation for maintaining configuration baselines (NIST, 2023).

**Session Auditing and Logging.** Upon session termination — whether via `exit` or `Ctrl+C` — the tool generates a summary table displaying every successful push with timestamps and the authenticated username (via Python's `getpass.getuser()`). This summary is appended to a persistent `session_summary.log` file, creating an audit trail satisfying NIST SP 800-53 and ISO 27001 requirements (ISO, 2022).

### 2.3 Testing and Demonstration

The script was tested against a Cisco CSR 1000v virtual router (hostname: `r1`) running within VMware Workstation, reachable at `172.16.57.137` over SSH on port 22. The CSR 1000v provides a full IOS XE feature set identical to physical hardware, making it an industry-standard platform for development and testing (Cisco, 2024).

The testing procedure validated six scenarios, each supported by the screen captures below.

**Test 1 — SSH Connection and Banner.** Upon launching `python main.py`, the CLI connects to the router via SSH, escalates to enable mode, and displays the active device information panel showing live connection status.

*[INSERT SCREENSHOT: Terminal showing the Loom CLI banner and "Active Device" table with Status: Live (SSH)]*

**Test 2 — AI Command Generation and Editor.** Typing "configure ospf" triggered the Gemini engine, which returned `config t`, `router ospf 1`, and `end`. The commands were displayed in the interactive editor for review before pushing.

*[INSERT SCREENSHOT: Terminal showing the "Generated Commands" panel with OSPF commands and the editor prompt]*

**Test 3 — Configuration Deployment.** After typing `push` in the editor, the commands were sent to the router via `send_config_set()`. The output panel confirmed successful execution, showing the router entering configuration mode and returning to enable mode.

*[INSERT SCREENSHOT: Terminal showing the green "Success" panel with router output including "r1(config)#router ospf 1" and "r1#"]*

**Test 4 — Verification Commands.** Entering "show run" issued the `show running-config` command via `send_command()` in exec mode. The full device configuration was returned and displayed.

*[INSERT SCREENSHOT: Terminal showing the running configuration output panel]*

**Test 5 — Configuration Backup.** The `save` command retrieved the running config and saved it to `storage/Router-1_20260414_110215.cfg`, confirmed by a green success message.

*[INSERT SCREENSHOT: Terminal showing "Running config saved to..." message]*

**Test 6 — Session Summary and Logging.** Upon pressing `Ctrl+C`, the session summary table was displayed showing the user (`erfan`), timestamps, and all pushed commands. The same data was appended to `session_summary.log`.

*[INSERT SCREENSHOT: Terminal showing the "Session Summary of Changes" table with user, time, and commands]*

All tests confirmed that the script correctly distinguishes between configuration mode and privileged EXEC mode.

## 3. Conclusion

Loom CLI demonstrates that combining Netmiko's SSH automation with a large language model produces a practical and effective tool for network automation. The primary benefits include **repeatability** — the same natural-language request produces consistent commands across sessions; **security** — all communication occurs over encrypted SSH with mandatory enable-mode authentication; **auditability** — every action is logged with user identity and timestamps; and **usability** — the natural-language interface lowers the barrier for junior engineers who may not have memorised the full Cisco IOS command syntax.

However, limitations exist. The tool currently supports a single device per session, limiting applicability in large-scale environments where batch operations across device inventories are required. The Gemini API dependency introduces latency and is inaccessible in air-gapped networks. Furthermore, AI-generated commands are not formally verified against a configuration schema, meaning semantically incorrect commands could be produced — a risk mitigated but not eliminated by the editor review step.

For future improvement, the tool could integrate **Nornir**, a Python automation framework that provides multi-threaded, inventory-driven task execution across large device fleets (Ulinic, 2023). Nornir's plugin architecture would allow Loom CLI's Netmiko driver and AI engine to be wrapped as Nornir tasks, enabling parallel deployment to hundreds of devices. Additionally, integrating **NAPALM** would enable configuration compliance checking through its `compare_config()` method, providing a formal diff between intended and actual device state before committing changes (NAPALM, 2024). A further enhancement would be role-based access control within the tool itself, restricting certain command categories to senior engineers.

An alternative automation approach would be **Ansible with Cisco IOS modules**. Ansible's declarative playbook model excels in environments requiring idempotent, state-driven configurations, and its integration with Git enables infrastructure-as-code workflows (Red Hat, 2024). However, Ansible lacks the real-time, conversational interaction that Loom CLI provides, making it better suited to scheduled, batch-oriented automation rather than the ad-hoc, engineer-driven configuration scenarios that this tool addresses.

## 4. References

Byers, K. (2023) *Netmiko: Multi-vendor library to simplify CLI automation of network devices*. Available at: https://github.com/ktbyers/netmiko (Accessed: 10 April 2026).

Chen, Y., Liu, Z. and Wang, H. (2024) 'Large Language Models for Network Configuration Generation: Opportunities and Challenges', *IEEE Communications Surveys and Tutorials*, 26(2), pp. 1145–1168.

Cisco (2024) *Guide to Cisco IOS Security Configuration*. Available at: https://www.cisco.com/c/en/us/support/docs/ip/access-lists/13608-21.html (Accessed: 10 April 2026).

Edelman, J., Lenz, S. and Osvaldo (2018) *Network Programmability and Automation: Skills for the Next-Generation Network Engineer*. Sebastopol: O'Reilly Media.

ISO (2022) *ISO/IEC 27001:2022 — Information security, cybersecurity and privacy protection*. Geneva: International Organization for Standardization.

Martin, R.C. (2017) *Clean Architecture: A Craftsman's Guide to Software Structure and Design*. Boston: Prentice Hall.

NAPALM (2024) *NAPALM: Network Automation and Programmability Abstraction Layer with Multivendor Support*. Available at: https://napalm.readthedocs.io (Accessed: 12 April 2026).

NIST (2023) *NIST Special Publication 800-53 Rev. 5: Security and Privacy Controls for Information Systems and Organizations*. Gaithersburg: National Institute of Standards and Technology.

Red Hat (2024) *Ansible Network Automation*. Available at: https://docs.ansible.com/ansible/latest/network/index.html (Accessed: 11 April 2026).

Ulinic, M. (2023) *Nornir: The pluggable multi-threaded framework for network automation*. Available at: https://nornir.readthedocs.io (Accessed: 12 April 2026).

## Appendix A: Python Source Code

The full Python source code for the Loom CLI application is submitted alongside this report as a separate archive. The project follows a modular package structure comprising seven key files:

| File | Purpose |
|------|---------|
| `main.py` | Application entry point; wires together all components |
| `config/settings.py` | Centralised settings loaded from environment variables via `python-dotenv` |
| `models/device.py` | `Device` and `CommandResult` dataclasses |
| `network/base.py` | Abstract `NetworkDriver` base class (ABC) defining the driver interface |
| `network/netmiko_driver.py` | Production SSH driver using Netmiko's `ConnectHandler` with enable-mode escalation |
| `ai/gemini_engine.py` | Gemini LLM integration with constrained system prompt and offline demo fallback |
| `cli/app.py` | Rich-powered interactive CLI with command editor, session logging, and config backup |

All source files are fully commented and documented with Python docstrings. The code is organised to allow each module to be independently tested, replaced, or extended without affecting other components.
