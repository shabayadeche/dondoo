import net from "node:net";
import { execFileSync } from "node:child_process";

const distro = process.env.WSL_DISTRO ?? "Ubuntu";
const localHost = process.env.LOCAL_HOST ?? "127.0.0.1";
const localPort = Number(process.env.LOCAL_PORT ?? "8069");
const targetPort = Number(process.env.TARGET_PORT ?? "8069");
const ipTtlMs = Number(process.env.WSL_IP_TTL_MS ?? "15000");

let cachedIp = "";
let cachedAt = 0;

function log(message) {
  const timestamp = new Date().toISOString();
  process.stdout.write(`[${timestamp}] ${message}\n`);
}

function getWslIp(forceRefresh = false) {
  const now = Date.now();
  if (!forceRefresh && cachedIp && now - cachedAt < ipTtlMs) {
    return cachedIp;
  }

  const output = execFileSync(
    "wsl.exe",
    ["-d", distro, "-u", "root", "--", "bash", "-lc", "hostname -I"],
    {
      encoding: "utf8",
      stdio: ["ignore", "pipe", "pipe"]
    }
  );

  const nextIp = output.trim().split(/\s+/)[0];
  if (!nextIp) {
    throw new Error(`No IP address returned from distro ${distro}`);
  }

  cachedIp = nextIp;
  cachedAt = now;
  return cachedIp;
}

function connectUpstream(client, attempt = 1) {
  const targetHost = getWslIp(attempt > 1);
  const upstream = net.createConnection({
    host: targetHost,
    port: targetPort
  });

  const retryable = new Set(["ECONNREFUSED", "EHOSTUNREACH", "ETIMEDOUT"]);

  upstream.once("connect", () => {
    client.pipe(upstream);
    upstream.pipe(client);
  });

  upstream.once("error", (error) => {
    upstream.destroy();
    if (attempt === 1 && retryable.has(error.code)) {
      log(`Refresh WSL IP after ${error.code}; retrying connection`);
      connectUpstream(client, 2);
      return;
    }

    log(`Upstream connection failed: ${error.code ?? "UNKNOWN"} ${error.message}`);
    client.destroy(error);
  });

  client.once("close", () => {
    upstream.destroy();
  });
}

const server = net.createServer((client) => {
  client.on("error", () => {
    client.destroy();
  });

  connectUpstream(client);
});

server.on("error", (error) => {
  log(`Proxy failed: ${error.code ?? "UNKNOWN"} ${error.message}`);
  process.exit(1);
});

server.listen(localPort, localHost, () => {
  const targetHost = getWslIp(true);
  log(`Proxy listening on http://${localHost}:${localPort} -> ${targetHost}:${targetPort}`);
});

function shutdown(signal) {
  log(`Received ${signal}, shutting down proxy`);
  server.close(() => {
    process.exit(0);
  });
}

process.on("SIGINT", () => shutdown("SIGINT"));
process.on("SIGTERM", () => shutdown("SIGTERM"));
