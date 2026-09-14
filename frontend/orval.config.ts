import { defineConfig } from "orval";

/**
 * Generates TypeScript types + typed fetch functions from ../openapi.yaml
 * (the backend contract the frontend expects — see that file's `info`
 * section) into src/api/generated/.
 *
 * src/api/client.ts wraps the generated fetch functions (unwrapping the
 * response and turning error envelopes into ApiError), and src/types
 * re-exports the generated model types, so neither can drift from
 * openapi.yaml. `baseUrl: "/api"` matches `servers` in the contract; the
 * Vite dev server proxies that prefix to the FastAPI backend (vite.config.ts).
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
