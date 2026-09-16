"""Player 3D AABB collision detection and smooth sliding resolution."""

from typing import List, Tuple


def point_in_aabb_expanded(
    px: float, pz: float, py: float,
    radius: float, height: float,
    box: Tuple[float, float, float, float, float, float]
) -> bool:
    """Check if player cylinder overlaps box."""
    min_x, min_y, min_z, max_x, max_y, max_z = box

    # Height check
    if py + height < min_y or py > max_y:
        return False

    # Closest point on 2D rectangle to player center (px, pz)
    closest_x = max(min_x, min(px, max_x))
    closest_z = max(min_z, min(pz, max_z))

    dx = px - closest_x
    dz = pz - closest_z
    return (dx * dx + dz * dz) < (radius * radius)


def check_player_collision(
    px: float, py: float, pz: float,
    radius: float, height: float,
    boxes: List[Tuple[float, float, float, float, float, float]]
) -> bool:
    """Returns True if player overlaps any obstacle box."""
    for box in boxes:
        if point_in_aabb_expanded(px, pz, py, radius, height, box):
            return True
    return False


def resolve_player_collision(
    old_x: float, old_z: float,
    new_x: float, new_z: float,
    py: float, radius: float, height: float,
    boxes: List[Tuple[float, float, float, float, float, float]]
) -> Tuple[float, float]:
    """Resolves player movement with smooth axial sliding along obstacle surfaces."""
    # Test new position directly
    if not check_player_collision(new_x, py, new_z, radius, height, boxes):
        return new_x, new_z

    # Try moving only along X (sliding along Z surface)
    can_x = not check_player_collision(new_x, py, old_z, radius, height, boxes)
    # Try moving only along Z (sliding along X surface)
    can_z = not check_player_collision(old_x, py, new_z, radius, height, boxes)

    if can_x and not can_z:
        return new_x, old_z
    elif can_z and not can_x:
        return old_x, new_z
    else:
        # Blocked in both directions
        return old_x, old_z
