"""Raycast and proximity detection for player interactions."""

import math
from dataclasses import dataclass
from typing import List, Optional, Tuple
from config.game_config import GameConfig
from devices.device import Device
from world.rack import Rack
from world.interactable import Interactable


from devices.port import Port


@dataclass
class InteractionTarget:
    target_type: str  # "PORT", "DEVICE", "RACK", "DESK", "NONE"
    interactable: Optional[Interactable] = None
    rack: Optional[Rack] = None
    targeted_u: Optional[int] = None
    device: Optional[Device] = None
    port: Optional[Port] = None
    port_world_pos: Optional[Tuple[float, float, float]] = None
    device_world_pos: Optional[Tuple[float, float, float]] = None
    distance: float = 0.0
    hint_text: str = ""


class InteractionDetector:
    """Performs 3D raycasting from player eye to detect objects and ports within reach."""

    @staticmethod
    def ray_aabb_intersect(
        ray_orig: Tuple[float, float, float],
        ray_dir: Tuple[float, float, float],
        box: Tuple[float, float, float, float, float, float],
        max_dist: float
    ) -> Optional[Tuple[float, float]]:
        """Slab method for Ray-AABB intersection. Returns (t_near, hit_y) or None."""
        ox, oy, oz = ray_orig
        dx, dy, dz = ray_dir
        min_x, min_y, min_z, max_x, max_y, max_z = box

        t_min = 0.0
        t_max = max_dist

        # X slab
        if abs(dx) < 1e-6:
            if ox < min_x or ox > max_x:
                return None
        else:
            tx1 = (min_x - ox) / dx
            tx2 = (max_x - ox) / dx
            t_min = max(t_min, min(tx1, tx2))
            t_max = min(t_max, max(tx1, tx2))
            if t_min > t_max:
                return None

        # Y slab
        if abs(dy) < 1e-6:
            if oy < min_y or oy > max_y:
                return None
        else:
            ty1 = (min_y - oy) / dy
            ty2 = (max_y - oy) / dy
            t_min = max(t_min, min(ty1, ty2))
            t_max = min(t_max, max(ty1, ty2))
            if t_min > t_max:
                return None

        # Z slab
        if abs(dz) < 1e-6:
            if oz < min_z or oz > max_z:
                return None
        else:
            tz1 = (min_z - oz) / dz
            tz2 = (max_z - oz) / dz
            t_min = max(t_min, min(tz1, tz2))
            t_max = min(t_max, max(tz1, tz2))
            if t_min > t_max:
                return None

        hit_y = oy + t_min * dy
        return t_min, hit_y

    def find_target(
        self,
        eye_pos: Tuple[float, float, float],
        forward: Tuple[float, float, float],
        interactables: List[Interactable],
        max_dist: float = GameConfig.INTERACT_MAX_DISTANCE,
        mode: str = "CABLING_CLI",
        has_held_cable: bool = False
    ) -> InteractionTarget:
        """Find the exact interactable, device, or RJ45 port centered directly under the crosshair reticle."""
        ex, ey, ez = eye_pos
        fx, fy, fz = forward

        # Collect racks and desk
        racks: List[Rack] = [item for item in interactables if isinstance(item, Rack)]
        other_items: List[Interactable] = [item for item in interactables if not isinstance(item, Rack)]

        # -------------------------------------------------------------
        # 1. PRIORITY 1: Precise RJ45 Port Aiming (In Cabling/CLI Mode)
        # Check all ports on all installed devices directly
        # -------------------------------------------------------------
        if mode == "CABLING_CLI":
            best_port: Optional[Port] = None
            best_port_device: Optional[Device] = None
            best_port_rack: Optional[Rack] = None
            best_port_pos: Optional[Tuple[float, float, float]] = None
            best_port_dist: float = 999.0
            best_port_offset_sq: float = 999.0

            for rack in racks:
                for dev in rack.devices:
                    if not dev.position:
                        continue
                    dev_cx, dev_cy, dev_cz = dev.position
                    for port in dev.ports.values():
                        lx, ly, lz = port.local_slot_pos
                        p_wx = dev_cx + lx
                        p_wy = dev_cy + ly
                        p_wz = dev_cz + lz

                        # Ray-to-point calculation
                        vx = p_wx - ex
                        vy = p_wy - ey
                        vz = p_wz - ez
                        t = vx * fx + vy * fy + vz * fz

                        if 0.2 < t <= max_dist:
                            # Perpendicular vector from line of sight to port center
                            perp_x = vx - t * fx
                            perp_y = vy - t * fy
                            perp_z = vz - t * fz
                            d_perp_sq = perp_x * perp_x + perp_y * perp_y + perp_z * perp_z

                            # Port hit tolerance: 2.8cm radius around socket center
                            port_radius_sq = 0.028 * 0.028  # ~2.8cm
                            if d_perp_sq <= port_radius_sq:
                                # Prioritize port closest to the center reticle ray
                                if d_perp_sq < best_port_offset_sq:
                                    best_port_offset_sq = d_perp_sq
                                    best_port_dist = t
                                    best_port = port
                                    best_port_device = dev
                                    best_port_rack = rack
                                    best_port_pos = (p_wx, p_wy, p_wz)

            if best_port and best_port_device and best_port_rack:
                if has_held_cable:
                    hint = f"[F] Plug Cable into {best_port_device.hostname}:{best_port.port_name}"
                elif best_port.connected_port:
                    hint = f"[F] Unplug Cable from {best_port_device.hostname}:{best_port.port_name} | [E] Open CLI"
                else:
                    hint = f"[F] Patch Cable from {best_port_device.hostname}:{best_port.port_name} | [E] Open CLI"

                dev_cx, dev_cy, dev_cz = best_port_device.position
                return InteractionTarget(
                    target_type="PORT",
                    interactable=best_port_rack,
                    rack=best_port_rack,
                    targeted_u=best_port_device.start_u,
                    device=best_port_device,
                    port=best_port,
                    port_world_pos=best_port_pos,
                    device_world_pos=(dev_cx, dev_cy, dev_cz),
                    distance=best_port_dist,
                    hint_text=hint
                )

        # -------------------------------------------------------------
        # 2. PRIORITY 2: Installed Device Chassis Raycast
        # Check all installed devices across racks
        # -------------------------------------------------------------
        best_dev: Optional[Device] = None
        best_dev_rack: Optional[Rack] = None
        best_dev_dist: float = max_dist + 1.0

        for rack in racks:
            for dev in rack.devices:
                if not dev.position:
                    continue
                dev_cx, dev_cy, dev_cz = dev.position
                hw = 0.241  # 48.2cm chassis width
                hh = (dev.u_height * 0.04445) / 2.0
                hd = 0.26   # chassis depth
                # Device bounding box
                dev_box = (
                    dev_cx - hw, dev_cy - hh, dev_cz - hd,
                    dev_cx + hw, dev_cy + hh, dev_cz + 0.26
                )
                hit_res = self.ray_aabb_intersect(eye_pos, forward, dev_box, max_dist)
                if hit_res is not None:
                    t_hit, _ = hit_res
                    if t_hit < best_dev_dist:
                        best_dev_dist = t_hit
                        best_dev = dev
                        best_dev_rack = rack

        if best_dev and best_dev_rack:
            dev_cx, dev_cy, dev_cz = best_dev.position
            if mode == "CABLING_CLI":
                hint = f"[E] Open CLI on {best_dev.hostname} | [R] Hardware Mode"
            else:
                hint = f"[E] Remove {best_dev.hostname} from Rack | [R] Cabling Mode"

            return InteractionTarget(
                target_type="DEVICE",
                interactable=best_dev_rack,
                rack=best_dev_rack,
                targeted_u=best_dev.start_u,
                device=best_dev,
                port=None,
                device_world_pos=(dev_cx, dev_cy, dev_cz),
                distance=best_dev_dist,
                hint_text=hint
            )

        # -------------------------------------------------------------
        # 3. PRIORITY 3: Server Rack Mounting Front Plane (Empty U Slots)
        # Intersect ray with rack front plane (Z = cz + 0.402)
        # -------------------------------------------------------------
        best_rack_hit: Optional[Tuple[Rack, int, float]] = None
        best_rack_dist: float = max_dist + 1.0

        for rack in racks:
            # Front rail plane at rack.position[2] + 0.402
            z_front = rack.position[2] + 0.402
            if abs(fz) > 1e-5:
                t = (z_front - ez) / fz
                if 0.1 < t < best_rack_dist:
                    hit_x = ex + t * fx
                    hit_y = ey + t * fy
                    half_w = rack.width_m / 2.0
                    if (rack.position[0] - half_w) <= hit_x <= (rack.position[0] + half_w):
                        if rack.base_y <= hit_y <= (rack.base_y + rack.total_height_m):
                            target_u = rack.get_u_from_world_y(hit_y)
                            best_rack_dist = t
                            best_rack_hit = (rack, target_u, t)

        if best_rack_hit is not None:
            rack, target_u, dist = best_rack_hit
            dev_at_u = rack.get_device_at_u(target_u)
            if dev_at_u:
                dev_cx, dev_cy, dev_cz = dev_at_u.position or (rack.position[0], rack.get_world_y_for_u(dev_at_u.start_u), rack.position[2] + 0.15)
                hint = f"[E] Open CLI on {dev_at_u.hostname}" if mode == "CABLING_CLI" else f"[E] Remove {dev_at_u.hostname}"
                return InteractionTarget(
                    target_type="DEVICE",
                    interactable=rack,
                    rack=rack,
                    targeted_u=target_u,
                    device=dev_at_u,
                    port=None,
                    device_world_pos=(dev_cx, dev_cy, dev_cz),
                    distance=dist,
                    hint_text=hint
                )
            else:
                if mode == "HARDWARE_MGMT":
                    hint = f"[E] Install Device at {rack.rack_id} U{target_u}"
                else:
                    hint = f"{rack.rack_id} [Slot U{target_u} Available] | [R] Hardware Mode"

                return InteractionTarget(
                    target_type="RACK",
                    interactable=rack,
                    rack=rack,
                    targeted_u=target_u,
                    device=None,
                    port=None,
                    distance=dist,
                    hint_text=hint
                )

        # -------------------------------------------------------------
        # 4. PRIORITY 4: Other Interactables
        # -------------------------------------------------------------
        for item in other_items:
            box = item.get_bounding_box()
            res = self.ray_aabb_intersect(eye_pos, forward, box, max_dist)
            if res is not None:
                dist, _ = res
                return InteractionTarget(
                    target_type="GENERIC",
                    interactable=item,
                    distance=dist,
                    hint_text=item.get_interaction_hint()
                )

        return InteractionTarget(target_type="NONE")
