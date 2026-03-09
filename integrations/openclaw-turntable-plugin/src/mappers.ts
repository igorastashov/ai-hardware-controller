export interface ToolError {
  code: string;
  message: string;
  http_status: number;
  escalation_required?: boolean;
  details?: Record<string, unknown>;
}

export interface ToolSuccess {
  ok: true;
  result: Record<string, unknown>;
}

export interface ToolFailure {
  ok: false;
  error: ToolError;
}

export type ToolResponse = ToolSuccess | ToolFailure;

function asRecord(value: unknown): Record<string, unknown> | null {
  if (typeof value === "object" && value !== null && !Array.isArray(value)) {
    return value as Record<string, unknown>;
  }
  return null;
}

export function mapApiSuccess(raw: unknown): ToolSuccess | null {
  const payload = asRecord(raw);
  if (!payload || payload.ok !== true) {
    return null;
  }
  const result = asRecord(payload.result) ?? {};
  return {
    ok: true,
    result,
  };
}

export function mapApiFailure(raw: unknown, fallbackCode: string): ToolFailure {
  const payload = asRecord(raw);
  const error = payload ? asRecord(payload.error) : null;
  if (payload && payload.ok === false && error) {
    return {
      ok: false,
      error: {
        code: typeof error.code === "string" ? error.code : fallbackCode,
        message: typeof error.message === "string" ? error.message : "Unknown API error.",
        http_status: typeof error.http_status === "number" ? error.http_status : 500,
      },
    };
  }

  return {
    ok: false,
    error: {
      code: fallbackCode,
      message: "Unexpected non-contract response from turntable API.",
      http_status: 502,
      escalation_required: true,
      details: {
        raw,
      },
    },
  };
}

export function mapTransportFailure(
  code: "UPSTREAM_UNAVAILABLE" | "UPSTREAM_TIMEOUT" | "UPSTREAM_INVALID_RESPONSE",
  message: string,
): ToolFailure {
  const httpStatusByCode: Record<string, number> = {
    UPSTREAM_UNAVAILABLE: 503,
    UPSTREAM_TIMEOUT: 504,
    UPSTREAM_INVALID_RESPONSE: 502,
  };
  return {
    ok: false,
    error: {
      code,
      message,
      http_status: httpStatusByCode[code],
      escalation_required: true,
    },
  };
}

export function mapSideEffectDisabled(toolName: string): ToolFailure {
  return {
    ok: false,
    error: {
      code: "SIDE_EFFECT_TOOL_DISABLED",
      message: `Tool '${toolName}' is disabled until allowlist/side-effect policy enables it.`,
      http_status: 403,
    },
  };
}

export function mapPolicyError(
  code: "DEVICE_NOT_IDLE" | "ANTI_FLOOD_GUARD" | "IDEMPOTENT_MOVE_SKIPPED" | "VALIDATION_ERROR",
  message: string,
  details?: Record<string, unknown>,
): ToolFailure {
  const status = code === "VALIDATION_ERROR" ? 422 : 409;
  return {
    ok: false,
    error: {
      code,
      message,
      http_status: status,
      details,
    },
  };
}
