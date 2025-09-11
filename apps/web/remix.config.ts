import type { RemixConfig } from "@remix-run/dev";

export default {
  future: {
    v3_fetcherPersist: true,
    v3_relativeSplatPath: true,
    v3_throwAbortReason: true,
  },
  serverModuleFormat: "esm",
  ignoredRouteFiles: ["**/.*"],
} satisfies RemixConfig;
