import { afterEach, describe, expect, it, vi } from "vitest";
import { loadPluginConfig } from "../src/config.js";
import { TurntableApiClient } from "../src/client.js";

class FakeResponse {
  private readonly body: unknown;
  constructor(body: unknown) {
    this.body = body;
  }
  async json(): Promise<unknown> {
    return this.body;
  }
}

describe("TurntableApiClient", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("returns payload on success", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => new FakeResponse({ ok: true, result: { status: "IDLE" } })));
    const client = new TurntableApiClient(loadPluginConfig({ baseUrl: "http://localhost:8000" }));
    const result = await client.post("/state");
    expect(result.ok).toBe(true);
  });

  it("maps unavailable transport failures", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        throw new Error("connection refused");
      }),
    );
    const client = new TurntableApiClient(
      loadPluginConfig({
        baseUrl: "http://localhost:8000",
        retry: { maxAttempts: 1, backoffMs: 50 },
      }),
    );
    const result = await client.post("/state");
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.failure.error.code).toBe("UPSTREAM_UNAVAILABLE");
    }
  });
});
