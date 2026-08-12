# Ansible Role: AmneziaWG

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An Ansible role to deploy and manage an [AmneziaWG](https://amnezia.org/) VPN server using either native packages or a Docker container.

## Features

- Deploy AmneziaWG server with native packages or Docker
- Automatic key generation and peer management
- Client lifecycle management (add/remove with auto-generated configs)
- Obfuscation parameter support (Jc, Jmin, Jmax, S1–S4, H1–H4)
- Idempotent client operations
- QR code generation for mobile clients

## Requirements

- Ansible >= 2.14
- Root privileges on the target host
- `qrencode` on the Ansible controller only when `amneziawg_show_qr=true`

### Install modes

| Mode | Default | Supported targets | Notes |
|------|---------|-------------------|-------|
| `native` | Yes | Ubuntu jammy/noble | Uses the Amnezia PPA and `awg-quick@<interface>` systemd unit. |
| `docker` | No | Debian bullseye/bookworm, Ubuntu jammy/noble, RedHat-family hosts with Docker package availability | Installs Docker if missing and uses `amneziawg@<interface>` systemd unit. |

### Native mode

- Ubuntu only.
- Adds `ppa:amnezia/ppa` automatically.
- Installs `software-properties-common`, `gnupg2`, matching `linux-headers`, and the `amneziawg` package.
- Does not require Docker.

### Docker mode

- Installs `docker.io` on Debian-family hosts or `docker` on RedHat-family hosts if Docker is missing.
- Pulls `docker.io/amneziavpn/amneziawg-go` using `amneziawg_version`.
- Runs the container through a systemd template unit.

## Role Variables

### Required

| Variable | Description |
|----------|-------------|
| `amneziawg_addresses` | List of VPN IP addresses with CIDR (e.g. `["10.8.1.1/24"]`). Server address. |

`amneziawg_private_key` is optional and auto-generated when empty. For stable production deployments, set it explicitly and store it with Ansible Vault.

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `amneziawg_state` | `present` | `present` or `absent` |
| `amneziawg_install_method` | `native` | `native` or `docker`. Native uses the Amnezia PPA (Ubuntu only). |
| `amneziawg_endpoint` | — | Public endpoint hostname or IP |
| `amneziawg_port` | `51820` | Listen port |
| `amneziawg_interface` | `awg0` | Interface name |
| `amneziawg_version` | `v3.0.20260805` | Docker image version |
| `amneziawg_as_spoke` | `false` | Hub-and-spoke mode |
| `amneziawg_remote_directory` | `/etc/amnezia/amneziawg` | Remote configuration directory |
| `amneziawg_service_enabled` | `true` | Enable the service at boot |
| `amneziawg_service_state` | `started` | Desired service state |
| `amneziawg_conf_backup` | `false` | Backup generated config before replacing it |

### Interface options

| Variable | Default | Description |
|----------|---------|-------------|
| `amneziawg_dns` | — | DNS value written to the server interface config |
| `amneziawg_mtu` | — | MTU value written to the server interface config |
| `amneziawg_fwmark` | — | FwMark value written to the server interface config |
| `amneziawg_table` | — | Routing table value written to the server interface config |
| `amneziawg_preup` | `[]` | List of `PreUp` commands written to the config |
| `amneziawg_postup` | `[]` | Docker mode only: host `ExecStartPost` commands |
| `amneziawg_predown` | `[]` | Docker mode only: host `ExecStopPost` commands run before post-down commands |
| `amneziawg_postdown` | `[]` | Docker mode only: host `ExecStopPost` commands run after pre-down commands |

### Obfuscation options

| Variable | Default | Description |
|----------|---------|-------------|
| `amneziawg_jc` | `0` | Junk packet count |
| `amneziawg_jmin` | `0` | Junk packet minimum size |
| `amneziawg_jmax` | `0` | Junk packet maximum size |
| `amneziawg_s1` | `0` | Junk packet S1 parameter |
| `amneziawg_s2` | `0` | Junk packet S2 parameter |
| `amneziawg_s3` | `0` | Junk packet S3 parameter |
| `amneziawg_s4` | `0` | Junk packet S4 parameter |
| `amneziawg_h1`–`h4` | `0` | Header obfuscation parameters (supports hyphenated ranges) |

### Peer and client options

| Variable | Default | Description |
|----------|---------|-------------|
| `amneziawg_unmanaged_peers` | `{}` | Static peer definitions rendered into the server config |
| `amneziawg_preshared_key` | — | Optional PSK assigned to newly generated clients |
| `amneziawg_client_action` | `''` | `add`, `remove`, or empty for server-only runs |
| `amneziawg_client_name` | `''` | Client name for add/remove actions |
| `amneziawg_client_address` | `''` | Client VPN address. Auto-assigned from the first server subnet when empty. |
| `amneziawg_client_dns` | `1.1.1.1` | DNS value written to generated client configs |
| `amneziawg_show_qr` | `false` | Generate a PNG QR code for new clients |
| `amneziawg_peers_file` | `{{ playbook_dir }}/../host_vars/{{ inventory_hostname }}/awg-peers.yml` | Local file used to persist generated peers |
| `amneziawg_clients_dir` | `{{ playbook_dir }}/../clients` | Local directory for generated client configs |

### Uninstall options

| Variable | Default | Description |
|----------|---------|-------------|
| `amneziawg_remove_docker_image` | `true` | Remove the Docker image during Docker uninstall |
| `amneziawg_remove_configs` | `true` | Remove `amneziawg_remote_directory` during uninstall |

See `defaults/main.yml` for the complete list.

## Dependencies

None.

## Example Playbook

### Server deployment (native default)

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

### Server deployment (Docker)

```yaml
---
- hosts: vpn_servers
  become: true
  roles:
    - role: amneziawg
      vars:
        amneziawg_install_method: docker
        amneziawg_addresses:
          - "10.8.1.1/24"
        amneziawg_endpoint: "vpn.example.com"
        amneziawg_port: "51820"
        amneziawg_private_key: "{{ vault_amneziawg_private_key }}"
        amneziawg_jc: 4
        amneziawg_jmin: 10
        amneziawg_jmax: 50
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

Generated peers are persisted on the Ansible controller in `amneziawg_peers_file`. By default this is `../host_vars/<inventory_hostname>/awg-peers.yml` relative to the playbook directory. Keep this file under inventory management and encrypt sensitive values when needed.

## Uninstall

Set `amneziawg_state=absent` to remove the service and installed artifacts:

```bash
ansible-playbook playbook.yml \
  -e "amneziawg_state=absent" \
  --tags amneziawg-uninstall
```

By default uninstall also removes the Docker image in Docker mode and deletes `amneziawg_remote_directory`. Set `amneziawg_remove_docker_image=false` or `amneziawg_remove_configs=false` to keep them.

## Tags

| Tag | Purpose |
|-----|---------|
| `amneziawg` | Run all role tasks |
| `amneziawg-install` | Install packages, image, entrypoint, and systemd units |
| `amneziawg-config` | Render config, peers, forwarding, and service state |
| `amneziawg-keys` | Generate or derive server keys |
| `amneziawg-clients` | Add or remove clients |
| `amneziawg-uninstall` | Remove AmneziaWG artifacts |

## License

MIT

## Author

vbaranov
