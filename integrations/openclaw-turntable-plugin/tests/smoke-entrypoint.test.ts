import { describe, expect, it } from "vitest";
import { runPluginSmokeEntrypoint } from "../src/plugin.js";

describe("smoke entrypoint", () => {
  it("returns plugin metadata without network calls", () => {
    const result = runPluginSmokeEntrypoint();
    expect(result.ok).toBe(true);
    expect(result.result.plugin_id).toBe("turntable");
    expect(result.result.tool_count).toBe(6);
  });
});
