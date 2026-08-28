import { buildApp } from "./app.js";
import { env } from "./lib/env.js";

const app = buildApp();

app
  .listen({
    host: "0.0.0.0",
    port: env.PORT
  })
  .then(() => {
    app.log.info(`Clinical API listening on port ${env.PORT}`);
  })
  .catch((error) => {
    app.log.error(error);
    process.exit(1);
  });
