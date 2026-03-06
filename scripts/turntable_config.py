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
    connect_retry_attempts: int
    connect_retry_delay_seconds: float
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
    rotate_start_delay_seconds: float
    tilt_start_delay_seconds: float
    completion_safety_buffer_seconds: float
    max_command_duration_seconds: float


@dataclass(frozen=True)
class SpeedCommandBounds:
    rotate_min_observed_ok: float
    rotate_max_observed_ok: float
    tilt_min_observed_ok: float
    tilt_max_observed_ok: float


TURNTABLE_DEVICE_NAME_HINT = "REVO_DUAL_AXIS_TABLE"
TURNTABLE_PRIMARY_CHAR_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"
TURNTABLE_PROTOCOL_QUERY_TILT_ANGLE = "+QR,TILTANGLE;"
TURNTABLE_PROTOCOL_QUERY_ROTATE_ANGLE = "+QT,TURNANGLE;"
TURNTABLE_PROTOCOL_QUERY_TILT_SPEED = "+QR,TILTSPEED;"
TURNTABLE_PROTOCOL_QUERY_ROTATE_SPEED = "+QT,TURNSPEED;"

AXIS_LIMITS = AxisLimits(
    rotate_min_deg=-3600.0,
    rotate_max_deg=3600.0,
    tilt_min_deg=-30.0,
    tilt_max_deg=30.0,
)

BLE_TIMING = BleTiming(
    command_gap_seconds=0.10,
    connect_timeout_seconds=15.0,
    connect_retry_attempts=3,
    connect_retry_delay_seconds=1.0,
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
    # Calibrated from manual observations (2026-03-06), conservative values.
    default_rotate_deg_per_s=10.5,
    default_tilt_deg_per_s=3.7,
    rotate_start_delay_seconds=2.5,
    tilt_start_delay_seconds=1.8,
    completion_safety_buffer_seconds=1.0,
    max_command_duration_seconds=20.0,
)

SPEED_BOUNDS = SpeedCommandBounds(
    rotate_min_observed_ok=18.0,
    rotate_max_observed_ok=90.0,
    tilt_min_observed_ok=40.0,
    tilt_max_observed_ok=90.0,
)
