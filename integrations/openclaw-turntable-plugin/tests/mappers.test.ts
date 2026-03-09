import { describe, expect, it } from "vitest";
import { mapApiFailure, mapApiSuccess, mapTransportFailure } from "../src/mappers.js";

describe("mappers", () => {
  it("maps success payload", () => {
    const mapped = mapApiSuccess({ ok: true, result: { x: 1 } });
    expect(mapped).toEqual({ ok: true, result: { x: 1 } });
  });

  it("maps contract failure payload", () => {
    const mapped = mapApiFailure(
      { ok: false, error: { code: "DEVICE_BUSY", message: "busy", http_status: 409 } },
      "MOVE_FAILED",
    );
    expect(mapped.ok).toBe(false);
    if (!mapped.ok) {
      expect(mapped.error.code).toBe("DEVICE_BUSY");
      expect(mapped.error.http_status).toBe(409);
    }
  });

  it("maps transport failure", () => {
    const mapped = mapTransportFailure("UPSTREAM_TIMEOUT", "timed out");
    expect(mapped.ok).toBe(false);
    if (!mapped.ok) {
      expect(mapped.error.http_status).toBe(504);
      expect(mapped.error.escalation_required).toBe(true);
    }
  });
});
