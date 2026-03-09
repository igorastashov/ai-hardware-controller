import { loadPluginConfig, type PluginConfig, type PluginConfigInput } from "./config.js";
import { TurntableApiClient } from "./client.js";
import {
  mapApiFailure,
  mapApiSuccess,
  mapPolicyError,
  mapSideEffectDisabled,
  type ToolFailure,
  type ToolResponse,
} from "./mappers.js";
import type { ToolInput, ToolName, TurntableStateResult } from "./types.js";

export interface TurntableToolSpec {
  name: ToolName;
  sideEffect: boolean;
  optional?: boolean;
}

export interface TurntablePlugin {
  id: string;
  config: PluginConfig;
  tools: TurntableToolSpec[];
  execute: (toolName: ToolName, input?: ToolInput) => Promise<ToolResponse>;
}

interface MotionFingerprint {
  rotation_deg: number;
  tilt_deg: number;
  rotate_speed_value?: number;
  tilt_speed_value?: number;
}

const TOOL_SPECS: TurntableToolSpec[] = [
  { name: "turntable_state", sideEffect: false },
  { name: "turntable_home", sideEffect: true },
  { name: "turntable_move_to", sideEffect: true },
  { name: "turntable_return_base", sideEffect: true },
  { name: "turntable_stop", sideEffect: true },
  { name: "turntable_commissioning_first_run", sideEffect: true, optional: true },
];

export function getToolSpecs(): TurntableToolSpec[] {
  return [...TOOL_SPECS];
}

function isSideEffectTool(toolName: ToolName): boolean {
  return TOOL_SPECS.some((item) => item.name === toolName && item.sideEffect);
}

function nowMs(): number {
  return Date.now();
}

function asNumber(value: unknown): number | null {
  if (typeof value !== "number" || Number.isNaN(value) || !Number.isFinite(value)) {
    return null;
  }
  return value;
}

function parseMoveInput(input: ToolInput | undefined): MotionFingerprint | ToolFailure {
  const safe = input ?? {};
  const rotation = asNumber(safe.rotation_deg);
  const tilt = asNumber(safe.tilt_deg);
  if (rotation === null || tilt === null) {
    return mapPolicyError("VALIDATION_ERROR", "rotation_deg and tilt_deg must be finite numbers.");
  }

  let rotateSpeed: number | undefined;
  if (safe.rotate_speed_value !== undefined) {
    const value = asNumber(safe.rotate_speed_value);
    if (value === null) {
      return mapPolicyError("VALIDATION_ERROR", "rotate_speed_value must be a finite number.");
    }
    rotateSpeed = value;
  }

  let tiltSpeed: number | undefined;
  if (safe.tilt_speed_value !== undefined) {
    const value = asNumber(safe.tilt_speed_value);
    if (value === null) {
      return mapPolicyError("VALIDATION_ERROR", "tilt_speed_value must be a finite number.");
    }
    tiltSpeed = value;
  }

  return {
    rotation_deg: rotation,
    tilt_deg: tilt,
    rotate_speed_value: rotateSpeed,
    tilt_speed_value: tiltSpeed,
  };
}

function validateMoveSafety(config: PluginConfig, payload: MotionFingerprint): ToolFailure | null {
  if (Math.abs(payload.tilt_deg) > config.safety.maxTiltDeg) {
    return mapPolicyError(
      "VALIDATION_ERROR",
      `Tilt must be within [-${config.safety.maxTiltDeg}, ${config.safety.maxTiltDeg}].`,
    );
  }
  if (payload.rotate_speed_value !== undefined && payload.rotate_speed_value < config.safety.minRotateSpeed) {
    return mapPolicyError(
      "VALIDATION_ERROR",
      `rotate_speed_value must be >= ${config.safety.minRotateSpeed}.`,
    );
  }
  if (payload.tilt_speed_value !== undefined && payload.tilt_speed_value < config.safety.minTiltSpeed) {
    return mapPolicyError(
      "VALIDATION_ERROR",
      `tilt_speed_value must be >= ${config.safety.minTiltSpeed}.`,
    );
  }
  return null;
}

function sameMotion(a: MotionFingerprint | null, b: MotionFingerprint): boolean {
  if (!a) {
    return false;
  }
  return (
    a.rotation_deg === b.rotation_deg &&
    a.tilt_deg === b.tilt_deg &&
    (a.rotate_speed_value ?? null) === (b.rotate_speed_value ?? null) &&
    (a.tilt_speed_value ?? null) === (b.tilt_speed_value ?? null)
  );
}

