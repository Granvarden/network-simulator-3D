# Network Simulator 3D - CLI Reference Guide

## 1. Overview

Network Simulator 3D features a Cisco IOS-inspired interactive Command Line Interface (CLI) for Routers and Switches, as well as a Windows Command Prompt environment for PC Workstations.

The CLI architecture is decoupled from UI rendering and physics engines:
```
Pygame UI / TerminalUI 
         │
    CLIEngine (Sessions, History, Tab Completion)
         │
    CLIParser (Tokenization, Caret Markers, Pipe Filters)
         │
   CommandRegistry (Prefix Matching, Ambiguity Detection)
         │
  Command Handlers (Exec, Common, Interface, VLAN, IP, Show)
         │
    Service Layer (InterfaceService, VlanService, RoutingService, DeviceService)
         │
    Device State (Router, Switch, PC - Single Source of Truth)
         │
    Network Engine (Layer 2 Switching, Layer 3 Routing, ICMP)
```

---

## 2. Command Modes & Prompt Hierarchy

### Cisco IOS Devices (Router & Switch)

| Mode | Prompt Format | Description | Entry Command | Exit Command |
|---|---|---|---|---|
| **User EXEC** | `Router>` | Basic monitoring and view commands | Session start or `disable` | `exit` / `quit` |
| **Privileged EXEC** | `Router#` | Advanced diagnostics and configuration entry | `enable` (or `en`) | `disable` or `exit` |
| **Global Configuration** | `Router(config)#` | Device-wide system configuration | `configure terminal` (or `conf t`) | `exit` (to Privileged EXEC) |
| **Interface Configuration** | `Router(config-if)#` | Per-interface IP and physical parameters | `interface <name>` (or `int g0/0`) | `exit` (to Global Config) |
| **VLAN Configuration** | `Switch(config-vlan)#` | Switch VLAN database management | `vlan <vlan_id>` | `exit` (to Global Config) |

> **Navigation Shortcuts**:
> - `end` or `Ctrl+Z`: Return directly to **Privileged EXEC** from any sub-configuration mode.
> - `Ctrl+C`: Abort current command line buffer.
> - `Ctrl+A` / `Ctrl+E`: Jump to beginning / end of line.
> - `Ctrl+U`: Clear input buffer.
> - `do <command>`: Execute any Privileged EXEC command (e.g. `do show ip int br`) from within any configuration mode without navigating back.

### Host PC Workstation

| Mode | Prompt Format | Description |
|---|---|---|
| **Command Prompt** | `C:\Users\Engineer>` | Standard host network diagnostic and IP configuration |

---

## 3. Cisco IOS Command Reference

### Executive & Navigation Commands
- `enable` / `en`: Elevate from User EXEC to Privileged EXEC mode.
- `disable` / `dis`: Drop from Privileged EXEC to User EXEC mode.
- `configure terminal` / `conf t`: Enter Global Configuration mode.
- `hostname <name>`: Rename system hostname (alphanumeric and hyphens, up to 63 chars).
- `exit` / `quit`: Move one level up the configuration hierarchy or disconnect session.
- `end`: Return immediately to Privileged EXEC mode.

### Interface Configuration Commands
- `interface <name>` / `int <name>`: Select an interface to configure (e.g. `interface GigabitEthernet0/0`, `int Gi0/1`, `int g0/2`).
- `ip address <ip> <subnet_mask>`: Assign an IPv4 address and netmask.
- `no ip address`: Remove configured IP address.
- `shutdown`: Administratively disable interface (turns physical port LED Amber).
- `no shutdown` / `no shut`: Administratively enable interface (turns physical port LED Green when cable connected).
- `description <text>` / `desc <text>`: Assign text label to interface (supports quotes e.g. `description "Core Backbone"`).
- `no description`: Remove interface description.
- `switchport mode access`: Configure interface as Layer 2 access port (Switch only).
- `switchport mode trunk`: Configure interface as 802.1Q trunk port (Switch only).
- `switchport access vlan <vlan_id>`: Assign switchport to a specific access VLAN.
- `switchport trunk allowed vlan <vlans>`: Specify allowed VLANs on trunk port (e.g. `10,20,30-40`).

