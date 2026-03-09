import { describe, expect, it } from "vitest";
import { loadPluginConfig } from "../src/config.js";

describe("loadPluginConfig", () => {
  it("loads defaults", () => {
    const cfg = loadPluginConfig();
    expect(cfg.baseUrl).toBe("http://192.168.31.97:8000");
    expect(cfg.allowSideEffects).toBe(false);
    expect(cfg.retry.maxAttempts).toBe(2);
  });

  it("accepts valid overrides", () => {
    const cfg = loadPluginConfig({
      baseUrl: "http://127.0.0.1:18000/",
      timeoutMs: 5000,
      allowSideEffects: true,
      retry: { maxAttempts: 3, backoffMs: 100 },
      safety: { maxTiltDeg: 20, minRotateSpeed: 18, minTiltSpeed: 40 },
      commandGapMs: 300,
      idempotencyWindowMs: 2000,
    });
    expect(cfg.baseUrl).toBe("http://127.0.0.1:18000");
    expect(cfg.timeoutMs).toBe(5000);
    expect(cfg.allowSideEffects).toBe(true);
    expect(cfg.commandGapMs).toBe(300);
  });

  it("rejects invalid ranges", () => {
    expect(() => loadPluginConfig({ timeoutMs: 10 })).toThrow("timeoutMs");
    expect(() => loadPluginConfig({ safety: { maxTiltDeg: 40 } })).toThrow("safety.maxTiltDeg");
    expect(() => loadPluginConfig({ retry: { maxAttempts: 10 } })).toThrow("retry.maxAttempts");
  });
});
