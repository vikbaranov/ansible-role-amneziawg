#!/usr/bin/env python3
"""
Parse an 'awg showconf' dump into a host_vars YAML file for the Ansible role.

Usage:
    python3 scripts/parse-existing-conf.py existing.conf > host_vars/vpn-server.yml
"""

import sys
import re
import yaml


def parse_config(text):
    result = {
        "amneziawg_addresses": [],  # Must be filled manually
        "amneziawg_port": "51820",
        "amneziawg_private_key": "",
        "amneziawg_jc": 0,
        "amneziawg_jmin": 0,
        "amneziawg_jmax": 0,
        "amneziawg_s1": 0,
        "amneziawg_s2": 0,
        "amneziawg_s3": 0,
        "amneziawg_s4": 0,
        "amneziawg_h1": 0,
        "amneziawg_h2": 0,
        "amneziawg_h3": 0,
        "amneziawg_h4": 0,
        "amneziawg_unmanaged_peers": {},
    }

    # --- Interface ---
    iface_match = re.search(r"\[Interface\](.+?)(?=\n\[Peer\]|\Z)", text, re.DOTALL)
    if not iface_match:
        print("ERROR: No [Interface] section found", file=sys.stderr)
        sys.exit(1)

    iface = iface_match.group(1)

    def iface_val(pattern, default=""):
        m = re.search(pattern, iface, re.MULTILINE)
        return m.group(1).strip() if m else default

    result["amneziawg_port"] = iface_val(r"^ListenPort\s*=\s*(\d+)")
    result["amneziawg_private_key"] = iface_val(r"^PrivateKey\s*=\s*(.+)")
    result["amneziawg_jc"] = int(iface_val(r"^Jc\s*=\s*(\d+)", "0"))
    result["amneziawg_jmin"] = int(iface_val(r"^Jmin\s*=\s*(\d+)", "0"))
    result["amneziawg_jmax"] = int(iface_val(r"^Jmax\s*=\s*(\d+)", "0"))
    result["amneziawg_s1"] = int(iface_val(r"^S1\s*=\s*(\d+)", "0"))
    result["amneziawg_s2"] = int(iface_val(r"^S2\s*=\s*(\d+)", "0"))
    result["amneziawg_s3"] = int(iface_val(r"^S3\s*=\s*(\d+)", "0"))
    result["amneziawg_s4"] = int(iface_val(r"^S4\s*=\s*(\d+)", "0"))
    result["amneziawg_h1"] = iface_val(r"^H1\s*=\s*(.+)", "0")
    result["amneziawg_h2"] = iface_val(r"^H2\s*=\s*(.+)", "0")
    result["amneziawg_h3"] = iface_val(r"^H3\s*=\s*(.+)", "0")
    result["amneziawg_h4"] = iface_val(r"^H4\s*=\s*(.+)", "0")

    # --- Peers ---
    peer_blocks = re.findall(r"\[Peer\](.+?)(?=\n\[Peer\]|\Z)", text, re.DOTALL)
    for idx, block in enumerate(peer_blocks, 1):
        def peer_val(pattern, default=""):
            m = re.search(pattern, block, re.MULTILINE)
            return m.group(1).strip() if m else default

        public_key = peer_val(r"^PublicKey\s*=\s*(.+)")
        allowed_ips = peer_val(r"^AllowedIPs\s*=\s*(.+)")
        if not public_key or not allowed_ips:
            continue

        peer_name = f"peer-{idx:02d}"
        peer_data = {
            "public_key": public_key,
            "allowed_ips": allowed_ips,
        }

        psk = peer_val(r"^PresharedKey\s*=\s*(.+)")
        if psk:
            peer_data["preshared_key"] = psk

        endpoint = peer_val(r"^Endpoint\s*=\s*(.+)")
        if endpoint:
            peer_data["endpoint"] = endpoint

        keepalive = peer_val(r"^PersistentKeepalive\s*=\s*(\d+)")
        if keepalive:
            peer_data["persistent_keepalive"] = int(keepalive)

        result["amneziawg_unmanaged_peers"][peer_name] = peer_data

    return result


def format_yaml(data):
    """Emit YAML with comments for manual edits."""
    lines = [
        "---",
        "# AmneziaWG host_vars (generated from awg showconf dump)",
        "# ⚠️  IMPORTANT: This file contains a PLAINTEXT private key.",
        "#    Encrypt it with Ansible Vault before committing to version control.",
        "#",
        "# To encrypt:",
        "#   ansible-vault encrypt_string --stdin-name 'amneziawg_private_key'",
        "#   (paste the private key, press Ctrl+D)",
        "# Then replace the plaintext private_key with the vault output.",
        "",
        "# ── Interface ───────────────────────────────────────────────────────────",
        "# TODO: Set your server VPN address (awg showconf does not include it)",
        '# amneziawg_addresses:\n#   - "10.8.1.1/24"',
        "",
        f'amneziawg_port: "{data["amneziawg_port"]}"',
        "",
        "# Server public endpoint — UPDATE THIS with your actual endpoint",
        "# amneziawg_endpoint: \"vpn.example.com\"",
        "",
        "# Private key — MUST be encrypted with Ansible Vault for production use",
        f"amneziawg_private_key: \"{data['amneziawg_private_key']}\"",
        "",
        "# ── Obfuscation parameters ─────────────────────────────────────────────",
    ]

    obfuscation = {
        "jc": data["amneziawg_jc"],
        "jmin": data["amneziawg_jmin"],
        "jmax": data["amneziawg_jmax"],
        "s1": data["amneziawg_s1"],
        "s2": data["amneziawg_s2"],
        "s3": data["amneziawg_s3"],
        "s4": data["amneziawg_s4"],
        "h1": data["amneziawg_h1"],
        "h2": data["amneziawg_h2"],
        "h3": data["amneziawg_h3"],
        "h4": data["amneziawg_h4"],
    }
    for k, v in obfuscation.items():
        lines.append(f"amneziawg_{k}: {v}")

    lines.append("")
    lines.append("# ── Peers migrated from existing configuration ───────────────────────────")
    lines.append("amneziawg_unmanaged_peers:")

    if not data["amneziawg_unmanaged_peers"]:
        lines.append("  {}")
    else:
        for name, peer in data["amneziawg_unmanaged_peers"].items():
            lines.append(f"  {name}:")
            lines.append(f"    public_key: {peer['public_key']}")
            lines.append(f"    allowed_ips: {peer['allowed_ips']}")
            if "preshared_key" in peer:
                lines.append(f"    preshared_key: {peer['preshared_key']}")
            if "persistent_keepalive" in peer:
                lines.append(f"    persistent_keepalive: {peer['persistent_keepalive']}")

    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <awg-showconf-dump.conf>", file=sys.stderr)
        sys.exit(1)

    with open(sys.argv[1], "r") as f:
        raw = f.read()

    parsed = parse_config(raw)
    print(format_yaml(parsed))
