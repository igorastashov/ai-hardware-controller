export type ToolName =
  | "turntable_state"
  | "turntable_home"
  | "turntable_move_to"
  | "turntable_return_base"
  | "turntable_stop"
  | "turntable_commissioning_first_run";

export type JsonValue =
  | null
  | string
  | number
  | boolean
  | JsonValue[]
  | { [key: string]: JsonValue };

export type ToolInput = Record<string, JsonValue>;

export interface TurntableStateResult {
  rotation_deg: number;
  tilt_deg: number;
  status: string;
  ble_connected: boolean;
  zero_calibrated: boolean;
  reference_frame: string;
  last_error_code?: string | null;
  last_error_message?: string | null;
}
