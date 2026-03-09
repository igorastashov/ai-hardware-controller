import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { createTurntablePlugin } from "../src/plugin.js";

class FakeResponse {
  private readonly body: unknown;
  readonly status: number;
  constructor(body: unknown, status = 200) {
    this.body = body;
    this.status = status;
  }
  async json(): Promise<unknown> {
    return this.body;
  }
}

describe("plugin contract", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("blocks side-effect tools when allowlist is disabled", async () => {
    const plugin = createTurntablePlugin({ allowSideEffects: false });
    const response = await plugin.execute("turntable_move_to", {
      rotation_deg: 10,
      tilt_deg: 2,
    });
    expect(response.ok).toBe(false);
    if (!response.ok) {
      expect(response.error.code).toBe("SIDE_EFFECT_TOOL_DISABLED");
    }
  });

  it("enforces state pre-check before motion", async () => {
    const fetchMock = vi.fn(async (url: string) => {
      if (url.endsWith("/state")) {
        return new FakeResponse({ ok: true, result: { status: "BUSY", ble_connected: true } });
      }
      return new FakeResponse({ ok: true, result: {} });
    });
    vi.stubGlobal("fetch", fetchMock);

    const plugin = createTurntablePlugin({ allowSideEffects: true, commandGapMs: 50 });
    const response = await plugin.execute("turntable_move_to", {
      rotation_deg: 10,
      tilt_deg: 0,
    });
    expect(response.ok).toBe(false);
    if (!response.ok) {
      expect(response.error.code).toBe("DEVICE_NOT_IDLE");
    }
  });

  it("runs motion happy path", async () => {
    const fetchMock = vi.fn(async (url: string) => {
      if (url.endsWith("/state")) {
        return new FakeResponse({ ok: true, result: { status: "IDLE", ble_connected: true } });
      }
      if (url.endsWith("/move-to")) {
        return new FakeResponse({ ok: true, result: { executed: [], rotation_deg: 10, tilt_deg: 0 } });
      }
      return new FakeResponse({ ok: true, result: {} });
    });
    vi.stubGlobal("fetch", fetchMock);
    const plugin = createTurntablePlugin({ allowSideEffects: true, commandGapMs: 50 });

    const response = await plugin.execute("turntable_move_to", {
      rotation_deg: 10,
      tilt_deg: 0,
    });
    expect(response.ok).toBe(true);
  });

  it("enforces anti-flood guard", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => new FakeResponse({ ok: true, result: {} })));
    const plugin = createTurntablePlugin({ allowSideEffects: true, commandGapMs: 500 });
    const first = await plugin.execute("turntable_home");
    expect(first.ok).toBe(true);
    const second = await plugin.execute("turntable_stop");
    expect(second.ok).toBe(false);
    if (!second.ok) {
      expect(second.error.code).toBe("ANTI_FLOOD_GUARD");
    }
  });

  it("enforces idempotency window for duplicate move", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string) => {
        if (url.endsWith("/state")) {
          return new FakeResponse({ ok: true, result: { status: "IDLE", ble_connected: true } });
        }
        return new FakeResponse({ ok: true, result: { ack: "+OK;" } });
      }),
    );
    const plugin = createTurntablePlugin({
      allowSideEffects: true,
      commandGapMs: 100,
      idempotencyWindowMs: 1500,
    });

    const first = await plugin.execute("turntable_move_to", {
      rotation_deg: 90,
      tilt_deg: 10,
    });
    expect(first.ok).toBe(true);
    vi.advanceTimersByTime(200);
    const second = await plugin.execute("turntable_move_to", {
      rotation_deg: 90,
      tilt_deg: 10,
    });
    expect(second.ok).toBe(false);
    if (!second.ok) {
      expect(second.error.code).toBe("IDEMPOTENT_MOVE_SKIPPED");
    }
  });
});