export function createTurntablePlugin(rawConfig?: PluginConfigInput): TurntablePlugin {
  const config = loadPluginConfig(rawConfig);
  const client = new TurntableApiClient(config);

  let lastSideEffectAt = 0;
  let lastMotion: MotionFingerprint | null = null;
  let lastMotionAt = 0;
  let motionInFlight = false;

  async function call(path: string, fallbackCode: string, body?: Record<string, unknown>): Promise<ToolResponse> {
    const http = await client.post(path, body);
    if (!http.ok) {
      return http.failure;
    }
    return mapApiSuccess(http.payload) ?? mapApiFailure(http.payload, fallbackCode);
  }

  async function safeStop(reason: string): Promise<ToolFailure> {
    const stop = await call("/stop", "STOP_FAILED");
    return mapPolicyError("DEVICE_NOT_IDLE", reason, {
      stop_attempted: true,
      stop_response: stop,
      escalation_required: true,
    });
  }

  function enforceSideEffectPolicy(toolName: ToolName): ToolFailure | null {
    if (!isSideEffectTool(toolName)) {
      return null;
    }
    if (!config.allowSideEffects) {
      return mapSideEffectDisabled(toolName);
    }
    const elapsed = nowMs() - lastSideEffectAt;
    if (elapsed < config.commandGapMs) {
      return mapPolicyError("ANTI_FLOOD_GUARD", "Command gap guard blocked side-effect tool call.", {
        elapsed_ms: elapsed,
        required_gap_ms: config.commandGapMs,
      });
    }
    return null;
  }

  async function execute(toolName: ToolName, input?: ToolInput): Promise<ToolResponse> {
    const sideEffectPolicyError = enforceSideEffectPolicy(toolName);
    if (sideEffectPolicyError) {
      return sideEffectPolicyError;
    }

    switch (toolName) {
      case "turntable_state": {
        return call("/state", "STATE_FAILED");
      }
      case "turntable_home": {
        lastSideEffectAt = nowMs();
        return call("/home", "HOME_FAILED");
      }
      case "turntable_return_base": {
        lastSideEffectAt = nowMs();
        return call("/return-base", "RETURN_BASE_FAILED");
      }
      case "turntable_stop": {
        lastSideEffectAt = nowMs();
        motionInFlight = false;
        return call("/stop", "STOP_FAILED");
      }
      case "turntable_commissioning_first_run": {
        lastSideEffectAt = nowMs();
        const body = {
          max_capability: input?.max_capability ?? true,
          include_busy_check: input?.include_busy_check ?? true,
          include_stop_check: input?.include_stop_check ?? true,
        };
        return call("/commissioning/first-run", "COMMISSIONING_FAILED", body);
      }
      case "turntable_move_to": {
        if (motionInFlight) {
          return mapPolicyError("DEVICE_NOT_IDLE", "Motion command rejected while another motion is active.");
        }
        const parsed = parseMoveInput(input);
        if ("ok" in parsed) {
          return parsed;
        }
        const safetyError = validateMoveSafety(config, parsed);
        if (safetyError) {
          return safetyError;
        }

        const elapsedSinceSameMotion = nowMs() - lastMotionAt;
        if (sameMotion(lastMotion, parsed) && elapsedSinceSameMotion < config.idempotencyWindowMs) {
          return mapPolicyError(
            "IDEMPOTENT_MOVE_SKIPPED",
            "Identical motion request skipped in idempotency window.",
            {
              window_ms: config.idempotencyWindowMs,
              elapsed_ms: elapsedSinceSameMotion,
            },
          );
        }

        const preState = await call("/state", "STATE_FAILED");
        if (!preState.ok) {
          return safeStop("State pre-check failed before motion.");
        }
        const preStateResult = preState.result as unknown as Partial<TurntableStateResult>;
        const status = String(preStateResult.status ?? "");
        if (status !== "IDLE") {
          return mapPolicyError("DEVICE_NOT_IDLE", `Motion blocked: runtime status is '${status}'.`, {
            pre_state: preState.result,
          });
        }

        motionInFlight = true;
        lastSideEffectAt = nowMs();
        lastMotion = parsed;
        lastMotionAt = nowMs();
        const move = await call("/move-to", "MOVE_FAILED", parsed as unknown as Record<string, unknown>);
        motionInFlight = false;
        if (!move.ok) {
          return safeStop("Motion command failed or ambiguous state detected.");
        }
        return move;
      }
      default: {
        return mapPolicyError("VALIDATION_ERROR", `Unknown tool '${toolName}'.`);
      }
    }
  }

  return {
    id: "turntable",
    config,
    tools: getToolSpecs(),
    execute,
  };
}

export function runPluginSmokeEntrypoint(rawConfig?: PluginConfigInput): { ok: boolean; result: Record<string, unknown> } {
  const plugin = createTurntablePlugin(rawConfig);
  return {
    ok: true,
    result: {
      plugin_id: plugin.id,
      tool_count: plugin.tools.length,
      side_effect_tools: plugin.tools.filter((item) => item.sideEffect).map((item) => item.name),
      config: plugin.config,
    },
  };
}
