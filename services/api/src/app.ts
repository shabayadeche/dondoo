import cors from "@fastify/cors";
import Fastify from "fastify";
import { env } from "./lib/env.js";
import { caseRoutes } from "./modules/cases/routes.js";
import { healthRoutes } from "./routes/health.js";
import { metaRoutes } from "./routes/meta.js";

export function buildApp() {
  const app = Fastify({
    logger: env.NODE_ENV !== "test"
  });

  app.register(cors, {
    origin: env.ALLOW_ORIGIN === "*" ? true : env.ALLOW_ORIGIN
  });

  app.register(healthRoutes);
  app.register(metaRoutes, { prefix: "/api" });
  app.register(caseRoutes, { prefix: "/api" });

  return app;
}

