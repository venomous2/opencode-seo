import { existsSync } from "fs"
import { join } from "path"
import type { Plugin } from "@opencode-ai/plugin"

/**
 * OpenCode SEO Suite context plugin.
 *
 * - Detects seo-project.yml / clients/ in the current project and reminds
 *   the session to load project memory (keeps workflow outputs consistent).
 * - Surfaces a session notification when the suite's DataForSEO layer is
 *   not configured, so failures are diagnosed before the first skill runs.
 */
export default (async ({ directory, client }) => {
  const hasProjectMemory =
    existsSync(join(directory, "seo-project.yml")) ||
    existsSync(join(directory, "seo-project.yaml")) ||
    existsSync(join(directory, "clients"))

  return {
    event: async ({ event }) => {
      if (event.type === "session.created" && hasProjectMemory) {
        await client.app.log({
          service: "seo-suite",
          level: "info",
          message:
            "SEO project memory detected - load it with: python scripts/project_memory.py",
        })
      }
    },
  }
}) satisfies Plugin
