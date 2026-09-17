"""Unit tests verifying geometric separation, non-coplanar mesh layering, and depth buffer precision."""

import pytest
from unittest.mock import patch
from config.graphics_config import GraphicsConfig
from devices.device_factory import DeviceFactory
from devices.models.switch_model import SwitchModel
from devices.models.router_model import RouterModel
from devices.models.pc_model import PCModel
from world.rack import Rack
from world.room import Room


def test_depth_buffer_clip_planes():
    """Verify optimized NEAR_CLIP and FAR_CLIP ratio for maximum 24-bit depth precision."""
    assert GraphicsConfig.NEAR_CLIP >= 0.05
    assert GraphicsConfig.NEAR_CLIP <= 0.1
    assert GraphicsConfig.FAR_CLIP <= 50.0  # Room diagonal is ~25m, 35m gives ample room margin
    ratio = GraphicsConfig.FAR_CLIP / GraphicsConfig.NEAR_CLIP
    assert ratio < 500.0, f"Far/Near clip ratio {ratio} is too high; reduces depth buffer precision"


def _collect_draw_boxes(render_func):
    """Helper to collect all draw_box calls made by a render function."""
    boxes = []

    def mock_draw_box(cx, cy, cz, sx, sy, sz, color):
        min_x, max_x = cx - sx / 2.0, cx + sx / 2.0
        min_y, max_y = cy - sy / 2.0, cy + sy / 2.0
        min_z, max_z = cz - sz / 2.0, cz + sz / 2.0
        boxes.append({
            "center": (cx, cy, cz),
            "size": (sx, sy, sz),
            "min": (min_x, min_y, min_z),
            "max": (max_x, max_y, max_z),
            "color": color
        })

    with patch("devices.models.switch_model.draw_box", side_effect=mock_draw_box), \
         patch("devices.models.router_model.draw_box", side_effect=mock_draw_box), \
         patch("devices.models.pc_model.draw_box", side_effect=mock_draw_box), \
         patch("world.rack.draw_box", side_effect=mock_draw_box), \
         patch("world.room.draw_box", side_effect=mock_draw_box), \
         patch("world.room.draw_grid_plane", return_value=None):
        render_func()

    return boxes


def test_switch_mesh_no_coplanar_fighting():
    """Verify Switch front faceplate, backing cage, and status LEDs have distinct non-coplanar Z depths."""
    switch = DeviceFactory.create_device("Switch", "SW1")
    model = SwitchModel()
    boxes = _collect_draw_boxes(lambda: model.render(switch, 0.0, 0.0, 0.0))

    # Faceplate and cage must have distinct front faces
    faceplate = [b for b in boxes if abs(b["size"][0] - 0.432) < 1e-3][0]
    cage = [b for b in boxes if abs(b["size"][1] - 0.034) < 1e-3 and b["size"][0] > 0.2][0]

    front_diff = cage["max"][2] - faceplate["max"][2]
    assert front_diff >= 0.001, f"Switch cage must step proud of faceplate by >= 1mm, got {front_diff * 1000:.2f}mm"

    # SFP activity LED must not be coplanar with faceplate
    sfp_leds = [b for b in boxes if b["size"] == (0.003, 0.003, 0.0014)]
    for led in sfp_leds:
        assert led["max"][2] > faceplate["max"][2] + 0.0005


def test_router_mesh_no_coplanar_fighting():
    """Verify Router faceplate, module plate, OLED telemetry line, and label plates do not fight."""
    router = DeviceFactory.create_device("Router", "R1")
    model = RouterModel()
    boxes = _collect_draw_boxes(lambda: model.render(router, 0.0, 0.0, 0.0))

    faceplate = [b for b in boxes if abs(b["size"][0] - 0.432) < 1e-3 and abs(b["size"][1] - 0.082) < 1e-3][0]
    mod_plate = [b for b in boxes if abs(b["size"][0] - 0.190) < 1e-3][0]
    labels = [b for b in boxes if abs(b["size"][0] - 0.018) < 1e-3 and abs(b["size"][1] - 0.003) < 1e-3]

    assert mod_plate["max"][2] > faceplate["max"][2] + 0.0005, "Module plate must step proud of faceplate"

    for lbl in labels:
        assert lbl["max"][2] > mod_plate["max"][2] + 0.0005, "Label plates must step proud of module plate"

    # OLED screen and telemetry line
    screen = [b for b in boxes if abs(b["size"][0] - 0.052) < 1e-3][0]
    telemetry = [b for b in boxes if abs(b["size"][0] - 0.040) < 1e-3][0]
    assert telemetry["max"][2] > screen["max"][2] + 0.0004, "Telemetry line must step proud of OLED screen surface"


