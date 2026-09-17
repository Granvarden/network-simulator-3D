# Network Simulator 3D - Device State & Single Source of Truth Architecture

## 1. Architectural Philosophy

In Network Simulator 3D, network configuration and operational state must adhere to the **Single Source of Truth (SSOT)** principle:

1. **No Duplicate State**: A piece of state (e.g. routing entry, VLAN definition, IP address) is stored in exactly one authoritative location.
2. **Directional Dependency Enforcement**:
   $$\text{UI Layer} \longrightarrow \text{CLI Engine} \longrightarrow \text{Service Layer} \longrightarrow \text{Device State} \longrightarrow \text{Network Engine}$$
3. **No Direct CLI Mutation**: CLI command handlers never directly mutate internal device fields (e.g., `port.ip_address = ...` or `router.static_routes.append(...)`). All mutations must pass through the **Service Layer**.
4. **Decoupled Ports**: Network ports (`Port`) have zero dependency on `NetworkEngine`. Link operational status is derived purely from physical cabling and administrative power states.
5. **Dynamic Running Configuration**: `show running-config` is never a stored text string. It is synthesized on-the-fly directly from live device state.

---

## 2. Core Architectural Components

### 2.1 Interface Normalizer (`devices/interface_normalizer.py`)
Provides deterministic resolution across all Cisco IOS interface abbreviations:
- Shorthands `g0/0`, `gi0/0`, `Gi0/0` normalize to canonical `GigabitEthernet0/0`.
- Shorthand converter produces standard Cisco abbreviation `Gi0/0`.
- Device port lookups via `device.get_port(name)` or `device.ports[name]` transparently resolve aliases using `PortDict`.

### 2.2 Deterministic Hexadecimal MAC Generator (`devices/mac_generator.py`)
Generates RFC-compliant locally administered unicast MAC addresses:
$$\text{MAC Format: } \texttt{02:00:00:XX:YY:ZZ}$$
- `0x02`: First octet sets Bit 1 (Locally Administered) and clears Bit 0 (Unicast).
- `XX:YY`: Deterministic 2-byte MD5 hash derived from `device_id`.
- `ZZ`: 1-byte interface index `port_idx & 0xFF`.
- Eliminates invalid non-hex characters resulting from raw string slicing.
- Formats to standard colon notation (`02:00:00:1a:2b:01`) or Cisco notation (`0200.001a.2b01`).

### 2.3 Routing Table Single Source of Truth (`network/routing_table.py` & `devices/router.py`)
- `Router.routing_table` (`RoutingTable`) is the sole authority for all routing decisions on a Router.
- The duplicate `router.static_routes` list is deprecated and maintained as a backwards-compatible property computed dynamically from `RoutingTable`.
- Connected routes (`C`) are dynamically synchronized via `Router.sync_connected_routes()` whenever an interface changes IP or operational link state (`AdminStatus.UP` and `LinkStatus.UP`).
- Routing evaluation uses **Longest Prefix Matching (LPM)** based on bitwise mask comparisons.

### 2.4 VLAN Database Single Source of Truth (`devices/vlan_database.py` & `devices/switch.py`)
- `Switch.vlan_database` (`VLANDatabase`) is the sole authority for 802.1Q VLAN entries.
- Reserved standard Cisco VLANs:
  - `VLAN 1`: Default access VLAN (Active, cannot be deleted or renamed).
  - `VLAN 1002-1005`: Reserved Cisco legacy defaults (`fddi-default`, `token-ring-default`, etc., cannot be deleted or renamed).
- Ports store only their assigned `vlan` ID reference and `switchport_mode` (`"access"` or `"trunk"`).
- Deleting a user VLAN automatically reassigns member access ports to default VLAN 1.

---

## 3. Service Layer Architecture (`services/`)

The Service Layer provides domain business logic and validation:

| Service | File | Responsibilities |
|---|---|---|
| `InterfaceService` | `services/interface_service.py` | Admin status toggling, IP/mask validation, duplicate IP conflict detection, broadcast/network IP rejection, description setting, switchport access/trunk configuration. |
| `VlanService` | `services/vlan_service.py` | VLAN creation/deletion/naming with reserved ID protection, `show vlan brief` aggregation. |
| `RoutingService` | `services/routing_service.py` | Static route and default route addition/removal, route lookups via LPM. |
| `DeviceService` | `services/device_service.py` | Hostname syntax validation, power state toggling, dynamic running-config generation, simulator platform version formatting. |

---

## 4. Session & History Isolation

In `CLIEngine` (`cli/cli_engine.py`):
- Each network device owns a dedicated `CLISession` (`cli/cli_session.py`).
- Session isolation ensures that navigating to `(config-if)#` on Router 1 does not pollute the terminal context, prompt, or command history when switching to Switch 1.
- History is bounded (100 entries) with duplicate consecutive suppression and clean Up/Down arrow recall.
- Tab completion is powered by `CLICompleter` inspecting the active `CommandRegistry` for the active mode.

---

## 5. Preparation for Phase 2: Packet-Based Network Simulator

The decoupled architecture established in this phase directly enables Phase 2:
1. **Discrete Packet Dispatch**: Ports maintain clean operational state, allowing discrete `Packet` / `EthernetFrame` / `IPPacket` objects to traverse physical cable connections.
2. **True ARP Resolution**: Devices can broadcast ARP requests and populate dynamic ARP tables without hardcoded engine lookups.
3. **Layer 2 / Layer 3 Frame Processing**: Switches inspect incoming frames, update MAC tables, and switch across VLAN boundaries (access/trunk). Routers evaluate TTL, decrement hop counts, and route via `RoutingTable.lookup()`.
