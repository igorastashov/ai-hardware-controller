import { runPluginSmokeEntrypoint } from "./plugin.js";

function main(): number {
  const result = runPluginSmokeEntrypoint();
  process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
  return result.ok ? 0 : 1;
}

process.exitCode = main();
