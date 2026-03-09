import {
  createTurntablePlugin,
  getToolSpecs,
  runPluginSmokeEntrypoint,
  type TurntablePlugin,
  type TurntableToolSpec,
} from "./src/plugin.js";
import { loadPluginConfig, type PluginConfig, type PluginConfigInput } from "./src/config.js";
import { mapApiFailure, mapApiSuccess, type ToolError, type ToolFailure, type ToolSuccess } from "./src/mappers.js";
import type { ToolName } from "./src/types.js";

interface RegisterToolSpec {
  name: string;
  description: string;
  parameters: {
    type: "object";
    properties: Record<string, unknown>;
    required?: string[];
    additionalProperties?: boolean;
  };
  execute: (_toolCallId: string, params?: Record<string, unknown>) => Promise<{
    content: Array<{ type: "text"; text: string }>;
  }>;
}

interface PluginApi {
  pluginConfig?: PluginConfigInput;
  registerTool?: (spec: RegisterToolSpec, options?: { optional?: boolean }) => void;
  registerAgentTool?: (spec: RegisterToolSpec, options?: { optional?: boolean }) => void;
}

const TOOL_DESCRIPTIONS: Record<ToolName, string> = {
  turntable_state: "Read turntable state and runtime health.",
  turntable_home: "Run homing once to establish reference frame.",
  turntable_move_to: "Move turntable to target rotation and tilt angles.",
  turntable_return_base: "Return turntable to base (software/power-on zero).",
  turntable_stop: "Emergency stop for active motion.",
  turntable_commissioning_first_run: "Execute first-run commissioning checks.",
};

function buildParameters(toolName: ToolName): RegisterToolSpec["parameters"] {
  if (toolName === "turntable_move_to") {
    return {
      type: "object",
      additionalProperties: false,
      required: ["rotation_deg", "tilt_deg"],
      properties: {
        rotation_deg: { type: "number" },
        tilt_deg: { type: "number" },
        rotate_speed_value: { type: "number" },
        tilt_speed_value: { type: "number" },
      },
    };
  }
  if (toolName === "turntable_commissioning_first_run") {
    return {
      type: "object",
      additionalProperties: false,
      properties: {
        max_capability: { type: "boolean" },
        include_busy_check: { type: "boolean" },
        include_stop_check: { type: "boolean" },
      },
    };
  }
  return {
    type: "object",
    additionalProperties: false,
    properties: {},
  };
}

function asToolText(payload: unknown): string {
  return JSON.stringify(payload);
}

function buildExternalToolNames(internalName: ToolName): string[] {
  const kebab = internalName.replaceAll("_", "-");
  if (kebab === internalName) {
    return [internalName];
  }
  // Register both variants for compatibility across OpenClaw tool-name validators.
  return [internalName, kebab];
}

export function register(api: PluginApi): void {
  const plugin = createTurntablePlugin(api.pluginConfig);
  const registerToolFn = api.registerTool ?? api.registerAgentTool;
  if (typeof registerToolFn !== "function") {
    const apiKeys = Object.keys(api as Record<string, unknown>);
    console.error(
      `[turntable-plugin] No tool registration function found. API keys: ${apiKeys.join(", ")}`,
    );
    return;
  }
  for (const spec of getToolSpecs()) {
    for (const externalName of buildExternalToolNames(spec.name)) {
      registerToolFn(
        {
          name: externalName,
          description: TOOL_DESCRIPTIONS[spec.name],
          parameters: buildParameters(spec.name),
          execute: async (_toolCallId, params) => {
            const result = await plugin.execute(spec.name, (params ?? {}) as Record<string, never>);
            return {
              content: [
                {
                  type: "text",
                  text: asToolText(result),
                },
              ],
            };
          },
        },
      );
    }
  }
}

export const activate = register;
export default register;

export {
  createTurntablePlugin, getToolSpecs, runPluginSmokeEntrypoint, type TurntablePlugin, type TurntableToolSpec,
  loadPluginConfig, type PluginConfig, type PluginConfigInput,
  mapApiFailure, mapApiSuccess, type ToolError, type ToolFailure, type ToolSuccess,
};
