import { appConfig } from "@phd-ass/config";
import { colonoscopyWorkflowSteps, dashboardSnapshot, workflowStepsByProcedure } from "@phd-ass/domain";
import type { FastifyPluginAsync } from "fastify";

export const metaRoutes: FastifyPluginAsync = async (app) => {
  app.get("/meta", async () => {
    return {
      appName: appConfig.appName,
      odooRecommendedModule: appConfig.odooRecommendedModule,
      odooRecommendedModuleLabel: appConfig.odooRecommendedModuleLabel,
      workflowSteps: colonoscopyWorkflowSteps,
      workflowStepsByProcedure,
      dashboardSnapshot
    };
  });
};
