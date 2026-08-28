import { caseSummarySchema, followUpTaskSchema, startCaseSchema } from "@phd-ass/domain";
import type { FastifyPluginAsync } from "fastify";
import { env } from "../../lib/env.js";
import { odooDraftCaseSchema } from "./odoo-draft-schema.js";
import { listCases, listTasks, upsertOdooDraftCase } from "./repository.js";

export const caseRoutes: FastifyPluginAsync = async (app) => {
  app.get("/cases", async () => {
    return caseSummarySchema.array().parse(listCases());
  });

  app.get("/tasks", async () => {
    return followUpTaskSchema.array().parse(listTasks());
  });

  app.post("/cases", async (request, reply) => {
    const payload = startCaseSchema.parse(request.body);

    return reply.code(201).send({
      message: "Case payload validated. Persistence wiring comes next.",
      payload
    });
  });

  app.post("/odoo/cases/upsert-draft", async (request, reply) => {
    const providedHeader = request.headers["x-phd-ass-api-key"];
    const providedKey = Array.isArray(providedHeader) ? providedHeader[0] : providedHeader;

    if (env.ODOO_BRIDGE_API_KEY && providedKey !== env.ODOO_BRIDGE_API_KEY) {
      return reply.code(403).send({
        message: "Invalid bridge API key."
      });
    }

    const payload = odooDraftCaseSchema.parse(request.body);
    const stored = upsertOdooDraftCase(payload);

    return reply.code(200).send({
      status: "ok",
      externalCaseId: stored.external_case_id,
      payloadVersion: "odoo-draft-v1"
    });
  });
};
