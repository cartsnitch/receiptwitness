import { createAuthClient } from "better-auth/react"
import type { BetterFetchPlugin } from "@better-fetch/fetch"

/**
 * Maps 'name' -> 'display_name' in register requests to match the API's RegisterRequest schema.
 */
const displayNameMapper: BetterFetchPlugin = {
  id: "display-name-mapper",
  name: "display-name-mapper",
  hooks: {
    onRequest: async (context) => {
      const url = typeof context.url === "string" ? context.url : context.url.pathname
      if (
        url.endsWith("/auth/register") &&
        context.method === "POST" &&
        context.body &&
        "name" in context.body
      ) {
        context.body = {
          ...context.body,
          display_name: context.body.name as string,
          name: undefined,
        }
      }
      return context
    },
  },
}

export const authClient = createAuthClient({
  baseURL: import.meta.env.VITE_AUTH_URL || "",
  basePath: "/auth",
  fetchPlugins: [displayNameMapper],
})

export const { useSession, signIn, signUp, signOut } = authClient
