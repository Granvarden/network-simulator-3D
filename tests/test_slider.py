"""Unit tests for Slider widget."""

import pytest
import pygame
from ui.widgets.slider import Slider


def test_slider_value_clamping_and_step():
    slider = Slider(x=10, y=10, w=200, h=30, min_val=0.05, max_val=1.00, initial_val=0.35, step=0.01)

    assert slider.value == 0.35
    assert 0.0 <= slider.normalized <= 1.0

    # Test clamping upper
    slider.set_value(2.50)
    assert slider.value == 1.00
    assert slider.normalized == 1.0

    # Test clamping lower
    slider.set_value(-0.50)
    assert slider.value == 0.05
    assert slider.normalized == 0.0

    # Test step rounding
    slider.set_value(0.4234)
    assert slider.value == 0.42


def test_slider_callback():
    changed_val = None

    def on_change(val: float):
        nonlocal changed_val
        changed_val = val

    slider = Slider(x=10, y=10, w=200, h=30, min_val=0.1, max_val=1.0, initial_val=0.3, on_change=on_change)
    slider.set_value(0.65)
    assert changed_val == 0.65


def test_slider_mouse_wheel_scroll():
    slider = Slider(x=0, y=0, w=200, h=30, min_val=0.1, max_val=1.0, initial_val=0.4)
    slider.is_hovered = True

    # Mouse wheel up (button 4)
    wheel_up_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 4, "pos": (50, 15)})
    handled = slider.handle_event(wheel_up_event)
    assert handled
    assert slider.value == 0.45

    # Mouse wheel down (button 5)
    wheel_down_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 5, "pos": (50, 15)})
    handled = slider.handle_event(wheel_down_event)
    assert handled
    assert slider.value == 0.40
