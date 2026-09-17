import os
import sys
sys.path.insert(0, ".")
import pygame
from OpenGL.GL import *
from config.game_config import GameConfig
from config.graphics_config import GraphicsConfig
from cli.cli_engine import CLIEngine
from devices.device_factory import DeviceFactory
from ui.terminal import TerminalUI
from rendering.ui_renderer import UIRenderer

def test_render_terminal():
    pygame.init()
    pygame.font.init()

    # 1920x1080 Full Screen Simulation
    w, h = 1920, 1080
    screen = pygame.display.set_mode((w, h), pygame.OPENGL | pygame.DOUBLEBUF)
    
    # Init OpenGL 2D ortho
    glDisable(GL_DEPTH_TEST)
    glDisable(GL_LIGHTING)
    glDisable(GL_CULL_FACE)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0.0, float(w), float(h), 0.0, -1.0, 1.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    engine = CLIEngine()
    router = DeviceFactory.create_device("Router", "R1")
    engine.attach_device(router)

    term = TerminalUI(cli_engine=engine, on_close=lambda: None, screen_w=w, screen_h=h)
    term.center_window(w, h)
    
    # 1. User Exec -> enable
    engine.active_session.input_buffer = "enable"
    engine.submit_command()

    # 2. Config mode -> interface
    engine.active_session.input_buffer = "conf t"
    engine.submit_command()
    engine.active_session.input_buffer = "int g0/1"
    engine.submit_command()

    # 3. Help ? in interface config mode
    engine.active_session.input_buffer = "?"
    engine.submit_command()

    # 4. Set IP address
    engine.active_session.input_buffer = "ip address 192.168.2.1 255.255.255.0"
    engine.submit_command()

    # 5. Ctrl+C in config mode exits back to privileged EXEC mode!
    engine.cancel_input()

    # 6. Show ip interface brief (must NOT contain Console!)
    engine.active_session.input_buffer = "sh ip int br"
    engine.submit_command()

    ui = UIRenderer()

    # Draw simulated 3D background with colored elements across the entire 1920x1080 frame
    glClearColor(0.18, 0.22, 0.28, 1.0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # Draw bright test bars at extreme edges to verify full backdrop coverage
    ui.draw_rect(0, 0, w, 24, (34, 197, 94)) # top bar
    ui.draw_rect(w - 60, 0, 60, h, (239, 68, 68)) # right extreme bar
    ui.draw_rect(0, h - 40, w, 40, (59, 130, 246)) # bottom extreme bar

    # Render terminal with screen_w=w, screen_h=h
    term.render(ui, screen_w=w, screen_h=h)
    pygame.display.flip()

    # Capture frame buffer
    glPixelStorei(GL_PACK_ALIGNMENT, 1)
    data = glReadPixels(0, 0, w, h, GL_RGB, GL_UNSIGNED_BYTE)
    surface = pygame.image.fromstring(data, (w, h), "RGB", True)

    out_dir = r"C:\Users\admin\.gemini\antigravity-ide\brain\582a192a-f9f4-4ab2-9a3a-77e4957961e5"
    out_path = os.path.join(out_dir, "terminal_fullscreen_fixed.png")
    pygame.image.save(surface, out_path)
    print("Saved full screenshot to:", out_path)

    # Save cropped view of the terminal itself
    crop_rect = pygame.Rect(int(term.x - 20), int(term.y - 20), int(term.w + 40), int(term.h + 40))
    cropped = surface.subsurface(crop_rect)
    zoom_path = os.path.join(out_dir, "terminal_zoom_fixed.png")
    pygame.image.save(cropped, zoom_path)
    print("Saved cropped zoom to:", zoom_path)
    pygame.quit()

if __name__ == "__main__":
    test_render_terminal()
