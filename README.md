# Ansible Role: AmneziaWG

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An Ansible role to deploy and manage [AmneziaWG](https://amnezia.org/) VPN server using a Docker container managed by systemd.

## Features

- Deploy AmneziaWG server in a Docker container with systemd
- Automatic key generation and peer management
- Client lifecycle management (add/remove with auto-generated configs)
- Obfuscation parameter support (Jc, Jmin, Jmax, S1–S4, H1–H4)
- Idempotent client operations
- QR code generation for mobile clients

## Requirements

- Ansible >= 2.14
- Docker on target host
- `qrencode` on Ansible controller (for QR generation)

## Role Variables

### Required

| Variable | Description |
|----------|-------------|
| `amneziawg_addresses` | List of VPN IP addresses with CIDR (e.g. `["10.8.1.1/24"]`). Server address. |
| `amneziawg_private_key` | Server private key. Auto-generated if empty. |

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `amneziawg_state` | `present` | `present` or `absent` |
| `amneziawg_endpoint` | — | Public endpoint hostname or IP |
| `amneziawg_port` | `51820` | Listen port |
| `amneziawg_interface` | `awg0` | Interface name |
| `amneziawg_version` | `v3.0.20260805` | Docker image version |
| `amneziawg_as_spoke` | `false` | Hub-and-spoke mode |
| `amneziawg_jc` | `0` | Junk packet count |
| `amneziawg_jmin` | `0` | Junk packet minimum size |
| `amneziawg_jmax` | `0` | Junk packet maximum size |
| `amneziawg_s1` | `0` | Junk packet S1 parameter |
| `amneziawg_s2` | `0` | Junk packet S2 parameter |
| `amneziawg_s3` | `0` | Junk packet S3 parameter |
| `amneziawg_s4` | `0` | Junk packet S4 parameter |
| `amneziawg_h1`–`h4` | `0` | Header obfuscation parameters (supports hyphenated ranges) |

See `defaults/main.yml` for the complete list.

## Dependencies

None.

## Example Playbook

### Server deployment

```yaml
---
- hosts: vpn_servers
  become: true
  roles:
    - role: amneziawg
      vars:
        amneziawg_addresses:
          - "10.8.1.1/24"
        amneziawg_endpoint: "vpn.example.com"
        amneziawg_port: "51820"
        amneziawg_private_key: "{{ vault_amneziawg_private_key }}"
        amneziawg_jc: 4
        amneziawg_jmin: 10
        amneziawg_jmax: 50
        amneziawg_unmanaged_peers:
          peer-01:
            public_key: OauurYLmBw455R2Jlx050PDfoed5VnAvraYbuDPW0S0=
            allowed_ips: 10.8.1.2/32
```

### Add a client

```bash
ansible-playbook playbook.yml \
  -e "amneziawg_client_action=add amneziawg_client_name=laptop" \
  --tags amneziawg-clients
```

### Remove a client

```bash
ansible-playbook playbook.yml \
  -e "amneziawg_client_action=remove amneziawg_client_name=laptop" \
  --tags amneziawg-clients
```

## Extract Config from Existing Server

Use the offline parser to migrate an existing AmneziaWG installation:

```bash
python3 scripts/parse-existing-conf.py existing.conf > host_vars/<target_host>.yml
```

**Important:** `awg showconf` does **not** include the `Address` field under `[Interface]`. You **must** manually edit the generated file and add:

```yaml
amneziawg_addresses:
  - "10.8.1.1/24"
```

### Post-extraction steps

1. Review the generated `host_vars/<target_host>.yml`
2. **Add the server's public endpoint**:
   ```yaml
   amneziawg_endpoint: "vpn.example.com"
   ```
3. **Add `amneziawg_addresses`** :
   ```yaml
   amneziawg_addresses:
     - "10.8.1.1/24"
   ```
4. **Encrypt the private key** with Ansible Vault:
   ```bash
   ansible-vault encrypt_string --stdin-name 'amneziawg_private_key'
   ```
5. **Replace** the plaintext `amneziawg_private_key` in the file with the vault output
6. **Deploy** the role:
   ```bash
   ansible-playbook -i inventory site.yml
   ```

## Client outputs

When adding a client, the role creates:

```
clients/<client_name>/
├── <client_name>.conf    # WireGuard config
└── <client_name>.png     # QR code (if amneziawg_show_qr=true)
```

## License

MIT

## Author

vbaranov
