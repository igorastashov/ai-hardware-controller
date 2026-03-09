import type { PluginConfig } from "./config.js";
import { mapTransportFailure, type ToolFailure } from "./mappers.js";

interface HttpResultOk {
  ok: true;
  payload: unknown;
}

interface HttpResultErr {
  ok: false;
  failure: ToolFailure;
}

export type HttpResult = HttpResultOk | HttpResultErr;

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}

function joinUrl(baseUrl: string, path: string): string {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${baseUrl}${normalizedPath}`;
}

export class TurntableApiClient {
  private readonly config: PluginConfig;

  constructor(config: PluginConfig) {
    this.config = config;
  }

  async post(path: string, body?: Record<string, unknown>): Promise<HttpResult> {
    const url = joinUrl(this.config.baseUrl, path);
    let attempt = 0;

    while (attempt < this.config.retry.maxAttempts) {
      attempt += 1;
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), this.config.timeoutMs);

      try {
        const response = await fetch(url, {
          method: "POST",
          headers: {
            "content-type": "application/json",
          },
          body: body ? JSON.stringify(body) : undefined,
          signal: controller.signal,
        });
        clearTimeout(timeout);

        let payload: unknown = null;
        try {
          payload = await response.json();
        } catch (_err) {
          return {
            ok: false,
            failure: mapTransportFailure(
              "UPSTREAM_INVALID_RESPONSE",
              `Turntable API returned non-JSON payload for '${path}'.`,
            ),
          };
        }

        return {
          ok: true,
          payload,
        };
      } catch (err) {
        clearTimeout(timeout);
        const message = err instanceof Error ? err.message : "Unknown transport failure.";
        const timedOut = message.toLowerCase().includes("abort");
        const failure = timedOut
          ? mapTransportFailure("UPSTREAM_TIMEOUT", `Turntable API timeout on '${path}'.`)
          : mapTransportFailure("UPSTREAM_UNAVAILABLE", `Turntable API unavailable on '${path}': ${message}`);

        if (attempt >= this.config.retry.maxAttempts) {
          return {
            ok: false,
            failure,
          };
        }
        await sleep(this.config.retry.backoffMs * attempt);
      }
    }

    return {
      ok: false,
      failure: mapTransportFailure("UPSTREAM_UNAVAILABLE", `Turntable API unavailable on '${path}'.`),
    };
  }
}
