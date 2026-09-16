"""Raycast and proximity detection for player interactions."""

import math
from dataclasses import dataclass
from typing import List, Optional, Tuple
from config.game_config import GameConfig
from devices.device import Device
from world.rack import Rack
from world.desk import Desk
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
        """Find the closest interactable and RJ45 port in crosshair view within reach."""
        closest_dist = max_dist + 1.0
        best_hit: Optional[Tuple[Interactable, float, float]] = None

        for item in interactables:
            box = item.get_bounding_box()
            res = self.ray_aabb_intersect(eye_pos, forward, box, max_dist)
            if res is not None:
                dist, hit_y = res
                if dist < closest_dist:
                    closest_dist = dist
                    best_hit = (item, dist, hit_y)

        if best_hit is None:
            return InteractionTarget(target_type="NONE")

        item, dist, hit_y = best_hit

        # If targeted item is a Server Rack
        if isinstance(item, Rack):
            target_u = item.get_u_from_world_y(hit_y)
            device_at_u = item.get_device_at_u(target_u)

            if device_at_u:
                if device_at_u.position:
                    dev_cx, dev_cy, dev_cz = device_at_u.position
                else:
                    dev_cy = item.get_world_y_for_u(device_at_u.start_u) + (device_at_u.u_height * item.u_height_m) / 2.0
                    dev_cz = item.position[2] + 0.15
                    dev_cx = item.position[0]
                dev_pos = (dev_cx, dev_cy, dev_cz)

                # Check if ray hits any specific RJ45 Port on this device
                best_port: Optional[Port] = None
                best_port_dist = 999.0
                best_port_pos: Optional[Tuple[float, float, float]] = None

                for port in device_at_u.ports.values():
                    lx, ly, lz = port.local_slot_pos
                    p_wx = dev_cx + lx
                    p_wy = dev_cy + ly
                    p_wz = dev_cz + lz
                    # Precision port bounding box for comfortable, accurate aiming
                    p_box = (p_wx - 0.016, p_wy - 0.012, p_wz - 0.025, p_wx + 0.016, p_wy + 0.012, p_wz + 0.025)
                    p_res = self.ray_aabb_intersect(eye_pos, forward, p_box, max_dist)
                    if p_res is not None:
                        p_dist, _ = p_res
                        if p_dist < best_port_dist:
                            best_port_dist = p_dist
                            best_port = port
                            best_port_pos = (p_wx, p_wy, p_wz)

                # Mode 1: Cabling & CLI Mode
                if mode == "CABLING_CLI":
                    if best_port:
                        if has_held_cable:
                            hint = f"[F] Plug Cable into {device_at_u.hostname}:{best_port.port_name}"
                        elif best_port.connected_port:
                            hint = f"[F] Unplug Cable from {device_at_u.hostname}:{best_port.port_name} | [E] Open CLI"
                        else:
                            hint = f"[F] Patch Cable from {device_at_u.hostname}:{best_port.port_name} | [E] Open CLI"

                        return InteractionTarget(
                            target_type="PORT",
                            interactable=item,
                            rack=item,
                            targeted_u=target_u,
                            device=device_at_u,
                            port=best_port,
                            port_world_pos=best_port_pos,
                            device_world_pos=dev_pos,
                            distance=best_port_dist,
                            hint_text=hint
                        )
                    else:
                        hint = f"[E] Open CLI on {device_at_u.hostname} | [R] Hardware Mode"
                        return InteractionTarget(
                            target_type="DEVICE",
                            interactable=item,
                            rack=item,
                            targeted_u=target_u,
                            device=device_at_u,
                            port=None,
                            device_world_pos=dev_pos,
                            distance=dist,
                            hint_text=hint
                        )
                # Mode 2: Hardware Management Mode
                else:
                    hint = f"[E] Remove {device_at_u.hostname} from Rack | [R] Cabling Mode"
                    return InteractionTarget(
                        target_type="DEVICE",
                        interactable=item,
                        rack=item,
                        targeted_u=target_u,
                        device=device_at_u,
                        port=None,
                        device_world_pos=dev_pos,
                        distance=dist,
                        hint_text=hint
                    )

            else:
                # Empty U Slot
                if mode == "HARDWARE_MGMT":
                    hint = f"[E] Install Device at {item.rack_id} U{target_u}"
                else:
                    hint = f"{item.rack_id} [Slot U{target_u} Available] | [R] Hardware Mode"

                return InteractionTarget(
                    target_type="RACK",
                    interactable=item,
                    rack=item,
                    targeted_u=target_u,
                    device=None,
                    port=None,
                    distance=dist,
                    hint_text=hint
                )

        # If targeted item is the Workstation Desk
        elif isinstance(item, Desk):
            return InteractionTarget(
                target_type="DESK",
                interactable=item,
                distance=dist,
                hint_text="[E] Engineer Workstation CLI"
            )

        return InteractionTarget(
            target_type="GENERIC",
            interactable=item,
            distance=dist,
            hint_text=item.get_interaction_hint()
        )
