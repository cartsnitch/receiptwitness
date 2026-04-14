import { createServer } from "node:http";
import { toNodeHandler } from "better-auth/node";
import { auth, pool } from "./auth.js";

const port = parseInt(process.env.PORT ?? "3001", 10);

const handler = toNodeHandler(auth);

const server = createServer(async (req, res) => {
  // Health check
  if (req.url === "/health" && req.method === "GET") {
    try {
      const client = await pool.connect();
      try {
        await Promise.race([
          client.query("SELECT 1"),
          new Promise((_, reject) => setTimeout(() => reject(new Error("DB timeout")), 2000)),
        ]);
      } finally {
        client.release();
      }
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ status: "ok", db: "connected" }));
    } catch {
      res.writeHead(503, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ status: "error", db: "unreachable" }));
    }
    return;
  }

  // All /auth/* routes handled by Better-Auth
  await handler(req, res);
});

server.listen(port, "0.0.0.0", () => {
  console.log(`CartSnitch auth service listening on port ${port}`);
});
