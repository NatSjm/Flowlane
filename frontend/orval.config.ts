import { defineConfig } from "orval";

/**
 * Generates TypeScript types + typed fetch functions from ../openapi.yaml
 * (the backend contract the frontend expects — see that file's `info`
 * section) into src/api/generated/.
 *
 * There's no real backend yet, so these generated fetch functions aren't
 * wired into the app — src/api/client.ts still implements the mock. They
 * exist so:
 *   1. the domain types in src/types (re-exported from src/api/generated/model)
 *      can never drift from openapi.yaml, and
 *   2. swapping the mock for the real backend later is "call these instead
 *      of the mock functions", not "write an HTTP client from scratch".
 *
 * Regenerate after editing ../openapi.yaml with `npm run generate:api`.
 */
export default defineConfig({
  flowlane: {
    input: {
      target: "../openapi.yaml",
    },
    output: {
      target: "src/api/generated/endpoints",
      schemas: "src/api/generated/model",
      mode: "tags-split",
      client: "fetch",
      baseUrl: "/api",
      clean: true,
      indexFiles: true,
    },
  },
});