### VLAN Database Commands (Switch)
- `vlan <vlan_id>`: Enter VLAN configuration mode for specified VLAN ID (1-4094).
- `name <vlan_name>`: Assign descriptive name to the VLAN (e.g. `name Engineering`).
- `no vlan <vlan_id>`: Delete user-defined VLAN. Reserved VLANs (1, 1002-1005) cannot be deleted.

### IP Routing Commands (Router)
- `ip route <network> <netmask> <next_hop>`: Configure static route or default route (`0.0.0.0 0.0.0.0 <gw>`). The next-hop can be an IP address or an egress interface.
- `no ip route <network> <netmask> <next_hop>`: Remove configured static route.
- `ip default-gateway <ip>`: Set default gateway for management.

### Diagnostic & Inspection Commands (`show`)
- `show running-config` / `sh run`: Display running configuration synthesized directly from live device state.
- `show ip interface brief` / `sh ip int br`: Display tabular status of all interfaces, IP addresses, admin status, and protocol status.
- `show interfaces [name]` / `sh int`: Detailed interface statistics, MAC addresses, line protocol, duplex, and speed.
- `show ip route` / `sh ip ro`: Display routing table with route codes (`C` - connected, `S` - static, `*` - default).
- `show vlan brief` / `sh vlan br`: Display summary of VLANs, status, and member ports.
- `show mac address-table` / `sh mac`: Display dynamic MAC address learning table (Switch only).
- `show version` / `sh ver`: Display simulator platform version, hardware details, base MAC, and uptime.

### Operational Commands
- `ping <ip>`: Send 5 ICMP Echo Requests with round-trip latency statistics (`!`, `.`).
- `clear mac address-table`: Flush dynamic MAC forwarding entries.
- `write memory` / `write` / `copy run start`: Save running configuration.

---

## 4. Host PC Command Reference

- `ipconfig`: Display basic IP address, subnet mask, and default gateway for `Ethernet0`.
- `ipconfig /all`: Display full TCP/IP host configuration including hostname and physical MAC address.
- `ipconfig /set <ip> <mask > [gateway]`: Configure IPv4 address, subnet mask, and optional default gateway.
- `ipconfig /disable`: Administratively disable `Ethernet0`.
- `ipconfig /enable`: Administratively enable `Ethernet0`.
- `netsh interface set interface eth0 admin=enable|disable`: Standard Windows network adapter control.
- `ping <destination_ip>`: Send 4 ICMP Echo requests with Windows ping formatting.
- `arp -a`: Display local host ARP cache table.
- `cls`: Clear terminal scrollback window.
- `help`: Display help summary for host commands.
- `exit`: Close PC terminal session.

---

## 5. Advanced Usability Features

### Command Abbreviation
Any unambiguous keyword prefix is accepted:
- `sh run` $\rightarrow$ `show running-config`
- `sh ip int br` $\rightarrow$ `show ip interface brief`
- `conf t` $\rightarrow$ `configure terminal`
- `int g0/0` $\rightarrow$ `interface GigabitEthernet0/0`
- `no shut` $\rightarrow$ `no shutdown`

### Tab Auto-Completion
Pressing `Tab` at any point auto-completes the keyword if unique, or lists available candidates if multiple matches exist.

### Output Stream Pipe Filtering
Append `|` followed by a filter:
- `| include <pattern>`: Show only lines containing pattern (e.g. `show run | include interface`).
- `| exclude <pattern>`: Show only lines not containing pattern.
- `| begin <pattern>`: Begin output display starting from first line containing pattern.
- `| section <pattern>`: Display entire configuration block matching pattern.

### Context-Sensitive Help
Type `?` at any point in the command line to view valid next keywords or parameters:
- `?` $\rightarrow$ list all commands in current mode.
- `show ?` $\rightarrow$ list all parameters valid for `show`.
