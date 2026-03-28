import { createServer } from "node:http";
import { toNodeHandler } from "better-auth/node";
import { auth } from "./auth.js";

const port = parseInt(process.env.PORT ?? "3001", 10);

const handler = toNodeHandler(auth);

const server = createServer(async (req, res) => {
  // Health check
  if (req.url === "/health" && req.method === "GET") {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ status: "ok" }));
    return;
  }

  // All /auth/* routes handled by Better-Auth
  await handler(req, res);
});

server.listen(port, "0.0.0.0", () => {
  console.log(`CartSnitch auth service listening on port ${port}`);
});
