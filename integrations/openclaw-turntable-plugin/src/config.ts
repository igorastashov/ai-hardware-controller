import { URL } from "node:url";

export interface PluginConfigInput {
  baseUrl?: unknown;
  timeoutMs?: unknown;
  retry?: {
    maxAttempts?: unknown;
    backoffMs?: unknown;
  };
  safety?: {
    maxTiltDeg?: unknown;
    minRotateSpeed?: unknown;
    minTiltSpeed?: unknown;
  };
  allowSideEffects?: unknown;
  commandGapMs?: unknown;
  idempotencyWindowMs?: unknown;
}

export interface PluginConfig {
  baseUrl: string;
  timeoutMs: number;
  retry: {
    maxAttempts: number;
    backoffMs: number;
  };
  safety: {
    maxTiltDeg: number;
    minRotateSpeed: number;
    minTiltSpeed: number;
  };
  allowSideEffects: boolean;
  commandGapMs: number;
  idempotencyWindowMs: number;
}

const DEFAULT_CONFIG: PluginConfig = {
  baseUrl: "http://192.168.31.97:8000",
  timeoutMs: 30_000,
  retry: {
    maxAttempts: 2,
    backoffMs: 400,
  },
  safety: {
    maxTiltDeg: 30,
    minRotateSpeed: 18,
    minTiltSpeed: 40,
  },
  allowSideEffects: false,
  commandGapMs: 250,
  idempotencyWindowMs: 1_500,
};

function readNumber(raw: unknown, fieldName: string): number {
  if (typeof raw !== "number" || Number.isNaN(raw) || !Number.isFinite(raw)) {
    throw new Error(`${fieldName} must be a finite number.`);
  }
  return raw;
}

function readInteger(raw: unknown, fieldName: string): number {
  const value = readNumber(raw, fieldName);
  if (!Number.isInteger(value)) {
    throw new Error(`${fieldName} must be an integer.`);
  }
  return value;
}

function validateRange(value: number, min: number, max: number, fieldName: string): number {
  if (value < min || value > max) {
    throw new Error(`${fieldName} must be within [${min}, ${max}].`);
  }
  return value;
}

export function loadPluginConfig(input?: PluginConfigInput): PluginConfig {
  const raw = input ?? {};
  const config: PluginConfig = structuredClone(DEFAULT_CONFIG);

  if (raw.baseUrl !== undefined) {
    if (typeof raw.baseUrl !== "string") {
      throw new Error("baseUrl must be a string.");
    }
    const parsed = new URL(raw.baseUrl);
    if (!parsed.protocol.startsWith("http")) {
      throw new Error("baseUrl must use http/https protocol.");
    }
    config.baseUrl = parsed.toString().replace(/\/$/, "");
  }

  if (raw.timeoutMs !== undefined) {
    config.timeoutMs = validateRange(readInteger(raw.timeoutMs, "timeoutMs"), 1_000, 120_000, "timeoutMs");
  }

  if (raw.retry !== undefined) {
    if (typeof raw.retry !== "object" || raw.retry === null) {
      throw new Error("retry must be an object.");
    }
    if (raw.retry.maxAttempts !== undefined) {
      config.retry.maxAttempts = validateRange(
        readInteger(raw.retry.maxAttempts, "retry.maxAttempts"),
        1,
        5,
        "retry.maxAttempts",
      );
    }
    if (raw.retry.backoffMs !== undefined) {
      config.retry.backoffMs = validateRange(
        readInteger(raw.retry.backoffMs, "retry.backoffMs"),
        50,
        10_000,
        "retry.backoffMs",
      );
    }
  }

  if (raw.safety !== undefined) {
    if (typeof raw.safety !== "object" || raw.safety === null) {
      throw new Error("safety must be an object.");
    }
    if (raw.safety.maxTiltDeg !== undefined) {
      config.safety.maxTiltDeg = validateRange(
        readNumber(raw.safety.maxTiltDeg, "safety.maxTiltDeg"),
        1,
        30,
        "safety.maxTiltDeg",
      );
    }
    if (raw.safety.minRotateSpeed !== undefined) {
      config.safety.minRotateSpeed = validateRange(
        readNumber(raw.safety.minRotateSpeed, "safety.minRotateSpeed"),
        1,
        90,
        "safety.minRotateSpeed",
      );
    }
    if (raw.safety.minTiltSpeed !== undefined) {
      config.safety.minTiltSpeed = validateRange(
        readNumber(raw.safety.minTiltSpeed, "safety.minTiltSpeed"),
        1,
        90,
        "safety.minTiltSpeed",
      );
    }
  }

  if (raw.allowSideEffects !== undefined) {
    if (typeof raw.allowSideEffects !== "boolean") {
      throw new Error("allowSideEffects must be boolean.");
    }
    config.allowSideEffects = raw.allowSideEffects;
  }

  if (raw.commandGapMs !== undefined) {
    config.commandGapMs = validateRange(
      readInteger(raw.commandGapMs, "commandGapMs"),
      50,
      5_000,
      "commandGapMs",
    );
  }

  if (raw.idempotencyWindowMs !== undefined) {
    config.idempotencyWindowMs = validateRange(
      readInteger(raw.idempotencyWindowMs, "idempotencyWindowMs"),
      100,
      10_000,
      "idempotencyWindowMs",
    );
  }

  return config;
}
