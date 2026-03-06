"""Turntable integration configuration.

All hardware-related constants live here to avoid magic numbers in runtime code.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class AxisLimits:
    rotate_min_deg: float
    rotate_max_deg: float
    tilt_min_deg: float
    tilt_max_deg: float


@dataclass(frozen=True)
class BleTiming:
    command_gap_seconds: float
    connect_timeout_seconds: float
    discovery_scan_seconds: float
    protocol_probe_wait_seconds: float
    motion_poll_interval_seconds: float
    motion_poll_total_seconds: float


@dataclass(frozen=True)
class StateConfidenceLifecycle:
    on_start: str
    on_home_success: str
    on_reconnect: str
    high_requires_hardware_feedback: bool


@dataclass(frozen=True)
class MotionTimingModel:
    default_rotate_deg_per_s: float
    default_tilt_deg_per_s: float
    completion_safety_buffer_seconds: float
    max_command_duration_seconds: float


TURNTABLE_DEVICE_NAME_HINT = "REVO_DUAL_AXIS_TABLE"
TURNTABLE_PRIMARY_CHAR_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"
TURNTABLE_PROTOCOL_QUERY_TILT_ANGLE = "+QR,TILTANGLE;"
TURNTABLE_PROTOCOL_QUERY_ROTATE_ANGLE = "+QT,TURNANGLE;"

AXIS_LIMITS = AxisLimits(
    rotate_min_deg=-3600.0,
    rotate_max_deg=3600.0,
    tilt_min_deg=-30.0,
    tilt_max_deg=30.0,
)

BLE_TIMING = BleTiming(
    command_gap_seconds=0.10,
    connect_timeout_seconds=15.0,
    discovery_scan_seconds=8.0,
    protocol_probe_wait_seconds=3.0,
    motion_poll_interval_seconds=0.5,
    motion_poll_total_seconds=8.0,
)

STATE_CONFIDENCE = StateConfidenceLifecycle(
    on_start="LOW",
    on_home_success="MEDIUM",
    on_reconnect="LOW",
    high_requires_hardware_feedback=True,
)

MOTION_TIMING = MotionTimingModel(
    default_rotate_deg_per_s=12.0,
    default_tilt_deg_per_s=6.0,
    completion_safety_buffer_seconds=0.8,
    max_command_duration_seconds=20.0,
)
