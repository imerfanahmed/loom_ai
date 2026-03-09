"""
Loom CLI — Gemini AI Engine
Generates Cisco IOS commands from natural-language descriptions using the
Google Gemini API (google.genai SDK).  Falls back to a demo response when
no API key is set.
"""

from __future__ import annotations

import re
from typing import List

from config import settings


# ── System prompt — accepts ALL Cisco IOS interactions ──────────────────────
_SYSTEM_PROMPT = """\
You are a Cisco IOS command-line expert.  The user will describe what they
want to do on a Cisco router or switch — this can be ANYTHING related to
Cisco networking, including but not limited to:

- Configuration commands (interfaces, routing, ACLs, VLANs, NAT, etc.)
- Show commands (show ip route, show interfaces, show running-config, etc.)
- Troubleshooting commands (ping, traceroute, debug, etc.)
- Verification commands (show ospf neighbors, show vlan brief, etc.)
- Device management (hostname, banners, users, SSH, etc.)
- Any other valid Cisco IOS command

Respond with ONLY the exact Cisco IOS commands needed — one command per line.
Do NOT include any explanation, markdown, code fences, comments, or extra text.

Rules:
- If the user asks for a CONFIGURATION task, provide config commands starting
  from global configuration mode (user is in `configure terminal`).
  End with `end` to return to privileged EXEC mode.
- If the user asks to SEE or SHOW something, provide the appropriate `show`
  command(s) from privileged EXEC mode.  Do NOT wrap these in config mode.
- If the user asks to troubleshoot, provide appropriate exec-level commands
  like `ping`, `traceroute`, `debug`, etc.
- If the request is ambiguous, make reasonable assumptions and use common defaults.
- ONLY respond with "ERROR: Not a networking request." if the request has
  absolutely nothing to do with networking (e.g. "write me a poem").
"""

# ── Hardcoded demos for offline / no-API-key mode ──────────────────────────
_DEMO_COMMANDS = {
    "default": [
        "interface GigabitEthernet0/1",
        " description Configured by Loom CLI",
        " ip address 10.0.0.1 255.255.255.0",
        " no shutdown",
        "end",
    ],
}


class GeminiEngine:
    """Interfaces with Google Gemini to generate Cisco IOS commands."""

    def __init__(self) -> None:
        self._client = None
        self._chat = None
        self._init_error: str = ""

        if settings.has_api_key:
            try:
                from google import genai

                self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
                self._chat = self._client.chats.create(
                    model=settings.GEMINI_MODEL,
                    config={"system_instruction": _SYSTEM_PROMPT},
                )
            except Exception as exc:
                self._client = None
                self._init_error = str(exc)

    # ── Public API ────────────────────────────────────────────────────────

    @property
    def is_live(self) -> bool:
        """True when connected to the real Gemini API."""
        return self._client is not None

    def generate_commands(
        self,
        user_prompt: str,
        device_hostname: str = "Router",
    ) -> List[str]:
        """
        Turn a plain-English request into a list of Cisco IOS commands.

        Returns
        -------
        list[str]
            Clean list of IOS commands, one per entry.
        """
        if not self.is_live:
            return self._demo_response(user_prompt)

        try:
            context = (
                f"Target device hostname: {device_hostname}\n"
                f"User request: {user_prompt}"
            )
            response = self._chat.send_message(context)
            return self._parse_response(response.text)
        except Exception as exc:
            return [f"ERROR: Gemini API call failed — {exc}"]

    # ── Internals ─────────────────────────────────────────────────────────

    @staticmethod
    def _parse_response(raw: str) -> List[str]:
        """Strip markdown fences and blank lines, return clean command list."""
        cleaned = re.sub(r"```(?:cisco|ios|text)?\n?", "", raw)
        cleaned = cleaned.replace("```", "")
        lines = [line.rstrip() for line in cleaned.strip().splitlines()]
        return [l for l in lines if l]

    @staticmethod
    def _demo_response(user_prompt: str) -> List[str]:
        """Return canned commands for demo / offline mode."""
        prompt_lower = user_prompt.lower()

        # ── Show commands ─────────────────────────────────────────────
        if "show" in prompt_lower or "info" in prompt_lower:
            if "route" in prompt_lower or "routing" in prompt_lower:
                return ["show ip route"]
            if "interface" in prompt_lower or "brief" in prompt_lower:
                return ["show ip interface brief"]
            if "run" in prompt_lower or "config" in prompt_lower:
                return ["show running-config"]
            if "vlan" in prompt_lower:
                return ["show vlan brief"]
            if "ospf" in prompt_lower:
                return ["show ip ospf neighbor"]
            if "arp" in prompt_lower:
                return ["show arp"]
            if "mac" in prompt_lower:
                return ["show mac address-table"]
            if "version" in prompt_lower:
                return ["show version"]
            # generic "show me info" / "get info"
            return [
                "show version",
                "show ip interface brief",
                "show ip route",
            ]

        # ── Troubleshooting ───────────────────────────────────────────
        if "ping" in prompt_lower:
            return ["ping 8.8.8.8"]
        if "trace" in prompt_lower:
            return ["traceroute 8.8.8.8"]

        # ── Configuration: VLANs ──────────────────────────────────────
        if "vlan" in prompt_lower:
            return [
                "vlan 10",
                " name SALES",
                "interface GigabitEthernet0/1",
                " switchport mode access",
                " switchport access vlan 10",
                " no shutdown",
                "end",
            ]

        # ── Configuration: OSPF / routing ─────────────────────────────
        if "ospf" in prompt_lower or "routing" in prompt_lower:
            return [
                "router ospf 1",
                " network 10.0.0.0 0.0.0.255 area 0",
                " network 192.168.1.0 0.0.0.255 area 0",
                "end",
            ]

        # ── Configuration: ACL ────────────────────────────────────────
        if "acl" in prompt_lower or "access-list" in prompt_lower:
            return [
                "ip access-list extended BLOCK_TELNET",
                " deny tcp any any eq 23",
                " permit ip any any",
                "interface GigabitEthernet0/1",
                " ip access-group BLOCK_TELNET in",
                "end",
            ]

        # ── Configuration: SSH ────────────────────────────────────────
        if "ssh" in prompt_lower:
            return [
                "hostname Router-1",
                "ip domain-name loom.local",
                "crypto key generate rsa modulus 2048",
                "ip ssh version 2",
                "line vty 0 4",
                " transport input ssh",
                " login local",
                "username admin privilege 15 secret Cisco123!",
                "end",
            ]

        # ── Configuration: NAT ────────────────────────────────────────
        if "nat" in prompt_lower:
            return [
                "interface GigabitEthernet0/0",
                " ip nat inside",
                "interface GigabitEthernet0/1",
                " ip nat outside",
                "ip nat inside source list 1 interface GigabitEthernet0/1 overload",
                "access-list 1 permit 192.168.1.0 0.0.0.255",
                "end",
            ]

        # ── Configuration: Hostname / banner ──────────────────────────
        if "hostname" in prompt_lower or "banner" in prompt_lower:
            return [
                "hostname Router-1",
                "banner motd # Authorized Access Only #",
                "end",
            ]

        # ── Configuration: Interface ──────────────────────────────────
        if "interface" in prompt_lower or "ip address" in prompt_lower:
            return _DEMO_COMMANDS["default"]

        # ── Fallback ──────────────────────────────────────────────────
        return _DEMO_COMMANDS["default"]