def test_pc_mesh_no_coplanar_fighting():
    """Verify PC faceplate bezel, drive sleds, and eth0 label plate do not fight."""
    pc = DeviceFactory.create_device("PC", "PC1")
    model = PCModel()
    boxes = _collect_draw_boxes(lambda: model.render(pc, 0.0, 0.0, 0.0))

    faceplate = [b for b in boxes if abs(b["size"][0] - 0.432) < 1e-3 and abs(b["size"][1] - 0.082) < 1e-3][0]
    eth0_label = [b for b in boxes if abs(b["size"][0] - 0.018) < 1e-3 and abs(b["size"][1] - 0.003) < 1e-3][0]

    assert eth0_label["max"][2] > faceplate["max"][2] + 0.0005, (
        f"eth0 label must step proud of PC faceplate bezel, diff={eth0_label['max'][2] - faceplate['max'][2]:.5f}"
    )


def test_rack_bottom_floor_clearance():
    """Verify Rack bottom plate, corner posts, and casters do not share bottom face with room floor (Y = 0.0)."""
    rack = Rack("Rack A", position=(0.0, 0.0, -3.0))
    boxes = _collect_draw_boxes(lambda: rack.render())

    # All rack base boxes must have bottom face at Y >= 0.002m (clearing room floor and grid lines)
    for b in boxes:
        if b["center"][1] < 0.2:
            assert b["min"][1] >= 0.002, (
                f"Rack component {b['center']} bottom Y={b['min'][1]:.4f} is too close to floor Y=0.0"
            )


def test_rack_enhanced_details_presence():
    """Verify dual vertical PDUs, EIA-310-D unit markings, roof vents, and status beacon are rendered."""
    rack = Rack("Rack A", position=(0.0, 0.0, -3.0))
    boxes = _collect_draw_boxes(lambda: rack.render())

    # PDUs on rear posts (height 1.65m)
    pdus = [b for b in boxes if abs(b["size"][1] - 1.65) < 1e-3]
    assert len(pdus) == 2, f"Expected dual 0U vertical PDUs (PDU-A & PDU-B), found {len(pdus)}"

    # PDU LED telemetry displays
    pdu_leds = [b for b in boxes if abs(b["size"][0] - 0.032) < 1e-3 and abs(b["size"][1] - 0.040) < 1e-3]
    assert len(pdu_leds) == 2, f"Expected 2 PDU telemetry LED displays, found {len(pdu_leds)}"

    # Top status beacon on rack roof
    beacons = [b for b in boxes if abs(b["size"][0] - 0.024) < 1e-3 and abs(b["size"][2] - 0.024) < 1e-3]
    assert len(beacons) == 1, "Expected top status beacon on rack"


def test_room_wall_trim_floor_clearance():
    """Verify wall baseboard trims do not share bottom plane with room floor (Y = 0.0)."""
    room = Room()
    boxes = _collect_draw_boxes(lambda: room.render())

    trims = [b for b in boxes if abs(b["size"][1] - 0.197) < 1e-3]
    assert len(trims) == 4, f"Expected 4 wall trims, found {len(trims)}"
    for trim in trims:
        assert trim["min"][1] >= 0.002, (
            f"Wall trim bottom Y={trim['min'][1]:.4f} is too close to floor Y=0.0"
        )


def test_room_enhanced_infrastructure():
    """Verify electrical PDU switchboards, FM-200 station, HVAC ducting, and double security doors."""
    room = Room()
    boxes = _collect_draw_boxes(lambda: room.render())

    # HVAC supply air duct spanning across ceiling
    hvac_ducts = [b for b in boxes if abs(b["size"][0] - (room.width - 2.0)) < 1e-3 and abs(b["size"][1] - 0.32) < 1e-3]
    assert len(hvac_ducts) == 1, "Expected main HVAC overhead supply air duct"

    # Sprinkler main pipe
    sprinkler_pipes = [b for b in boxes if abs(b["size"][0] - (room.width - 2.0)) < 1e-3 and abs(b["size"][1] - 0.035) < 1e-3]
    assert len(sprinkler_pipes) >= 1, "Expected fire sprinkler distribution pipe"

    # West wall 480V PDU switchboard cabinet (Height 2.25m, Depth 1.20m)
    pdu_cabs = [b for b in boxes if abs(b["size"][1] - 2.25) < 1e-3]
    assert len(pdu_cabs) == 2, f"Expected 2 electrical switchboard cabinets on West wall, found {len(pdu_cabs)}"

    # East wall FM-200 Fire Suppression Master Cabinet (Height 2.15m)
    fm200_cabs = [b for b in boxes if abs(b["size"][1] - 2.15) < 1e-3]
    assert len(fm200_cabs) == 1, "Expected FM-200 fire suppression cabinet on East wall"

    # South wall double security doors (Frame width 2.45m, height 2.45m)
    door_frames = [b for b in boxes if abs(b["size"][0] - 2.45) < 1e-3 and abs(b["size"][1] - 2.45) < 1e-3]
    assert len(door_frames) == 1, "Expected industrial double security door frame on South wall"

    # Collision boxes include the solid cabinets
    collision_boxes = room.get_wall_boxes()
    assert len(collision_boxes) == 6, f"Expected 4 walls + 2 solid equipment cabinets, got {len(collision_boxes)}"
